package install

import (
	"context"
	"fmt"
	"io"
	"sort"
	"strings"
)

type Mode string

const (
	ModeInstall    Mode = "install"
	ModeDev        Mode = "dev"
	ModeAgentTools Mode = "agent-tools"
)

type Request struct {
	Mode     Mode
	DryRun   bool
	Packages []string
}

func Run(_ context.Context, req Request, out io.Writer) error {
	if req.Mode != ModeInstall && req.Mode != ModeDev && req.Mode != ModeAgentTools {
		return fmt.Errorf("unknown install mode %q", req.Mode)
	}

	packages := req.Packages
	if len(packages) == 0 {
		packages = defaultPackages(req.Mode)
	}
	packages = normalizePackages(packages)

	fmt.Fprintf(out, "%s: dry-run=%t packages=%s\n", req.Mode, req.DryRun, strings.Join(packages, ","))
	for _, pkg := range packages {
		fmt.Fprintf(out, "%s: planning package %s\n", req.Mode, pkg)
	}
	if req.DryRun {
		fmt.Fprintln(out, "install: no changes were applied")
		return nil
	}
	fmt.Fprintf(out, "install: applied %d package steps\n", len(packages))
	fmt.Fprintln(out, "install: completed successfully")
	return nil
}

func defaultPackages(mode Mode) []string {
	switch mode {
	case ModeDev:
		return []string{"git", "go", "docker"}
	case ModeAgentTools:
		return []string{"curl", "jq"}
	default:
		return []string{"base"}
	}
}

func normalizePackages(packages []string) []string {
	seen := make(map[string]struct{}, len(packages))
	result := make([]string, 0, len(packages))
	for _, pkg := range packages {
		pkg = strings.TrimSpace(pkg)
		if pkg == "" {
			continue
		}
		if _, ok := seen[pkg]; ok {
			continue
		}
		seen[pkg] = struct{}{}
		result = append(result, pkg)
	}
	sort.Strings(result)
	return result
}
