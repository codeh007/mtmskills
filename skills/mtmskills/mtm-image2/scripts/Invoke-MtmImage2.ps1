param(
  [string]$Prompt,
  [string]$PromptFile,
  [string[]]$Image,
  [string]$Mask,
  [string]$Output,
  [string]$PromptOutput,
  [string]$BaseUrl = $env:OPENAI_BASE_URL,
  [string]$ApiKey = $env:OPENAI_API_KEY,
  [string]$Model = $env:OPENAI_IMAGE_MODEL,
  [string]$Size = "1024x1024",
  [ValidateSet("auto", "low", "medium", "high")]
  [string]$Quality = "high",
  [int]$N = 1,
  [ValidateSet("png", "jpeg", "webp")]
  [string]$Format = "png",
  [int]$Compression = -1,
  [ValidateSet("auto", "opaque")]
  [string]$Background,
  [ValidateSet("auto", "low")]
  [string]$Moderation = "auto",
  [string]$OutputDir = $env:MTM_IMAGE2_OUTPUT_DIR,
  [string]$ReportOutput
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Net.Http

function Get-DefaultValue($Value, $Fallback) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return $Fallback }
  return $Value
}

function Get-CodexAuthKey {
  $authPath = Join-Path $HOME ".codex/auth.json"
  if (-not (Test-Path -LiteralPath $authPath)) { return $null }
  try {
    $auth = Get-Content -LiteralPath $authPath -Raw | ConvertFrom-Json
    if ($auth.OPENAI_API_KEY) { return [string]$auth.OPENAI_API_KEY }
    if ($auth.SUB2API_API_KEY) { return [string]$auth.SUB2API_API_KEY }
    if ($auth.api_key) { return [string]$auth.api_key }
    if ($auth.apiKey) { return [string]$auth.apiKey }
  } catch {
    return $null
  }
  return $null
}

function Normalize-BaseUrl([string]$Url) {
  $u = Get-DefaultValue $Url "https://sub2api.yuepa8.com"
  $u = $u.TrimEnd("/")
  if ($u.EndsWith("/v1")) { return $u }
  return "$u/v1"
}

function New-Slug([string]$Text) {
  $slug = $Text.ToLowerInvariant() -replace "[^a-z0-9\u4e00-\u9fff]+", "-"
  $slug = $slug.Trim("-")
  if ($slug.Length -gt 40) { $slug = $slug.Substring(0, 40).Trim("-") }
  if ([string]::IsNullOrWhiteSpace($slug)) { return "image" }
  return $slug
}

function Get-RequestPrompt {
  if (-not [string]::IsNullOrWhiteSpace($PromptFile)) {
    if (-not (Test-Path -LiteralPath $PromptFile)) {
      throw "Prompt file not found: $PromptFile"
    }
    return Get-Content -LiteralPath $PromptFile -Raw
  }
  if ([string]::IsNullOrWhiteSpace($Prompt)) {
    throw "Provide -Prompt or -PromptFile."
  }
  return $Prompt
}

