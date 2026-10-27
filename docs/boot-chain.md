# Surface RT boot chain and security analysis

The boot device is fixed to the boot flash (board straps or a fuse override). Details of each stage are in
`firststage.md`.

| # | Term | What | Where | Verified by | With |
|---|---|---|---|---|---|
| 0 | **boot ROM** | Tegra 3 mask ROM, runs on the AVP | in the SoC, immutable | – (root of trust) | – |
| 1 | **BCT** | boot configuration: SDRAM timings, location and hash of the first stage | boot flash `0x000000` | boot ROM | device key (SBK, AES) |
| 2 | **first stage** (`SecureT30Sec`) | NVIDIA/Microsoft loader (SEC module, OpenSSL 0.9.8l); brings up SDRAM, loads the UEFI image | boot flash `0x100000` | boot ROM | SBK, hash in the BCT |
| 3 | **UEFI image** (`SurfaceRTUEFI.bin`) | SEC module `OemkSec` with the **secure monitor**, UEFI drivers, boot menu | eMMC hardware boot partitions (boot0, backup in boot1), located through the `NVDAUEFI` table | first stage | PKCS#7, "Microsoft Surface for RT Firmware CA 2012" |
| 4 | **OS loader** | Windows boot manager, or Linux's EFI stub | EFI system partition | UEFI image (Secure Boot) | off on our unit (Yahallo) |

- **Boot flash:** the W25Q32 on SPI4; holds stages 1 and 2 only. Its write protection decides whether stages 1–2
  can be replaced (the SBK is per device and readable through Fusée Gelée, so the boot ROM's check is no barrier
  for the owner).
- Stages 0–2 and the UEFI image's SEC module run in the Secure world; the monitor is installed by stage 3, so
  code in stage 2 or 3 runs before it exists.

## Weaknesses

From the first stage, the UEFI image and our unit's eMMC boot partitions (`firststage.md`).

1. **Unsigned metadata is a pre-verification write, so the signature can be skipped.** The `NVDAUEFI` table and
   the `UEFIDATA` block (boot0 `0x1F1000`) supply the destination, read length, verified length and entry offset,
   none under the signature, all in the eMMC boot partitions — writable from the OS (Linux: `force_ro`, a software
   switch), so user-writable in the chain's own threat model (Windows RT's lock-down is aimed at the device's
   owner, administrators included: no unsigned code, no other OS, Secure Boot not switchable). The first stage
   copies the image, from where the table says and as many bytes as `UEFIDATA` says, to the unsigned load address
   *before* it verifies, with no bounds check, so the metadata is an unauthenticated write into the Secure-world
   stage before trust exists. The signed image is not load-bearing: aiming the load address at the verify routine runs attacker
   bytes in place of `Pkcs7Verify`, with no genuine image (demonstrated end to end in the emulator;
   `firststage.md`).
2. **A generic parser in the Secure world before trust is established.** The first stage verifies with OpenSSL
   0.9.8l (November 2009; the first stage was built about 2012–2014): full ASN.1/X.509/PKCS#7 decoding of data
   from the eMMC, in the Secure world, before the monitor exists. In the boot flash, so never updated if the flash
   is locked.
3. **A lightweight verifier was present and is unused.** The first stage contains NVIDIA's own check (fixed
   format, 2048-bit RSA key compare, SHA-256, RSA), never called. Inference: the PKCS#7 path replaced it to anchor
   trust in Microsoft's certificate (who decided is not known: NVIDIA's build, Microsoft's anchor).
4. **No dead-code elimination.** The unused verifier has no reference at all, so the link did not prune sections;
   most of OpenSSL (printing, S/MIME, engines, configuration) is linked in. OpenSSL's tables (ASN.1 templates,
   method tables) would keep much of it alive even with pruning.
5. **Patched trust model.** The anchor is an intermediate CA; the first stage marks matching certificates
   (`0x12345678` at `+0x5c`) so that OpenSSL accepts them as root (inference from the code).
6. **Several copies of the same crypto stack** in one firmware: OpenSSL 0.9.8l in the first stage,
   `CardhuTZSecSvcs`, `NvImageVerificationDxe`, `NvFwPkgUpdateDxe`.
7. **Unfixable root.** The boot ROM's recovery mode is exploitable (Fusée Gelée) and the device key is readable
   through it; the vendors declined fixes for the Secure-world bugs (Yahallo: Microsoft and NVIDIA "wontfix",
   hardware end of life).

Hardware AES was available (boot ROM, `NvAesDxe`): checking an update once against Microsoft's key and storing it
encrypted with the device key (as the update path already does for the BCT) would have avoided 2–6 at boot.

## Booting U-Boot in place of the UEFI image

Running our own code needs no open case and no boot-flash write: the first stage loads and launches it from the
eMMC boot partitions, which the OS can write (`force_ro`). The route uses the pre-verification write of
**weakness 1**, so it needs neither the signed image nor the signature:

- Both image entries, the normal one (type `0x0b`) and the one used after a watchdog reset (`0x0d`), point at a
  small stub, `UEFIDATA`'s image sizes at the stub's, and the unsigned `load_address` at the first stage's verify
  path, so the stub runs in place of verification on either path.
