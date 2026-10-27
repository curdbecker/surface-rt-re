# Build environment for this repository: every tool build.sh needs (payloads, U-Boot, the disk-mode image). The
# sources are not copied into the image; the checkout is mounted:
#   git clone --recurse-submodules <repository> && cd surface-rt-re
#   docker build -t surface-rt-re .
#   docker run --rm -v "$PWD:/src" surface-rt-re [payloads | u-boot | diskmode | all]
# Results land in out/ (payloads in payloads/), owned like the checkout. The disk-mode build needs root and the
# CAP_SYS_CHROOT / CAP_MKNOD capabilities, which a default docker run grants (no --privileged), and network at
# run time (signature-checked pmOS/Alpine packages). Its work directories stay inside the container, since a
# bind mount (Docker Desktop on macOS in particular) supports neither chroot nor device nodes.
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl tar openssl python3 patch git build-essential \
        qemu-user-static device-tree-compiler gcc-arm-none-eabi \
        bc bison flex libssl-dev libgnutls28-dev uuid-dev swig python3-dev python3-setuptools python3-pyelftools \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'

WORKDIR /src
ENTRYPOINT ["sh", "/src/build.sh"]
CMD ["all"]
