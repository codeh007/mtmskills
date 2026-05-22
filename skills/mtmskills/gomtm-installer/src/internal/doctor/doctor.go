package doctor

import (
	"context"
	"fmt"
	"io"

	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/platform"
)

func Run(_ context.Context, out io.Writer) error {
	p := platform.Detect()
	fmt.Fprintf(out, "doctor: platform=%s\n", p.String())
	if !p.IsSupported() {
		return fmt.Errorf("unsupported platform %s", p.String())
	}
	fmt.Fprintln(out, "doctor: supported platform detected")
	fmt.Fprintln(out, "doctor: placeholder checks passed")
	return nil
}
