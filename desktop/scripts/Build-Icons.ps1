[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
& mise -C $repositoryRoot run desktop:icons
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
