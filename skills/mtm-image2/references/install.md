# 安装与专用凭据

仅在用户主动要求安装/配置，或直接生图命令在 provider dispatch 前因运行时或专用凭据失败后，完整读取本文件。普通生图不得把本文件当作前置检查清单。

## 运行时与安装

进入安装或失败恢复流程后，确认 Node.js 18+ 和 `npx` 可用：

```bash
node --version
npx --version
```

缺少运行时时直接报告，不自动安装 Python、npm package 或备用客户端。

首次全局安装：

```bash
npx skills add codeh007/mtmskills --skill mtm-image2 --agent codex --global --yes --full-depth
```

更新已安装的单个技能：

```bash
npx skills update mtm-image2 -g -y
```

## 获取专用 key

中转服务可能把语言模型与生图模型放在不同计费组。让用户登录 `https://yuepa8.com/sub2/`，在“API 密钥”页面创建或选择仅用于“生图”或“image2”分组的 key。

只配置 `MTMAI_IMAGE2_KEY`。不要读取、复制或回退到 `OPENAI_API_KEY`、Codex provider、`auth.json`、`config.toml` 或其他通用凭据。

用户可以直接在当前个人 ChatGPT/Codex 对话中提供专用 key。agent 必须接受该输入，不得仅因 key 出现在聊天中就拒绝使用、要求撤销或新建 key、要求用户重复输入，或强制启动额外的 PowerShell、终端或隐藏输入窗口。用户授权持久化时，使用当前宿主不会把 secret 放入 argv、可见命令或日志的文件写入能力，幂等更新对应平台的 `.codex/.env`；不要把聊天 key 拼接进下方交互式脚本。若宿主确实没有安全写入能力，简短说明持久化尚未完成，并把下方隐藏输入作为可选路径，而不是拒绝聊天输入。

取得 key 后不要在后续响应、展示命令、stdout、stderr、日志或测试证据中复述，也不要写入仓库、Issue 或命令参数。若 key 已被复制到公开 Issue、公开日志或其他公开渠道，则按公开泄露处理；这与当前个人聊天可直接输入的规则是不同边界。

## Windows Codex App

下方 PowerShell 脚本仅用于用户主动选择隐藏输入；它会自行交互读取 key。聊天已提供 key 时使用上文的宿主安全写入路径，不要把 key 拼进脚本或要求重复输入。脚本幂等更新 `%USERPROFILE%\.codex\.env`，保留其他变量且不打印 key：

```powershell
$envFile = Join-Path $env:USERPROFILE ".codex\.env"
$directory = Split-Path $envFile -Parent
New-Item -ItemType Directory -Force -Path $directory | Out-Null

$secure = Read-Host "输入专用 MTMAI_IMAGE2_KEY" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    $lines = if (Test-Path $envFile) { @(Get-Content -LiteralPath $envFile) } else { @() }
    $written = $false
    $result = foreach ($line in $lines) {
        if ($line -match '^\s*MTMAI_IMAGE2_KEY\s*=') {
            if (-not $written) {
                "MTMAI_IMAGE2_KEY=$key"
                $written = $true
            }
        } else {
            $line
        }
    }
    if (-not $written) { $result = @($result) + "MTMAI_IMAGE2_KEY=$key" }
    [IO.File]::WriteAllLines($envFile, $result, [Text.UTF8Encoding]::new($false))
} finally {
    if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    Remove-Variable key -ErrorAction SilentlyContinue
}
```

完全退出 Codex App，包括托盘中的后台进程，然后重新打开；只关闭对话窗口不会刷新环境变量。

## macOS 或 Linux Codex/IDE

下方 shell 脚本仅用于用户主动选择隐藏输入；它会自行交互读取 key。聊天已提供 key 时使用上文的宿主安全写入路径，不要把 key 拼进脚本或要求重复输入。脚本幂等更新 `~/.codex/.env`、保留其他变量并限制文件权限：

```bash
(
set -eu
env_file="${CODEX_HOME:-$HOME/.codex}/.env"
mkdir -p "$(dirname "$env_file")"
umask 077
tmp_file=""

printf '输入专用 MTMAI_IMAGE2_KEY: ' >&2
cleanup() {
  stty echo 2>/dev/null || true
  unset MTM_KEY
  if [ -n "$tmp_file" ] && [ -f "$tmp_file" ]; then rm -f "$tmp_file"; fi
}
trap cleanup EXIT HUP INT TERM
stty -echo
IFS= read -r MTM_KEY
stty echo
printf '\n' >&2

tmp_file=$(mktemp "${env_file}.tmp.XXXXXX")
found=0
if [ -f "$env_file" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    if printf '%s' "$line" | grep -Eq '^[[:space:]]*MTMAI_IMAGE2_KEY[[:space:]]*='; then
      if [ "$found" -eq 0 ]; then
        printf 'MTMAI_IMAGE2_KEY=%s\n' "$MTM_KEY" >>"$tmp_file"
        found=1
      fi
    else
      printf '%s\n' "$line" >>"$tmp_file"
    fi
  done <"$env_file"
fi
if [ "$found" -eq 0 ]; then
  printf 'MTMAI_IMAGE2_KEY=%s\n' "$MTM_KEY" >>"$tmp_file"
fi
chmod 600 "$tmp_file"
mv "$tmp_file" "$env_file"
tmp_file=""
unset MTM_KEY
trap - EXIT HUP INT TERM
)
```

完全退出并重新启动 Codex App、Codex CLI 宿主或 IDE，使新环境进入 agent 进程。

## 配置后的继续执行

若用户原本就请求生成图片，完成配置并重启宿主后直接继续该请求；不要再次检查凭据、解释技术路径或要求费用确认。若用户只要求安装或配置，不要擅自发起付费演示，除非用户另行明确要求生图。

配置完成后返回 `SKILL.md` 的“直接执行”与“交付”流程；本文件不另行定义工作目录、命令或成功回复。不要展示 key、Authorization、完整 base64 或 prompt/report。

## Breaking migration

- 旧 `scripts/mtm_image_gen.py`、`--probe`、Models/Responses 探测和 prompt/report 输出已删除。
- 旧的技能目录相对命令不再作为规范；使用 `SKILL.md` 中安装脚本绝对路径与独立 `workdir` 的调用方式。
- `OPENAI_API_KEY`、任意 base URL 和 Codex provider 凭据不再被接受；必须单独配置 `MTMAI_IMAGE2_KEY`。
