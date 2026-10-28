# Surface RT reverse engineering

Reverse engineering of the Microsoft Surface RT (Tegra30): building and installing U-Boot in place of the UEFI
image, the boot chain and its security analysis, a Unicorn emulator of the first stage, booting and debugging
U-Boot without a console, and the IDA loader. Commands below run from this directory.

## Building

```sh
git clone --recurse-submodules <repository> && cd surface-rt-re
./build.sh              # everything; all but tegrarcm in the container (docker)
./build.sh --local      # or everything on the host
```

`build.sh` applies the submodules' patch series (`patches/u-boot/`, `patches/fusee/`) where their files do not hold
them yet, leaving files changed otherwise as they are, then builds the targets `payloads`, `u-boot`, `fusee`,
`tegrarcm`, `diskmode` (`all` by default; results in `out/`, `payloads/` and `fusee-tools/`). It runs as the
user; only the disk-mode build takes root, through sudo on the host.

tegrarcm is always built on the host: it needs autoconf, automake, libtool, pkg-config, libusb-1.0 and crypto++.
`--local` also needs the tools the `Dockerfile` installs, and a Linux host for `diskmode`. The boot-trace build of
U-Boot is under Debugging U-Boot without a console (below).

## Installing U-Boot

With the device in APX (hold Volume-Up, tap Power) and connected over USB:

```sh
uv sync --group bootstrap
# --backup saves the factory state of boot0 + boot1 before the first install. The device keeps no copy, and only
# this file brings UEFI back: keep it safe. Later installs (--reinstall) take no backup.
sudo .venv/bin/python srt_uboot.py bootstrap --backup srt-emmc-factory.bin
```

Back to the factory UEFI, again from APX:

```sh
sudo .venv/bin/python srt_uboot.py bootstrap --uninstall --backup srt-emmc-factory.bin
```

With the device already in disk mode, or on the device itself, the same without the APX chain:

```sh
sudo .venv/bin/python srt_uboot.py backup --backup srt-emmc-factory.bin    # once, before the first install
sudo .venv/bin/python srt_uboot.py install
sudo .venv/bin/python srt_uboot.py uninstall --backup srt-emmc-factory.bin
```

What `bootstrap` does after the one APX entry:

1. Fusée Gelée (`fusee-tools`) opens the boot ROM's recovery mode and `tegrarcm` RAM-loads U-Boot. Started this
   way, without the stub's launch marker, U-Boot enters fastboot.
2. fastboot boots the disk-mode image, a pmOS initramfs that exposes the eMMC as USB mass storage: boot0 and
   boot1 read-write, the user area read-only.
3. `srt_uboot.py` writes U-Boot over boot0's backup UEFI image and the stub into boot0's empty region, and points
   both image entries and `UEFIDATA` at the stub; boot1 keeps the factory UEFI image. An uninstall restores the
   backup here instead.
4. It reboots the device over the disk-mode USB network. From then on the first stage runs the stub at every cold
   boot, and the stub starts U-Boot.

On the device itself, `srt_uboot.py` writes `/dev/mmcblk0boot0` and `boot1` directly, which is step 3 alone.
`srt_uboot.py --help` lists the commands and where they find the boot partitions.

## Boot chain and security analysis

| Component | What | Where | Verified by | With |
|---|---|---|---|---|
| **boot ROM** | Tegra 3 mask ROM, runs on the AVP; boots from the boot flash (board straps or a fuse override) | in the SoC, immutable | – (root of trust) | – |
| **first stage** (`SecureT30Sec`) | NVIDIA/Microsoft loader (SEC module, OpenSSL 0.9.8l); brings up SDRAM, loads the UEFI image | boot flash `0x100000` | boot ROM | SBK, hash in the BCT |
| **UEFI image** (`SurfaceRTUEFI.bin`) | SEC module `OemkSec` with the **secure monitor**, UEFI drivers, boot menu | eMMC hardware boot partitions (boot1, backup in boot0), located through the `NVDAUEFI` table | first stage | PKCS#7, "Microsoft Surface for RT Firmware CA 2012" |
| **OS loader** | Windows boot manager, or Linux's EFI stub | EFI system partition | UEFI image (Secure Boot) | Windows bootmgr certificate store |

The boot ROM, the first stage and the UEFI image's SEC module run in the Secure world. The UEFI image installs the
secure monitor, so the first stage and the UEFI image's own code up to that point run before it exists.

