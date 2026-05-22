package app

import (
	"context"
	"flag"
	"fmt"
	"io"
	"path/filepath"
	"strings"

	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/bootstrap"
	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/doctor"
	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/install"
	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/platform"
	"github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/release"
	remotebootstrap "github.com/codeh007/mtmskills/skills/gomtm-installer/src/internal/remote/bootstrap"
)

const defaultRepository = "codeh007/mtmskills"

func Run(ctx context.Context, args []string, out, errOut io.Writer) error {
	_ = errOut
	if len(args) == 0 {
		usage(out)
		return nil
	}

	switch args[0] {
	case "-h", "--help", "help":
		usage(out)
		return nil
	case "--version", "version":
		fmt.Fprintln(out, release.VersionString())
		return nil
	case "doctor":
		return doctor.Run(ctx, out)
	case "bootstrap":
		return runBootstrap(ctx, args[1:], out)
	case "install":
		return runInstall(ctx, args[1:], out, install.ModeInstall)
	case "dev":
		return runInstall(ctx, args[1:], out, install.ModeDev)
	case "agent-tools":
		return runInstall(ctx, args[1:], out, install.ModeAgentTools)
	case "remote":
		return runRemote(ctx, args[1:], out)
	case "release":
		return runRelease(ctx, args[1:], out)
	case "platform":
		fmt.Fprintln(out, platform.Detect().String())
		return nil
	default:
		return fmt.Errorf("unknown command %q", args[0])
	}
}

func runBootstrap(ctx context.Context, args []string, out io.Writer) error {
	fs := flag.NewFlagSet("bootstrap", flag.ContinueOnError)
	fs.SetOutput(out)
	dryRun := fs.Bool("dry-run", false, "show actions without applying them")
	if err := fs.Parse(args); err != nil {
		return err
	}
	return bootstrap.Run(ctx, bootstrap.Options{DryRun: *dryRun}, out)
}

func runInstall(ctx context.Context, args []string, out io.Writer, mode install.Mode) error {
	fs := flag.NewFlagSet(string(mode), flag.ContinueOnError)
	fs.SetOutput(out)
	dryRun := fs.Bool("dry-run", false, "show actions without applying them")
	if err := fs.Parse(args); err != nil {
		return err
	}
	return install.Run(ctx, install.Request{Mode: mode, DryRun: *dryRun, Packages: fs.Args()}, out)
}

func runRemote(ctx context.Context, args []string, out io.Writer) error {
	if len(args) == 0 {
		return fmt.Errorf("remote requires a subcommand")
	}
	if args[0] != "bootstrap" {
		return fmt.Errorf("unknown remote subcommand %q", args[0])
	}
	fs := flag.NewFlagSet("remote bootstrap", flag.ContinueOnError)
	fs.SetOutput(out)
	dryRun := fs.Bool("dry-run", false, "show actions without applying them")
	if err := fs.Parse(args[1:]); err != nil {
		return err
	}
	return remotebootstrap.Run(ctx, remotebootstrap.Options{DryRun: *dryRun, Target: strings.Join(fs.Args(), " ")}, out)
}

func runRelease(ctx context.Context, args []string, out io.Writer) error {
	if len(args) == 0 {
		return fmt.Errorf("release requires a subcommand")
	}
	switch args[0] {
	case "urls":
		return runReleaseURLs(args[1:], out)
	case "command":
		return runReleaseCommand(args[1:], out)
	case "bootstrap":
		return runReleaseBootstrap(args[1:], out)
	case "download":
		return runReleaseDownload(ctx, args[1:], out)
	case "verify":
		return runReleaseVerify(args[1:], out)
	case "install":
		return runReleaseInstall(ctx, args[1:], out)
	default:
		return fmt.Errorf("unknown release subcommand %q", args[0])
	}
}

func runReleaseURLs(args []string, out io.Writer) error {
	fs := flag.NewFlagSet("release urls", flag.ContinueOnError)
	fs.SetOutput(out)
	repository := fs.String("repo", defaultRepository, "GitHub repository in owner/name form")
	version := fs.String("version", release.Version, "release tag to resolve")
	if err := fs.Parse(args); err != nil {
		return err
	}
	artifact := release.DefaultArtifact(*repository, *version)
	fmt.Fprintln(out, artifact.BinaryURL())
	fmt.Fprintln(out, artifact.ChecksumURL())
	return nil
}

func runReleaseCommand(args []string, out io.Writer) error {
	fs := flag.NewFlagSet("release command", flag.ContinueOnError)
	fs.SetOutput(out)
	repository := fs.String("repo", defaultRepository, "GitHub repository in owner/name form")
	version := fs.String("version", release.Version, "release tag to resolve")
	output := fs.String("output", "./mtminstaller", "destination binary path")
	if err := fs.Parse(args); err != nil {
		return err
	}
	artifact := release.DefaultArtifact(*repository, *version)
	fmt.Fprintln(out, release.DownloadCommand(artifact, *output))
	return nil
}

