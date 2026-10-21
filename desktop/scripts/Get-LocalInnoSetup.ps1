[CmdletBinding()]
param(
    [string] $OutputRoot = ".desktop-artifacts",
    [string] $ResultFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$downloadUrl = "https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe"
$expectedSha256 = "9C73C3BAE7ED48D44112A0F48E66742C00090BDB5BEF71D9D3C056C66E97B732"

function Resolve-RepositoryPath([string] $Candidate) {
    if ([System.IO.Path]::IsPathRooted($Candidate)) {
        return [System.IO.Path]::GetFullPath($Candidate)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $Candidate))
}

function New-RunDirectory([string] $BaseDirectory) {
    if (-not (Test-Path -LiteralPath $BaseDirectory)) {
        New-Item -ItemType Directory -Path $BaseDirectory | Out-Null
    }
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
    $directory = Join-Path $BaseDirectory "inno-tool-$stamp-$PID-$suffix"
    if (Test-Path -LiteralPath $directory) {
        throw "Refusing to reuse Inno Setup dependency directory: $directory"
    }
    New-Item -ItemType Directory -Path $directory | Out-Null
    return $directory
}

$curl = (Get-Command -Name "curl.exe" -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$innounp = (Get-Command -Name "innounp" -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$runDirectory = New-RunDirectory (Resolve-RepositoryPath $OutputRoot)
$installer = Join-Path $runDirectory "innosetup-6.7.3.exe"

& $curl --fail --location --retry 3 --output $installer $downloadUrl
if ($LASTEXITCODE -ne 0) {
    throw "Official Inno Setup download failed: $downloadUrl"
}
$actualSha256 = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToUpperInvariant()
if ($actualSha256 -ne $expectedSha256) {
    throw "Official Inno Setup SHA-256 mismatch. Expected $expectedSha256, got $actualSha256."
}
$installerSignature = Get-AuthenticodeSignature -LiteralPath $installer
if ($installerSignature.Status -ne "Valid" -or $null -eq $installerSignature.SignerCertificate -or
    $installerSignature.SignerCertificate.Subject -notlike "*Pyrsys B.V.*") {
    throw "Official Inno Setup signature is not a valid Pyrsys B.V. signature."
}

& $innounp -t -b -q $installer
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup archive integrity check failed: $installer"
}
$extraction = Join-Path $runDirectory "extracted"
& $innounp -x -b -q "-d$extraction" $installer
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup local extraction failed: $installer"
}
$compiler = Join-Path $extraction "{app}\ISCC.exe"
if (-not (Test-Path -LiteralPath $compiler -PathType Leaf)) {
    throw "The official Inno Setup extraction did not contain {app}\ISCC.exe."
}
$compilerSignature = Get-AuthenticodeSignature -LiteralPath $compiler
if ($compilerSignature.Status -ne "Valid") {
    throw "Extracted ISCC.exe signature is not valid: $($compilerSignature.Status)"
}

$result = [ordered]@{
    run_directory = $runDirectory
    download_url = $downloadUrl
    installer = $installer
    installer_sha256 = $actualSha256
    signer_subject = $installerSignature.SignerCertificate.Subject
    compiler_path = $compiler
    compiler_sha256 = (Get-FileHash -LiteralPath $compiler -Algorithm SHA256).Hash
    compiler_signature = $compilerSignature.Status.ToString()
    mode = "local-extraction-no-install-no-path-change"
}
if ($ResultFile) {
    $resolvedResultFile = Resolve-RepositoryPath $ResultFile
    $resultParent = Split-Path $resolvedResultFile -Parent
    if (-not (Test-Path -LiteralPath $resultParent)) {
        New-Item -ItemType Directory -Path $resultParent | Out-Null
    }
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resolvedResultFile -Encoding utf8
}
$result | ConvertTo-Json -Depth 5
