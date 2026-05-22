#!/usr/bin/env python3
"""Run GitHub Actions locally with nektos/act.

It installs or finds the upstream `act` CLI, builds a transparent command line,
prints it, and executes it from the target repository.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterable

GITHUB_API_LATEST = "https://api.github.com/repos/nektos/act/releases/latest"
DEFAULT_MEDIUM_RUNNERS = {
    "ubuntu-latest": "ghcr.io/catthehacker/ubuntu:act-latest",
    "ubuntu-22.04": "ghcr.io/catthehacker/ubuntu:act-22.04",
    "ubuntu-20.04": "ghcr.io/catthehacker/ubuntu:act-20.04",
    "ubuntu-18.04": "ghcr.io/catthehacker/ubuntu:act-18.04",
}


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)

    if args.command == "doctor":
        return doctor(repo, args)

    act = resolve_act(args.act, args.install, args.version)
    cmd = build_act_command(act, repo, args)
    print("+ " + shell_join(cmd), flush=True)
    return subprocess.call(cmd, cwd=repo)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在本机用 upstream nektos/act 运行 GitHub Actions。"
    )
    parser.add_argument(
        "command",
        choices=["run", "list", "validate", "doctor"],
        help="run 执行 workflow；list 列出；validate 只校验；doctor 检查本机环境。",
    )
    parser.add_argument("event", nargs="?", default="push", help="事件名，默认 push。")
    parser.add_argument("--repo", default=".", help="目标 git 仓库目录。")
    parser.add_argument("--act", help="act 二进制路径；不传则优先 PATH，再按需安装。")
    parser.add_argument("--install", action="store_true", help="找不到 act 时安装到用户缓存目录。")
    parser.add_argument("--version", default="latest", help="act 版本，例如 v0.2.88；默认 latest。")
    parser.add_argument("-W", "--workflow", help="workflow 文件或目录，传给 act -W。")
    parser.add_argument("-j", "--job", help="只运行指定 job id。")
    parser.add_argument("-e", "--event-file", help="事件 payload JSON 文件。")
    parser.add_argument("--input", action="append", default=[], help="workflow_dispatch 输入 KEY=VALUE，可重复。")
    parser.add_argument("--input-file", help=".env 格式输入文件。")
    parser.add_argument("--secret", action="append", default=[], help="secret 名称或 KEY=VALUE，可重复。")
    parser.add_argument("--secret-file", default=".secrets", help="secret 文件；默认 .secrets。")
    parser.add_argument("--var", action="append", default=[], help="GitHub repository variable，可重复。")
    parser.add_argument("--var-file", default=".vars", help="vars 文件；默认 .vars。")
    parser.add_argument("--env", action="append", default=[], help="容器环境变量，可重复。")
    parser.add_argument("--env-file", default=".env", help="env 文件；默认 .env。")
    parser.add_argument(
        "--runner-size",
        choices=["micro", "medium", "none"],
        default="medium",
        help="runner 映射：medium 使用 catthehacker/ubuntu，micro 使用 act 默认，none 不追加 -P。",
    )
    parser.add_argument("--platform", action="append", default=[], help="额外 -P 映射 runner=image。")
    parser.add_argument("--container-architecture", help="例如 linux/amd64；Apple Silicon 常用。")
    parser.add_argument("--bind", action="store_true", help="传给 act --bind，绑定工作区而不是复制。")
    parser.add_argument("--offline", action="store_true", help="传给 act --action-offline-mode。")
    parser.add_argument("--no-pull", action="store_true", help="传给 act --pull=false。")
    parser.add_argument("--artifact-path", help="启用 artifact server 并指定目录。")
    parser.add_argument("--cache-path", help="指定 cache server 存储目录。")
    parser.add_argument("--json", action="store_true", help="act JSON 日志。")
    parser.add_argument("--verbose", action="store_true", help="act verbose 日志。")
    parser.add_argument("--dryrun", action="store_true", help="传给 act --dryrun。")
    parser.add_argument("--", dest="extra", nargs=argparse.REMAINDER, help="追加原样 act 参数。")
    return parser.parse_args()


def resolve_repo(raw: str) -> Path:
    repo = Path(raw).expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"仓库目录不存在: {repo}")
    workflows = repo / ".github" / "workflows"
    if not workflows.exists():
        raise SystemExit(f"未找到 {workflows}；请在含 GitHub Actions 的仓库运行。")
    return repo


def resolve_act(raw_path: str | None, install: bool, version: str) -> str:
    if raw_path:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"act 路径不存在: {path}")
        return str(path)

    found = shutil.which("act")
    if found:
        return found
    if not install:
        raise SystemExit("未在 PATH 中找到 act；请先安装，或加 --install 自动安装。")
    return str(install_act(version))


def install_act(version: str) -> Path:
    tag, assets = latest_release() if version == "latest" else (version, [])
    asset_name = asset_name_for_current_platform()
    url = find_asset_url(tag, assets, asset_name)

    install_dir = Path.home() / ".cache" / "github-actions-local" / tag
    binary = install_dir / ("act.exe" if platform.system().lower().startswith("win") else "act")
    if binary.exists():
        return binary

    install_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".zip" if asset_name.endswith(".zip") else ".tar.gz"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        download(url, tmp_path)
        extract_binary(tmp_path, install_dir, binary.name)
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    finally:
        tmp_path.unlink(missing_ok=True)
    return binary


def latest_release() -> tuple[str, list[dict[str, str]]]:
    request = urllib.request.Request(
        GITHUB_API_LATEST,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "github-actions-local"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    return data["tag_name"], data.get("assets", [])


def asset_name_for_current_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    os_name = {"linux": "Linux", "darwin": "Darwin", "windows": "Windows"}.get(system)
    arch = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "i386": "i386",
        "i686": "i386",
        "riscv64": "riscv64",
        "armv7l": "armv7",
        "armv6l": "armv6",
    }.get(machine)
    if not os_name or not arch:
        raise SystemExit(f"当前平台暂未映射 act 预构建资产: {system}/{machine}")
    ext = "zip" if os_name == "Windows" else "tar.gz"
    return f"act_{os_name}_{arch}.{ext}"


def find_asset_url(tag: str, assets: list[dict[str, str]], asset_name: str) -> str:
    for asset in assets:
        if asset.get("name") == asset_name:
            return asset["browser_download_url"]
    return f"https://github.com/nektos/act/releases/download/{tag}/{asset_name}"


def download(url: str, dest: Path) -> None:
    print(f"下载 act: {url}", flush=True)
    request = urllib.request.Request(url, headers={"User-Agent": "github-actions-local"})
    with urllib.request.urlopen(request, timeout=120) as response, dest.open("wb") as output:
        shutil.copyfileobj(response, output)


def extract_binary(archive: Path, dest_dir: Path, binary_name: str) -> None:
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            member = first_member_named(zf.namelist(), binary_name)
            zf.extract(member, dest_dir)
            extracted = dest_dir / member
    else:
        with tarfile.open(archive, "r:gz") as tf:
            names = tf.getnames()
            member = first_member_named(names, binary_name)
            tf.extract(member, dest_dir, filter="data")
            extracted = dest_dir / member
    target = dest_dir / binary_name
    if extracted != target:
        shutil.move(str(extracted), target)


def first_member_named(names: Iterable[str], binary_name: str) -> str:
    for name in names:
        if Path(name).name == binary_name:
            return name
    raise SystemExit(f"压缩包中未找到 {binary_name}")


def build_act_command(act: str, repo: Path, args: argparse.Namespace) -> list[str]:
    cmd = [act]
    if args.command == "list":
        cmd.append("--list")
        if args.event != "push":
            cmd.append(args.event)
    elif args.command == "validate":
        cmd.extend([args.event, "--dryrun", "--validate"])
    else:
        cmd.append(args.event)

    add_opt(cmd, "-W", args.workflow)
    add_opt(cmd, "-j", args.job)
    add_opt(cmd, "-e", args.event_file)
    add_repeated(cmd, "--input", args.input)
    add_opt(cmd, "--input-file", args.input_file)
    add_repeated(cmd, "--secret", args.secret)
    add_file_if_exists(cmd, "--secret-file", repo / args.secret_file)
    add_repeated(cmd, "--var", args.var)
    add_file_if_exists(cmd, "--var-file", repo / args.var_file)
    add_repeated(cmd, "--env", args.env)
    add_file_if_exists(cmd, "--env-file", repo / args.env_file)

    if args.runner_size == "medium":
        for runner, image in DEFAULT_MEDIUM_RUNNERS.items():
            cmd.extend(["-P", f"{runner}={image}"])
    add_repeated(cmd, "-P", args.platform)
    add_opt(cmd, "--container-architecture", args.container_architecture)
    add_opt(cmd, "--artifact-server-path", args.artifact_path)
    add_opt(cmd, "--cache-server-path", args.cache_path)

    if args.bind:
        cmd.append("--bind")
    if args.offline:
        cmd.append("--action-offline-mode")
    if args.no_pull:
        cmd.append("--pull=false")
    if args.json:
        cmd.append("--json")
    if args.verbose:
        cmd.append("--verbose")
    if args.dryrun:
        cmd.append("--dryrun")
    if args.extra:
        cmd.extend(args.extra)
    return cmd


def doctor(repo: Path, args: argparse.Namespace) -> int:
    print(f"repo: {repo}")
    print(f"workflows: {repo / '.github' / 'workflows'}")
    act_path = shutil.which("act") or "未找到"
    docker_path = shutil.which("docker") or "未找到"
    print(f"act: {act_path}")
    print(f"docker: {docker_path}")
    if docker_path != "未找到":
        subprocess.call([docker_path, "version"], cwd=repo)
    if act_path != "未找到":
        subprocess.call([act_path, "--version"], cwd=repo)
        subprocess.call([act_path, "--bug-report"], cwd=repo)
    if args.install and act_path == "未找到":
        print(f"installed act: {install_act(args.version)}")
    return 0


def add_opt(cmd: list[str], name: str, value: str | None) -> None:
    if value:
        cmd.extend([name, value])


def add_repeated(cmd: list[str], name: str, values: list[str]) -> None:
    for value in values:
        cmd.extend([name, value])


def add_file_if_exists(cmd: list[str], name: str, path: Path) -> None:
    if path.exists():
        cmd.extend([name, str(path)])


def shell_join(cmd: list[str]) -> str:
    return " ".join(sh_quote(part) for part in cmd)


def sh_quote(value: str) -> str:
    if not value or any(ch.isspace() or ch in "'\"$`\\" for ch in value):
        return "'" + value.replace("'", "'\\''") + "'"
    return value


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
