<#
.SYNOPSIS
    Check (and optionally fix) the WinForms "anchored control collapses to Height 0" issue.

.DESCRIPTION
    On .NET 8, a control anchored Top|Bottom (e.g. a TableLayoutPanel filling a region) collapses
    to Height 0 when the host app is DPI-aware (PerMonitorV2) AND the legacy anchor layout engine
    is in use (System.Windows.Forms.AnchorLayoutV2 == off). The DPI rescale pass runs on the
    control while it is still detached and the V1 anchor engine latches a transient 0 height.

    Two consistent, safe configurations exist:
      * HighDpiMode  : DPI-aware (PerMonitorV2) PLUS AnchorLayoutV2 = true   (crisp on high-DPI)
      * Old mode     : DPI-unaware                                           (uniform bitmap scaling)
    The broken state is the mix: DPI-aware + AnchorLayoutV2 off.

    This script scans a project folder for WinForms executable projects, reports the state of each,
    and (interactively) applies one of the two safe configurations. Read-only until you confirm an
    action; backs up every file it edits to <file>.bak; writes a Markdown report to the chosen root.

.PARAMETER ProjectPath
    Optional. Folder to analyze. If omitted, an interactive menu lets you pick the current directory
    or type a path. The script works regardless of the current working directory.

.PARAMETER Action
    Optional. One of 'HighDpiMode' | 'OldMode' | 'None'. If omitted, an interactive menu asks.
    Supplying it (with -ProjectPath) makes the run non-interactive.

.EXAMPLE
    .\Repair-WinFormsDpiAnchor.ps1
    Fully interactive: choose folder, see the report, choose an action.

.EXAMPLE
    .\Repair-WinFormsDpiAnchor.ps1 -ProjectPath "C:\src\5315_LAG" -Action None
    Non-interactive check only; writes a report, changes nothing.

.NOTES
    Reference: dotnet/winforms issue #6041 (anchor-layout-changes-in-net80)
    dotnet/winforms anchor-layout-changes-in-net80.md ; winforms issue #6041.
#>
[CmdletBinding()]
param(
    [string]$ProjectPath,
    [ValidateSet('HighDpiMode', 'OldMode', 'None')]
    [string]$Action
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ----------------------------------------------------------------------------- helpers

function Write-Section {
    param([string]$Title)
    Write-Host ''
    Write-Host ('=' * 72) -ForegroundColor DarkCyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ('=' * 72) -ForegroundColor DarkCyan
}

# Strip XML/HTML comment blocks so detection only sees ACTIVE markup.
function Remove-XmlComments {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return '' }
    return [System.Text.RegularExpressions.Regex]::Replace($Text, '(?s)<!--.*?-->', '')
}

# ----------------------------------------------------------------------------- Phase 0

function Resolve-Target {
    param([string]$Path)

    if ($Path) {
        if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
            throw "Project path not found or not a folder: $Path"
        }
        return (Resolve-Path -LiteralPath $Path).Path
    }

    while ($true) {
        Write-Section 'Phase 0 - choose the project folder'
        Write-Host "  [1] Use the current directory  ($($PWD.Path))"
        Write-Host "  [2] Enter a project path"
        Write-Host "  [3] Exit"
        $choice = (Read-Host 'Select 1, 2 or 3').Trim()
        switch ($choice) {
            '1' { return $PWD.Path }
            '2' {
                $p = (Read-Host 'Project folder path').Trim('"', ' ')
                if (Test-Path -LiteralPath $p -PathType Container) {
                    return (Resolve-Path -LiteralPath $p).Path
                }
                Write-Host "  Not a valid folder: $p" -ForegroundColor Yellow
            }
            '3' { return $null }
            default { Write-Host '  Please enter 1, 2 or 3.' -ForegroundColor Yellow }
        }
    }
}

# ----------------------------------------------------------------------------- discovery

function Get-WinFormsExeProjects {
    param([string]$Root)

    $result = @()
    $csprojs = Get-ChildItem -LiteralPath $Root -Recurse -Filter *.csproj -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\(bin|obj)\\' }

    foreach ($cs in $csprojs) {
        $text = Get-Content -LiteralPath $cs.FullName -Raw
        $isWinForms = $text -match '<UseWindowsForms>\s*true\s*</UseWindowsForms>'
        $isExe = $text -match '<OutputType>\s*WinExe\s*</OutputType>'
        if ($isWinForms -or $isExe) {
            $result += [pscustomobject]@{
                Name      = $cs.BaseName
                CsprojPath = $cs.FullName
                Dir       = $cs.DirectoryName
                Text      = $text
            }
        }
    }
    return $result
}

