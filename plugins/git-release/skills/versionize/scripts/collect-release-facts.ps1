<#
.SYNOPSIS
  Gathers every machine-readable fact a ReleaseNote needs in ONE read-only pass and prints it as
  compact JSON: repo set + git facts, pre-flight cleanliness, youngest build per executable
  project, DLL identity, frameworks and central package versions. Optionally, the commit log of
  each repo since a recorded baseline (for -upd).

.DESCRIPTION
  Never builds, stages, or commits. Reads .csproj files, built DLL metadata and git plumbing only.

.PARAMETER Target
  A .sln/.slnx, a project file, or a folder (defaults to the current directory).

.PARAMETER Since
  For -upd: "RepoName=sha;RepoName2=sha" — the per-repo last commits recorded in the existing
  ReleaseNote. Emits `log` (hash|subject) per repo for <sha>..HEAD.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File collect-release-facts.ps1 -Target "C:\repos\5309_FAEL\Sistec.5309.sln"
#>
param(
    [string]$Target = (Get-Location).Path,
    [string]$Since = ''
)

# 'Continue': under PowerShell 5.1 a git stderr line would otherwise become a terminating error.
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Fail([string]$msg, [int]$code = 2) {
    [pscustomobject]@{ error = $msg; usage = '/versionize -new|-upd "<.sln, project file, or folder>" [--out <path>]' } |
        ConvertTo-Json -Compress
    exit $code
}

function Get-RepoTop([string]$dir) {
    $top = & git -C $dir rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $top) { return (Resolve-Path $top).Path }
    return $null
}

function Find-Solutions([string]$dir) {
    @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.sln', '.slnx' })
}

function Get-GitRepos([string]$dir) {
    @(Get-ChildItem -LiteralPath $dir -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName '.git') } | ForEach-Object FullName)
}

# --- Resolve target -----------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath $Target)) { Fail "path not found: $Target" }
$item = Get-Item -LiteralPath $Target
$root = $null; $stem = $null; $mode = $null
if (-not $item.PSIsContainer -and $item.Extension -in '.sln', '.slnx') {
    $root = $item.DirectoryName; $stem = $item.BaseName; $mode = 'solution'
}
elseif ($item.PSIsContainer) {
    $sl = Find-Solutions $item.FullName
    if ($sl.Count -gt 1) { Fail "several solutions in $($item.FullName): $(($sl | ForEach-Object Name) -join ', ') - pass the one to use" 3 }
    if ($sl.Count -eq 1) { $root = $item.FullName; $stem = $sl[0].BaseName; $mode = 'solution' }
    elseif ((Get-GitRepos $item.FullName).Count -gt 0) { $root = $item.FullName; $stem = $item.Name; $mode = 'solution' }
    else { $top = Get-RepoTop $item.FullName; if ($top) { $root = $top; $stem = Split-Path $top -Leaf; $mode = 'single-repo' } }
}
else {
    $top = Get-RepoTop $item.DirectoryName
    if ($top) { $root = $top; $stem = $item.BaseName; $mode = 'single-repo' }
}
if (-not $root) { Fail "no solution or git repo resolves from: $Target" }

$repoPaths = @()
if ($mode -eq 'solution') {
    if (Test-Path -LiteralPath (Join-Path $root '.git')) { $repoPaths += $root }
    $repoPaths += Get-GitRepos $root
    if ($repoPaths.Count -eq 0) { $top = Get-RepoTop $root; if ($top) { $repoPaths = @($top); $mode = 'single-repo' } }
}
else { $repoPaths = @($root) }
if ($repoPaths.Count -eq 0) { Fail "no git repo found under $root" }

# --- Baseline for -upd ----------------------------------------------------------------------------
$sinceMap = @{}
foreach ($pair in ($Since -split ';')) {
    if ($pair -match '^\s*([^=]+?)\s*=\s*([0-9a-fA-F]{4,40})\s*$') { $sinceMap[$Matches[1]] = $Matches[2] }
}

