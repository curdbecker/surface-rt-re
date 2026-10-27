# Payloads for the SecureT30Sec hijacks. Arm GNU Toolchain (arm-none-eabi); the .S files go through the C
# preprocessor (gcc driver), so they include the shared headers. Build: make -C payloads
#
# The .bin files and securet30sec_functions.h are generated and committed, so the installer works without a
# toolchain; after changing a payload or the loader's FUNCTIONS: make -C payloads && git diff --exit-code payloads

CC = arm-none-eabi-gcc
OBJCOPY = arm-none-eabi-objcopy
CPPFLAGS = -I. -I..
ASFLAGS = -march=armv7-a

BINS = uart_stub.bin uboot_stub.bin uboot_stub-boottrace.bin

all: $(BINS)

# FN_<name> for each first-stage function in the loader's FUNCTIONS table
securet30sec_functions.h: ../securet30sec_loader.py
	PYTHONPATH=.. python3 -c 'import securet30sec_loader as s; print(s.function_defines(), end="")' > $@

STUB_DEPS = uboot_stub.h ../securet30sec.h ../boottrace.h securet30sec_functions.h
uboot_stub.o: $(STUB_DEPS)

# the stub recording the boot trace (uboot_stub.S)
uboot_stub-boottrace.o: uboot_stub.S $(STUB_DEPS)
	$(CC) $(CPPFLAGS) $(ASFLAGS) -DBOOTTRACE -c $< -o $@

%.o: %.S
	$(CC) $(CPPFLAGS) $(ASFLAGS) -c $< -o $@

%.bin: %.o
	$(OBJCOPY) -O binary $< $@

clean:
	rm -f *.o

.PHONY: all clean