# ----------------------------------------------------------------------------- DPI detection

function Resolve-ManifestPath {
    param([pscustomobject]$Project)

    $m = [regex]::Match($Project.Text, '<ApplicationManifest>\s*(?<p>[^<]+?)\s*</ApplicationManifest>')
    if ($m.Success) {
        $candidate = Join-Path $Project.Dir $m.Groups['p'].Value
        if (Test-Path -LiteralPath $candidate) { return (Resolve-Path -LiteralPath $candidate).Path }
    }
    foreach ($rel in @('app.manifest', 'Properties\app.manifest')) {
        $candidate = Join-Path $Project.Dir $rel
        if (Test-Path -LiteralPath $candidate) { return (Resolve-Path -LiteralPath $candidate).Path }
    }
    return $null
}

function Test-DpiAware {
    param([pscustomobject]$Project)

    # 1) Manifest (authoritative if it sets DPI).
    $manifest = Resolve-ManifestPath -Project $Project
    if ($manifest) {
        $active = Remove-XmlComments (Get-Content -LiteralPath $manifest -Raw)
        if ($active -match '(?i)<dpiAwareness[^>]*>\s*(PerMonitorV2|PerMonitor|System)') {
            return [pscustomobject]@{ Aware = $true; Source = "manifest dpiAwareness"; Manifest = $manifest }
        }
        if ($active -match '(?i)<dpiAware[^>]*>\s*(true/pm|true|PM)\s*</dpiAware>') {
            return [pscustomobject]@{ Aware = $true; Source = "manifest dpiAware"; Manifest = $manifest }
        }
        if ($active -match '(?i)<dpiAware[^>]*>\s*false\s*</dpiAware>') {
            return [pscustomobject]@{ Aware = $false; Source = "manifest dpiAware=false"; Manifest = $manifest }
        }
        # manifest present but DPI block commented/absent -> fall through to csproj/Program.cs
    }

    # 2) csproj <ApplicationHighDpiMode>.
    $hm = [regex]::Match($Project.Text, '(?i)<ApplicationHighDpiMode>\s*(?<v>[A-Za-z]+)\s*</ApplicationHighDpiMode>')
    if ($hm.Success) {
        $v = $hm.Groups['v'].Value
        $aware = $v -match '(?i)^(SystemAware|PerMonitor|PerMonitorV2)$'
        return [pscustomobject]@{ Aware = $aware; Source = "csproj ApplicationHighDpiMode=$v"; Manifest = $manifest }
    }

    # 3) Program.cs SetHighDpiMode / ApplicationConfiguration.Initialize().
    $prog = Get-ChildItem -LiteralPath $Project.Dir -Recurse -Filter Program.cs -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\(bin|obj)\\' } | Select-Object -First 1
    if ($prog) {
        $ptext = Get-Content -LiteralPath $prog.FullName -Raw
        $shd = [regex]::Match($ptext, '(?i)SetHighDpiMode\s*\(\s*(?:HighDpiMode\.)?(?<v>[A-Za-z]+)')
        if ($shd.Success) {
            $v = $shd.Groups['v'].Value
            $aware = $v -match '(?i)^(SystemAware|PerMonitor|PerMonitorV2)$'
            return [pscustomobject]@{ Aware = $aware; Source = "Program.cs SetHighDpiMode($v)"; Manifest = $manifest }
        }
        if ($ptext -match '(?i)ApplicationConfiguration\.Initialize\s*\(') {
            return [pscustomobject]@{ Aware = $true; Source = "ApplicationConfiguration.Initialize (default SystemAware)"; Manifest = $manifest }
        }
    }

    # 4) Nothing sets it -> DPI-unaware.
    return [pscustomobject]@{ Aware = $false; Source = "default (no DPI setting)"; Manifest = $manifest }
}

# ----------------------------------------------------------------------------- AnchorLayoutV2 detection

