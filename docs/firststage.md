# Surface RT boot firmware — findings

Reverse-engineering notes on the Surface RT (Tegra30) boot firmware: the boot-flash first stage `SecureT30Sec`
and the main UEFI (`SurfaceRTUEFI.bin`, with the secure monitor) that it loads. The tooling and its usage are at
the repository root (`README.md`); exact addresses are in the IDA loader's labels (`securet30sec_loader.py`), not
repeated here. The boot chain and its security analysis are in `boot-chain.md`, power management and the Windows
RT side in `platform.md`.

## Boot flash and the trust anchor

Winbond W25Q32 (`25Q32BVIP`, WSON 6×5) on SPI4 (`spi@7000da00`, chip select 1). The BCT is encrypted with the
device key (SBK); the bootloader is encrypted too; the rest is erased. The BCT has one bootloader entry (load and
entry `0x80808000`), no fallback.

The decrypted bootloader is a firmware volume with one SEC module, `SecureT30Sec` (`NvMainBoardsPkg/SecureBootT30`,
OpenSSL 0.9.8l), followed by a certificate block `NVDASPICERTIFICA` (16-byte name, u32 length, DER): "Microsoft
Surface for RT Firmware CA 2012", issued by "Microsoft Surface Services for Windows RT CA 2012", RSA-2048/SHA-256,
`CA:TRUE, pathlen:0`, valid to 2027. The BCT length covers the cert block too, so the trust anchor is under the
boot ROM's hash. The main UEFI is not in the flash; it lives on the eMMC and `SecureT30Sec` checks its signature
before loading it.

## The first stage (`SecureT30Sec`)

TE image, runs at `0x80808000`; platform code ARM, OpenSSL and its glue Thumb-2.

- `load_uefi`: `decide_use_backup` (watchdog-reset reason from `PMC_RST_STATUS`, plus a compiled-in flag) chooses
  the backup copy; `find_nvdauefi_table` scans eMMC boot0/boot1 in 16 KiB steps for the `NVDAUEFI` table and, via
  `parse_nvdauefi_table`, pivots its entries by type into `nvdauefi_ctx`; `uefidata_read` reads the (unsigned)
  `UEFIDATA` header; `read_image_block` loads the image to its load address; `read_signature_block` reads the
  `NVDASPISIGNATURE` block and `read_trusted_cert` the embedded anchor.
- `Pkcs7Verify`: EDK2-style around OpenSSL `PKCS7_verify(…, flags 0)` (MD5/SHA-1/SHA-256 registered; bare
  SignedData wrapped into a ContentInfo before `d2i_PKCS7`), called with the signature DER and its length, the
  trust anchor, and the loaded image and its size as the signed content. Failure hangs at `verify_failed`
  (inference: the watchdog then resets into the backup copy); success (`verify_ok`) does cache/MMU teardown and
  jumps.
- An NVIDIA verifier without OpenSSL (fixed format, 2048-bit RSA key compare, SHA-256, RSA) is present but never
  reached.

## The eMMC `NVDAUEFI` table (our unit)

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

## The unsigned metadata: a pre-verification write and the entry_offset hijack

The PKCS#7 signature covers the image bytes alone. Everything that says *where* those bytes land and *where
execution goes* is unsigned, in the `NVDAUEFI` table and the `UEFIDATA` block, both in the eMMC boot partitions.

`read_image_block` copies `uefidata.image_size` (`+0x38`) bytes from the image entry's device and offset to
`uefidata.load_address` (`+0x40`) before `Pkcs7Verify` runs, with no bounds check on the destination. After a
watchdog reset it takes the backup image entry and `backup_image_size` (`+0x50`) instead, as long as that entry's
offset and size and both backup sizes in `UEFIDATA` are nonzero (otherwise the normal entry). Source, length and
destination all come from the unsigned table and `UEFIDATA`, and the check comes after the copy. So the unsigned
metadata is an unauthenticated write into the running Secure-world stage, before trust is established, and **the
signed image is not load-bearing**: point the image entry at a small payload, `image_size` at its length and
`load_address` at the `Pkcs7Verify` entry, and the stage's own `bl Pkcs7Verify` runs the payload — no genuine
image, no signature, no trust anchor. Shown in the emulator: with the image entry (type `0x0b`) repointed to the
84-byte `payloads/uart_stub.bin`, `image_size` set to one block and `load_address` to `Pkcs7Verify`, the stage
prints the payload's line and finishes without loading the image (`0x80108000` stays zero) or running the verify.

