[CmdletBinding()]
param([Parameter(Mandatory)][string] $Installation, [Parameter(Mandatory)][string] $ResultFile)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Windows-Signing.ps1')
$expected = Get-ExpectedSigningCertificate (Join-Path $PSScriptRoot '../packaging/windows/smart-search.cer')
try {
    $results = foreach ($relative in @('SmartSearch.Desktop.exe', 'Update.exe', 'current/SmartSearch.Desktop.exe',
        'current/SmartSearch.Desktop.dll')) {
        Test-WindowsSignature (Join-Path $Installation $relative) $expected
    }
    $results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ResultFile -Encoding utf8
}
finally { $expected.Dispose() }