# --- Git facts + pre-flight per repo ------------------------------------------------------------
$repos = @()
foreach ($r in $repoPaths) {
    $name = Split-Path $r -Leaf
    $gitDir = & git -C $r rev-parse --git-dir 2>$null
    if ($LASTEXITCODE -ne 0) { Fail "unreadable git repo: $r (release note would misstate the snapshot)" 4 }
    if (-not [System.IO.Path]::IsPathRooted($gitDir)) { $gitDir = Join-Path $r $gitDir }

    $last = (& git -C $r log -1 --format='%h|%H|%s|%ci' 2>$null) -split '\|', 4
    $porc = @(& git -C $r status --porcelain 2>$null)
    $op = @()
    if (Test-Path (Join-Path $gitDir 'MERGE_HEAD')) { $op += 'merge' }
    if ((Test-Path (Join-Path $gitDir 'rebase-merge')) -or (Test-Path (Join-Path $gitDir 'rebase-apply'))) { $op += 'rebase' }
    if (Test-Path (Join-Path $gitDir 'CHERRY_PICK_HEAD')) { $op += 'cherry-pick' }
    $ab = & git -C $r rev-list --left-right --count '@{u}...HEAD' 2>$null
    $behind = $null; $ahead = $null
    if ($LASTEXITCODE -eq 0 -and $ab -match '^(\d+)\s+(\d+)$') { $behind = [int]$Matches[1]; $ahead = [int]$Matches[2] }

    $entry = [ordered]@{
        name      = $name
        path      = $r
        remote    = [string](& git -C $r remote get-url origin 2>$null)
        branch    = [string](& git -C $r rev-parse --abbrev-ref HEAD 2>$null)
        head      = $last[0]
        headFull  = $last[1]
        subject   = $last[2]
        date      = $last[3]
        staged    = @($porc | Where-Object { $_ -match '^[MADRC]' }).Count
        unstaged  = @($porc | Where-Object { $_ -match '^.[MD]' }).Count
        untracked = @($porc | Where-Object { $_ -like '`?`?*' }).Count
        inProgress = $op
        ahead     = $ahead
        behind    = $behind
    }
    if ($sinceMap.ContainsKey($name)) {
        $entry.since = $sinceMap[$name]
        $entry.log = @(& git -C $r log "$($sinceMap[$name])..HEAD" --format='%h|%s' 2>$null)
    }
    $repos += [pscustomobject]$entry
}

# --- Projects: frameworks + executable projects -------------------------------------------------
$skipDir = '\\(bin|obj|packages|node_modules|\.git|\.vs)\\'
$projFiles = @(foreach ($r in $repoPaths) {
    Get-ChildItem -LiteralPath $r -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.csproj', '.vbproj' } |
        Where-Object { $_.FullName -notmatch $skipDir }
})

$frameworks = @()
$apps = @()
foreach ($p in $projFiles) {
    [xml]$x = $null
    try { [xml]$x = Get-Content -LiteralPath $p.FullName -Raw } catch { continue }
    $props = @($x.Project.PropertyGroup)
    $tf = ($props | ForEach-Object { $_.TargetFramework; $_.TargetFrameworks; $_.TargetFrameworkVersion } | Where-Object { $_ } | Select-Object -First 1)
    $outType = ($props | ForEach-Object { $_.OutputType } | Where-Object { $_ } | Select-Object -First 1)
    $outPath = ($props | ForEach-Object { $_.OutputPath; $_.OutDir; $_.BaseOutputPath } | Where-Object { $_ -is [string] -and $_ } | Select-Object -First 1)
    $frameworks += [pscustomobject]@{ project = $p.BaseName; tf = [string]$tf; type = [string]$outType }
    if ($outType -in 'Exe', 'WinExe' -and $p.BaseName -notmatch '(Test|Tests|Spec)$') {
        $apps += [pscustomobject]@{ file = $p; outPath = $outPath }
    }
}

