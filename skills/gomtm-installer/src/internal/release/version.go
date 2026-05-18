package release

import (
	"fmt"
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

func normalizeVersion(version string) string {
	version = strings.TrimSpace(version)
	if version == "" {
		return Version
	}
	return version
}