### The first stage (`SecureT30Sec`)

Exact addresses are in the IDA loader's labels (The IDA loader, below), not repeated here.

#### Boot flash and the trust anchor

Winbond W25Q32 (`25Q32BVIP`, WSON 6×5) on SPI4 (`spi@7000da00`, chip select 1). It holds only the BCT (boot
configuration table, at `0x000000`: SDRAM timings, location and hash of the first stage), which the boot ROM reads,
and the first stage (`0x100000`); the rest is erased. It is write-protected on the Surface RT, so neither can be
replaced, but readable; the analysis uses an available dump (`data/spi-flash/`). Both are encrypted with the device
key (SBK). The BCT has one bootloader entry (load and entry `0x80808000`), no fallback.

The decrypted bootloader is a firmware volume with one SEC module, `SecureT30Sec` (`NvMainBoardsPkg/SecureBootT30`,
OpenSSL 0.9.8l), followed by a certificate block `NVDASPICERTIFICA` (16-byte name, u32 length, DER): "Microsoft
Surface for RT Firmware CA 2012", issued by "Microsoft Surface Services for Windows RT CA 2012", RSA-2048/SHA-256,
`CA:TRUE, pathlen:0`, valid to 2027. The BCT length covers the cert block too, so the trust anchor is under the
boot ROM's hash. The main UEFI is not in the flash; it lives on the eMMC and `SecureT30Sec` checks its signature
before loading it.

#### Loading and verification

TE image, runs at `0x80808000`; platform code ARM, OpenSSL and its glue Thumb-2.

- `load_uefi`: `decide_use_backup` (watchdog-reset reason from `PMC_RST_STATUS`, plus a compiled-in flag) chooses
  the backup copy; `find_nvdauefi_table` scans eMMC boot0/boot1 in 16 KiB steps for the `NVDAUEFI` table and, via
  `parse_nvdauefi_table`, pivots its entries by type into `nvdauefi_ctx`; `uefidata_read` reads the (unsigned)
  `UEFIDATA` header; `read_image_block` loads the image to its load address; `read_signature_block` reads the
  `NVDASPISIGNATURE` block and `read_trusted_cert` the embedded anchor.
- `Pkcs7Verify`: EDK2-style around OpenSSL `PKCS7_verify(…, flags 0)` (MD5/SHA-1/SHA-256 registered; bare
  SignedData wrapped into a ContentInfo before `d2i_PKCS7`), called with the signature DER and its length, the
  trust anchor, and the loaded image and its size as the signed content. Failure hangs at `verify_failed`
  (the watchdog then resets into the backup copy); success (`verify_ok`) does cache/MMU teardown and
  jumps.

#### The eMMC `NVDAUEFI` table

From `data/emmc/boot0.bin`, `boot1.bin`. The table is at boot0 offset `0x8000`; each entry is `type`, `device`
(0 = boot device/SPI, 1 = boot0, 2 = boot1), u64 `offset`, u64 `size`, u64 `load_address`.

| Type | Where | Size | Content |
|---|---|---|---|
| `0x2` | boot0 `0x8000` | `0x1000` | this table |
| `0x4` | boot0 `0x9000` | `0x40000` | UEFI variable store (`gEfiVariableGuid`) |
| `0xd` | boot0 `0x50000` | `0x1A0000` | UEFI image, backup copy (after a watchdog reset), load `0x80108000`; = `SurfaceRTUEFI.bin` from `0x78`, `0x16F000` used |
| `0x10` | boot0 `0x1F0000` | `0x1000` | `NVDASPISIGNATURE` for the boot0 copy: detached PKCS#7 SignedData (`0x702` bytes, SHA-256/RSA; leaf valid 2013-01-24 to 2014-04-24) |
| `0x11` | boot0 `0x1F1000` | `0x1000` | `UEFIDATA` (tag at `+0x20`): image size `+0x38`, load `+0x40` = `0x80108000`, entry offset `+0x48` = 0; backup fields at `+0x50` |
| `0xb` | boot1 `0x0` | `0x1A0000` | UEFI image, normal copy (identical) |
| `0xe` | boot1 `0x1A0000` | `0x1000` | signature block for it (identical) |
| `0x1`, `0x3` | boot device | `0x8000`, `0x80000` | BCT, first stage (load `0x80808000`) |
| `0x13` | boot0 `0x0` | `0x8000` | empty |

