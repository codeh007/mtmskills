package main

import (
	"context"
	"fmt"
	"os"

	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/app"
)

func main() {
	if err := app.Run(context.Background(), os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, "mtminstaller:", err)
		os.Exit(1)
	}
}
