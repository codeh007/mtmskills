[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('status', 'tree', 'find', 'invoke', 'set-value', 'toggle', 'select', 'expand', 'collapse', 'focus', 'scroll', 'assert')]
    [string]$CommandName,

    [long]$Hwnd = 0,
    [string]$Name = '',
    [string]$AutomationId = '',
    [string]$ControlType = '',
    [string]$ClassName = '',
    [string]$Text = '',
    [switch]$Regex,
    [int]$Index = 0,
    [int]$MaxDepth = 8,
    [int]$Limit = 80,
    [switch]$IncludeOffscreen,
    [string]$Value = '',
    [ValidateSet('LargeIncrement', 'LargeDecrement', 'SmallIncrement', 'SmallDecrement', 'NoAmount')]
    [string]$HorizontalAmount = 'NoAmount',
    [ValidateSet('LargeIncrement', 'LargeDecrement', 'SmallIncrement', 'SmallDecrement', 'NoAmount')]
    [string]$VerticalAmount = 'NoAmount',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
}
catch {
    [ordered]@{
        status = 'error'
        command = $CommandName
        error_type = $_.Exception.GetType().FullName
        error = $_.Exception.Message
    } | ConvertTo-Json -Depth 12 -Compress
    exit 1
}

function Write-Json {
    param([object]$Data)
    $Data | ConvertTo-Json -Depth 12 -Compress
}

function Test-TextMatch {
    param(
        [AllowNull()][string]$Candidate,
        [string]$Needle,
        [bool]$UseRegex
    )
    if ([string]::IsNullOrEmpty($Needle)) {
        return $true
    }
    $value = [string]$Candidate
    if ($UseRegex) {
        return $value -match $Needle
    }
    return $value.IndexOf($Needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}

function Normalize-ControlType {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ''
    }
    $normalized = $Value.Trim()
    if ($normalized.StartsWith('ControlType.', [System.StringComparison]::OrdinalIgnoreCase)) {
        $normalized = $normalized.Substring('ControlType.'.Length)
    }
    return $normalized
}

function Get-RootElement {
    param([long]$WindowHandle)
    if ($WindowHandle -gt 0) {
        $element = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$WindowHandle)
        if ($null -eq $element) {
            throw "No UI Automation element exists for HWND $WindowHandle."
        }
        return $element
    }
    return [System.Windows.Automation.AutomationElement]::RootElement
}

function Get-ControlChildren {
    param([System.Windows.Automation.AutomationElement]$Element)
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $child = $null
    try {
        $child = $walker.GetFirstChild($Element)
    }
    catch {
        return
    }
    while ($null -ne $child) {
        $child
        try {
            $child = $walker.GetNextSibling($child)
        }
        catch {
            break
        }
    }
}

function Get-SupportedPatternNames {
    param([System.Windows.Automation.AutomationElement]$Element)
    $names = New-Object System.Collections.Generic.List[string]
    try {
        foreach ($pattern in $Element.GetSupportedPatterns()) {
            $name = $pattern.ProgrammaticName
            if ($name.StartsWith('Pattern.', [System.StringComparison]::OrdinalIgnoreCase)) {
                $name = $name.Substring('Pattern.'.Length)
            }
            if ($name.EndsWith('PatternIdentifiers.Pattern', [System.StringComparison]::OrdinalIgnoreCase)) {
                $name = $name.Substring(0, $name.Length - 'Identifiers.Pattern'.Length)
            }
            $names.Add($name)
        }
    }
    catch {
    }
    return @($names)
}

function Convert-Element {
    param(
        [System.Windows.Automation.AutomationElement]$Element,
        [int]$Depth = 0
    )
    $current = $Element.Current
    $rect = $current.BoundingRectangle
    $runtimeId = $null
    try {
        $ids = $Element.GetRuntimeId()
        if ($ids) {
            $runtimeId = [string]::Join('.', $ids)
        }
    }
    catch {
    }

    $clickable = $null
    try {
        $point = $Element.GetClickablePoint()
        $clickable = [ordered]@{
            x = [int][Math]::Round($point.X)
            y = [int][Math]::Round($point.Y)
        }
    }
    catch {
    }

    $controlType = ''
    try {
        $controlType = Normalize-ControlType $current.ControlType.ProgrammaticName
    }
    catch {
    }

    return [ordered]@{
        depth = $Depth
        name = $current.Name
        automation_id = $current.AutomationId
        control_type = $controlType
        localized_control_type = $current.LocalizedControlType
        class_name = $current.ClassName
        framework_id = $current.FrameworkId
        help_text = $current.HelpText
        process_id = $current.ProcessId
        enabled = $current.IsEnabled
        offscreen = $current.IsOffscreen
        rect = [ordered]@{
            left = [int][Math]::Round($rect.Left)
            top = [int][Math]::Round($rect.Top)
            right = [int][Math]::Round($rect.Right)
            bottom = [int][Math]::Round($rect.Bottom)
            width = [int][Math]::Round($rect.Width)
            height = [int][Math]::Round($rect.Height)
        }
        clickable_point = $clickable
        runtime_id = $runtimeId
        patterns = @(Get-SupportedPatternNames $Element)
    }
}

