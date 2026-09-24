<#
.SYNOPSIS
  Collects the pending git changes (staged + unstaged + untracked) of a solution's repo set in ONE
  pass and prints a compact, budgeted text summary for writing a commit message.

.DESCRIPTION
  Read-only: runs only git status/diff. Resolves the target (.sln/.slnx, project file, folder, or
  the current directory) to a root + repo set, then per changed repo prints status, --stat, and
  the zero-context hunks with generated/lockfile noise excluded. Two budgets keep the output small:
  a per-repo cap (-RepoBudget) and a global cap across all repos (-GlobalBudget). A repo over
  budget is reported at file level only and flagged "[hunks omitted: ...]" — nothing is dropped
  silently.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File collect-changes.ps1 -Target "C:\repos\5315_LAG"
#>
param(
    [string]$Target = (Get-Location).Path,
    [int]$RepoBudget = 600,
    [int]$GlobalBudget = 1500
)

# 'Continue', not 'Stop': under PowerShell 5.1 any git stderr line (e.g. CRLF warnings) would
# otherwise become a terminating NativeCommandError even when redirected.
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Exclude = @(
    ':(exclude)**/obj/**', ':(exclude)**/bin/**', ':(exclude)**/*.Designer.cs',
    ':(exclude)**/*.min.*', ':(exclude)**/*-lock.json', ':(exclude)**/*.lock',
    ':(exclude)**/packages.lock.json', ':(exclude)**/*.resx'
)

function Get-RepoTop([string]$dir) {
    $top = & git -C $dir rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $top) { return (Resolve-Path $top).Path }
    return $null
}

function Find-Solutions([string]$dir) {
    @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.sln', '.slnx' })
}

# --- Resolve target -> root, stem, mode --------------------------------------------------------
if (-not (Test-Path -LiteralPath $Target)) {
    Write-Output "ERROR: path not found: $Target"
    Write-Output 'USAGE: /gitize [--scope|-s "<.sln, project file, or folder>"]'
    exit 2
}
$item = Get-Item -LiteralPath $Target
$root = $null; $stem = $null; $mode = $null

if (-not $item.PSIsContainer -and $item.Extension -in '.sln', '.slnx') {
    $root = $item.DirectoryName; $stem = $item.BaseName; $mode = 'solution'
}
elseif ($item.PSIsContainer) {
    # Walk up from the folder to the nearest solution; stop at the first enclosing repo boundary
    # only if no solution exists above it (multi-repo workspaces keep the .sln outside any repo).
    $d = $item.FullName
    # A workspace folder with no solution file of its own but with git sub-repos (e.g. the .slnx
    # lives inside one of them) is still a multi-repo target: scan its subfolders.
    if ((Find-Solutions $d).Count -eq 0 -and -not (Test-Path -LiteralPath (Join-Path $d '.git')) -and
        @(Get-ChildItem -LiteralPath $d -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName '.git') }).Count -gt 0) {
        $root = $d; $stem = $item.Name; $mode = 'solution'; $d = $null
    }
    while ($d) {
        $sl = Find-Solutions $d
        if ($sl.Count -eq 1) { $root = $d; $stem = $sl[0].BaseName; $mode = 'solution'; break }
        if ($sl.Count -gt 1) {
            Write-Output "AMBIGUOUS: several solutions in $d -> $(($sl | ForEach-Object Name) -join ', ')"
            Write-Output 'Ask the user which one, then re-run with -Target "<that .sln>".'
            exit 3
        }
        $parent = Split-Path $d -Parent
        if ($parent -eq $d) { break }
        $d = $parent
    }
    if (-not $root) {
        $top = Get-RepoTop $item.FullName
        if ($top) { $root = $top; $stem = Split-Path $top -Leaf; $mode = 'single-repo' }
    }
}
else {
    $top = Get-RepoTop $item.DirectoryName
    if ($top) { $root = $top; $stem = $item.BaseName; $mode = 'single-repo' }
}

if (-not $root) {
    Write-Output "ERROR: no .sln/.slnx or git repo resolves from: $Target"
    Write-Output 'USAGE: /gitize [--scope|-s "<.sln, project file, or folder>"]'
    exit 2
}

# --- Discover repo set --------------------------------------------------------------------------
$repos = @()
if ($mode -eq 'solution') {
    if (Test-Path -LiteralPath (Join-Path $root '.git')) { $repos += $root }
    $repos += @(Get-ChildItem -LiteralPath $root -Directory |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName '.git') } |
        ForEach-Object FullName)
    if ($repos.Count -eq 0) {
        # The solution sits inside a single repo (not a multi-repo workspace).
        $top = Get-RepoTop $root
        if ($top) { $repos = @($top); $mode = 'single-repo' }
    }
}
else { $repos = @($root) }