`parse_nvdauefi_table` demultiplexes each entry by `type` into a fixed slot of `nvdauefi_ctx` (jump table on types
1..0x18; a second compact on-disk layout when the table's `+8` field is 1). The whole struct is passed by value to
the block selectors. Normal boot uses types `0xb`/`0xe` (boot1); a watchdog reset uses `0xd`/`0x10` (boot0). Only
the image and signature are redundant; the table and the `UEFIDATA` block exist once, and load address and entry
offset are shared by both copies, so a damaged block affects both.

### Weaknesses

From the first stage and our unit's eMMC boot partitions (above), and the UEFI image (`docs/platform.md`). The first
three build on each other.

1. **The metadata that places the image is unsigned.** The PKCS#7 signature covers the image bytes alone. Where
   they are read from, how many, where they land and where execution goes come from the `NVDAUEFI` table and the
   `UEFIDATA` block (image size `+0x38`, load address `+0x40`, entry offset `+0x48`), unsigned and in the eMMC
   boot partitions. Those are writable from the OS (Linux: `force_ro`, a software switch), so user-writable in the
   chain's own threat model (Windows RT's lock-down is aimed at the device's owner, administrators included: no
   unsigned code, no other OS, Secure Boot not switchable). This alone runs own code after a genuine verification:
   the stage jumps to `load_address + entry_offset` through `bx r0` at `uefi_jump` with no range check, so a
   payload in the unused `UEFIDATA` tail with `entry_offset` pointed at it runs once the real image has verified
   (Running your own code).
2. **Worse: the image copy is a write before the verification.** `read_image_block` copies `image_size` bytes from
   the image entry's device and offset to `load_address` *before* `Pkcs7Verify` runs, with no bounds check on the
   destination. After a watchdog reset it takes the backup image entry and `backup_image_size` (`+0x50`) instead,
   as long as that entry's offset and size and both backup sizes are nonzero (otherwise the normal entry). Source,
   length and destination are all unsigned, so the metadata is an unauthenticated write into the running
   Secure-world stage, before trust is established.
3. **Worse still: the write can replace the verification.** With the image entry pointed at a small payload,
   `image_size` at its length and `load_address` at the `Pkcs7Verify` entry, the stage's own `bl Pkcs7Verify` runs
   the payload: no genuine image, no signature, no trust anchor. The signed image is not load-bearing. The U-Boot
   route uses exactly this (Booting U-Boot in place of the UEFI image).
4. **A generic parser in the Secure world before trust is established.** The first stage verifies with OpenSSL
   0.9.8l (November 2009; the first stage was built about 2012–2014): full ASN.1/X.509/PKCS#7 decoding of data
   from the eMMC, in the Secure world, before the monitor exists, from the write-protected boot flash.
5. **A lightweight verifier was present and is unused.** The first stage contains NVIDIA's own check (fixed
   format, 2048-bit RSA key compare, SHA-256, RSA), never called. Inference: the PKCS#7 path replaced it to anchor
   trust in Microsoft's certificate (who decided is not known: NVIDIA's build, Microsoft's anchor).
6. **Far more code than the check needs.** The first stage needs one PKCS#7 signature check, but carries most of
   OpenSSL (printing, S/MIME, engines, configuration). Nothing was pruned: the unused verifier, with no reference
   at all, is linked in too.
7. **Several copies of the same crypto stack** in one firmware: OpenSSL 0.9.8l in the first stage,
   `CardhuTZSecSvcs`, `NvImageVerificationDxe`, `NvFwPkgUpdateDxe`.
8. **Unfixable root.** The boot ROM's recovery mode is exploitable (Fusée Gelée) and the device key is readable
   through it; the vendors declined fixes for the Secure-world bugs (Yahallo: Microsoft and NVIDIA "wontfix",
   hardware end of life).

Hardware AES was available (boot ROM, `NvAesDxe`): checking an update once against Microsoft's key and storing it
encrypted with the device key (as the update path already does for the BCT) would have avoided 4–7 at boot.

## Emulating the first stage