function Save-Text([string]$Path, [string]$Text) {
  $parent = Split-Path -Parent $Path
  if (-not [string]::IsNullOrWhiteSpace($parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

function Save-Json([string]$Path, $Value) {
  $parent = Split-Path -Parent $Path
  if (-not [string]::IsNullOrWhiteSpace($parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  $Value | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Save-ImageData($Item, [string]$TargetPath) {
  $parent = Split-Path -Parent $TargetPath
  if (-not [string]::IsNullOrWhiteSpace($parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  if ($Item.b64_json) {
    [System.IO.File]::WriteAllBytes($TargetPath, [Convert]::FromBase64String([string]$Item.b64_json))
    return
  }
  if ($Item.url) {
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile([string]$Item.url, $TargetPath)
    return
  }
  throw "Image response item has neither b64_json nor url."
}

function Invoke-JsonPost([string]$Url, [hashtable]$Body, [string]$Bearer) {
  $json = $Body | ConvertTo-Json -Depth 8
  $client = New-Object System.Net.Http.HttpClient
  $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", $Bearer)
  $client.DefaultRequestHeaders.UserAgent.ParseAdd("mtm-image2/1.0")
  $client.DefaultRequestHeaders.Accept.ParseAdd("application/json")
  $content = New-Object System.Net.Http.StringContent($json, [System.Text.Encoding]::UTF8, "application/json")
  $response = $client.PostAsync($Url, $content).Result
  $text = $response.Content.ReadAsStringAsync().Result
  if (-not $response.IsSuccessStatusCode) {
    throw "API request failed ($([int]$response.StatusCode)): $text"
  }
  return $text | ConvertFrom-Json
}

function Invoke-MultipartPost([string]$Url, [string]$Bearer, [string]$RequestPrompt) {
  $client = New-Object System.Net.Http.HttpClient
  $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", $Bearer)
  $client.DefaultRequestHeaders.UserAgent.ParseAdd("mtm-image2/1.0")
  $client.DefaultRequestHeaders.Accept.ParseAdd("application/json")
  $form = New-Object System.Net.Http.MultipartFormDataContent
  $openStreams = New-Object System.Collections.Generic.List[System.IO.Stream]

  try {
    $form.Add((New-Object System.Net.Http.StringContent($Model)), "model")
    $form.Add((New-Object System.Net.Http.StringContent($RequestPrompt)), "prompt")
    $form.Add((New-Object System.Net.Http.StringContent($Size)), "size")
    $form.Add((New-Object System.Net.Http.StringContent($Quality)), "quality")
    $form.Add((New-Object System.Net.Http.StringContent([string]$N)), "n")
    $form.Add((New-Object System.Net.Http.StringContent($Format)), "output_format")
    if ($Compression -ge 0) {
      $form.Add((New-Object System.Net.Http.StringContent([string]$Compression)), "output_compression")
    }
    if (-not [string]::IsNullOrWhiteSpace($Background)) {
      $form.Add((New-Object System.Net.Http.StringContent($Background)), "background")
    }

    foreach ($path in $Image) {
      if (-not (Test-Path -LiteralPath $path)) { throw "Image file not found: $path" }
      $stream = [System.IO.File]::OpenRead((Resolve-Path -LiteralPath $path))
      $openStreams.Add($stream)
      $fileContent = New-Object System.Net.Http.StreamContent($stream)
      $form.Add($fileContent, "image[]", [System.IO.Path]::GetFileName($path))
    }
    if (-not [string]::IsNullOrWhiteSpace($Mask)) {
      if (-not (Test-Path -LiteralPath $Mask)) { throw "Mask file not found: $Mask" }
      $maskStream = [System.IO.File]::OpenRead((Resolve-Path -LiteralPath $Mask))
      $openStreams.Add($maskStream)
      $maskContent = New-Object System.Net.Http.StreamContent($maskStream)
      $form.Add($maskContent, "mask", [System.IO.Path]::GetFileName($Mask))
    }

    $response = $client.PostAsync($Url, $form).Result
    $text = $response.Content.ReadAsStringAsync().Result
    if (-not $response.IsSuccessStatusCode) {
      throw "API request failed ($([int]$response.StatusCode)): $text"
    }
    return $text | ConvertFrom-Json
  } finally {
    foreach ($stream in $openStreams) { $stream.Dispose() }
    $form.Dispose()
    $client.Dispose()
  }
}

$ApiKey = Get-DefaultValue $ApiKey $env:SUB2API_API_KEY
$ApiKey = Get-DefaultValue $ApiKey (Get-CodexAuthKey)
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  throw "Missing API key. Set OPENAI_API_KEY or SUB2API_API_KEY, or configure ~/.codex/auth.json."
}

$Model = Get-DefaultValue $Model "gpt-image-2"
$OutputDir = Get-DefaultValue $OutputDir "mtm-image2-output"
$base = Normalize-BaseUrl $BaseUrl
$requestPrompt = Get-RequestPrompt
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$slug = New-Slug $requestPrompt

if ([string]::IsNullOrWhiteSpace($PromptOutput)) {
  $PromptOutput = Join-Path $OutputDir "prompts/$slug-$stamp.md"
}
Save-Text $PromptOutput $requestPrompt

if ([string]::IsNullOrWhiteSpace($Output)) {
  $Output = Join-Path $OutputDir "images/$slug-$stamp.$Format"
}
if ([string]::IsNullOrWhiteSpace($ReportOutput)) {
  $ReportOutput = Join-Path $OutputDir "reports/$slug-$stamp.json"
}

if ($Image -and $Image.Count -gt 0) {
  $endpoint = "$base/images/edits"
  $result = Invoke-MultipartPost $endpoint $ApiKey $requestPrompt
} else {
  $endpoint = "$base/images/generations"
  $body = @{
    model = $Model
    prompt = $requestPrompt
    size = $Size
    quality = $Quality
    n = $N
    output_format = $Format
    moderation = $Moderation
  }
  if ($Compression -ge 0) { $body.output_compression = $Compression }
  if (-not [string]::IsNullOrWhiteSpace($Background)) { $body.background = $Background }
  $result = Invoke-JsonPost $endpoint $body $ApiKey
}

$written = @()
for ($i = 0; $i -lt $result.data.Count; $i++) {
  if ($result.data.Count -eq 1) {
    $target = $Output
  } else {
    $dir = Split-Path -Parent $Output
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($Output)
    $ext = [System.IO.Path]::GetExtension($Output)
    $target = Join-Path $dir "$stem-$i$ext"
  }
  Save-ImageData $result.data[$i] $target
  $written += $target
}

$report = [ordered]@{
  mode = $(if ($Image -and $Image.Count -gt 0) { "edit" } else { "generate" })
  endpoint = $endpoint
  model = $Model
  prompt = $PromptOutput
  images = $written
  report = $ReportOutput
}

Save-Json $ReportOutput $report
$report | ConvertTo-Json -Depth 8
