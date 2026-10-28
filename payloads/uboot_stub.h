/*
 * The design-C loader stub's contract (uboot_stub.S): where it sits on the eMMC, where it expects U-Boot, and the
 * launch marker it leaves for U-Boot. The installer (srt_uboot.py) reads this header and writes to match, checking
 * it against the NVDAUEFI table; U-Boot's board code (board/microsoft/surface-rt/surface-rt.c) includes it.
 */
#ifndef UBOOT_STUB_H
#define UBOOT_STUB_H

#include "securet30sec.h"

/* The stub: on boot0, inside the region the table marks NVDAUEFI_TYPE_EMPTY */
#define STUB_OFFSET     0x1000

/* U-Boot (u-boot-dtb-tegra.bin: SPL + U-Boot proper): in the factory NVDAUEFI_TYPE_IMAGE_BACKUP slot on boot0,
 * read whole (bytes past the image land in RAM unused); boot1 keeps the factory image */
#define UBOOT_DEVICE    NVDAUEFI_DEVICE_BOOT0
#define UBOOT_OFFSET    0x50000
#define UBOOT_SIZE      0x1a0000

/* Launch-path marker: the stub writes LAUNCH_MAGIC to LAUNCH_MARKER on the eMMC cold-boot path; U-Boot's board
 * code reads and clears it (absent, i.e. RAM-loaded over APX -> fastboot). PMC_SCRATCH43 is in the always-on
 * domain, survives the warm resets of the hand-off, and is outside the scratch1..23 that SPL clears. */
#define LAUNCH_MARKER   0x7000e62c
#define LAUNCH_MAGIC    0x5e7b0001

/* The AVP (not the A9) starts U-Boot, at the SPL load address: CONFIG_SPL_TEXT_BASE, with U-Boot proper packed at
 * CONFIG_TEXT_BASE inside the same image. SPL then brings the clocks up and resets the A9 cleanly (spl.c). */
#define UBOOT_DEST      0x80108000

/* Restarting the AVP from the A9 (NVIDIA's tegra avp/nvavp drivers): halt it, point its reset vector at the SPL,
 * pulse its reset in the clock-and-reset controller, then release the flow-controller halt so it runs. */
#define FLOW_HALT_COP_EVENTS    0x60007004
#define FLOW_MODE_STOP          0x40000000      /* 2 << 29 */
#define FLOW_MODE_NONE          0x0
#define EVP_COP_RESET_VECTOR    0x6000f200
#define CLK_RST_L_SET           0x60006300      /* RST_DEVICES_L SET */
#define CLK_RST_L_CLR           0x60006304      /* RST_DEVICES_L CLR */
#define COP_RESET_BIT           0x2             /* PERIPH_ID_COP = bit 1 */
#define TIMERUS_CNTR_1US        0x60005010

/* Boot trace (-DBOOTTRACE): RCM in PMC_SCRATCH0 makes the boot ROM enter APX at the next reset; MAIN_RST is the
 * reset known to honour it */
#define PMC_CNTRL           0x7000e400
#define PMC_CNTRL_MAIN_RST  0x10
#define PMC_SCRATCH0        0x7000e450
#define PMC_RST_STATUS      0x7000e5b4
#define PMC_RST_WATCHDOG    1
#define PMC_SCRATCH0_RCM    2

#endif /* UBOOT_STUB_H */