function Test-AnchorLayoutV2 {
    param([pscustomobject]$Project)

    if ($Project.Text -match '(?i)<RuntimeHostConfigurationOption[^>]*System\.Windows\.Forms\.AnchorLayoutV2[^>]*Value\s*=\s*"\s*true\s*"') {
        return [pscustomobject]@{ On = $true; Source = 'csproj RuntimeHostConfigurationOption' }
    }

    $tmpl = Join-Path $Project.Dir 'runtimeconfig.template.json'
    if (Test-Path -LiteralPath $tmpl) {
        $t = Get-Content -LiteralPath $tmpl -Raw
        if ($t -match '(?i)"System\.Windows\.Forms\.AnchorLayoutV2"\s*:\s*true') {
            return [pscustomobject]@{ On = $true; Source = 'runtimeconfig.template.json' }
        }
    }

    $rc = Get-ChildItem -LiteralPath $Project.Dir -Recurse -Filter '*.runtimeconfig.json' -File -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($rc) {
        $r = Get-Content -LiteralPath $rc.FullName -Raw
        if ($r -match '(?i)"System\.Windows\.Forms\.AnchorLayoutV2"\s*:\s*true') {
            return [pscustomobject]@{ On = $true; Source = 'built runtimeconfig.json' }
        }
    }

    return [pscustomobject]@{ On = $false; Source = 'not set' }
}

# ----------------------------------------------------------------------------- exposure (anchored Top|Bottom)

function Get-AnchoredTopBottomCount {
    param([pscustomobject]$Project)

    $count = 0
    $designers = Get-ChildItem -LiteralPath $Project.Dir -Recurse -Filter '*.Designer.cs' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\(bin|obj)\\' }
    foreach ($d in $designers) {
        $dt = Get-Content -LiteralPath $d.FullName -Raw
        foreach ($line in ([regex]::Matches($dt, '(?im)^\s*\S+\.Anchor\s*=\s*[^;]+;'))) {
            $v = $line.Value
            if ($v -match '(?i)AnchorStyles\.Top' -and $v -match '(?i)AnchorStyles\.Bottom') { $count++ }
        }
    }
    return $count
}

# ----------------------------------------------------------------------------- analyze

function Get-Analysis {
    param([string]$Root)

    $projects = Get-WinFormsExeProjects -Root $Root
    $rows = @()
    foreach ($p in $projects) {
        $dpi = Test-DpiAware -Project $p
        $alv2 = Test-AnchorLayoutV2 -Project $p
        $anchored = Get-AnchoredTopBottomCount -Project $p

        if (-not $dpi.Aware) {
            $verdict = 'SAFE (old / DPI-unaware mode)'
            $issue = $false
        }
        elseif ($alv2.On) {
            $verdict = 'SAFE (HighDpiMode + AnchorLayoutV2)'
            $issue = $false
        }
        else {
            $verdict = 'ISSUE PRESENT (DPI-aware + AnchorLayoutV2 off)'
            $issue = $true
        }

        $rows += [pscustomobject]@{
            Project        = $p.Name
            CsprojPath     = $p.CsprojPath
            Dir            = $p.Dir
            DpiAware       = $dpi.Aware
            DpiSource      = $dpi.Source
            ManifestPath   = $dpi.Manifest
            AnchorV2       = $alv2.On
            AnchorV2Source = $alv2.Source
            AnchoredTopBottom = $anchored
            Verdict        = $verdict
            IssuePresent   = $issue
        }
    }
    return , $rows
}

