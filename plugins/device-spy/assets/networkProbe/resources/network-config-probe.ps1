<#
.SYNOPSIS
    Collect the network configuration / health of the production PC into a single Markdown
    report (./network.config.md), to investigate the NIC link-flaps (e1rexpress Event 27)
    and IP-address conflicts (Tcpip Event 4199).

.DESCRIPTION
    Gathers, in one pass:
      - adapter inventory, link status, MAC, driver version/date
      - NIC advanced properties (Energy-Efficient Ethernet, Flow Control, Speed/Duplex,
        Green/Idle, Wake) + power management  <- prime suspects for the link flaps
      - full IP config (ipconfig /all + Get-NetIPConfiguration)
      - IP interface settings incl. DadTransmits (duplicate-address detection)  <- Ev 4199
      - ARP / neighbor table + a duplicate IP<->MAC analysis  <- find the conflicting host
      - routes, DNS
      - connectivity tests to gateway, production hosts and the conflicting addresses
      - recent System events from e1rexpress (27/32/33) and Tcpip (4199)

    Run on the PRODUCTION PC, preferably from an elevated PowerShell. Read-only (the only
    write is the report file). Each section is independent; failures are noted and skipped.

.PARAMETER OutFile
    Report path. Default: .\network.config.md

.PARAMETER DaysBack
    How far back to pull NIC/Tcpip events. Default: 7.

.PARAMETER PingTargets
    Hosts to test. Default: the auto-detected gateway(s) only. Pass extra hosts to test
    (e.g. production servers, or addresses seen conflicting).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\network-config-probe.ps1
#>

[CmdletBinding()]
param(
    [string]  $OutFile     = 'network.config.md',
    [int]     $DaysBack    = 7,
    [string[]]$PingTargets = @()
)

$ErrorActionPreference = 'Continue'
$sb = New-Object System.Text.StringBuilder

function Add-Line([string]$t='') { [void]$sb.AppendLine($t) }
# Run a scriptblock / native command, capture its text, wrap it in a fenced code block.
function Add-Section([string]$title, [scriptblock]$body, [string]$note='') {
    Add-Line "## $title"
    if ($note) { Add-Line "*$note*"; Add-Line '' }
    Add-Line '```'
    try {
        $out = & $body 2>&1 | Out-String
        if ([string]::IsNullOrWhiteSpace($out)) { Add-Line '(no data)' } else { Add-Line ($out.TrimEnd()) }
    } catch { Add-Line "ERROR: $($_.Exception.Message)" }
    Add-Line '```'
    Add-Line ''
    Write-Host "  + $title"
}

# Fetch a single PnP device property (returns $null on any failure).
function Get-PnpProp([string]$InstanceId, [string]$Key) {
    try { (Get-PnpDeviceProperty -InstanceId $InstanceId -KeyName $Key -ErrorAction Stop).Data } catch { $null }
}

# Decode an Intel VEN_8086 PCI hardware/device id to a friendly NIC model (best-effort).
function Resolve-IntelModel([string[]]$HardwareIds) {
    $map = @{
        '1533'='I210'; '1531'='I210'; '1536'='I210'; '1537'='I210'; '1538'='I210'; '157B'='I210'; '157C'='I210'; '15F6'='I210';
        '1539'='I211'; '1540'='I211';
        '15B7'='I219-LM'; '15B8'='I219-V'; '15D7'='I219-LM'; '15D8'='I219-V'; '15E3'='I219-LM';
        '15F4'='I219-LM'; '15F5'='I219-V'; '15FB'='I219-V'; '15FC'='I219-V'; '0D4E'='I219-LM'; '0D4F'='I219-V'; '0DC7'='I219-LM';
        '10D3'='82574L'; '10F6'='82574L'
    }
    foreach ($h in @($HardwareIds)) {
        if ($h -match 'VEN_8086.*DEV_([0-9A-Fa-f]{4})') {
            $dev = $matches[1].ToUpper()
            if ($map.ContainsKey($dev)) { return "$($map[$dev]) (DEV_$dev)" }
            return "Intel DEV_$dev (unmapped)"
        }
    }
    return 'n/a'
}

