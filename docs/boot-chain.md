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

1. **Unsigned metadata decides what is verified and where execution starts.** The `UEFIDATA` block (boot0
   `0x1F1000`) supplies load address, length of the checked data and entry offset; it is not covered by the
   signature. It lies in the eMMC boot partitions, writable from the OS (Linux: `force_ro`, a software switch), so
   user-writable in the chain's own threat model: Windows RT's lock-down is aimed at the device's owner,
   administrators included (no unsigned code, no other OS, Secure Boot not switchable). It is used by the most
   privileged code before anything else runs.
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

## Booting without the monitor (U-Boot via RCM)

The preferred route to run our own code without opening the device or touching the boot flash: preload U-Boot
over USB through the boot ROM's recovery mode (RCM / Fusée Gelée) from a PC, then boot Linux from U-Boot. U-Boot's
`surface-rt_defconfig` is documented as an APX RAM preload (Power + Volume up), and `re-crypt` (grate-driver)
carries a `surface-rt` BCT. It needs a USB A-to-A cable and a PC at every cold boot.
