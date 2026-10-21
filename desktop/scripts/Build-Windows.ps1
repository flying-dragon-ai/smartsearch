[CmdletBinding()]
param(
    [ValidateSet("x64", "arm64")]
    [string] $Architecture = "x64",
    [ValidateSet("Debug", "Release")]
    [string] $Configuration = "Release",
    [string] $PythonPath = "python",
    [string] $OutputRoot = ".desktop-artifacts",
    [ValidateSet("Auto", "Required", "Skip")]
    [string] $InstallerMode = "Auto",
    [string] $PreviousReleaseDirectory,
    [ValidateSet("Required", "Skip")]
    [string] $SigningMode = "Skip"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$signingEnabled = $SigningMode -eq 'Required'
$signatures = @()
$signingCertificate = $null
if ($signingEnabled) {
    . (Join-Path $PSScriptRoot 'Windows-Signing.ps1')
    $signingCertificate = Get-ExpectedSigningCertificate (Join-Path $PSScriptRoot '../packaging/windows/smart-search.cer')
    Assert-SigningCertificate $signingCertificate $signingCertificate
    $identityPath = "Cert:/CurrentUser/My/$($signingCertificate.Thumbprint)"
    if (-not (Test-Path -LiteralPath $identityPath) -or -not (Get-Item -LiteralPath $identityPath).HasPrivateKey) {
        throw 'Required signing identity is missing. Import the pinned PFX before building; no unsigned fallback.'
    }
    $null = Get-WindowsSignTool
}

function Resolve-ExecutablePath([string] $Candidate) {
    if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
        return [System.IO.Path]::GetFullPath($Candidate)
    }
    return (Get-Command -Name $Candidate -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
}

function Resolve-RepositoryPath([string] $Candidate) {
    if ([System.IO.Path]::IsPathRooted($Candidate)) {
        return [System.IO.Path]::GetFullPath($Candidate)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $Candidate))
}

function Get-PythonArchitecture([string] $PythonExecutable) {
    # The interpreter target controls PyInstaller output, including x64 Python
    # running under Windows on ARM emulation.
    $reported = [string] (& $PythonExecutable -c "import sysconfig; print(sysconfig.get_platform())")
    if ($LASTEXITCODE -ne 0) {
        throw "Could not determine the selected Python architecture."
    }
    switch ($reported.Trim().ToLowerInvariant()) {
        "win-amd64" { return "x64" }
        "win-arm64" { return "arm64" }
        default { throw "Unsupported Python architecture for PyInstaller: $reported" }
    }
}

function New-RunDirectory([string] $BaseDirectory, [string] $Prefix) {
    if (-not (Test-Path -LiteralPath $BaseDirectory)) {
        New-Item -ItemType Directory -Path $BaseDirectory | Out-Null
    }
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
    $directory = Join-Path $BaseDirectory "$Prefix-$stamp-$PID-$suffix"
    if (Test-Path -LiteralPath $directory) {
        throw "Refusing to reuse build directory: $directory"
    }
    New-Item -ItemType Directory -Path $directory | Out-Null
    return $directory
}

function Copy-WindowsProjectSource([string] $SourceDirectory, [string] $DestinationDirectory) {
    if (Test-Path -LiteralPath $DestinationDirectory) {
        throw "Refusing to reuse staged project directory: $DestinationDirectory"
    }
    New-Item -ItemType Directory -Path $DestinationDirectory | Out-Null
    $sourcePrefix = [System.IO.Path]::GetFullPath($SourceDirectory).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    Get-ChildItem -LiteralPath $SourceDirectory -Recurse -File -Force | ForEach-Object {
        $relativePath = $_.FullName.Substring($sourcePrefix.Length)
        if ($relativePath -match '(^|[\\/])(bin|obj|\.desktop-artifacts)([\\/]|$)') {
            return
        }
        $target = Join-Path $DestinationDirectory $relativePath
        $targetParent = Split-Path $target -Parent
        if (-not (Test-Path -LiteralPath $targetParent)) {
            New-Item -ItemType Directory -Path $targetParent | Out-Null
        }
        Copy-Item -LiteralPath $_.FullName -Destination $target
    }
}

function Get-ProjectVersion([string] $ProjectRoot) {
    $versionLine = Select-String -LiteralPath (Join-Path $ProjectRoot "pyproject.toml") -Pattern '^\s*version\s*=\s*"([^"]+)"' | Select-Object -First 1
    if ($null -eq $versionLine -or $versionLine.Line -notmatch '^\s*version\s*=\s*"([^"]+)"') {
        throw "Could not read the project version from pyproject.toml."
    }
    return $Matches[1]
}

$python = Resolve-ExecutablePath $PythonPath
$dotnet = Resolve-ExecutablePath "dotnet"
$pythonArchitecture = Get-PythonArchitecture $python
if ($pythonArchitecture -ne $Architecture) {
    throw "Requested Windows $Architecture, but the selected Python is $pythonArchitecture. PyInstaller must run under matching architecture Python."
}
$outputBase = Resolve-RepositoryPath $OutputRoot
$runDirectory = New-RunDirectory $outputBase "windows-$Architecture"
$backendManifest = Join-Path $runDirectory "backend.json"
$backendBuilder = Join-Path $PSScriptRoot "build_backend.py"