Write-Host "Collecting network configuration..."

# ---- Header ----
Add-Line "# Network configuration probe - $env:COMPUTERNAME"
Add-Line ''
Add-Line "- Generated : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
Add-Line "- Host      : $env:COMPUTERNAME   User: $env:USERNAME"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
Add-Line "- Elevated  : $admin$(if(-not $admin){'  (run as Administrator for complete data)'})"
Add-Line ''
Add-Line "> Purpose: investigate NIC link-flaps (e1rexpress Ev27) + IP conflicts (Tcpip Ev4199)."
Add-Line ''

# ---- Adapters ----
Add-Section 'Adapters (status / speed / MAC / driver)' {
    Get-NetAdapter | Sort-Object ifIndex |
        Format-Table -AutoSize ifIndex, Name, InterfaceDescription, Status, LinkSpeed, MacAddress, DriverVersion, DriverDate
}

Add-Section 'NIC hardware ID + driver provenance (physical NICs; VPN/virtual excluded)' {
    # Physical NICs only: exclude VPN/virtual/loopback; keep the CODESYS ETHERCAT binding.
    Get-NetAdapter -ErrorAction SilentlyContinue |
        Where-Object { $_.InterfaceDescription -notmatch 'TeamViewer|VPN|Virtual|Loopback' } |
        Sort-Object ifIndex |
        ForEach-Object {
            $id    = $_.PnPDeviceID
            $hwids = Get-PnpProp $id 'DEVPKEY_Device_HardwareIds'
            $cids  = Get-PnpProp $id 'DEVPKEY_Device_CompatibleIds'
            [pscustomobject]@{
                Name             = $_.Name
                InterfaceDesc    = $_.InterfaceDescription
                Status           = $_.Status
                MacAddress       = $_.MacAddress
                ResolvedModel    = Resolve-IntelModel $hwids
                PnPDeviceID      = $id
                HardwareIDs      = if ($hwids) { ($hwids -join '; ') } else { 'n/a' }
                CompatibleIDs    = if ($cids)  { ($cids  -join '; ') } else { 'n/a' }
                MatchingDeviceId = Get-PnpProp $id 'DEVPKEY_Device_MatchingDeviceId'
                DriverDesc       = Get-PnpProp $id 'DEVPKEY_Device_DriverDesc'
                DriverProvider   = Get-PnpProp $id 'DEVPKEY_Device_DriverProvider'
                DriverInfPath    = Get-PnpProp $id 'DEVPKEY_Device_DriverInfPath'
                DriverFileName   = $_.DriverFileName
                DriverVersion    = $_.DriverVersion
                DriverDate       = $_.DriverDate
            }
        } | Format-List
} 'Per NIC: HardwareIDs (PCI VEN/DEV/SUBSYS) + MatchingDeviceId (what the driver bound on -> exact vs compatible/fallback) + driver provider/INF/version/date. ResolvedModel decodes Intel DEV ids (1533=I210, 1539=I211, 15xx=I219).'

Add-Section 'All network-class PnP devices (incl. hidden) — reveals EtherCAT silicon' {
    # Get-PnpDevice -Class Net lists hidden/RTE-bound silicon too: the real Intel chip behind
    # the CODESYS EtherExpress (EtherCAT) adapter is here even though Get-NetAdapter masks it.
    Get-PnpDevice -Class Net -ErrorAction SilentlyContinue |
        Sort-Object FriendlyName |
        ForEach-Object {
            $id    = $_.InstanceId
            $hwids = Get-PnpProp $id 'DEVPKEY_Device_HardwareIds'
            [pscustomobject]@{
                FriendlyName  = $_.FriendlyName
                Status        = $_.Status
                Problem       = $_.Problem
                ResolvedModel = Resolve-IntelModel $hwids
                InstanceId    = $id
                HardwareIDs   = if ($hwids) { ($hwids -join '; ') } else { 'n/a' }
                DriverDesc    = Get-PnpProp $id 'DEVPKEY_Device_DriverDesc'
                DriverProvider= Get-PnpProp $id 'DEVPKEY_Device_DriverProvider'
                DriverInfPath = Get-PnpProp $id 'DEVPKEY_Device_DriverInfPath'
                DriverVersion = Get-PnpProp $id 'DEVPKEY_Device_DriverVersion'
                DriverDate    = Get-PnpProp $id 'DEVPKEY_Device_DriverDate'
            }
        } | Format-List
} 'Includes HIDDEN net devices -> the underlying Intel silicon the CODESYS RTE took over for EtherCAT (decisive for the I210-vs-I211 + CmpEt1000Drv-supported question). Also a true silicon census.'

