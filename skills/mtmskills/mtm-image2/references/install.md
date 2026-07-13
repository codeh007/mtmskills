# 安装与专用凭据

## 运行时与安装

先确认 Node.js 18+ 和 `npx` 可用：

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

只配置 `MTMAI_IMAGE2_KEY`。不要读取、复制或回退到 `OPENAI_API_KEY`、Codex provider、`auth.json`、`config.toml` 或其他通用凭据；不要把 key 写入仓库、Issue、命令参数或聊天回执。

## Windows Codex App

在 PowerShell 中运行以下脚本。它通过隐藏输入读取 key，幂等更新 `%USERPROFILE%\.codex\.env`，保留其他变量且不打印 key：

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

在交互式 shell 中运行以下脚本。它隐藏输入、幂等更新 `~/.codex/.env`、保留其他变量并限制文件权限：

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

## 首次演示

确认重启后的进程已有 `MTMAI_IMAGE2_KEY`。真实验证会产生外部费用；得到用户授权后，在技能目录只执行一次低成本正常生图：

```bash
node scripts/generate.mjs --prompt "70年代中国农村家庭的全家福照片" --size 1024x1024 --quality low
```

只报告最终图片路径，不展示 key、Authorization、完整 base64 或 prompt/report。

## Breaking migration

- 旧 `scripts/mtm_image_gen.py`、`--probe`、Models/Responses 探测和 prompt/report 输出已删除。
- 旧命令必须改为 `node scripts/generate.mjs --prompt "<图片描述>"`。
- `OPENAI_API_KEY`、任意 base URL 和 Codex provider 凭据不再被接受；必须单独配置 `MTMAI_IMAGE2_KEY`。
