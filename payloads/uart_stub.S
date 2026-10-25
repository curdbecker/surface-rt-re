@ Demo payload for the SecureT30Sec entry_offset hijack: print a line on Tegra UARTA, then return.
@
@ The first stage verifies the signed image, then does bx r0 to load_address + uefidata.entry_offset. entry_offset
@ comes from the unsigned UEFIDATA block, so a payload placed in that block (and entry_offset pointed at it) runs
@ with the image signature valid. See tools/surface-rt/README.md and fw_emu.py --payload.
@
@ Position-independent (PC-relative string, MMIO base built with movw/movt). Enters in ARM state (bx to an even
@ address). On real hardware the UART must already be clocked and pinned, and a real payload would hand off to the
@ next stage rather than return; here it jumps to the emulator's phase-end sentinel so the run stops cleanly.
@ Keep branch targets local (no .global): a global target makes the assembler leave a relocation that objcopy of
@ the unlinked object cannot resolve, so the branch would fall back to branching to itself.
    .equ SENTINEL, 0xfffffff0
    .arm
    .section .text
    .global _start
_start:
    movw r1, #0x6000
    movt r1, #0x7000            @ r1 = UARTA base 0x70006000 (THR at +0, LSR at +0x14)
    adr  r2, msg
.Lchar:
    ldrb r3, [r2], #1
    cmp  r3, #0
    beq  .Ldone
.Lwait:
    ldr  r0, [r1, #0x14]        @ LSR
    tst  r0, #0x20             @ THRE: transmit holding register empty
    beq  .Lwait
    strb r3, [r1]              @ THR
    b    .Lchar
.Ldone:
    ldr  pc, =SENTINEL         @ hand back to the emulator; the run ends with reason "returned"
    .ltorg
msg:
    .asciz "SecureT30Sec -> payload: it works\r\n"