Add-Section 'Signed network drivers (Win32_PnPSignedDriver, class NET)' {
    Get-CimInstance Win32_PnPSignedDriver -ErrorAction SilentlyContinue |
        Where-Object { $_.DeviceClass -eq 'NET' } |
        Sort-Object DeviceName |
        Format-List DeviceName, DriverVersion, DriverDate, DriverProviderName, InfName, IsSigned, HardWareID, DeviceID
} 'Clean per-device driver version/date/provider/INF for the "are the drivers up to date?" check (compare DriverVersion/DriverDate to the latest Intel/CODESYS release).'

Add-Section 'pnputil /enum-drivers (network-class INFs)' {
    $raw = pnputil /enum-drivers | Out-String
    # Filter by the Net setup-class GUID (locale-independent; the "Class Name" label is localized,
    # e.g. Italian "Nome classe", so matching the text 'Net' fails on non-English Windows).
    ($raw -split "(?:\r?\n){2,}") | Where-Object { $_ -match '(?i)4d36e972-e325-11ce-bfc1-08002be10318' } | ForEach-Object { $_.Trim(); '' }
} 'Installed/staged driver packages of Net class (matched by class GUID) -> published INF name, provider, version, date, signer; shows whether a newer net INF is already on the box.'

Add-Section 'NIC advanced properties (EEE / Flow Control / Speed-Duplex / Power)' {
    Get-NetAdapterAdvancedProperty -ErrorAction SilentlyContinue |
        Sort-Object Name, DisplayName |
        Format-Table -AutoSize Name, DisplayName, DisplayValue, RegistryKeyword
} 'Look for Energy-Efficient Ethernet/Green Ethernet = Enabled, Flow Control, and Speed&Duplex=Auto.'

Add-Section 'NIC power management' {
    Get-NetAdapter | ForEach-Object {
        $pm = $null; try { $pm = Get-NetAdapterPowerManagement -Name $_.Name -ErrorAction Stop } catch {}
        [pscustomobject]@{ Adapter=$_.Name; AllowComputerToTurnOff=if($pm){$pm.AllowComputerToTurnOffDevice}else{'n/a'} }
    } | Format-Table -AutoSize
} 'AllowComputerToTurnOff = Enabled can cause link drops -> set Disabled.'

# ---- IP configuration ----
Add-Section 'ipconfig /all' { ipconfig /all }

Add-Section 'Get-NetIPConfiguration (per interface)' {
    Get-NetIPConfiguration -All -Detailed -ErrorAction SilentlyContinue | Out-String
}

Add-Section 'IP interfaces (incl. DadTransmits / DHCP)' {
    Get-NetIPInterface -ErrorAction SilentlyContinue |
        Sort-Object InterfaceAlias, AddressFamily |
        Format-Table -AutoSize InterfaceAlias, AddressFamily, Dhcp, ConnectionState, DadTransmits, NlMtu, InterfaceMetric
} 'DadTransmits = duplicate-address detection probes (relevant to Tcpip Ev4199).'

Add-Section 'IPv4 addresses' {
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Sort-Object InterfaceAlias | Format-Table -AutoSize InterfaceAlias, IPAddress, PrefixLength, PrefixOrigin, SuffixOrigin, AddressState
}