func runReleaseBootstrap(args []string, out io.Writer) error {
	fs := flag.NewFlagSet("release bootstrap", flag.ContinueOnError)
	fs.SetOutput(out)
	repository := fs.String("repo", defaultRepository, "GitHub repository in owner/name form")
	version := fs.String("version", release.Version, "release tag to resolve")
	if err := fs.Parse(args); err != nil {
		return err
	}
	artifact := release.DefaultArtifact(*repository, *version)
	fmt.Fprint(out, release.BootstrapScript(artifact))
	return nil
}

func runReleaseDownload(ctx context.Context, args []string, out io.Writer) error {
	fs := flag.NewFlagSet("release download", flag.ContinueOnError)
	fs.SetOutput(out)
	repository := fs.String("repo", defaultRepository, "GitHub repository in owner/name form")
	version := fs.String("version", release.Version, "release tag to download")
	destination := fs.String("output", "./mtminstaller", "destination binary path")
	if err := fs.Parse(args); err != nil {
		return err
	}
	artifact := release.DefaultArtifact(*repository, *version)
	checksumPath := *destination + ".sha256"
	if err := release.Download(ctx, artifact.BinaryURL(), *destination); err != nil {
		return err
	}
	if err := release.Download(ctx, artifact.ChecksumURL(), checksumPath); err != nil {
		return err
	}
	if err := release.VerifyChecksum(*destination, checksumPath); err != nil {
		return err
	}
	fmt.Fprintf(out, "release: downloaded %s\n", filepath.Clean(*destination))
	fmt.Fprintf(out, "release: verified %s\n", filepath.Clean(checksumPath))
	return nil
}

func runReleaseVerify(args []string, out io.Writer) error {
	fs := flag.NewFlagSet("release verify", flag.ContinueOnError)
	fs.SetOutput(out)
	checksumPath := fs.String("checksum", "", "path to sha256 checksum file")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() != 1 {
		return fmt.Errorf("release verify requires exactly one binary path")
	}
	if *checksumPath == "" {
		return fmt.Errorf("release verify requires --checksum")
	}
	if err := release.VerifyChecksum(fs.Arg(0), *checksumPath); err != nil {
		return err
	}
	fmt.Fprintln(out, "release: checksum verified")
	return nil
}

func runReleaseInstall(ctx context.Context, args []string, out io.Writer) error {
	fs := flag.NewFlagSet("release install", flag.ContinueOnError)
	fs.SetOutput(out)
	repository := fs.String("repo", defaultRepository, "GitHub repository in owner/name form")
	version := fs.String("version", release.Version, "release tag to install")
	destination := fs.String("output", "./mtminstaller", "destination binary path")
	if err := fs.Parse(args); err != nil {
		return err
	}
	artifact := release.DefaultArtifact(*repository, *version)
	checksumPath := *destination + ".sha256"
	if err := release.Download(ctx, artifact.BinaryURL(), *destination); err != nil {
		return err
	}
	if err := release.Download(ctx, artifact.ChecksumURL(), checksumPath); err != nil {
		return err
	}
	if err := release.VerifyChecksum(*destination, checksumPath); err != nil {
		return err
	}
	if err := release.MakeExecutable(*destination); err != nil {
		return err
	}
	fmt.Fprintf(out, "release: installed %s\n", filepath.Clean(*destination))
	return nil
}

func usage(out io.Writer) {
	fmt.Fprintln(out, "mtminstaller - gomtm installer")
	fmt.Fprintln(out, "")
	fmt.Fprintln(out, "Usage:")
	fmt.Fprintln(out, "  mtminstaller doctor")
	fmt.Fprintln(out, "  mtminstaller bootstrap [--dry-run]")
	fmt.Fprintln(out, "  mtminstaller install [--dry-run] [packages...]")
	fmt.Fprintln(out, "  mtminstaller dev [--dry-run] [packages...]")
	fmt.Fprintln(out, "  mtminstaller agent-tools [--dry-run] [packages...]")
	fmt.Fprintln(out, "  mtminstaller remote bootstrap [--dry-run] <target>")
	fmt.Fprintln(out, "  mtminstaller release urls [--repo owner/name] [--version tag]")
	fmt.Fprintln(out, "  mtminstaller release command [--repo owner/name] [--version tag] [--output path]")
	fmt.Fprintln(out, "  mtminstaller release bootstrap [--repo owner/name] [--version tag]")
	fmt.Fprintln(out, "  mtminstaller release download [--repo owner/name] [--version tag] [--output path]")
	fmt.Fprintln(out, "  mtminstaller release verify --checksum path <binary>")
	fmt.Fprintln(out, "  mtminstaller release install [--repo owner/name] [--version tag] [--output path]")
	fmt.Fprintln(out, "  mtminstaller platform")
	fmt.Fprintln(out, "  mtminstaller --version")
}