function Show-Report {
    param([object[]]$Rows, [string]$Root)

    Write-Section 'Phase 1 - check & summary'
    Write-Host "  Scanned root : $Root"
    if (-not $Rows -or $Rows.Count -eq 0) {
        Write-Host '  No WinForms executable projects (WinExe / UseWindowsForms) found.' -ForegroundColor Yellow
        return
    }
    Write-Host "  WinForms exe projects: $($Rows.Count)"
    Write-Host ''
    foreach ($r in $Rows) {
        $color = if ($r.IssuePresent) { 'Red' } else { 'Green' }
        Write-Host "  * $($r.Project)" -ForegroundColor White
        Write-Host "      DPI-aware        : $($r.DpiAware)  [$($r.DpiSource)]"
        Write-Host "      AnchorLayoutV2   : $($r.AnchorV2)  [$($r.AnchorV2Source)]"
        Write-Host "      Anchored Top|Bot : $($r.AnchoredTopBottom) control(s) at risk"
        Write-Host "      Verdict          : $($r.Verdict)" -ForegroundColor $color
        Write-Host ''
    }
    $issues = @($Rows | Where-Object IssuePresent)
    if ($issues.Count -gt 0) {
        Write-Host "  CONCLUSION: issue present in $($issues.Count) of $($Rows.Count) project(s)." -ForegroundColor Red
    }
    else {
        Write-Host "  CONCLUSION: all $($Rows.Count) project(s) are SAFE." -ForegroundColor Green
    }
}

# ----------------------------------------------------------------------------- Phase 2 menu

function Get-ActionChoice {
    Write-Section 'Phase 2 - choose an action'
    Write-Host '  [a] Use HighDpiMode  (DPI-aware PerMonitorV2 + AnchorLayoutV2 = true) - crisp & safe'
    Write-Host '  [b] Use old mode     (make the app DPI-unaware)                       - uniform scaling'
    Write-Host '  [c] Do nothing       (report only)'
    while ($true) {
        $c = (Read-Host 'Select a, b or c').Trim().ToLower()
        switch ($c) {
            'a' { return 'HighDpiMode' }
            'b' { return 'OldMode' }
            'c' { return 'None' }
            default { Write-Host '  Please enter a, b or c.' -ForegroundColor Yellow }
        }
    }
}

# ----------------------------------------------------------------------------- Phase 3 apply

function Backup-File {
    param([string]$Path, [System.Collections.Generic.List[string]]$Changes)
    $bak = "$Path.bak"
    if (-not (Test-Path -LiteralPath $bak)) {
        Copy-Item -LiteralPath $Path -Destination $bak
        $Changes.Add("backup : $bak")
    }
}

function Set-AnchorLayoutV2InCsproj {
    param([string]$CsprojPath, [System.Collections.Generic.List[string]]$Changes)

    $text = Get-Content -LiteralPath $CsprojPath -Raw
    if ($text -match '(?i)System\.Windows\.Forms\.AnchorLayoutV2') {
        # Force any existing entry to true.
        $new = [regex]::Replace($text,
            '(?i)(<RuntimeHostConfigurationOption[^>]*System\.Windows\.Forms\.AnchorLayoutV2[^>]*Value\s*=\s*")[^"]*(")',
            '${1}true${2}')
        if ($new -ne $text) {
            Backup-File -Path $CsprojPath -Changes $Changes
            Set-Content -LiteralPath $CsprojPath -Value $new -Encoding UTF8
            $Changes.Add("csproj : set AnchorLayoutV2=true ($CsprojPath)")
        }
        else {
            $Changes.Add("csproj : AnchorLayoutV2 already true ($CsprojPath)")
        }
        return
    }

    $block = @"
  <ItemGroup>
    <RuntimeHostConfigurationOption Include="System.Windows.Forms.AnchorLayoutV2" Value="true" Trim="false" />
  </ItemGroup>
"@
    $idx = $text.LastIndexOf('</Project>')
    if ($idx -lt 0) { $Changes.Add("csproj : SKIPPED (no </Project>) $CsprojPath"); return }
    Backup-File -Path $CsprojPath -Changes $Changes
    $new = $text.Insert($idx, $block + [Environment]::NewLine)
    Set-Content -LiteralPath $CsprojPath -Value $new -Encoding UTF8
    $Changes.Add("csproj : added AnchorLayoutV2=true ($CsprojPath)")
}