# --- Youngest build per app + DLL identity --------------------------------------------------------
$familyRx = '^(Sistec|Esa|EasyModbus|Kuka|Opc\.Ua|OPCFoundation|Abc\.Zebus|MySql|MySqlConnector|MySqlBackup|Dapper)'
$builds = @()
foreach ($a in $apps) {
    $projDir = $a.file.DirectoryName
    # Follow the declared OutputPath up to its first MSBuild property; the computed tail
    # (e.g. "HMI v$(_AsmVerMajorMinor)") is resolved by picking the youngest subfolder below.
    $bases = @()
    if ($a.outPath) {
        $resolvable = ($a.outPath -replace '\$\(Configuration\)', 'Release' -split '\$\(')[0].TrimEnd('\', '/')
        if ($resolvable) { $bases += (Join-Path $projDir $resolvable) }
    }
    $bases += (Join-Path $projDir 'bin\Release'), (Join-Path $projDir 'bin\Debug')

    $best = $null
    foreach ($b in $bases) {
        if (-not (Test-Path -LiteralPath $b)) { continue }
        $cands = @(Get-Item -LiteralPath $b) + @(Get-ChildItem -LiteralPath $b -Directory -Recurse -Depth 2 -ErrorAction SilentlyContinue)
        foreach ($c in $cands) {
            $newest = Get-ChildItem -LiteralPath $c.FullName -File -Filter *.dll -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($newest -and (-not $best -or $newest.LastWriteTime -gt $best.time)) {
                $best = [pscustomobject]@{ folder = $c.FullName; time = $newest.LastWriteTime }
            }
        }
        if ($best) { break }   # the declared base wins over the bin\Release / bin\Debug fallbacks
    }

    $build = [ordered]@{ project = $a.file.BaseName; csproj = $a.file.FullName; folder = $null; built = $null; dlls = @(); other = 0 }
    if ($best) {
        $build.folder = $best.folder
        $build.built = $best.time.ToString('yyyy-MM-dd HH:mm:ss')
        $bin = @(Get-ChildItem -LiteralPath $best.folder -File | Where-Object { $_.Extension -in '.dll', '.exe' })
        $dllNames = @($bin | Where-Object Extension -eq '.dll' | ForEach-Object BaseName)
        # An SDK app ships <App>.dll plus an <App>.exe apphost: read the managed .dll only.
        $bin = @($bin | Where-Object { $_.Extension -eq '.dll' -or $dllNames -notcontains $_.BaseName })
        foreach ($d in $bin) {
            if ($d.BaseName -notmatch $familyRx -and $d.BaseName -ne $a.file.BaseName) { $build.other++; continue }
            $vi = $d.VersionInfo
            $asmVer = $null
            try { $asmVer = [System.Reflection.AssemblyName]::GetAssemblyName($d.FullName).Version.ToString() } catch { }
            $sha = if ($vi.ProductVersion -match '\+([0-9a-f]{7,40})') { $Matches[1].Substring(0, 7) } else { $null }
            $build.dlls += [pscustomobject]@{
                name = $d.BaseName; version = $asmVer; file = $vi.FileVersion; company = $vi.CompanyName
                title = $vi.FileDescription; sha = $sha
            }
        }
    }
    $builds += [pscustomobject]$build
}

# --- Stale-build check: newest tracked source vs youngest build ---------------------------------
$newestSrc = $null
foreach ($r in $repoPaths) {
    # -Include is ignored with -LiteralPath on PowerShell 5.1, so filter by extension explicitly.
    $f = Get-ChildItem -LiteralPath $r -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.cs', '.vb', '.xaml', '.csproj', '.props' } |
        Where-Object { $_.FullName -notmatch $skipDir } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($f -and (-not $newestSrc -or $f.LastWriteTime -gt $newestSrc.LastWriteTime)) { $newestSrc = $f }
}
$stale = @()
foreach ($b in $builds) {
    if (-not $b.built) { $stale += "$($b.project): no built DLL found (fall back to .csproj version)"; continue }
    $bt = [datetime]$b.built
    # 2 s tolerance: MSBuild touches project files during the same build, and copies reset mtimes.
    if ($newestSrc -and $newestSrc.LastWriteTime -gt $bt.AddSeconds(2)) {
        $stale += "$($b.project): source $($newestSrc.Name) ($($newestSrc.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))) newer than build ($($b.built))"
    }
    $appDll = $b.dlls | Where-Object { $_.name -eq $b.project } | Select-Object -First 1
    $repo = $repos | Where-Object { $b.csproj.StartsWith($_.path, [StringComparison]::OrdinalIgnoreCase) } |
        Sort-Object { $_.path.Length } -Descending | Select-Object -First 1
    if ($appDll -and $appDll.sha -and $repo -and -not $repo.headFull.StartsWith($appDll.sha)) {
        $n = & git -C $repo.path rev-list --count "$($appDll.sha)..HEAD" 2>$null
        if ($LASTEXITCODE -eq 0 -and [int]$n -gt 0) { $stale += "$($b.project): built from $($appDll.sha), HEAD is $n commit(s) ahead ($($repo.head))" }
    }
}

# --- Central packages + global.json -------------------------------------------------------------
$packages = @()
foreach ($r in $repoPaths) {
    foreach ($dp in Get-ChildItem -LiteralPath $r -Recurse -File -Filter Directory.Packages.props -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch $skipDir }) {
        [xml]$px = Get-Content -LiteralPath $dp.FullName -Raw
        foreach ($pv in @($px.Project.ItemGroup.PackageVersion)) {
            if ($pv.Include -match $familyRx) { $packages += "$($pv.Include)=$($pv.Version)" }
        }
    }
}
$globalJson = @(@(foreach ($r in @($root) + $repoPaths) { $g = Join-Path $r 'global.json'; if (Test-Path $g) { $g } }) | Select-Object -Unique)