Write-Output "ROOT: $root"
Write-Output "STEM: $stem"
Write-Output "MODE: $mode"
Write-Output "REPOS: $($repos.Count) ($(($repos | ForEach-Object { Split-Path $_ -Leaf }) -join ', '))"

# --- Collect ------------------------------------------------------------------------------------
$used = 0
$changed = 0
$notes = @()

foreach ($r in $repos) {
    $name = Split-Path $r -Leaf
    $status = @(& git -C $r status --short --untracked-files=all 2>$null)
    # Untracked build output (bin/obj not yet in .gitignore) is noise: count it, don't list it.
    $buildNoise = @($status | Where-Object { $_ -match '^\?\? (.*/)?(bin|obj)/' })
    $status = @($status | Where-Object { $_ -notmatch '^\?\? (.*/)?(bin|obj)/' })
    if ($status.Count -eq 0) {
        if ($buildNoise.Count) { $notes += "$name : only untracked bin/obj output ($($buildNoise.Count) files) - ignored" }
        continue
    }
    $changed++

    # Diff against HEAD = staged + unstaged in one go; a repo with no commit yet has no HEAD, so
    # fall back to the staged diff alone.
    & git -C $r rev-parse --verify -q HEAD *> $null
    [string[]]$base = if ($LASTEXITCODE -eq 0) { 'HEAD' } else { '--staged' }

    # Per-file churn (binary files report "-" and count as 0).
    $files = @()
    foreach ($l in @(& git -C $r diff --numstat @base -- . @Exclude 2>$null)) {
        $p = $l -split "`t", 3
        $n = 0
        if ($p[0] -match '^\d+$') { $n += [int]$p[0] }
        if ($p[1] -match '^\d+$') { $n += [int]$p[1] }
        $files += [pscustomobject]@{ Path = $p[2]; Churn = $n }
    }
    $churn = ($files | Measure-Object Churn -Sum).Sum
    if (-not $churn) { $churn = 0 }

    Write-Output ''
    Write-Output "=== REPO $name  (files: $($status.Count), churn: $churn lines)"
    Write-Output '--- status'
    $status | ForEach-Object { Write-Output $_ }
    Write-Output '--- stat'
    & git -C $r diff --stat=120 @base 2>$null | ForEach-Object { Write-Output $_ }

    # A single file that dominates the diff (over half the repo budget) is summarized from its
    # stat line only; the rest of the repo still gets its hunks read if they fit.
    $big = @($files | Where-Object { $_.Churn -gt [math]::Floor($RepoBudget / 2) })
    $readable = $churn - (($big | Measure-Object Churn -Sum).Sum)
    $remaining = $GlobalBudget - $used
    if ($readable -gt $RepoBudget -or $readable -gt $remaining) {
        $why = if ($readable -gt $RepoBudget) { "repo churn $readable > repo budget $RepoBudget" } else { "global budget exhausted ($used/$GlobalBudget used)" }
        Write-Output "[hunks omitted: $why - summarize this repo from status + stat]"
        $notes += "$name : file-level only ($why)"
        continue
    }

    $skip = @($big | ForEach-Object { ":(exclude)$($_.Path)" })
    foreach ($b in $big) {
        Write-Output "[hunks omitted for $($b.Path): $($b.Churn) lines - summarize from stat]"
        $notes += "$name/$($b.Path) : file-level only ($($b.Churn) lines)"
    }
    if ($readable -gt 0) {
        Write-Output '--- hunks (unified=0, noise excluded)'
        # Keep only the lines that carry meaning; index/mode headers are noise for a summary.
        & git -C $r diff --unified=0 --no-color @base -- . @Exclude @skip 2>$null |
            Where-Object { $_ -notmatch '^(index |new file mode|deleted file mode|similarity index|--- |\+\+\+ )' } |
            ForEach-Object { Write-Output $_ }
    }
    $used += $readable

    $untracked = @($status | Where-Object { $_ -like '`?`? *' })
    if ($untracked.Count -gt 0) {
        Write-Output "--- untracked: $($untracked.Count) file(s) listed in status (content not read)"
    }
}

Write-Output ''
if ($changed -eq 0) { Write-Output 'RESULT: CLEAN (nothing to commit)'; exit 0 }
Write-Output "RESULT: $changed changed repo(s), $used/$GlobalBudget hunk lines read"
if ($notes.Count) { Write-Output 'TRUNCATION:'; $notes | ForEach-Object { Write-Output "  $_" } }