function Enable-ManifestDpi {
    param([string]$ManifestPath, [System.Collections.Generic.List[string]]$Changes)

    $text = Get-Content -LiteralPath $ManifestPath -Raw

    # If an active DPI block already exists, nothing to do.
    $active = Remove-XmlComments $text
    if ($active -match '(?i)<dpiAware') {
        $Changes.Add("manifest : already DPI-aware ($ManifestPath)")
        return
    }

    # Uncomment a commented asm.v3 windowsSettings block if present.
    $m = [regex]::Match($text, '(?s)<!--\s*(?<b>\s*<application\s+xmlns="urn:schemas-microsoft-com:asm\.v3".*?</application>)\s*-->')
    if ($m.Success) {
        Backup-File -Path $ManifestPath -Changes $Changes
        $new = $text.Remove($m.Index, $m.Length).Insert($m.Index, $m.Groups['b'].Value.Trim())
        Set-Content -LiteralPath $ManifestPath -Value $new -Encoding UTF8
        $Changes.Add("manifest : uncommented PerMonitorV2 block ($ManifestPath)")
        return
    }

    # Else inject a fresh block before </assembly>.
    $idx = $text.LastIndexOf('</assembly>')
    if ($idx -lt 0) { $Changes.Add("manifest : SKIPPED (no </assembly>) $ManifestPath"); return }
    $block = @"
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
"@
    Backup-File -Path $ManifestPath -Changes $Changes
    $new = $text.Insert($idx, $block + [Environment]::NewLine)
    Set-Content -LiteralPath $ManifestPath -Value $new -Encoding UTF8
    $Changes.Add("manifest : injected PerMonitorV2 block ($ManifestPath)")
}

function Disable-ManifestDpi {
    param([string]$ManifestPath, [System.Collections.Generic.List[string]]$Changes)

    $text = Get-Content -LiteralPath $ManifestPath -Raw
    $active = Remove-XmlComments $text
    if ($active -notmatch '(?i)<dpiAware') {
        $Changes.Add("manifest : already DPI-unaware ($ManifestPath)")
        return
    }

    # Comment out the active asm.v3 windowsSettings application block.
    $m = [regex]::Match($text, '(?s)<application\s+xmlns="urn:schemas-microsoft-com:asm\.v3".*?</application>')
    if (-not $m.Success) {
        $Changes.Add("manifest : SKIPPED (unexpected shape - edit by hand) $ManifestPath")
        return
    }
    Backup-File -Path $ManifestPath -Changes $Changes
    $comment = "<!-- DPI awareness disabled by Repair-WinFormsDpiAnchor.ps1 (DPI-unaware = old mode). -->" +
        [Environment]::NewLine + "  <!--" + [Environment]::NewLine + "  " + $m.Value + [Environment]::NewLine + "  -->"
    $new = $text.Remove($m.Index, $m.Length).Insert($m.Index, $comment)
    Set-Content -LiteralPath $ManifestPath -Value $new -Encoding UTF8
    $Changes.Add("manifest : commented out DPI block ($ManifestPath)")
}

function Set-CsprojHighDpiMode {
    param([string]$CsprojPath, [string]$Value, [System.Collections.Generic.List[string]]$Changes)

    $text = Get-Content -LiteralPath $CsprojPath -Raw
    if ($text -match '(?i)<ApplicationHighDpiMode>') {
        $new = [regex]::Replace($text, '(?i)<ApplicationHighDpiMode>\s*[A-Za-z]+\s*</ApplicationHighDpiMode>',
            "<ApplicationHighDpiMode>$Value</ApplicationHighDpiMode>")
        if ($new -ne $text) {
            Backup-File -Path $CsprojPath -Changes $Changes
            Set-Content -LiteralPath $CsprojPath -Value $new -Encoding UTF8
            $Changes.Add("csproj : ApplicationHighDpiMode=$Value ($CsprojPath)")
        }
        return $true
    }
    return $false
}

function Invoke-Fix {
    param([object[]]$Rows, [string]$ActionName)

    $changes = [System.Collections.Generic.List[string]]::new()
    if ($ActionName -eq 'None') {
        $changes.Add('No changes (action = do nothing).')
        return $changes
    }

    foreach ($r in $Rows) {
        if ($ActionName -eq 'HighDpiMode') {
            Set-AnchorLayoutV2InCsproj -CsprojPath $r.CsprojPath -Changes $changes
            if ($r.ManifestPath) {
                Enable-ManifestDpi -ManifestPath $r.ManifestPath -Changes $changes
            }
            elseif (-not $r.DpiAware) {
                if (-not (Set-CsprojHighDpiMode -CsprojPath $r.CsprojPath -Value 'PerMonitorV2' -Changes $changes)) {
                    # add a fresh property near the AnchorLayoutV2 option is overkill; note for manual add
                    $changes.Add("csproj : no manifest & no ApplicationHighDpiMode - add <ApplicationHighDpiMode>PerMonitorV2</ApplicationHighDpiMode> manually ($($r.CsprojPath))")
                }
            }
        }
        elseif ($ActionName -eq 'OldMode') {
            if ($r.ManifestPath) {
                Disable-ManifestDpi -ManifestPath $r.ManifestPath -Changes $changes
            }
            # Neutralize an aware csproj HighDpiMode if present.
            Set-CsprojHighDpiMode -CsprojPath $r.CsprojPath -Value 'DpiUnaware' -Changes $changes | Out-Null
        }
    }
    return $changes
}

