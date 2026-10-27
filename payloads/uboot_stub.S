@ Design-C loader stub for SecureT30Sec: boot U-Boot in place of the UEFI image.
@
@ Delivered by the first stage's unsigned pre-verification write (boot-chain.md, weakness 1): both NVDAUEFI image
@ entries (normal and watchdog-backup) point at this stub and UEFIDATA.load_address aims at the Pkcs7Verify entry,
@ so read_image_block writes the stub over the verify routine before the stage reaches its `bl Pkcs7Verify` — the
@ call then runs the stub. No genuine image, no signature. The stub disarms the stage's watchdog (armed before
@ every verification), loads stock U-Boot (SPL + proper) from its eMMC slot to the SPL load address (uboot_stub.h),
@ cleans the data cache so the image reaches DRAM, and hands the SPL to the AVP exactly as the APX path does: SPL
@ brings the clocks up and resets the A9 cleanly, so U-Boot proper starts from a fresh A9 instead of the state the
@ first stage left. The A9 then only parks until the SPL resets it.
@
@ The FN_* addresses are the first stage's own routines (securet30sec_functions.h, generated from the loader's
@ FUNCTIONS); ARM state throughout. The stub never returns, so clobbering lr and the verify routine is fine.
@
@ Built with -DBOOTTRACE (uboot_stub-boottrace.bin), the stub records the boot trace (boottrace.h): checkpoints
@ 1-3, an empty console log for an instrumented U-Boot to fill, and RCM with the watchdog armed instead of
@ disarmed, so the run ends in APX whatever happens after the hand-over; if the boot ROM boots on after the
@ watchdog reset, the stub, entered again, finds the trace and enters APX itself.
#include "securet30sec.h"
#include "securet30sec_functions.h"
#include "uboot_stub.h"
#include "boottrace.h"

    .macro checkpoint n
#ifdef BOOTTRACE
    ldr  r0, =BOOTTRACE_PROGRESS
    ldr  r1, =BOOTTRACE_MAGIC + \n
    str  r1, [r0]
#endif
    .endm

    @ u32 word sum of the U-Boot slot in memory, stored to reg
    .macro slot_sum reg
#ifdef BOOTTRACE
    ldr  r0, =UBOOT_DEST
    ldr  r1, =UBOOT_DEST + UBOOT_SIZE
    mov  r2, #0
1:  ldr  r3, [r0], #4
    add  r2, r2, r3
    cmp  r0, r1
    blo  1b
    ldr  r0, =\reg
    str  r2, [r0]
#endif
    .endm

    .arm
    .section .text
    .global _start
_start:
#ifdef BOOTTRACE
    @ Re-entered after the watchdog reset of a trace run (the boot ROM booted on despite RCM): keep the trace,
    @ mark it and enter APX through MAIN_RST
    ldr  r0, =PMC_RST_STATUS
    ldr  r1, [r0]
    and  r1, r1, #7
    cmp  r1, #PMC_RST_WATCHDOG
    bne  1f
    ldr  r0, =BOOTTRACE_PROGRESS
    ldr  r1, [r0]
    ldr  r2, =BOOTTRACE_MAGIC
    eor  r3, r1, r2
    lsrs r3, r3, #16
    bne  1f
    orr  r1, r1, #BOOTTRACE_VIA_WDT
    str  r1, [r0]
    ldr  r0, =PMC_SCRATCH0
    mov  r1, #PMC_SCRATCH0_RCM
    str  r1, [r0]
    ldr  r0, =PMC_CNTRL
    ldr  r1, [r0]
    orr  r1, r1, #PMC_CNTRL_MAIN_RST
    str  r1, [r0]
2:  b    2b
1:
#endif
    checkpoint 1                @ the stub runs in place of Pkcs7Verify
#ifdef BOOTTRACE
    ldr  r0, =PMC_SCRATCH0
    mov  r1, #PMC_SCRATCH0_RCM
    str  r1, [r0]
    mov  r1, #1                @ wdt_arm(wdt, start = 1, period): arm the watchdog, the end of every run
    ldr  r2, =BOOTTRACE_WDT_US
#else
    mov  r1, #0                 @ wdt_arm(wdt, start = 0, period): disarm the watchdog before the (slow) image read
    mov  r2, #0
#endif
    mov  r0, #0
    ldr  r4, =FN_wdt_arm
    blx  r4

    mov  r0, #UBOOT_DEVICE
    ldr  r1, =UBOOT_OFFSET
    ldr  r2, =UBOOT_SIZE
    ldr  r3, =UBOOT_DEST
    ldr  r4, =FN_emmc_read
    blx  r4                     @ emmc_read(device, byte offset, byte size, dest)
    slot_sum BOOTTRACE_SUM_READ @ emmc_read returns 0 whatever happened: check the bytes
    checkpoint 2                @ U-Boot is read

    mov  r0, #0
    ldr  r4, =FN_emmc_select_partition
    blx  r4                     @ access 0: back to the user area, as verify_ok does
    ldr  r4, =FN_dcache_clean_invalidate_all
    blx  r4
    ldr  r4, =FN_icache_invalidate_all
    blx  r4
    ldr  r4, =FN_tlb_bp_invalidate_all
    blx  r4
    ldr  r4, =FN_dcache_disable
    blx  r4
    ldr  r4, =FN_icache_disable
    blx  r4
    ldr  r4, =FN_mmu_disable
    blx  r4                     @ MMU off: the stub's own VA stays valid (flat DRAM at 0x80808xxx)

#ifdef BOOTTRACE
    ldr  r0, =BOOTTRACE_LOG     @ physical now; the stage's page table need not map it
    ldr  r1, =BOOTTRACE_LOG_MAGIC
    mov  r2, #0
    stm  r0, {r1, r2}           @ magic, length 0
#endif
    slot_sum BOOTTRACE_SUM_JUMP @ from DRAM, as the AVP will fetch it
    checkpoint 3               @ caches and MMU are off, about to start the AVP

    @ Start the SPL on the AVP (the dcache clean above put the image in DRAM for it). The AVP leaves reset still
    @ halted and only runs once the flow-controller halt is cleared, so the reset makes it restart at the vector
    @ instead of continuing in the first stage's halt loop.
    ldr  r0, =FLOW_HALT_COP_EVENTS
    ldr  r1, =FLOW_MODE_STOP
    str  r1, [r0]               @ keep the AVP halted
    dsb
    ldr  r0, =EVP_COP_RESET_VECTOR
    ldr  r1, =UBOOT_DEST
    str  r1, [r0]               @ AVP reset vector = SPL
    dsb
    ldr  r0, =CLK_RST_L_SET
    mov  r1, #COP_RESET_BIT
    str  r1, [r0]               @ assert COP reset
    dsb
    ldr  r0, =TIMERUS_CNTR_1US  @ wait ~10 us
    ldr  r1, [r0]
    add  r1, r1, #10
1:  ldr  r2, [r0]
    subs r2, r2, r1
    bmi  1b
    ldr  r0, =CLK_RST_L_CLR
    mov  r1, #COP_RESET_BIT
    str  r1, [r0]               @ deassert COP reset
    dsb
    ldr  r0, =FLOW_HALT_COP_EVENTS
    mov  r1, #FLOW_MODE_NONE
    str  r1, [r0]               @ release the halt: the AVP runs the SPL, which resets the A9
    dsb

2:  wfe                         @ park the A9; the SPL holds it in reset and restarts it at U-Boot proper
    b    2b
    .ltorg
