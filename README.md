# Surface RT reverse engineering

Reverse engineering of the Microsoft Surface RT (Tegra30), orthogonal to the 88W8797 WLAN/BT work it grew out of:
the boot firmware (the first stage `SecureT30Sec` and the UEFI/monitor it loads), a Unicorn emulator that boots
the stage, the boot chain and its security analysis, and the platform (power management, the Windows RT side).
Commands below run from this directory.

## Building

Check out with the U-Boot submodule (`git clone --recurse-submodules`, or `git submodule update --init` in an
existing checkout). Everything the repository produces is built by `build.sh` (targets `payloads`, `u-boot`,
`diskmode`, `all`), most simply in the container of the `Dockerfile`, which holds every tool needed:

```sh
docker build -t surface-rt-re .
docker run --rm -v "$PWD:/src" surface-rt-re            # all targets; results in out/
```

## Layout

| Path | What |
|---|---|
| [`docs/firststage.md`](docs/firststage.md) | findings: the first stage, the UEFI/monitor, the `NVDAUEFI` table, the unsigned-metadata write and entry_offset hijack, and emulation |
| [`docs/boot-chain.md`](docs/boot-chain.md) | the boot chain, its security weaknesses, and booting U-Boot in place of the UEFI image |
| [`docs/platform.md`](docs/platform.md) | power management (the reboot-hang root cause and fix) and the Windows RT side |
| `securet30/` | the emulator package: `image.py` (`Image`: a TE/PE image or a firmware-volume blob, unwrapped and mapped whole), `soc.py` (`Tegra`: the CPU/SoC model), `sdhci.py` (`Sdhci`/`EmmcCard`), `nvdauefi.py` (the eMMC `NVDAUEFI` table and `UEFIDATA` block, read as the first stage reads them), `uboot.py` (`UBootSymbols`: U-Boot proper's symbols, relocated or not), `cli.py` (the command line) |
| `uboot_emmc.py` | host-side eMMC installer (Linux, macOS): status/backup/install/uninstall of U-Boot over the disk-mode USB mass storage |
| `securet30sec.h` | the first stage's types and the `NVDAUEFI` values, shared by the loader (IDA types and enums), `securet30.nvdauefi` and the payloads |
| `boottrace.h` | the boot trace's layout (progress register, DRAM log, watchdog period), shared by the trace stub, an instrumented U-Boot and the disk-mode read-out |
| `securet30sec_loader.py` | IDA 9.x loader for the decrypted bootloader blob: runtime layout, ARM/Thumb, `.reloc` fixups, Tegra30 blocks and registers, known functions and data, the types of `securet30sec.h`, and OpenSSL function identification after auto-analysis. Its tables import without IDA (the emulator, the installer and the payload build read them) |
| `gen_securet30sec_openssl.py`, `securet30sec_openssl.{h,json}` | the loader's OpenSSL header and identification table, and their generator |
| `payloads/` | payloads for the pre-verify write and the entry_offset hijack: `uart_stub.S` (demo), `uboot_stub.S` + `uboot_stub.h` (the design-C U-Boot loader stub and its eMMC placement; `uboot_stub-boottrace.bin` records the boot trace of `boottrace.h`, `docs/boot-chain.md`), `Makefile` (preprocessed assembly; generates the function addresses from the loader). The `.bin` files and the generated `securet30sec_functions.h` are committed; after a change, `make -C payloads && git diff --exit-code payloads` |
| `build.sh`, `Dockerfile` | the build of everything below (`out/`), and its container with every tool needed (no host root) |
| `u-boot/` | U-Boot, as a submodule (upstream, built with `surface-rt_defconfig`) |
| `u-boot-env-overrides.txt` | our changes to U-Boot's default environment; `build.sh u-boot` writes the complete environment the installer stores (`out/u-boot-env.txt`), since a stored environment replaces U-Boot's built-in defaults |
| `diskmode/` | the disk-mode image: `build-pmos-surface-rt-diskmode.sh` + the `00*-initramfs-*.patch` series (a `fastboot boot` pmOS image that exposes the eMMC as USB mass storage), `srt-boottrace` (its boot-trace read-out) |
| `patches/` | downstream Linux integration: the Surface RT kernel patches (serial-tegra DMA residue, the tps65910 shutdown fix) |
| `data/` | the inputs and reference material: the decrypted bootloader and eMMC boot dumps, the SPI-flash and PMIC dumps, ACPI tables, and the Windows driver package (large, kept local) |

## Emulating the first stage

`Tegra` boots the stage on a Unicorn Cortex-A9 against a model of the Tegra30 blocks it touches; registers without
a model read back what was last written, and cp15/cp14 operations Unicorn cannot decode are logged (`cp15`) and
skipped. `Image` unwraps the firmware volume and maps it whole, so the reset vector, the headers and the appended
`NVDASPICERTIFICA` trust anchor are all present — that anchor is what `Pkcs7Verify` checks the image signature
against. `sdhci.py` models the SDHCI controller and eMMC card at the wire-protocol level (register semantics after
QEMU's `hw/sd`), serving `data/emmc/boot0.bin` and `boot1.bin` as the two boot areas (`--boot0`/`--boot1` for
other images). What the boot ROM leaves behind is supplied from the BCT (`--bct`; `firststage.md`, Emulation).

A run can be bounded with `--stop` (a loader symbol or hex address), `--timeout`, or
`--count`. To run to the image-entry jump, after a full, real verification (~10M blocks):

```sh
uv run python -m securet30 run data/spi-flash/leander-bootloader-decrypted.bin --stop uefi_jump --timeout 60 --regs
```

`--stop` takes loader symbols (no magic addresses): `load_uefi` (fast), `verify_ok`, `verify_failed`, `uefi_jump`.
`--regs`/`--stack` give register and stack context at the stop; `--live` flows the UART like a terminal with a
debugger-style status line pinned below it (PC resolved to the nearest loader symbol); `--mmio` lists the accesses
to hardware without a model; hook `Tegra.at(va, fn)` for intermediate state.

### Booting the installed U-Boot

Back boot0 with what `uboot_emmc.py install` wrote (a backup of the device after the install, or the install run
against a copy of the dumps), and the run follows the stub's hand-off to the AVP into U-Boot's SPL (a further AVP
phase); the run shows SPL's UART-A banner. Modelling stops partway through SPL's clock init, where it reads
flow-controller registers the model does not cover, so the run does not reach U-Boot proper — the hand-off
itself is what this verifies. `--uboot-map` (written by `build.sh u-boot`) symbolizes U-Boot before and after its
relocation, also in `--stack`'s list of code addresses on the stack:

```sh
uv run python -m securet30 run data/spi-flash/leander-bootloader-decrypted.bin --boot0 installed-boot0.bin \
    --uboot-map out/u-boot.map --timeout 15 --mmio
```

### Running your own code (the entry_offset hijack)

The image is signed, but `uefidata.entry_offset` — where the stage jumps after verify — is not. A payload placed
in the unused tail of the UEFIDATA block, with `entry_offset` pointed at it, runs with the image signature valid.
`--payload` injects a raw ARM binary and does the redirect (the entry offset is computed for you):

```sh
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
