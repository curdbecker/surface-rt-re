/*
 * Surface RT first stage (SecureT30Sec): its data structures and the eMMC NVDAUEFI layout they describe.
 *
 * Shared by the IDA loader (types and enums), the host-side installer (field offsets and values, through
 * securet30sec_loader.read_header) and the assembly payloads (the #defines; the C part is hidden from the
 * assembler by __ASSEMBLER__).
 */
#ifndef SECURET30SEC_H
#define SECURET30SEC_H

/* NVDAUEFI table: magic, and the step the first stage scans boot0/boot1 in for it */
#define NVDAUEFI_MAGIC                  "NVDAUEFI"
#define NVDAUEFI_TABLE_STEP             0x4000
#define UEFIDATA_TAG                    "UEFIDATA"

/* NVDAUEFI_ENTRY.device */
#define NVDAUEFI_DEVICE_BOOT_DEVICE     0           /* the boot device (SPI flash) */
#define NVDAUEFI_DEVICE_BOOT0           1
#define NVDAUEFI_DEVICE_BOOT1           2

/* NVDAUEFI_ENTRY.type, as far as identified */
#define NVDAUEFI_TYPE_BCT               0x01
#define NVDAUEFI_TYPE_TABLE             0x02
#define NVDAUEFI_TYPE_FIRST_STAGE       0x03
#define NVDAUEFI_TYPE_VAR_STORE         0x04
#define NVDAUEFI_TYPE_IMAGE             0x0b        /* UEFI image, normal copy */
#define NVDAUEFI_TYPE_IMAGE_BACKUP      0x0d        /* UEFI image used after a watchdog reset */
#define NVDAUEFI_TYPE_SIGNATURE         0x0e
#define NVDAUEFI_TYPE_SIGNATURE_BACKUP  0x10
#define NVDAUEFI_TYPE_UEFIDATA          0x11
#define NVDAUEFI_TYPE_EMPTY             0x13

#ifndef __ASSEMBLER__

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;
typedef u32 EFI_STATUS;             /* EDK2 status; high bit set = error (EFI_SUCCESS = 0) */

struct NVDA_BLOCK {                 /* NVDASPICERTIFICA / NVDASPISIGNATURE: name, length, DER */
    char name[16];
    u32 length;
};

struct NVDAUEFI_ENTRY {
    u32 type;                       /* NVDAUEFI_TYPE_* */
    u32 device;                     /* NVDAUEFI_DEVICE_* */
    u64 offset;
    u64 size;
    u64 load_address;
    u8 reserved[16];
};

struct NVDAUEFI_TABLE {             /* found at a NVDAUEFI_TABLE_STEP boundary of boot0/boot1 */
    char magic[8];                  /* NVDAUEFI_MAGIC */
    u32 unknown_08;
    u8 unknown_0c[0x20];
    u32 count;
    struct NVDAUEFI_ENTRY entries[20];
    u8 tail[0x10];
};

struct UEFIDATA_HEADER {            /* first 0x280 bytes of the UEFIDATA block (NVDAUEFI_TYPE_UEFIDATA) */
    u8 unknown_00[0x20];
    char tag[8];                    /* UEFIDATA_TAG */
    u32 unknown_28;
    u32 unknown_2c;
    u32 unknown_30;
    u32 unknown_34;
    u32 image_size;                 /* checked length, normal copy */
    u32 signature_size;
    u64 load_address;               /* shared by both copies */
    u64 entry_offset;               /* shared by both copies */
    u32 backup_image_size;          /* boot0 copy */
    u32 backup_signature_size;
    u64 backup_load_address;
    u8 unknown_60[0x220];
};

struct EMMC_GEOMETRY {
    u32 unknown_00;
    u32 unknown_04;
    u32 boot_size;
    u32 block_length;
    u32 capacity;
};

struct NVDAUEFI_SLOT {             /* one NVDAUEFI entry demultiplexed by type (fields from NVDAUEFI_ENTRY) */
    u64 offset;
    u64 size;
    u32 device;
    u32 pad;
};

struct NVDAUEFI_SLOT5 {            /* a demultiplexed entry that also carries a load address and a trailing word */
    u64 offset;
    u64 size;
    u32 device;
    u32 pad;
    u64 load_address;
    u64 extra;
};

struct NVDAUEFI_CTX {              /* parse_nvdauefi_table pivots the table by entry type into these fixed slots */
    struct NVDAUEFI_SLOT  bct;              /* NVDAUEFI_TYPE_BCT */
    struct NVDAUEFI_SLOT5 first_stage;      /* NVDAUEFI_TYPE_FIRST_STAGE */
    struct NVDAUEFI_SLOT  var_store;        /* NVDAUEFI_TYPE_VAR_STORE */
    struct NVDAUEFI_SLOT  nvdauefi_table;   /* NVDAUEFI_TYPE_TABLE */
    struct NVDAUEFI_SLOT  type_05;
    struct NVDAUEFI_SLOT  type_06;
    struct NVDAUEFI_SLOT  type_07;
    struct NVDAUEFI_SLOT  type_08;
    struct NVDAUEFI_SLOT  type_09;
    struct NVDAUEFI_SLOT  type_0a;
    struct NVDAUEFI_SLOT5 image;            /* NVDAUEFI_TYPE_IMAGE (boot1) */
    struct NVDAUEFI_SLOT5 type_0c;
    struct NVDAUEFI_SLOT  signature;        /* NVDAUEFI_TYPE_SIGNATURE (boot1) */
    struct NVDAUEFI_SLOT  type_0f;
    struct NVDAUEFI_SLOT5 image_backup;     /* NVDAUEFI_TYPE_IMAGE_BACKUP (boot0) */
    struct NVDAUEFI_SLOT  signature_backup; /* NVDAUEFI_TYPE_SIGNATURE_BACKUP (boot0) */
    struct NVDAUEFI_SLOT  uefidata;         /* NVDAUEFI_TYPE_UEFIDATA */
    struct NVDAUEFI_SLOT  empty_13;         /* NVDAUEFI_TYPE_EMPTY */
    struct NVDAUEFI_SLOT  type_14;
    struct NVDAUEFI_SLOT  type_15;
    struct NVDAUEFI_SLOT5 type_16;
    struct NVDAUEFI_SLOT  type_17;          /* type 0x17 is skipped by the parser; slot stays zero */
    struct NVDAUEFI_SLOT5 type_18;
    struct NVDAUEFI_SLOT  tail;
};

struct HEAP_CONTEXT {
    u8 unknown_00[0x20];
    u64 top;
    u64 floor;
};

typedef struct NVDA_BLOCK NVDA_BLOCK;
typedef struct NVDAUEFI_ENTRY NVDAUEFI_ENTRY;
typedef struct NVDAUEFI_TABLE NVDAUEFI_TABLE;
typedef struct UEFIDATA_HEADER UEFIDATA_HEADER;
typedef struct EMMC_GEOMETRY EMMC_GEOMETRY;
typedef struct NVDAUEFI_SLOT NVDAUEFI_SLOT;
typedef struct NVDAUEFI_SLOT5 NVDAUEFI_SLOT5;
typedef struct NVDAUEFI_CTX NVDAUEFI_CTX;
typedef struct HEAP_CONTEXT HEAP_CONTEXT;

#endif /* __ASSEMBLER__ */

#endif /* SECURET30SEC_H */
