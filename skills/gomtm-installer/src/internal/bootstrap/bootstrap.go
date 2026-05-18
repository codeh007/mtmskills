package bootstrap

import (
	"context"
	"fmt"
	"io"

	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/platform"
)

type Options struct {
	DryRun bool
}

func Run(_ context.Context, opts Options, out io.Writer) error {
	p := platform.Detect()
	fmt.Fprintf(out, "bootstrap: platform=%s dry-run=%t\n", p.String(), opts.DryRun)
	if !p.IsSupported() {
		return fmt.Errorf("unsupported platform %s", p.String())
	}
	if opts.DryRun {
		fmt.Fprintln(out, "bootstrap: no changes were applied")
		return nil
	}
	fmt.Fprintln(out, "bootstrap: verified platform compatibility")
	fmt.Fprintln(out, "bootstrap: placeholder implementation completed")
	return nil
}
