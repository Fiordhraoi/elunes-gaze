param(
    [Parameter(Mandatory=$true)]
    [ValidateRange(10000,999999)]
    [int]$InterfaceVersion
)
$ErrorActionPreference = 'Stop'
$addonFolder = Join-Path $PSScriptRoot 'ElunesGazePoC'
$templatePath = Join-Path $addonFolder 'ElunesGazePoC.toc.in'
$tocPath = Join-Path $addonFolder 'ElunesGazePoC.toc'
if (Test-Path -LiteralPath $tocPath) { throw 'A TOC already exists. Edit its Interface line manually to update it.' }
$toc = (Get-Content -LiteralPath $templatePath -Raw).Replace('@INTERFACE@', [string]$InterfaceVersion)
[System.IO.File]::WriteAllText($tocPath, $toc, [System.Text.UTF8Encoding]::new($false))
Write-Host "Prepared $addonFolder for interface $InterfaceVersion. Copy this folder into your Retail Interface\AddOns folder while WoW is closed."