The milder variant keeps the genuine image: the jump target is `load_address + entry_offset` (`+0x40`, `+0x48`),
through `bx r0` at `uefi_jump` with no range check, so a payload in the unused `UEFIDATA` tail with `entry_offset`
pointed at it runs after a real, successful verification (`securet30 run --payload`, `payloads/uart_stub.S`).

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
would make the 4 MiB read-only for good on a "P" part); whether any was applied on a unit is settled only by
reading the status registers. The boot device comes from board straps or a fuse override; the update path writes
per boot device and can burn fuses, and update images are PKCS#7-verified.

## Emulation

`securet30` boots the stage on a Unicorn Cortex-A9 against a model of the Tegra30 blocks it touches, with the eMMC
controller and card modelled and backed by the boot-partition dumps. The run reproduces the structure: the stage
boots on the **AVP**, brings up clocks and power, programs the A9 reset vector into EVP and halts at the FLOW
controller (`PG_UP_TAG` distinguishes AVP from CPU); the A9 does CPU/cache/TrustZone set-up (`NSACR` grants
non-secure access to CP10/CP11) and enables the MMU. It then drives the real eMMC wire protocol (card init, CMD6
partition switches, SDMA reads), fetches the `NVDAUEFI` table, the `UEFIDATA` block, the signed image (~1.46 MiB to
`0x80108000`) and the signature, and **verifies**: the real RSA-2048/SHA-256 `Pkcs7Verify` returns 1, then the
stage reaches the `load_address + entry_offset` jump.

The one fidelity requirement is that the whole firmware volume is mapped, not just an extracted TE section: the
appended `NVDASPICERTIFICA` trust anchor is what `Pkcs7Verify` checks against, so without it the verification
fails in the ASN.1 parse. `Image` unwraps the volume and maps it whole, so verification succeeds as on hardware.

Supplied because the boot ROM is not run: the page table at the stage's own `TTBR0` (`_build_pt` fills it with
1 MiB sections, identity from `0x40000000` up and the low 0-based range aliased to DRAM at `0x80000000`) and the
0-based stack backed by real RAM. From the BCT (layout after NVIDIA's cbootimage, `src/t30`), what the boot ROM
leaves for later stages: a copy of the BCT in IRAM that the Boot Information Table points to (`+0x3c`; U-Boot
reads ODMDATA through it), and PLLM and `MC_EMEM_CFG` (DRAM size in MiB) from the SDRAM set the RAM-code strap
selects. Our BCT's four sets all give 2048 MiB and M = 12, N = 750, except set 1 (N = 667). With that DRAM size
the stage sizes its own heap (`0x80888120` up to `0xffee0000`). Reset values are not modelled (unwritten registers read 0); PLLD and PLLD2 stand in with
DIVM 1, because U-Boot's `clock_init` divides by it and the APX path, where nothing programs PLLD2, shows that
the real reset value is nonzero. The fidelity of the hardware model is an assumption, not a measurement.

Followed into the installed boot (`--boot0` with an installed boot0): the emulator runs the stage, the stub, and
the stub's hand-off to the AVP, and from there U-Boot's SPL (a second AVP phase; its banner on UART A). It stops
partway through SPL's clock init, which reads flow-controller registers the model does not cover, so it does not
reach U-Boot proper. The first stage touches no PL310 (the L2 cache stays off) and leaves PLLP at 408 MHz, PLLX
at 1 GHz (the CPU's clock), PLLC at 650 MHz and PLLU at 960 MHz (13 MHz oscillator), PLLD and PLLD2 unprogrammed
— the last two the reason SPL's `clock_early_init` is needed (boot-chain.md).
