# Surface RT platform notes (power management, Type Cover, main UEFI and monitor, Windows RT side)

Board: Tegra30 (T30), Cardhu-derived. Power: TI TPS659110 PMIC (`ti,tps65911`, I2C5 `0x2d`) and TPS62361 core
regulator (I2C5 `0x60`); the embedded controller (battery, charger) sits on the same bus at `0x0a`. Reference
material (ACPI tables, the TPS65911 data sheet, the Windows driver package, PMIC dumps) is under `data/`.

## Power management

### Rails and the shutdown path

| Rail | Regulator | Control |
|---|---|---|
| `vdd_cpu` | TPS65911 VDDCTRL (external FET controller) | assigned to the EN1 input (`EN1_SMPS_ASS` `0x46` bit 3): EN1 high → `VDDCtrl_OP` (`0x28`), EN1 low → `VDDCtrl_SR` (`0x29`), which is 0 (off) |
| `vdd_core` | TPS62361 | I2C only |

Linux powers off with TPS65911 `DEV_OFF` and restarts with `DEV_OFF_RST` (DEVCTRL `0x3F`, sys-off handlers in
`drivers/mfd/tps65910.c`); PMC `MAIN_RST` is the low-priority restart fallback. Both PMIC commands work, from
userspace and late in shutdown.

### PMIC state: firmware hand-over vs. running Linux

Full dumps: `data/pmic/tps65911-regs-firmware.txt` (start of the TPS65911 probe, after a long-press power-off) and
`tps65911-regs-linux.txt` (`i2cdump` under Linux). All differences (RTC left out) and the power-relevant registers
that agree:

| Reg | Firmware | Linux | Meaning |
|---|---|---|---|
| `0x28` VDDCTRL_OP | `0x27` | `0x23` | 1.05 V / 1.0 V (CPU voltage scaling) |
| `0x29` VDDCTRL_SR | `0x00` | `0x00` | `vdd_cpu` off while EN1 is low |
| `0x35` LDO6 | `0x11` | `0x10` | Linux switches LDO6 off |
| `0x3F` DEVCTRL | `0x96` | `0x96` | `PWR_OFF_SEQ`, `SR_CTL_I2C_SEL`, `DEV_ON`, `DEV_SLP` |
| `0x40` DEVCTRL2 | `0x76` | `0x76` | `DCDC_SLEEP_LVL`, SLEEP input active-low, `PWON_LP_OFF`, `PWON_LP_RST` |
| `0x41` SLEEP_KEEP_LDO_ON | `0xde` | `0x00` | firmware's sleep configuration, cleared by the regulator driver's probe |
| `0x42` SLEEP_KEEP_RES_ON | `0xc7` | `0xc0` | ditto (VIO/VDD1/VDD2 keep-on) |
| `0x43` SLEEP_SET_LDO_OFF | `0x21` | `0x00` | ditto |
| `0x44` SLEEP_SET_RES_OFF | `0x08` | `0x00` | ditto (`VDDCTRL_SETOFF`) |
| `0x46` EN1_SMPS_ASS | `0x08` | `0x08` | `vdd_cpu` under EN1 control, set by the firmware |
| `0x51` INT_MSK | `0xff` | `0xbf` | one PMIC interrupt unmasked by Linux |

PMIC GPIO2 (`0x62` = `0x87`: forced low in SLEEP, set high, reads high) shows the PMIC is ACTIVE while Linux runs.

## Type Cover

### Wiring

From the libre-tegra device tree (`tegra30-microsoft-surface-rt.dts`), working under Linux:

| Item | Value |
|---|---|
| Bus | I2C1 (`i2c@7000c000`, `lcd_ddc`), 400 kHz; shared with the sensor hub (HID, `0x28`) |
| Address | `0x00` (the general-call address; Linux's I2C core has a Surface RT/2 exception to accept it) |
| HID descriptor register | `0x0041` |
| Attach detect | GPIO S0, active high (cover attached) |
| Interrupt | GPIO O5, level low |
| Supplies | TPS65911 LDO3 `vdd_cover` 2.8 V, LDO1 `vddio_sensor` 1.8 V |

Linux drives it with the generic `i2c-hid` stack, no device-specific code: the cover sits under an
`i2c-hotplug-gpio` node, a pass-through I2C adapter that is added while S0 is high and removed while it is low.

### HID reports

The cover enumerates as `045E:079C`. Input reports from its report descriptor:

| ID | Collection | Input layout |
|---|---|---|
| 1 | Keyboard | modifiers (8 bits, usages `E0`–`E7`), then 10 key bytes (array, usages `00`–`91`); 12 bytes with the ID |
| 2 | Mouse (touchpad) | 5 buttons, 3 bits padding, relative X, Y, wheel, AC pan (8 bits each) |
| 3 | Consumer control | one 16-bit usage, `000`–`3FF` |
| 7 | Vendor page `FF05` | 2 bytes and 32 bytes; output reports of the same shape |

The keyboard report has no reserved byte after the modifiers and 10 key slots, so it is not the boot-keyboard
layout. The descriptor has no LED output report. The other HID-over-I2C devices on the board are the Atmel
touchscreen (`03EB:8207`, I2C2 `0x5b`) and the sensor hub (`045E:0798`).

U-Boot takes the cover as console input (`stdin` device `i2c-hid-kbd`) with `patches/u-boot/0002`–`0005`, the
same device-tree nodes as Linux. The keyboard driver polls and handles attach and detach while the console is
polled.

## The main UEFI and its secure monitor (`SurfaceRTUEFI.bin`)

A UEFI firmware volume built from NVIDIA's Cardhu code (`NvMainBoardsPkg/OemkS`). The SEC module `OemkSec` is the
secure monitor. Its SMC entry handles two services; anything else hangs:

- **2, L2 cache** (PL310): r1 selects enable / disable / write-back enable-disable / full-line-of-zeros — the
  `TZ_L2C310_*` operations Linux already uses.
- **5, power** (r1 = 1): r2 = 2 per-CPU power-down (L1 clean, leave SMP, SCU power status; CPU0 also syncs and
  disables the L2; ends in `wfe` until the flow controller power-gates the CPU). r2 = 0 is LP0 (CPU0 only; L2 off,
  code copied to IRAM, MMU off; sets the warm-boot scratch and EMC self-refresh).
- **Resume:** the monitor owns the CPU reset vector (EVP), restores its own state, and returns to the normal world
  at the CPU's parking-protocol mailbox page `+0x800` (SVC, IRQ/FIQ masked); no resume address is passed in a
  register. The mailboxes are `0x82000000 + (cpu + 1) × 0x1000`: `ProcessorId` at `+0`, `EntryPoint` at `+8`.
- **Parking loop** (installed into each mailbox page for boot and resume alike): checks `ProcessorId == MPIDR` CPU
  number and `EntryPoint != 0` before each `wfi`, clears `EntryPoint`, and jumps with `bx`. With `EntryPoint = 0` a
  resumed CPU parks there for good.

`ResetSystem` uses PMC `MAIN_RST` (never `DEV_OFF_RST`); shutdown clears the PMIC's power sequence and asserts
`DEV_OFF`. `NvSpiFlashDxe` holds the boot-flash status-register writes (unlock, /WP lock, and a permanent lock that
would make the 4 MiB read-only for good on a "P" part). The boot device comes from board straps or a fuse override; the update path writes
per boot device and can burn fuses, and update images are PKCS#7-verified.

## Windows RT side

From the ACPI tables and the driver package in `data/windows-drivers/`.

- FACP: hardware-reduced ACPI, Low Power S0 Idle (Connected Standby, no S3), no reset register. Shutdown and
  reboot therefore go through UEFI `ResetSystem`.
- PMIC device `\_SB.PMUD`, `_HID` `NVDAF241` (SSDT): I2C5 `0x2d` and `0x60`, interrupt `0x76` (GIC SPI 86). Driver
  `pmu.sys` (`pmu.inf`), NVIDIA "Tegra PMU Driver" 9.17.13.0888, built from NVIDIA's Cardhu PMU source (strings:
  "NVIDIA CARDHU PMU Driver", `Tps6591xInitDriverSettings`). Not yet analysed.
- Deep idle on Windows RT is NVIDIA's PEP (`nvpep.sys`, "NVIDIA Power Mgmt Controller"): strings name LP0 and LP2
  decisions, LP-cluster switching, LP0 wake sources, DVFS through the PMU driver, and its own LP0 resume code
  ("AVP warmboot code", "Core Warmboot Code", "LP0 iRAM code"). Connected Standby therefore uses LP0 on this board.
- Secure-monitor calls in the driver package: one `smc #0` stub in `nvpep.sys`, none in `pmu.sys` or
  `HalExtTegra2.dll`. Its three callers pass r0 = 5, r1 = 1: LP2 CPU power-gate (r2 = 2, r3 = 1 on CPUs other than
  0), cluster switch (r2 = 2; inference from FLOW_CLUSTER_CONTROL), LP0 (r2 = 0, r3 = 0; sets PMC_SCRATCH4
  bit 31). All branch on a "monitor present" byte; without it they run ARM equivalents of the monitor's code,
  which write the resume address into the CPU reset vector themselves. After wake-up, `FLOW_CPUn_CSR` is set to
  `0xC000`. The monitor itself is described above.
- AML touches the PMIC only in power resources (LDO switching, e.g. LDO5 `0x32` in `PRS1`) and for the RTC
  (`ACPI000E`); DEVCTRL, EN1 and VDDCTRL are left to the driver and the firmware.
- Secondary CPUs start through the ACPI parking protocol (MADT mailboxes); Linux uses
  `arch/arm/kernel/acpi_parking_protocol.c` with the mailboxes hardcoded.