function Test-ElementMatch {
    param([System.Windows.Automation.AutomationElement]$Element)
    try {
        $current = $Element.Current
    }
    catch {
        return $false
    }

    if (-not $IncludeOffscreen -and $current.IsOffscreen) {
        return $false
    }

    if (-not (Test-TextMatch $current.Name $Name $Regex.IsPresent)) {
        return $false
    }
    if (-not (Test-TextMatch $current.AutomationId $AutomationId $Regex.IsPresent)) {
        return $false
    }
    if (-not (Test-TextMatch $current.ClassName $ClassName $Regex.IsPresent)) {
        return $false
    }

    $expectedType = Normalize-ControlType $ControlType
    if ($expectedType) {
        $actualType = Normalize-ControlType $current.ControlType.ProgrammaticName
        if ($actualType -ne $expectedType) {
            return $false
        }
    }

    if ($Text) {
        $actualType = Normalize-ControlType $current.ControlType.ProgrammaticName
        $fields = @(
            $current.Name,
            $current.AutomationId,
            $current.ClassName,
            $current.LocalizedControlType,
            $current.HelpText,
            $actualType
        )
        $matched = $false
        foreach ($field in $fields) {
            if (Test-TextMatch $field $Text $Regex.IsPresent) {
                $matched = $true
                break
            }
        }
        if (-not $matched) {
            return $false
        }
    }

    return $true
}

function Search-Elements {
    param(
        [System.Windows.Automation.AutomationElement]$Root,
        [int]$SearchMaxDepth,
        [int]$SearchLimit,
        [switch]$MatchOnly
    )

    $results = @()
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue([pscustomobject]@{ Element = $Root; Depth = 0 })

    while ($queue.Count -gt 0 -and @($results).Count -lt $SearchLimit) {
        $item = $queue.Dequeue()
        $element = $item.Element
        $depth = [int]$item.Depth

        $include = $true
        if ($MatchOnly) {
            $include = Test-ElementMatch $element
        }
        elseif (-not $IncludeOffscreen) {
            try {
                $include = -not $element.Current.IsOffscreen
            }
            catch {
                $include = $false
            }
        }

        if ($include) {
            try {
                $results += (Convert-Element $element $depth)
            }
            catch {
            }
        }

        if ($depth -lt $SearchMaxDepth) {
            foreach ($child in Get-ControlChildren $element) {
                $queue.Enqueue([pscustomobject]@{ Element = $child; Depth = ($depth + 1) })
            }
        }
    }

    return $results
}

function Select-TargetElement {
    param([System.Windows.Automation.AutomationElement]$Root)
    $matches = @(Search-Elements -Root $Root -SearchMaxDepth $MaxDepth -SearchLimit ([Math]::Max($Limit, $Index + 1)) -MatchOnly)
    if ($matches.Count -le $Index) {
        throw "No UI Automation element matched the query at index $Index. Matched $($matches.Count) element(s)."
    }

    $runtimeId = $matches[$Index].runtime_id
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue([pscustomobject]@{ Element = $Root; Depth = 0 })
    while ($queue.Count -gt 0) {
        $item = $queue.Dequeue()
        $element = $item.Element
        try {
            $converted = Convert-Element $element ([int]$item.Depth)
            if ($converted.runtime_id -eq $runtimeId) {
                return $element
            }
        }
        catch {
        }
        if ([int]$item.Depth -lt $MaxDepth) {
            foreach ($child in Get-ControlChildren $element) {
                $queue.Enqueue([pscustomobject]@{ Element = $child; Depth = ([int]$item.Depth + 1) })
            }
        }
    }
    throw "Matched UI Automation element became unavailable."
}

