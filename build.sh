#!/bin/sh
# Builds what this repository needs, after applying its patches to the submodules:
#   payloads  payloads/*.bin and payloads/securet30sec_functions.h (committed; see payloads/Makefile)
#   u-boot    U-Boot from the u-boot submodule (surface-rt_defconfig): out/u-boot-dtb-tegra.bin (SPL + U-Boot
#             proper, which srt_uboot.py installs and the APX preload also uses), out/u-boot-dtb.bin (U-Boot
#             proper alone), and its symbols out/u-boot.map (securet30 run --uboot-map)
#   fusee     fusee-tools' Tegra30 payloads (fusee-tools/payloads/out/T30, patch_irom.bin among them)
#   tegrarcm  fusee-tools/tegrarcm/src/tegrarcm, always on the host (it drives the host's USB)
#   diskmode  out/pmos-surface-rt-diskmode.img (diskmode/build-pmos-surface-rt-diskmode.sh; root, Linux)
#   all       all of the above (the default)
#
# Usage: build.sh [--local] [target...]
# By default every target but tegrarcm runs in the container of ./Dockerfile (needs docker); --local runs them
# all on the host, with the tools the Dockerfile lists. Only the diskmode step runs as root (through sudo on the
# host). Patches are applied only where their files do not hold them yet; files changed otherwise are built as
# they are. Work directories live under $WORK (default: a new temporary directory), outside the checkout.
set -eu

SRC=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$SRC/out}
WORK=${WORK:-$(mktemp -d)}
CROSS_COMPILE=${CROSS_COMPILE:-arm-none-eabi-}
IMAGE=surface-rt-re
P=$SRC/patches

die() {
	echo "error: $*" >&2
	exit 1
}

as_root() {
	if [ "$(id -u)" = 0 ]; then "$@"; else sudo "$@"; fi
}

# Exits unless every command named is on PATH.
need() {
	missing=
	for c in "$@"; do
		command -v "$c" >/dev/null 2>&1 || missing="$missing $c"
	done
	[ -z "$missing" ] || die "missing on the host:$missing"
}

# apply_patches DIR PATCH...: apply the series to the git tree DIR unless the files it touches already hold
# its result; if they hold something else, warn and leave them.
apply_patches() {
	dir=$1
	shift
	idx=$WORK/patch-index
	rm -f "$idx"
	GIT_INDEX_FILE=$idx git -C "$dir" read-tree HEAD
	GIT_INDEX_FILE=$idx git -C "$dir" apply --cached "$@"
	paths=$(git -C "$dir" apply --numstat "$@" | cut -f3)
	# shellcheck disable=SC2086 # one path per word
	if GIT_INDEX_FILE=$idx git -C "$dir" diff --quiet -- $paths; then
		:
	elif git -C "$dir" apply --check "$@" 2>/dev/null; then
		git -C "$dir" apply "$@"
		echo "applied to ${dir#"$SRC"/}: $(for p in "$@"; do basename "$p"; done | tr '\n' ' ')"
	else
		echo "warning: ${dir#"$SRC"/} differs from its patches; building it as it is" >&2
	fi
}

patch_target() {
	case $1 in
		u-boot) apply_patches "$SRC/u-boot" "$P"/u-boot/0*.patch ;;
		fusee)
			apply_patches "$SRC/fusee-tools" "$P/fusee/0001-scripts-use-tegrarcm-instead-of-nvflash.patch"
			apply_patches "$SRC/fusee-tools/fusee-launcher-new" \
				"$P/fusee/0001-Skip-USB-teardown-after-the-trigger-without-tty-outp.patch"
			;;
		tegrarcm)
			apply_patches "$SRC/fusee-tools/tegrarcm" \
				"$P/fusee/0001-main-send-GET_PLATFORM_INFO-before-reading-the-BCT.patch"
			;;
	esac
}

