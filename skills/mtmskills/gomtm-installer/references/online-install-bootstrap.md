# Online Install Bootstrap Notes

The public bootstrap path should stay minimal and predictable.

## Current shape

`mtminstaller release bootstrap` prints a tiny shell script that:

1. detects `linux` / `darwin` and `amd64` / `arm64`,
2. downloads `mtminstaller-<os>-<arch>` from the release asset URL,
3. downloads the matching `.sha256`,
4. verifies the checksum,
5. marks the binary executable,
6. `exec`s the downloaded binary.

## Intended public use

```bash
curl -fsSL https://.../install.sh | bash
```

The script should not contain installer business logic. It should only bootstrap the prebuilt `mtminstaller` binary.

## Keep it short

Prefer a single `case` for platform detection, a temporary directory, and one execution path. Avoid extra abstractions in the script body unless they remove duplication elsewhere.
