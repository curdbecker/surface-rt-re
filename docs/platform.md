# Surface RT platform notes (power management, Windows RT side)

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

### Reboot and power-off hang (root cause)

`tps65910_shutdown()` (`drivers/regulator/tps65910-regulator.c`) takes every registered rail off external control
during the driver shutdown phase. For `vdd_cpu` that clears `VDDCTRL_EN1`, the CPU rail drops, and the board hangs
before the PMIC power-off or restart command is sent. The PMIC stays on: black screen, recovery only with a long
press of the power button. With the hook disabled, `reboot` and `poweroff` both work.

`ti,regulator-ext-sleep-control = <1>` on `vddctrl` keeps the probe from clearing the firmware's EN1 assignment;
without it the probe would do the same as the shutdown hook.

Fix: `vendor/0002-…` adds the PMIC property `ti,keep-ext-sleep-control-on-shutdown` (binding, driver: the hook
returns early) and sets it for the Surface RT. With it, Linux keeps the EN1 assignment; the PMIC's `DEV_OFF_RST`
(restart) and `DEV_OFF` (power-off) end it along with everything else. Opt-in, because the hook does no harm where
removing the external control leaves the rail on (the data sheet's behaviour; Transformers, Nexus 7, Chagall with
Android bootloaders). Tested on the Surface RT: `reboot` and `poweroff` work.

Measurements that led there:

| Test | Result |
|---|---|
| PMC `MAIN_RST` written with `devmem2`, EN1 assignment and SR = 0 left as they are | board dark, PMIC on |
| same, with `VDDCTRL_SR` set to the OP value first | reboots |
| `EN1_SMPS_ASS` cleared, SR = 0 | dies at once, backlight off |
| `EN1_SMPS_ASS` cleared, SR = OP value | dies at once, backlight on |
| `DEV_OFF_RST` written from userspace | cold restart |
| `reboot` / `poweroff` with `tps65910_shutdown()` disabled | both work |

So the PMC reset drops EN1 (the CPU rail falls to SR), and clearing the EN1 assignment is fatal on this board
whatever SR holds. The TPS65911 data sheet says clearing it has no effect (the rail then follows its registers:
`0x27` ST = on, OP voltage); why it kills the board here is open.

The firmware's own `ResetSystem` (`firststage.md`) also clears `EN1_SMPS_ASS` (to `0x00`), as its last PMIC write,
followed by two unidentified optional hooks and PMC `MAIN_RST`, with no delay. Hypothesis, fits all measurements
but not tested: the reset lands before the rail collapses, and after it the bootloader, which runs on the AVP
rather than the CPUs, powers the CPU rail under register control. It may also depend on firmware state we do not
know (the hooks, the sleep registers Linux clears at probe).

### Open

- Why clearing `VDDCTRL_EN1` is fatal (PMIC EEPROM variant or board wiring).
- Deep suspend and LP2 CPU idle under the monitor is moot under the U-Boot route (`boot-chain.md`): without the
  monitor in the boot path, Linux drives the stock Tegra30 idle path directly.

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
  `0xC000`. The monitor itself is in `firststage.md`.
- AML touches the PMIC only in power resources (LDO switching, e.g. LDO5 `0x32` in `PRS1`) and for the RTC
  (`ACPI000E`); DEVCTRL, EN1 and VDDCTRL are left to the driver and the firmware.
- Secondary CPUs start through the ACPI parking protocol (MADT mailboxes); Linux uses
  `arch/arm/kernel/acpi_parking_protocol.c` with the mailboxes hardcoded.