$catalog = @(foreach ($r in $repoPaths) { $c = Join-Path $r 'FeatureCatalog.md'; if (Test-Path $c) { $c } })

# Paths are emitted relative to the root: the absolute prefix repeated on every row is pure token cost.
function Rel([string]$p) { if ($p -and $p.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { $p.Substring($root.Length).TrimStart([char]92) } else { $p } }
foreach ($o in $repos) { $o.path = Rel $o.path; if (-not $o.path) { $o.path = '.' } }
foreach ($o in $builds) { $o.csproj = Rel $o.csproj; $o.folder = Rel $o.folder }
$globalJson = @($globalJson | ForEach-Object { Rel $_ })
$catalog = @($catalog | ForEach-Object { Rel $_ })

[pscustomobject]@{
    root       = $root
    stem       = $stem
    mode       = $mode
    repos      = $repos
    builds     = $builds
    frameworks = $frameworks
    packages   = @($packages | Sort-Object -Unique)
    globalJson = $globalJson
    catalog    = $catalog
    preflight  = [pscustomobject]@{
        dirty      = @($repos | Where-Object { $_.staged + $_.unstaged + $_.untracked -gt 0 } | ForEach-Object { "$($_.name) (S$($_.staged)/U$($_.unstaged)/?$($_.untracked))" })
        inProgress = @($repos | Where-Object { $_.inProgress.Count } | ForEach-Object { "$($_.name): $($_.inProgress -join ',')" })
        stale      = $stale
        unpushed   = @($repos | Where-Object { $_.ahead -or $_.behind } | ForEach-Object { "$($_.name): +$($_.ahead)/-$($_.behind)" })
    }
} | ConvertTo-Json -Depth 6 -Compress