& $python $backendBuilder --output-root $runDirectory --result-file $backendManifest --smoke
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller backend build failed. Its fresh evidence directory is $runDirectory."
}
$backend = Get-Content -Raw -LiteralPath $backendManifest | ConvertFrom-Json
$backendDirectory = [string] $backend.bundle_directory
if (-not (Test-Path -LiteralPath $backendDirectory -PathType Container)) {
    throw "Backend manifest does not point to a bundle directory: $backendDirectory"
}

$projectSourceDirectory = Join-Path $repositoryRoot "desktop\windows"
$projectSource = Join-Path $projectSourceDirectory "SmartSearch.Desktop.csproj"
if (-not (Test-Path -LiteralPath $projectSource -PathType Leaf)) {
    throw "Windows desktop project is not available: $projectSource"
}
$stagedProjectDirectory = Join-Path $runDirectory "windows-source"
Copy-WindowsProjectSource $projectSourceDirectory $stagedProjectDirectory
$localizationPath = Join-Path $stagedProjectDirectory "messages.json"
Copy-Item -LiteralPath (Join-Path $repositoryRoot "src/smart_search/assets/i18n/messages.json") -Destination $localizationPath
$project = Join-Path $stagedProjectDirectory "SmartSearch.Desktop.csproj"
$publishDirectory = Join-Path $runDirectory "publish"
$platform = if ($Architecture -eq "arm64") { "ARM64" } else { "x64" }
$version = Get-ProjectVersion $repositoryRoot
& $dotnet publish $project --configuration $Configuration --runtime "win-$Architecture" --self-contained true --output $publishDirectory "-p:Platform=$platform" "-p:Version=$version" "-p:LocalizationPath=$localizationPath"
if ($LASTEXITCODE -ne 0) {
    throw "dotnet publish failed. Its fresh evidence directory is $runDirectory."
}

$desktopExecutable = Join-Path $publishDirectory "SmartSearch.Desktop.exe"
if (-not (Test-Path -LiteralPath $desktopExecutable -PathType Leaf)) {
    throw "dotnet publish did not create the expected desktop executable: $desktopExecutable"
}
foreach ($resource in @("App.xbf", "MainWindow.xbf", "SmartSearch.Desktop.pri", "Assets/smart-search.ico", "Assets/smart-search.png", "Assets/mascot.png")) {
    if (-not (Test-Path -LiteralPath (Join-Path $publishDirectory $resource) -PathType Leaf)) {
        throw "Published Windows app is missing its compiled UI resource: $resource"
    }
}
$standaloneCLI = Join-Path $backendDirectory "smart-search.exe"
if (Test-Path -LiteralPath (Join-Path $publishDirectory "backend")) {
    throw 'The native App must not contain a bundled CLI.'
}
$ownedFiles = @($desktopExecutable, (Join-Path $publishDirectory 'SmartSearch.Desktop.dll'), $standaloneCLI)
$thirdPartyHashes = @{}
if ($signingEnabled) {
    foreach ($file in Get-ChildItem -LiteralPath $publishDirectory -File -Recurse) {
        if ($file.FullName -notin $ownedFiles) {
            $thirdPartyHashes[$file.FullName] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        }
    }
    foreach ($file in $ownedFiles) { $signatures += Invoke-WindowsSigning $file $signingCertificate }
}

$installer = [ordered]@{
    status = "skipped"
    path = $null
    note = "Installer packaging was not requested."
}
if ($InstallerMode -ne "Skip") {
    $packageResult = Join-Path $runDirectory 'package-result.json'
    & (Join-Path $PSScriptRoot 'Package-Windows.ps1') -PublishDirectory $publishDirectory `
        -OutputDirectory (Join-Path $runDirectory 'installer') -Version $version -Architecture $Architecture `
        -SigningMode $SigningMode -PreviousReleaseDirectory $PreviousReleaseDirectory -ResultFile $packageResult
    $installer = Get-Content -Raw -LiteralPath $packageResult | ConvertFrom-Json
    $signatures += @($installer.signatures)
}

if ($signingEnabled) {
    foreach ($file in $thirdPartyHashes.Keys) {
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $thirdPartyHashes[$file]) {
            throw "Signing/packaging changed a file outside the owned signing allowlist: $file"
        }
    }
    $signingCertificate.Dispose()
}

$cliOutput = Join-Path $runDirectory 'installer'
& $python (Join-Path $PSScriptRoot 'package_cli.py') --bundle $backendDirectory --output $cliOutput --platform windows --architecture $Architecture --version $version
if ($LASTEXITCODE -ne 0) { throw 'Standalone CLI packaging failed.' }

$result = [ordered]@{
    version = $version
    run_directory = $runDirectory
    staged_project_directory = $stagedProjectDirectory
    publish_directory = $publishDirectory
    desktop_executable = $desktopExecutable
    backend = $backend
    installer = $installer
    signing = [ordered]@{
        mode = $SigningMode
        kind = if ($signingEnabled) { 'self-signed' } else { 'unsigned-test' }
        files = $signatures
        unchanged_other_files = $thirdPartyHashes.Count
        user_trust_store_modified = $false
    }
}
$resultPath = Join-Path $runDirectory "result.json"
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8
Write-Output "Windows artifact: $runDirectory"