check_target() {
	case $1 in
		payloads) need make "${CROSS_COMPILE}gcc" python3 ;;
		u-boot) need make "${CROSS_COMPILE}gcc" bison flex ;;
		fusee) need make "${CROSS_COMPILE}gcc" ;;
		tegrarcm)
			need make autoreconf pkg-config c++
			pkg-config --exists libusb-1.0 || die "libusb-1.0 not found by pkg-config (needed by tegrarcm)"
			;;
		diskmode) [ "$(id -u)" = 0 ] || need sudo ;;
	esac
}

build_payloads() {
	make -C "$SRC/payloads"
}

build_u_boot() {
	b=$WORK/u-boot
	# Reproducible: the build timestamp is the U-Boot commit's.
	SOURCE_DATE_EPOCH=$(git -C "$SRC/u-boot" log -1 --format=%ct)
	export SOURCE_DATE_EPOCH
	# The same compiler for every step: Kconfig evaluates it, so a defconfig made against another one would
	# leave options the build then asks about.
	set -- -C "$SRC/u-boot" O="$b" CROSS_COMPILE="$CROSS_COMPILE"
	make "$@" surface-rt_defconfig
	make "$@" -j"$(getconf _NPROCESSORS_ONLN)"
	cp "$b/u-boot-dtb-tegra.bin" "$b/u-boot-dtb.bin" "$OUT/"
	cp "$b/System.map" "$OUT/u-boot.map"
}

build_fusee() {
	make -C "$SRC/fusee-tools/payloads" -j1 ARCH=arm CROSS_COMPILE="$CROSS_COMPILE" T30
}

build_tegrarcm() {
	t=$SRC/fusee-tools/tegrarcm
	[ -f "$t/Makefile" ] || (cd "$t" && ./autogen.sh)
	make -C "$t"
}

build_diskmode() {
	img=$OUT/pmos-surface-rt-diskmode.img
	as_root env WORK="$WORK/pmos" sh "$SRC/diskmode/build-pmos-surface-rt-diskmode.sh" "$img"
	[ "$(id -u)" = 0 ] || sudo chown "$(id -u):$(id -g)" "$img"
}

local=
if [ "${1:-}" = --local ]; then
	local=1
	shift
fi
[ $# -gt 0 ] || set -- all
targets=
for t in "$@"; do
	case $t in
		payloads | u-boot | fusee | tegrarcm | diskmode) targets="$targets $t" ;;
		all) targets="$targets payloads u-boot fusee tegrarcm diskmode" ;;
		*) die "unknown target '$t' (payloads, u-boot, fusee, tegrarcm, diskmode, all)" ;;
	esac
done

# The host part: tegrarcm always, everything with --local; the rest goes to the container.
host= container=
for t in $targets; do
	if [ -n "$local" ] || [ "$t" = tegrarcm ]; then host="$host $t"; else container="$container $t"; fi
done
[ -z "$container" ] || command -v docker >/dev/null 2>&1 || die "docker not found; install it, or build on the host with --local"
need git
for t in $host; do check_target "$t"; done
mkdir -p "$OUT"
# Patches are applied on the host, so the container does not leave root-owned files in the submodules.
if [ -z "${PATCHES_APPLIED:-}" ]; then
	for t in $targets; do patch_target "$t"; done
fi

if [ -n "$container" ]; then
	# no build context: the image copies nothing, the checkout is mounted
	docker build -q -t "$IMAGE" - <"$SRC/Dockerfile" >/dev/null
	# shellcheck disable=SC2086 # one target per word
	docker run --rm -v "$SRC:/src" -v "$OUT:/out" -e OUT=/out -e PATCHES_APPLIED=1 "$IMAGE" $container
fi
for t in $host; do
	case $t in
		u-boot) build_u_boot ;;
		*) "build_$t" ;;
	esac
done

# Run as root (the container): hand the results to the checkout's owner.
if [ "$(id -u)" = 0 ]; then
	for d in "$OUT" "$SRC/payloads" "$SRC/fusee-tools/payloads/out"; do
		[ ! -e "$d" ] || chown -R "$(stat -c %u:%g "$SRC")" "$d"
	done
fi