# ---- ARP / neighbors + duplicate analysis ----
Add-Section 'ARP / neighbor table (Get-NetNeighbor)' {
    Get-NetNeighbor -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.State -ne 'Unreachable' -and $_.LinkLayerAddress } |
        Sort-Object IPAddress | Format-Table -AutoSize IPAddress, LinkLayerAddress, State, InterfaceAlias
}

Add-Section 'arp -a (raw)' { arp -a }

Add-Section 'Duplicate-IP / duplicate-MAC analysis' {
    $nb = Get-NetNeighbor -AddressFamily IPv4 -ErrorAction SilentlyContinue |
          Where-Object { $_.LinkLayerAddress -and $_.State -ne 'Unreachable' }
    "IPs answered by more than one MAC (= address conflict):"
    $nb | Group-Object IPAddress | Where-Object Count -gt 1 |
        ForEach-Object { "  {0}  ->  {1}" -f $_.Name, (($_.Group.LinkLayerAddress | Sort-Object -Unique) -join ', ') }
    ""
    "MACs holding more than one IP (informational):"
    $nb | Group-Object LinkLayerAddress | Where-Object Count -gt 1 |
        ForEach-Object { "  {0}  ->  {1}" -f $_.Name, (($_.Group.IPAddress | Sort-Object -Unique) -join ', ') }
} 'If an IP maps to 2+ MACs, that is the conflict source (Ev4199).'

# ---- Routes / DNS ----
Add-Section 'Routing table (IPv4)' {
    Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Sort-Object RouteMetric | Format-Table -AutoSize DestinationPrefix, NextHop, RouteMetric, InterfaceAlias
}
Add-Section 'DNS servers' {
    Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Format-Table -AutoSize InterfaceAlias, ServerAddresses
}

# ---- Connectivity ----
$gw = (Get-NetIPConfiguration -ErrorAction SilentlyContinue | Where-Object IPv4DefaultGateway).IPv4DefaultGateway.NextHop | Sort-Object -Unique
$targets = @($gw) + $PingTargets | Where-Object { $_ } | Select-Object -Unique
Add-Section 'Connectivity tests (gateway + provided targets)' {
    foreach ($t in $targets) {
        $r = Test-Connection -ComputerName $t -Count 2 -ErrorAction SilentlyContinue
        if ($r) { "{0,-16} reachable  avg={1} ms" -f $t, ([math]::Round((($r | Measure-Object ResponseTime -Average).Average),0)) }
        else    { "{0,-16} NO REPLY" -f $t }
    }
} "Targets: $($targets -join ', ')"

# ---- Recent NIC / Tcpip events ----
Add-Section "System events: e1rexpress + Tcpip (last $DaysBack days)" {
    Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='e1rexpress','Tcpip'; StartTime=(Get-Date).AddDays(-$DaysBack)} -ErrorAction SilentlyContinue |
        Sort-Object TimeCreated |
        Select-Object @{N='Time';E={$_.TimeCreated.ToString('MM-dd HH:mm:ss')}}, Id, ProviderName, LevelDisplayName, @{N='Msg';E={(($_.Message -split "`r?`n")[0])}} |
        Format-Table -AutoSize
} 'Ev27=link down, Ev32=link up, Ev33=transition; Tcpip 4199 = IP conflict.'

Add-Section "Event summary (counts, last $DaysBack days)" {
    Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='e1rexpress','Tcpip'; StartTime=(Get-Date).AddDays(-$DaysBack)} -ErrorAction SilentlyContinue |
        Group-Object ProviderName, Id | Sort-Object Count -Descending |
        Format-Table -AutoSize Count, Name
}

# ---- Extras (netsh) ----
Add-Section 'netsh interface ipv4 show config' { netsh interface ipv4 show config }

# ---- write ----
$path = $OutFile
try { $resolved = (Resolve-Path -LiteralPath (Split-Path -Parent $OutFile) -ErrorAction SilentlyContinue) } catch {}
$sb.ToString() | Set-Content -LiteralPath $path -Encoding UTF8
$full = (Resolve-Path -LiteralPath $path).Path
Write-Host ''
Write-Host "Report written -> $full" -ForegroundColor Green
