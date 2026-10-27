/*
 * Boot trace: how far a boot without a console got, read back in disk mode (docs/boot-chain.md). Shared by the
 * trace stub (payloads/uboot_stub.S), an instrumented U-Boot (KCFLAGS="-include boottrace.h") and the read-out
 * (diskmode/srt-boottrace). Plain integer #defines only: shell tools read them too.
 */
#ifndef BOOTTRACE_H
#define BOOTTRACE_H

/* Last checkpoint reached: BOOTTRACE_MAGIC | n. PMC_SCRATCH42: kept across the watchdog reset, not written by
 * the first stage, and outside the SCRATCH1..23 that U-Boot clears */
#define BOOTTRACE_PROGRESS      0x7000e544
#define BOOTTRACE_MAGIC         0x5b700000
/* Set in the progress register by the trace stub when it is re-entered after the watchdog reset with a trace
 * present: it then enters APX through MAIN_RST and leaves the trace as it is */
#define BOOTTRACE_VIA_WDT       0x100

/* u32 word sums over the U-Boot slot the stub read (uboot_stub.h), after the read with the caches on and after
 * the teardown with them off (what U-Boot fetches); PMC_SCRATCH40 and 39 */
#define BOOTTRACE_SUM_READ      0x7000e53c
#define BOOTTRACE_SUM_JUMP      0x7000e538

/* Console log in DRAM: u32 BOOTTRACE_LOG_MAGIC, u32 length, then the text; above the disk-mode kernel's mem= */
#define BOOTTRACE_LOG           0xf0000000
#define BOOTTRACE_LOG_SIZE      0x10000
#define BOOTTRACE_LOG_MAGIC     0x5b70106

/* The trace stub arms the first stage's watchdog with this period and RCM set, so every run ends in APX */
#define BOOTTRACE_WDT_US        30000000

#endif /* BOOTTRACE_H */
