package platform

import (
	"runtime"
	"strings"
)

type Platform struct {
	OS   string
	Arch string
}

func Detect() Platform {
	return Platform{OS: runtime.GOOS, Arch: runtime.GOARCH}
}

func (p Platform) String() string {
	return strings.TrimSpace(p.OS + "/" + p.Arch)
}

func (p Platform) IsSupported() bool {
	switch p.OS {
	case "linux", "darwin", "windows":
	default:
		return false
	}
	switch p.Arch {
	case "amd64", "arm64":
	default:
		return false
	}
	return true
}
