# Surface RT reverse engineering

Reverse engineering of the Microsoft Surface RT (Tegra30), orthogonal to the 88W8797 WLAN/BT work it grew out of:
the boot firmware (the first stage `SecureT30Sec` and the UEFI/monitor it loads), a Unicorn emulator that boots
the stage, the boot chain and its security analysis, and the platform (power management, the Windows RT side).
Commands below run from this directory.

## Layout

| Path | What |
|---|---|
| [`docs/firststage.md`](docs/firststage.md) | findings: the first stage, the UEFI/monitor, the `NVDAUEFI` table, the entry_offset hijack, and emulation |
| [`docs/boot-chain.md`](docs/boot-chain.md) | the boot chain, its security weaknesses, and the U-Boot/RCM fallback |
| [`docs/platform.md`](docs/platform.md) | power management (the reboot-hang root cause and fix) and the Windows RT side |
| `securet30/` | the emulator package: `image.py` (`Image`: a TE/PE image or a firmware-volume blob, unwrapped and mapped whole), `soc.py` (`Tegra`: the CPU/SoC model), `sdhci.py` (`Sdhci`/`EmmcCard`), `cli.py` (the command line) |
| `securet30sec_loader.py` | IDA 9.x loader for the decrypted bootloader blob: runtime layout, ARM/Thumb, `.reloc` fixups, Tegra30 blocks and registers, known functions, data and types, and OpenSSL function identification after auto-analysis. Its tables import without IDA (the emulator reads them for symbols) |
| `gen_securet30sec_openssl.py`, `securet30sec_openssl.{h,json}` | the loader's OpenSSL header and identification table, and their generator |
| `payloads/` | demo payloads for the entry_offset hijack (`uart_stub.S`, `Makefile`) |
| `patches/` | downstream Linux integration: the Surface RT kernel patches (serial-tegra DMA residue, the tps65910 shutdown fix) |
| `data/` | the inputs and reference material: the decrypted bootloader and eMMC boot dumps, the SPI-flash and PMIC dumps, ACPI tables, and the Windows driver package (large, kept local) |

## Emulating the first stage

`Tegra` boots the stage on a Unicorn Cortex-A9 against a model of the Tegra30 blocks it touches; registers without
a model read back what was last written, and cp15/cp14 operations Unicorn cannot decode are logged (`cp15`) and
skipped. `Image` unwraps the firmware volume and maps it whole, so the reset vector, the headers and the appended
`NVDASPICERTIFICA` trust anchor are all present — that anchor is what `Pkcs7Verify` checks the image signature
against. `sdhci.py` models the SDHCI controller and eMMC card at the wire-protocol level (register semantics after
QEMU's `hw/sd`), serving `data/emmc/boot0.bin` and `boot1.bin` as the two boot areas.

There is no hang detection, so bound a run with `--stop` (a loader symbol or hex address), `--timeout`, or
`--count`. To run to the image-entry jump, after a full, real verification (~10M blocks, a few minutes):

```sh
uv run python -m securet30 run data/spi-flash/leander-bootloader-decrypted.bin --stop uefi_jump --timeout 600 --regs
```

`--stop` takes loader symbols (no magic addresses): `load_uefi` (fast), `verify_ok`, `verify_failed`, `uefi_jump`.
`--regs`/`--stack` give register and stack context at the stop; `--live` flows the UART like a terminal with a
debugger-style status line pinned below it (PC resolved to the nearest loader symbol); hook `Tegra.at(va, fn)` for
intermediate state.

### Running your own code (the entry_offset hijack)

The image is signed, but `uefidata.entry_offset` — where the stage jumps after verify — is not. A payload placed
in the unused tail of the UEFIDATA block, with `entry_offset` pointed at it, runs with the image signature valid.
`--payload` injects a raw ARM binary and does the redirect (the entry offset is computed for you):

```sh
make -C payloads                                         # assemble uart_stub.bin (Arm GNU Toolchain)
uv run python -m securet30 run data/spi-flash/leander-bootloader-decrypted.bin --payload payloads/uart_stub.bin --live
```

`uart_stub.S` prints a line on UARTA, then jumps to the emulator's phase-end sentinel so the run ends cleanly on
its own (a real payload would hand off to the next stage instead). `--payload-offset` moves it within the block.

## The IDA loader

Link it into IDA's `loaders` directory, e.g. `ln -s "$PWD/securet30sec_loader.py" ~/.idapro/loaders/`; it reads
`securet30sec_openssl.{h,json}` from its own (link-resolved) directory. Running it as a script on an open database
re-applies the tables and the OpenSSL identification; it marks its own symbols auto-generated and never overwrites
a user name.

`gen_securet30sec_openssl.py --tarball openssl-0.9.8l.tar.gz --edk2 EDK2_REPO [--rev REV]` regenerates the two
committed files from the OpenSSL 0.9.8l release tarball (`openssl.org/source/old/0.9.x/`, checked against its
SHA-256) and an edk2 clone, by default at `5359174326^`, the last commit with 0.9.8l. Needs `arm-none-eabi-gcc`
(preprocessing) and libclang (dependency group `tools`).

UEFI images come out of firmware volumes with `uefi-firmware-parser` (dependency group `tools`), e.g.
`uv run uefi-firmware-parser -b -e -o OUT data/spi-flash/leander-bootloader-decrypted.bin`; the first stage is then
`OUT/volume-0/file-6d98fdc6-…-0967/section1.te`. The next-stage `SurfaceRTUEFI.bin` (SEC module `OemkSec` with the
secure monitor, DXE modules under a nested volume) comes from the Surface RT Windows driver package, not shipped
here. Addresses given to the tools are runtime addresses (image base + RVA).
