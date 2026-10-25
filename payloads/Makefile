# Demo payloads for the SecureT30Sec entry_offset hijack (fw_emu.py --payload).
# Arm GNU Toolchain (arm-none-eabi). Build: make -C tools/surface-rt/payloads

AS = arm-none-eabi-as
OBJCOPY = arm-none-eabi-objcopy
ASFLAGS = -march=armv7-a

BINS = uart_stub.bin

all: $(BINS)

%.bin: %.S
	$(AS) $(ASFLAGS) $< -o $*.o
	$(OBJCOPY) -O binary $*.o $@

clean:
	rm -f *.o *.bin

.PHONY: all clean
