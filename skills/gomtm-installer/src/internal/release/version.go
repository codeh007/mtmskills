package release

import (
	"fmt"
	"path/filepath"
	"runtime"
	"strings"
)

var (
	Version = "dev"
	Commit  = "none"
	Date    = "unknown"
)

type Artifact struct {
	Repository string
	Version    string
	OS         string
	Arch       string
}

func VersionString() string {
	return fmt.Sprintf("mtminstaller %s commit=%s date=%s", Version, Commit, Date)
}

func DefaultArtifact(repository, version string) Artifact {
	return Artifact{Repository: repository, Version: normalizeVersion(version), OS: runtime.GOOS, Arch: runtime.GOARCH}
}

func (a Artifact) BinaryName() string {
	return fmt.Sprintf("mtminstaller-%s-%s", a.OS, a.Arch)
}

func (a Artifact) ChecksumName() string {
	return a.BinaryName() + ".sha256"
}

func (a Artifact) BinaryURL() string {
	return a.assetURL(a.BinaryName())
}

func (a Artifact) ChecksumURL() string {
	return a.assetURL(a.ChecksumName())
}

func (a Artifact) assetURL(name string) string {
	return fmt.Sprintf("https://github.com/%s/releases/download/%s/%s", strings.Trim(a.Repository, "/"), normalizeVersion(a.Version), name)
}

func DownloadCommand(a Artifact, destination string) string {
	destination = filepath.Clean(destination)
	checksum := destination + ".sha256"
	return fmt.Sprintf(`mkdir -p %q && curl -fsSL %q -o %q && curl -fsSL %q -o %q && if command -v sha256sum >/dev/null 2>&1; then (cd %q && sha256sum -c %q); elif command -v shasum >/dev/null 2>&1; then expected="$(cut -d' ' -f1 %q)"; actual="$(shasum -a 256 %q | awk '{print $1}')"; [ "$expected" = "$actual" ] || { echo "mtminstaller: checksum mismatch" >&2; exit 1; }; else echo "mtminstaller: sha256 verification tool not found" >&2; exit 1; fi && chmod +x %q`, filepath.Dir(destination), a.BinaryURL(), destination, a.ChecksumURL(), checksum, filepath.Dir(destination), filepath.Base(checksum), checksum, destination, destination)
}

func BootstrapScript(a Artifact) string {
	return fmt.Sprintf(`#!/usr/bin/env bash
set -euo pipefail
repo=%q
version=%q
platform="$(uname -s):$(uname -m)"
case "${platform}" in
  Linux:x86_64|Linux:amd64) os=linux; arch=amd64 ;;
  Linux:aarch64|Linux:arm64) os=linux; arch=arm64 ;;
  Darwin:x86_64|Darwin:amd64) os=darwin; arch=amd64 ;;
  Darwin:aarch64|Darwin:arm64) os=darwin; arch=arm64 ;;
  *) echo "mtminstaller: unsupported platform ${platform}" >&2; exit 1 ;;
esac
base_url="https://github.com/${repo}/releases/download/${version}"
binary_name="mtminstaller-${os}-${arch}"
checksum_name="${binary_name}.sha256"
tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT
curl -fsSL "${base_url}/${binary_name}" -o "${tmpdir}/${binary_name}"
curl -fsSL "${base_url}/${checksum_name}" -o "${tmpdir}/${checksum_name}"
if command -v sha256sum >/dev/null 2>&1; then
  (cd "${tmpdir}" && sha256sum -c "${checksum_name}")
elif command -v shasum >/dev/null 2>&1; then
  expected="$(cut -d' ' -f1 "${tmpdir}/${checksum_name}")"
  actual="$(shasum -a 256 "${tmpdir}/${binary_name}" | awk '{print $1}')"
  [ "${expected}" = "${actual}" ] || { echo "mtminstaller: checksum mismatch" >&2; exit 1; }
else
  echo "mtminstaller: sha256 verification tool not found" >&2
  exit 1
fi
chmod +x "${tmpdir}/${binary_name}"
exec "${tmpdir}/${binary_name}" "$@"
`, a.Repository, normalizeVersion(a.Version))
}

func normalizeVersion(version string) string {
	version = strings.TrimSpace(version)
	if version == "" {
		return Version
	}
	return version
}
