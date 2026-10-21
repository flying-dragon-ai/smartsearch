[CmdletBinding()]
param(
    [Parameter(Mandatory)][string] $PublishDirectory,
    [Parameter(Mandatory)][string] $OutputDirectory,
    [Parameter(Mandatory)][ValidatePattern('^\d+\.\d+\.\d+$')][string] $Version,
    [ValidateSet('x64', 'arm64')][string] $Architecture = 'x64',
    [ValidateSet('Required', 'Skip')][string] $SigningMode = 'Skip',
    [string] $PreviousReleaseDirectory,
    [string] $TestPackageId,
    [Parameter(Mandatory)][string] $ResultFile
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $PSScriptRoot 'Windows-Signing.ps1')
$PublishDirectory = [IO.Path]::GetFullPath($PublishDirectory)
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Package output must be a new directory.' }
if (-not (Test-Path -LiteralPath (Join-Path $PublishDirectory 'SmartSearch.Desktop.exe'))) { throw 'Missing published App.' }
if ($SigningMode -eq 'Required') {
    $expected = Get-ExpectedSigningCertificate (Join-Path $PSScriptRoot '../packaging/windows/smart-search.cer')
    try {
        foreach ($owned in @('SmartSearch.Desktop.exe', 'SmartSearch.Desktop.dll')) {
            Test-WindowsSignature (Join-Path $PublishDirectory $owned) $expected | Out-Null
        }
    }
    finally { $expected.Dispose() }
}
$packId = "com.smartsearch.desktop.win-$Architecture"
if ($TestPackageId) {
    if ($TestPackageId -notmatch '^com\.smartsearch\.test\.[a-z0-9.-]+$') {
        throw 'Test package IDs must use the isolated test namespace.'
    }
    $packId = $TestPackageId
}
$title = if ($TestPackageId) { $TestPackageId } else { "Smart Search" }
$shortcuts = if ($TestPackageId) { "None" } else { "StartMenuRoot" }
$channel = "win-$Architecture-stable"
$working = Join-Path (Split-Path $OutputDirectory -Parent) ("vpk-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $working | Out-Null
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$hasBaseline = $false
if ($PreviousReleaseDirectory) {
    $feed = Get-Content -Raw -LiteralPath (Join-Path $PreviousReleaseDirectory "releases.$channel.json") | ConvertFrom-Json
    $base = @($feed.Assets | Where-Object { $_.Type -eq 'Full' -and $_.PackageId -eq $packId } |
        Sort-Object { [version]$_.Version } -Descending)
    if ($base.Count -ne 1 -or [version]$base[0].Version -ge [version]$Version) { throw 'Expected exactly one older matching baseline.' }
    $asset = $base[0]
    if ([IO.Path]::GetFileName($asset.FileName) -ne $asset.FileName) { throw 'Unsafe baseline filename.' }
    $path = Join-Path $PreviousReleaseDirectory $asset.FileName
    if ((Get-Item -LiteralPath $path).Length -ne $asset.Size -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $asset.SHA256) { throw 'Baseline integrity failed.' }
    Copy-Item -LiteralPath $path -Destination $working
    Copy-Item -LiteralPath (Join-Path $PreviousReleaseDirectory "releases.$channel.json") -Destination $working
    $hasBaseline = $true
}
Push-Location $repositoryRoot
try {
    & dotnet tool restore
    if ($LASTEXITCODE -ne 0) { throw 'Could not restore the pinned Velopack CLI.' }
    $arguments = @('pack', '--yes', '--skip-updates', '--packId', $packId, '--packVersion', $Version,
        '--packDir', $PublishDirectory, '--mainExe', 'SmartSearch.Desktop.exe', '--packTitle', $title,
        '--packAuthors', 'Smart Search', '--runtime', "win-$Architecture", '--channel', $channel,
        '--outputDir', $working, '--icon', (Join-Path $repositoryRoot 'desktop/windows/Assets/smart-search.ico'),
        '--shortcuts', $shortcuts, '--noPortable', '--delta', 'BestSpeed',
        '--instWelcome', (Join-Path $repositoryRoot 'desktop/packaging/windows/migration.txt'))
    if ($SigningMode -eq 'Required') {
        # Own App files are already signed. vpk packages its unsigned Update.exe as
        # Squirrel.exe and adds an execution stub; preserve every other dependency.
        $sign = '"{0}" -NoProfile -File "{1}" -VelopackHelper -Path {{{{file}}}}' -f
            (Get-Process -Id $PID).Path, (Join-Path $PSScriptRoot 'Sign-WindowsFile.ps1')
        $arguments += @('--signTemplate', $sign, '--signParallel', '1', '--signExclude', '(?i)^(?!.*(?:^|[\\/])(?:Squirrel\.exe|SmartSearch\.Desktop_ExecutionStub\.exe)$).*')
    }
    & dotnet tool run vpk -- @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Velopack packaging failed.' }
}
finally { Pop-Location }
$feedPath = Join-Path $working "releases.$channel.json"
$feed = Get-Content -Raw -LiteralPath $feedPath | ConvertFrom-Json
$feed.Assets = @($feed.Assets | Where-Object { $_.Version -eq $Version -and $_.PackageId -eq $packId })
if (@($feed.Assets | Where-Object Type -eq 'Full').Count -ne 1) { throw 'Expected a complete target package.' }
if ($hasBaseline -and @($feed.Assets | Where-Object Type -eq 'Delta').Count -ne 1) { throw 'The expected delta package was not created.' }
foreach ($asset in $feed.Assets) { Copy-Item -LiteralPath (Join-Path $working $asset.FileName) -Destination $OutputDirectory }
$feed | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $OutputDirectory "releases.$channel.json") -Encoding utf8
$setup = Join-Path $working "$packId-$channel-Setup.exe"
$label = if ($SigningMode -eq 'Required') { 'signed' } else { 'unsigned-test' }
$downloadArchitecture = if ($Architecture -eq 'x64') { 'x86_64' } else { $Architecture }
$installer = Join-Path $OutputDirectory "SmartSearch-v$Version-windows-Setup-$downloadArchitecture.exe"
Copy-Item -LiteralPath $setup -Destination $installer
$signatures = @()
if ($SigningMode -eq 'Required') {
    $certificate = Get-ExpectedSigningCertificate (Join-Path $PSScriptRoot '../packaging/windows/smart-search.cer')
    try {
        $signatures += Test-WindowsSignature $installer $certificate
        $full = @($feed.Assets | Where-Object Type -eq 'Full')[0]
        $zip = [IO.Compression.ZipFile]::OpenRead((Join-Path $OutputDirectory $full.FileName))
        try {
            foreach ($helper in @('Squirrel.exe', 'SmartSearch.Desktop_ExecutionStub.exe')) {
                $entry = $zip.GetEntry("lib/app/$helper")
                if ($null -eq $entry) { throw "Required framework helper is missing: $helper" }
                $evidence = Join-Path $working "verified-$helper"
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $evidence)
                $signatures += Test-WindowsSignature $evidence $certificate
            }
        }
        finally { $zip.Dispose() }
    }
    finally { $certificate.Dispose() }
}
[ordered]@{
    status = "built-$label-package"; path = $installer; framework = 'Velopack'; pack_id = $packId;
    channel = $channel; directory = $OutputDirectory; baseline = $hasBaseline; delta = $hasBaseline;
    signatures = $signatures; test_identity = [bool]$TestPackageId;
    note = 'Per-user framework installation; shared config, CLI and Skills remain outside the App.'
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ResultFile -Encoding utf8