# ----------------------------------------------------------------------------- Phase 4 report

function Write-ReportFile {
    param([string]$Root, [object[]]$Rows, [string]$ActionName, [object[]]$Changes)

    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $path = Join-Path $Root "DpiAnchorReport_$stamp.md"
    $now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("# WinForms DPI / anchor rendering report")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("- Generated : $now")
    [void]$sb.AppendLine("- Scanned root : ``$Root``")
    [void]$sb.AppendLine("- Action chosen : **$ActionName**")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("## Findings")
    [void]$sb.AppendLine()
    if (-not $Rows -or $Rows.Count -eq 0) {
        [void]$sb.AppendLine("No WinForms executable projects found.")
    }
    else {
        [void]$sb.AppendLine("| Project | DPI-aware | DPI source | AnchorLayoutV2 | Anchored Top\|Bottom | Verdict |")
        [void]$sb.AppendLine("|---|---|---|---|---|---|")
        foreach ($r in $Rows) {
            [void]$sb.AppendLine("| $($r.Project) | $($r.DpiAware) | $($r.DpiSource) | $($r.AnchorV2) ($($r.AnchorV2Source)) | $($r.AnchoredTopBottom) | $($r.Verdict) |")
        }
    }
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("## Changes applied")
    [void]$sb.AppendLine()
    if (-not $Changes -or $Changes.Count -eq 0) {
        [void]$sb.AppendLine("None.")
    }
    else {
        foreach ($c in $Changes) { [void]$sb.AppendLine("- $c") }
    }
    if ($ActionName -ne 'None') {
        [void]$sb.AppendLine()
        [void]$sb.AppendLine("> A **rebuild** is required for the change to take effect (DPI/anchor settings are baked at build).")
    }
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("## Background")
    [void]$sb.AppendLine("Anchored Top\|Bottom controls collapse to Height 0 when an app is DPI-aware (PerMonitorV2) AND the .NET 8 legacy anchor engine is used (System.Windows.Forms.AnchorLayoutV2 off). Safe configs: DPI-aware + AnchorLayoutV2=true, OR DPI-unaware. See dotnet/winforms issue #6041 (anchor-layout-changes-in-net80).")

    Set-Content -LiteralPath $path -Value $sb.ToString() -Encoding UTF8
    return $path
}

# ----------------------------------------------------------------------------- main

function Invoke-Main {
    Write-Host ''
    Write-Host 'Repair-WinFormsDpiAnchor - check & fix the anchored-control DPI collapse' -ForegroundColor Cyan

    $root = Resolve-Target -Path $ProjectPath
    if (-not $root) { Write-Host 'Exit.' -ForegroundColor Yellow; return }

    $rows = Get-Analysis -Root $root
    Show-Report -Rows $rows -Root $root

    $chosen = $Action
    if (-not $chosen) {
        if (-not $rows -or $rows.Count -eq 0) {
            $chosen = 'None'
        }
        else {
            $chosen = Get-ActionChoice
        }
    }

    Write-Section "Phase 3 - apply: $chosen"
    $changes = Invoke-Fix -Rows $rows -ActionName $chosen
    foreach ($c in $changes) { Write-Host "  $c" }

    Write-Section 'Phase 4 - save report'
    $reportPath = Write-ReportFile -Root $root -Rows $rows -ActionName $chosen -Changes $changes
    Write-Host "  Report written: $reportPath" -ForegroundColor Green
    if ($chosen -ne 'None') {
        Write-Host '  Remember to REBUILD the affected project(s).' -ForegroundColor Yellow
    }
}

Invoke-Main