The emulator boots the stage on a Unicorn Cortex-A9 against a model of the Tegra30 blocks it touches; registers
without a model read back what was last written, and cp15/cp14 operations Unicorn cannot decode are logged and
skipped. The firmware volume is mapped whole, so the reset vector, the headers and the appended `NVDASPICERTIFICA`
trust anchor are all present — that anchor is what `Pkcs7Verify` checks the image signature against. The SDHCI
controller and eMMC card are modelled at the wire-protocol level (register semantics after QEMU's `hw/sd`),
serving `data/emmc/boot0.bin` and `boot1.bin` as the two boot areas (`--boot0`/`--boot1` for other images). What
the boot ROM leaves behind is supplied from the BCT (`--bct`).

A run follows the stage's own structure. It starts on the AVP, which brings up clocks and power, programs the A9
reset vector (EVP) and halts itself at the flow controller (`PG_UP_TAG` tells AVP from CPU). The A9 then sets up
the CPU, caches and TrustZone (`NSACR` grants non-secure access to CP10/CP11) and enables the MMU. It drives the
eMMC wire protocol (card init, CMD6 partition switches, SDMA reads), fetches the `NVDAUEFI` table, the `UEFIDATA`
block, the signed image (~1.46 MiB to `0x80108000`) and the signature, and verifies for real: the RSA-2048/SHA-256
`Pkcs7Verify` returns 1 before the stage reaches the `load_address + entry_offset` jump.

A run can be bounded with `--stop` (a loader symbol such as `load_uefi`, `verify_ok`, `verify_failed`,
`uefi_jump`, or a hex address), `--timeout`, or `--count`. To run to the image-entry jump, after a full, real
verification (~10M blocks):

```sh
uv run python -m securet30 run data/spi-flash/leander-bootloader-decrypted.bin --stop uefi_jump --timeout 60 --regs
```

`--regs`/`--stack` give register and stack context at the stop; `--live` flows the UART like a terminal with a
debugger-style status line pinned below it (PC resolved to the nearest loader symbol); `--mmio` lists the accesses
to hardware without a model, and `--mmio BLOCK|LO-HI ...` (a Tegra30 block of the loader, such as `GIC` or `PMC`,
or a hex range) logs every access to them in order, each with the model that served it (`store`: none); hook `Tegra.at(va, fn)` for intermediate state.

### Running your own code

The emulator demonstrates the unsigned metadata (Weaknesses) on the real stage, with own code after a genuine
verification: `--payload` places a raw ARM binary in the unused tail of the `UEFIDATA` block and points
`entry_offset` at it (computed for you); the stage verifies the real image and then jumps to the payload:

```sh
uv run python -m securet30 run data/spi-flash/leander-bootloader-decrypted.bin --payload payloads/uart_stub.bin --live
```

`uart_stub.S` prints a line on UARTA, then jumps to the emulator's phase-end sentinel so the run ends cleanly on
its own (a real payload would hand off to the next stage instead). `--payload-offset` moves it within the block.

## Booting U-Boot in place of the UEFI image

The route uses the write that replaces the verification (Weaknesses): no open case, no boot-flash write, no
signed image.

- Both image entries, the normal one (type `0x0b`) and the one used after a watchdog reset (`0x0d`), point at a
  small stub, `UEFIDATA`'s image sizes at the stub's, and the unsigned `load_address` at the first stage's verify
  path, so the stub runs in place of verification on either path.
- The stub disarms the stage's watchdog (5 s, armed before every verification, so that a hang falls back to the
  backup copy), loads U-Boot (`u-boot-dtb-tegra.bin`: SPL + U-Boot proper) — written over the backup UEFI
  image on boot0 — to SPL's load address (`SPL_TEXT_BASE`), and cleans the data cache so the image reaches DRAM.
  It then hands the SPL to the AVP exactly as the boot ROM does on the APX path: it halts the AVP, points its reset
  vector (`EVP_COP_RESET_VECTOR`) at the SPL, pulses its reset in the clock-and-reset controller and
  clears the flow-controller halt (NVIDIA's `nvavp` restart sequence). The A9 then parks. SPL runs its own clock
  and PMIC init and `start_cpu`, which holds the A9 in reset, sets its vector to U-Boot proper (`TEXT_BASE`) and
  releases it, so **U-Boot proper starts on a freshly reset A9**, not on the A9 the first stage left.
- This is the clean route. Our first version jumped to U-Boot proper directly on the A9 and stalled in the
  display controller probe: on tegra30 U-Boot runs `clock_early_init` (PLLP to 408 MHz, PLLC, PLLD, …) only in
  SPL, and `board_init_f` guards its own call with `clock_early_init_done()`, which on tegra30 is the weak stub
  that always returns true. Entered directly, U-Boot proper never runs it, leaves the PLLs at the first stage's
  settings, and the display probe hangs. The SPL route runs it, like the APX path.

## Debugging U-Boot without a console

The unopened Surface RT has no reachable UART, so a boot that stalls before the display comes up shows nothing.
The boot trace (`payloads/boottrace.h`) records one boot in a PMC scratch register and a DRAM log, both of which
survive a warm reset, and disk mode reads it back afterwards. A trace run:

1. Build U-Boot with the instrumentation, on the host (the container does not see `KCFLAGS`):
   ```sh
   git -C u-boot apply ../patches/u-boot/boottrace.patch
   OUT=out/boottrace KCFLAGS="-include $PWD/payloads/boottrace.h" ./build.sh --local u-boot
   ```
2. Install it with the trace stub, from APX:
   `srt_uboot.py --images out/boottrace bootstrap --reinstall --stub payloads/uboot_stub-boottrace.bin`.
   Its closing reboot is the trace run, which ends in APX however far U-Boot got.
3. From there, bring the device into disk mode (`srt_uboot.py bootstrap --no-install`) and run `srt-boottrace` in
   its shell. It prints the cause of the last reset, the last checkpoint, the stub's sums of the U-Boot it loaded
   against the slot on the eMMC, and the console log, then clears the trace.
4. Still in disk mode, `srt_uboot.py install --reinstall` puts the normal U-Boot and stub back; then reboot.

How it works:

- The trace stub writes checkpoints 1–3, sums the U-Boot slot twice (after the read, and from DRAM after the
  teardown; `emmc_read` returns 0 whatever happens, so only the bytes tell), starts an empty console log in DRAM,
  sets RCM in `PMC_SCRATCH0` and arms the first stage's watchdog instead of disarming it, so the watchdog reset
  ends the run in APX.
- If the boot ROM boots on after the watchdog reset instead, the first stage runs the stub again (its backup
  path); the stub finds the trace, marks it and enters APX through `MAIN_RST`, the reset known to honour RCM.
- The instrumented U-Boot continues the checkpoints and copies its console into the log. It also logs
  `[start <dev>]`/`[started]` around each console device's `start()` and `[probe <dev>]`/`[/<dev>]` (or
  `[fail <dev>]`) around each driver-model probe.