function Get-Pattern {
    param(
        [System.Windows.Automation.AutomationElement]$Element,
        [System.Windows.Automation.AutomationPattern]$Pattern,
        [string]$Name
    )
    $patternObject = $null
    if (-not $Element.TryGetCurrentPattern($Pattern, [ref]$patternObject)) {
        throw "Matched element does not support $Name."
    }
    return $patternObject
}

try {
    if ($CommandName -eq 'status') {
        Write-Json ([ordered]@{
            status = 'ok'
            provider = 'System.Windows.Automation'
            assemblies = @('UIAutomationClient', 'UIAutomationTypes')
        })
        exit 0
    }

    $root = Get-RootElement $Hwnd

    if ($CommandName -eq 'tree') {
        Write-Json ([ordered]@{
            status = 'ok'
            command = 'tree'
            hwnd = $Hwnd
            max_depth = $MaxDepth
            limit = $Limit
            nodes = @(Search-Elements -Root $root -SearchMaxDepth $MaxDepth -SearchLimit $Limit)
        })
        exit 0
    }

    if ($CommandName -eq 'find') {
        $matches = @(Search-Elements -Root $root -SearchMaxDepth $MaxDepth -SearchLimit $Limit -MatchOnly)
        Write-Json ([ordered]@{
            status = 'ok'
            command = 'find'
            hwnd = $Hwnd
            count = $matches.Count
            matches = $matches
        })
        exit 0
    }

    if ($CommandName -eq 'assert') {
        $matches = @(Search-Elements -Root $root -SearchMaxDepth $MaxDepth -SearchLimit 1 -MatchOnly)
        Write-Json ([ordered]@{
            status = 'ok'
            command = 'assert'
            hwnd = $Hwnd
            passed = ($matches.Count -gt 0)
            matches = $matches
        })
        exit 0
    }

    $target = Select-TargetElement $root
    $before = Convert-Element $target

    if ($DryRun) {
        Write-Json ([ordered]@{
            status = 'dry-run'
            command = $CommandName
            hwnd = $Hwnd
            target = $before
        })
        exit 0
    }

    switch ($CommandName) {
        'invoke' {
            $pattern = Get-Pattern $target ([System.Windows.Automation.InvokePattern]::Pattern) 'InvokePattern'
            $pattern.Invoke()
        }
        'set-value' {
            $pattern = Get-Pattern $target ([System.Windows.Automation.ValuePattern]::Pattern) 'ValuePattern'
            if ($pattern.Current.IsReadOnly) {
                throw 'Matched element ValuePattern is read-only.'
            }
            $pattern.SetValue($Value)
        }
        'toggle' {
            $pattern = Get-Pattern $target ([System.Windows.Automation.TogglePattern]::Pattern) 'TogglePattern'
            $pattern.Toggle()
        }
        'select' {
            $pattern = Get-Pattern $target ([System.Windows.Automation.SelectionItemPattern]::Pattern) 'SelectionItemPattern'
            $pattern.Select()
        }
        'expand' {
            $pattern = Get-Pattern $target ([System.Windows.Automation.ExpandCollapsePattern]::Pattern) 'ExpandCollapsePattern'
            $pattern.Expand()
        }
        'collapse' {
            $pattern = Get-Pattern $target ([System.Windows.Automation.ExpandCollapsePattern]::Pattern) 'ExpandCollapsePattern'
            $pattern.Collapse()
        }
        'focus' {
            $target.SetFocus()
        }
        'scroll' {
            $pattern = Get-Pattern $target ([System.Windows.Automation.ScrollPattern]::Pattern) 'ScrollPattern'
            $pattern.Scroll(
                [System.Windows.Automation.ScrollAmount]::$HorizontalAmount,
                [System.Windows.Automation.ScrollAmount]::$VerticalAmount
            )
        }
        default {
            throw "Unsupported UI Automation command: $CommandName"
        }
    }

    Start-Sleep -Milliseconds 80
    $after = Convert-Element $target
    Write-Json ([ordered]@{
        status = 'ok'
        command = $CommandName
        hwnd = $Hwnd
        target = $before
        after = $after
    })
    exit 0
}
catch {
    $invocation = $_.InvocationInfo
    Write-Json ([ordered]@{
        status = 'error'
        command = $CommandName
        error_type = $_.Exception.GetType().FullName
        error = $_.Exception.Message
        script_stack = $_.ScriptStackTrace
        position = if ($invocation) { $invocation.PositionMessage } else { '' }
    })
    exit 1
}