- The stub disarms the stage's watchdog (5 s, armed before every verification, so that a hang falls back to the
  backup copy), loads stock U-Boot (`u-boot-dtb-tegra.bin`: SPL + U-Boot proper) — written over the backup UEFI
  image on boot0 (`0x50000`) — to `SPL_TEXT_BASE` `0x80108000`, and cleans the data cache so the image reaches
  DRAM. It then hands the SPL to the AVP exactly as the boot ROM does on the APX path: it halts the AVP, points
  its reset vector (`EVP_COP_RESET_VECTOR`) at the SPL, pulses its reset in the clock-and-reset controller and
  clears the flow-controller halt (NVIDIA's `nvavp` restart sequence). The A9 then parks. SPL runs its own clock
  and PMIC init and `start_cpu`, which holds the A9 in reset, sets its vector to U-Boot proper (`0x80110000`) and
  releases it, so **U-Boot proper starts on a freshly reset A9**, not on the A9 the first stage left. The
  installer checks the stub's load address against the build's `SPL_TEXT_BASE`.
- This is the clean route: entering U-Boot proper directly on the A9 (an earlier design) stalled in the display
  controller probe. On tegra30 U-Boot runs `clock_early_init` (PLLP to 408 MHz, PLLC, PLLD, …) only in SPL;
  `board_init_f` guards its own call with `clock_early_init_done()`, which on tegra30 is the weak stub that always
  returns true. A direct-to-proper boot therefore never runs it and leaves the PLLs at the first stage's settings,
  and the display probe hangs. The SPL route runs it, like the APX path.
- Everything lives on boot0; boot1 keeps the factory UEFI image and its signature. U-Boot keeps its stock
  `surface-rt_defconfig`.

Installed from the host, with the device in disk mode. A pmOS image `fastboot boot`ed over the boot ROM's
recovery mode (RCM / Fusée Gelée) exposes the eMMC boot partitions to the host as USB mass storage, boot0/boot1
read-write and the user area read-only (`build.sh diskmode`, `diskmode/`). The image's devicetree puts the OTG
port into peripheral mode, and its debug shell exposes the LUNs through pmOS's `pmos.usb-storage=`, which
`diskmode/0001-initramfs-usb-storage-multiple-luns.patch` extends to several devices; the console shell stays up. The host tool
`uboot_emmc.py` then backs up boot0+boot1, writes U-Boot, the stub and the patched `NVDAUEFI` table /
`UEFIDATA` to the LUNs, and `uninstall` restores from that backup. It also stores U-Boot's environment at the end
of boot0 (where `surface-rt_defconfig` keeps it, past every `NVDAUEFI` entry), unless a valid one is there: the
complete environment, U-Boot's defaults with `u-boot-env-overrides.txt` applied, because U-Boot replaces its
built-in defaults with a stored environment rather than merging. The override boots the first bootflow found
and falls back to the boot menu. U-Boot and that environment are built from the `u-boot` submodule by `build.sh
u-boot`. The device image carries no U-Boot, stub, installer or Python — the host owns them, and the backup lives
on the host, not on the device. The device then boots U-Boot on its own at every cold boot. The APX RAM preload (U-Boot over USB without writing eMMC, Power +
Volume up; `re-crypt`, grate-driver, carries a `surface-rt` BCT) stays as a recovery path that needs a PC and a
USB A-to-A cable each boot.

Without a console, a boot reports how far it got through the boot trace (`boottrace.h`), recorded in one run
and read back afterwards. The trace stub (`payloads/uboot_stub-boottrace.bin`, `uboot_emmc.py install --stub`)
writes checkpoints to a PMC scratch register, sums the U-Boot slot it loaded twice (after the read, and from DRAM
after the teardown; `emmc_read` returns 0 whatever happens, so only the bytes tell), starts an empty console log
in DRAM, sets RCM in `PMC_SCRATCH0` and arms the first stage's watchdog instead of disarming it, meant to end
every run in USB recovery mode (APX). If the boot ROM boots on after the watchdog reset instead, the first stage
runs the stub again (its backup path); the stub finds the trace, marks it and enters APX through `MAIN_RST`, the
reset known to honour RCM, so the trace survives either way. A U-Boot built with `KCFLAGS="-include boottrace.h"` and the boot-trace
instrumentation (a local test patch) continues the checkpoints and copies its console into the log. Disk mode
reads it all back, with the cause of the last reset and the sums compared against the slot on the eMMC, and
clears it: `srt-boottrace` in its shell (`devmem2`; the kernel's `mem=` keeps Linux below the log).

| Checkpoint | Reached |
|---|---|
| 1 | stub entry: the stub runs in place of `Pkcs7Verify` |
| 2 | the first stage's eMMC read of U-Boot returned |
| 3 | the stage's teardown returned; caches and MMU are off |
| 4–9 | U-Boot `board_init_f`: entry, before `arch_cpu_init`, after `initf_dm`, before `env_init`, after `console_init_f`, after `dram_init` |
| 10–15 | U-Boot `board_init_r`: entry (relocated), after `initr_dm`, `initr_mmc`, `initr_env`, `stdio_add_devices`, before `run_main_loop` |
| 16–19 | inside `console_init_r` (between 14 and 15): before and after the `iomux_doenv` of `stdin`, `stdout`, `stderr` |

The instrumented U-Boot also logs `[start <dev>]`/`[started]` around each console device's `start()` and
`[probe <dev>]`/`[/<dev>]` (or `[fail <dev>]`) around each driver-model probe.

The emulator runs the same trace (`securet30 run` with the traced boot0; the progress register and the log are in
its PMC model and DRAM).

This boot trace is what located the display-controller stall of the direct-to-proper design (above): on a unit,
the stub ran, both slot sums matched the eMMC, and U-Boot proper reached checkpoint 14 and `[probe dc@54200000]`
with no closing `[/dc@54200000]` — a hang in the display controller probe, which `iomux_doenv` triggers lazily
for `vidconsole`. That drove the move to the SPL/AVP route, which boots U-Boot with its display up on the unit.