- `srt-boottrace` reads the trace with `devmem2`; the disk-mode kernel's `mem=` keeps Linux below the log.

| Checkpoint | Reached |
|---|---|
| 1 | stub entry: the stub runs in place of `Pkcs7Verify` |
| 2 | the first stage's eMMC read of U-Boot returned |
| 3 | the stage's teardown returned; caches and MMU are off |
| 4–9 | U-Boot `board_init_f`: entry, before `arch_cpu_init`, after `initf_dm`, before `env_init`, after `console_init_f`, after `dram_init` |
| 10–15 | U-Boot `board_init_r`: entry (relocated), after `initr_dm`, `initr_mmc`, `initr_env`, `stdio_add_devices`, before `run_main_loop` |
| 16–19 | inside `console_init_r` (between 14 and 15): before and after the `iomux_doenv` of `stdin`, `stdout`, `stderr` |

Example: the trace located the display-controller stall of our first version, which jumped to U-Boot proper
directly, so SPL's `clock_early_init` never ran and the PLLs stayed at the first stage's settings (Booting U-Boot
in place of the UEFI image).
The stub ran, both slot sums matched the eMMC, and U-Boot proper reached checkpoint 14 and `[probe dc@54200000]`
with no closing `[/dc@54200000]`: a hang in the display controller probe, which `iomux_doenv` triggers lazily for
`vidconsole`.

### In the emulator

The emulator trades the device's exact behaviour for full introspection. Install into copies of the dumps, then
boot the installed copy:

```sh
mkdir -p out/installed && cp data/emmc/boot0.bin data/emmc/boot1.bin out/installed/
uv run python srt_uboot.py --boot0 out/installed/boot0.bin --boot1 out/installed/boot1.bin install --yes
uv run python -m securet30 run data/spi-flash/leander-bootloader-decrypted.bin --boot0 out/installed/boot0.bin \
    --uboot-map out/u-boot.map --timeout 15 --mmio
```

The run follows the stub's hand-off to the AVP into U-Boot's SPL (a further AVP phase) and shows SPL's UART-A
banner. Modelling stops partway through SPL's clock init, where it reads flow-controller registers the model does
not cover, so the run does not reach U-Boot proper — the hand-off itself is what this verifies. Installed with the
trace stub (`--stub payloads/uboot_stub-boottrace.bin`), the emulator runs the boot trace too (the progress
register and the log are in its PMC model and DRAM). `--uboot-map` (written by `build.sh u-boot`) symbolizes
U-Boot before and after its relocation, also in `--stack`'s list of code addresses on the stack.

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

