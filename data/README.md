# Surface RT reference material

Third-party material about the Microsoft Surface RT (Tegra30), kept here for reference. None of it is
covered by this repository's license; the rights stay with the authors and copyright holders named below.
Retrieved 2026-10-24.

## `acpi/` — ACPI tables

The Surface RT's ACPI tables, dumped from its UEFI firmware and decompiled, by the **Open Surface RT**
community project. They are published on its wiki, which has no public source repository:

- Wiki: <https://open-rt.gitbook.io/open-surfacert/> (Surface RT > UEFI > ACPI Tables)
- Dumped tables (`*.bin`): `ACPI-Tables-SurfaceRT.zip`, attached to
  <https://open-rt.gitbook.io/open-surfacert/surface-rt/uefi/acpi-tables>
- Decompiled tables (`*.ASL` by the Microsoft ASL compiler, `*.dsl` by iasl):
  `ACPI-Tables-SurfaceRT-decompiled.zip`, same page

MSDM (`MSDM0000.bin`, `MSDM0000.dsl`) carries the Windows product key of the device the tables were dumped
from, as published there.

## `pmic/` — PMIC data sheet

`tps65911-datasheet-swcs049s.pdf`: Texas Instruments, *TPS65911 Integrated Power Management Unit
Top Specification*, SWCS049S (June 2010, revised August 2018), © Texas Instruments.
Source: <https://www.ti.com/lit/ds/symlink/tps65911.pdf>

`tps65911-regs-*.txt`: our own register dumps of this board's PMIC (`uefi`: the UEFI's hand-over; `linux-uefi`,
`linux-uboot`: running Linux, booted through the UEFI or U-Boot); how each was taken is in its header.

## `spi-flash/` — boot flash (W25Q32) data sheet and published dumps

- `w25q32bv-datasheet.pdf`: Winbond, *W25Q32BV 3V 32M-bit serial flash memory with dual and quad SPI*,
  revision I (2013-10-04), © Winbond.
- From the Open Surface RT wiki, <https://open-rt.gitbook.io/open-surfacert/surface-rt/firmware/spi-flash>,
  as published there (the files are device-specific, encrypted with each device's key):
  - `leander-mtd0.bin`: @Leander's full SPI flash dump (4 MiB; file "mtd0"); the page gives that device's
    platform key (SBK) `28a5d126adf421e6a39bfc8f7ff32308`.
  - `leander-bct-encrypted.bct` ("surfacert-encrypted.bct") and `leander-bct-nvflash.bct`
    ("surfacert.bin", the BCT as read by nvflash).
  - `cts-mtd0.bin`: CTS's full SPI flash dump ("mtd0Original_CTS.bin").
- Derived here from `leander-mtd0.bin` with the published key (AES-128-CBC, IV 0; the first 16 bytes of the
  BCT are its hash and stay as they are): `leander-bct-decrypted.bin` (`0x000000`, 6128 bytes) and
  `leander-bootloader-decrypted.bin` (`0x100000`, length `0x7E560` from the BCT).

## `emmc/` — our unit's eMMC hardware boot partitions

`boot0.bin`, `boot1.bin`: `dd` of `/dev/mmcblk0boot0` and `boot1` on our Surface RT (2 MiB each,
2026-10-25), read-only dumps of the area the first stage loads the UEFI image from.

## `windows-drivers/` — Windows RT 8.1 driver package (not in Git for now)

The Surface RT's driver store (`Install/`, `Boot_WinRe/`), from the Internet Archive item
"Windows RT Drivers": <https://archive.org/details/windows-rt-drivers>, file
`Extracted/Microsoft_Surface_RT_Drivers.zip`, extracted unchanged. The drivers are © their vendors
(Microsoft, NVIDIA, Marvell and others).

The same item has packages for other Windows RT devices, among them `Microsoft_Surface_2_Drivers.zip`
for the Surface 2 (Tegra 4), which uses the 88W8797 in a similar configuration.