## Layout

| Path | What |
|---|---|
| [`docs/platform.md`](docs/platform.md) | power management (rails, the PMIC hand-over), the Type Cover, the main UEFI and its secure monitor, and the Windows RT side |
| `securet30/` | the emulator package: `image.py` (`Image`: a TE/PE image or a firmware-volume blob, unwrapped and mapped whole), `soc.py` (`Tegra`: the CPU/SoC model), `sdhci.py` (`Sdhci`/`EmmcCard`), `nvdauefi.py` (the eMMC `NVDAUEFI` table and `UEFIDATA` block, read as the first stage reads them), `uboot.py` (`UBootSymbols`: U-Boot proper's symbols, relocated or not), `cli.py` (the command line) |
| `srt_uboot.py` | the U-Boot installer (Linux, macOS): status / backup / install / uninstall on the eMMC boot partitions -- locally on the Surface RT (`/dev/mmcblk0boot0/1`, force_ro cleared) or on a host over the disk-mode USB mass storage -- and `bootstrap`, the one-shot remote install (or uninstall) from a single APX entry (RAM-load U-Boot, fastboot-boot disk mode, write the eMMC, reboot) |
| `securet30sec.h` | the first stage's types and the `NVDAUEFI` values, shared by the loader (IDA types and enums), `securet30.nvdauefi` and the payloads |
| `securet30sec_loader.py` | IDA 9.x loader for the decrypted bootloader blob: runtime layout, ARM/Thumb, `.reloc` fixups, Tegra30 blocks and registers, known functions and data, the types of `securet30sec.h`, and OpenSSL function identification after auto-analysis. Its tables import without IDA (the emulator, the installer and the payload build read them) |
| `gen_securet30sec_openssl.py`, `securet30sec_openssl.{h,json}` | the loader's OpenSSL header and identification table, and their generator |
| `payloads/` | the payload stubs the first stage runs, and their shared headers (`build.sh payloads`; the `.bin` files are committed) |
| `build.sh`, `Dockerfile` | the build (submodule patches, then the targets; Building), and the container it runs them in |
| `u-boot/` | U-Boot, as a submodule (upstream, built with `surface-rt_defconfig`) |
| `fusee-tools/` | the APX recovery/install tooling, as a submodule (libre-tegra, with its own `tegrarcm` and `fusee-launcher-new` submodules): fusée gelée (`fusee-launcher.py patch_irom.bin`) then `tegrarcm` to read the BCT (`get_bct.sh`) or RAM-load U-Boot over USB (`run_bootloader.sh`). Patched by `patches/fusee/` |
| `diskmode/` | the disk-mode image: `build-pmos-surface-rt-diskmode.sh` + the `00*-initramfs-*.patch` series (a `fastboot boot` pmOS image that exposes the eMMC as USB mass storage), `srt-boottrace` (its boot-trace read-out) |
| `patches/` | `linux-libre-tegra/` (the Surface RT patches against the libre-tegra kernel: the serial-tegra DMA residue, and kCFI types for the Tegra sleep routines that C calls through pointers, which CPU offline and suspend need); `u-boot/` (the `u-boot` series: the Surface RT board code and boot command, i.e. the normal `bootcmd` (first bootflow, else the boot menu) and the stub's launch marker read in board code, so a RAM preload over APX enters fastboot; the Type Cover as console input: a pass-through I2C bus for GPIO-detected hot-plugged devices, HID keyboard report handling shared with the Apple SPI keyboard, a polled HID-over-I2C keyboard driver, the Surface RT device tree and `stdin`; USB host storage and networking: VBUS (GPIO DD6) driven off in early board code instead of a device-tree hog, so the EHCI driver can switch it; and, outside the series, the boot-trace instrumentation, test only); and `fusee/` (the `fusee-tools` changes: tegrarcm `GET_PLATFORM_INFO` order, the fusee-launcher macOS teardown fix, and the scripts' switch to tegrarcm). `build.sh` applies the `u-boot` and `fusee` series to the submodules |
| `data/` | the inputs and reference material: the decrypted bootloader and eMMC boot dumps, the SPI-flash and PMIC dumps, ACPI tables, and the Windows driver package (large, kept local) |
