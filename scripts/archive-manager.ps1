#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [Parameter(Position=0,Mandatory=$true)]
    [ValidateSet('status','fetch','plan','sync','security','validate','push','backup','restore','add','extract','promote','update','verify-branches','push-safe')]
    [string]$Command,
    [string]$Repository = (Get-Location).Path,
    [string]$Branch, [string]$Project, [string]$Destination,
    [string]$Bundle, [string]$FrontendRepo, [string]$BackendRepo, [string]$SourceRepo,
    [string]$Candidate, [switch]$Approve, [switch]$ContinueOnError,
    [string]$Report
)
$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction Stop
$arguments = @((Join-Path $PSScriptRoot 'archive_manager.py'), $Command, '--repository', $Repository)
foreach ($pair in @(@('candidate',$Candidate),@('branch',$Branch),@('project',$Project),@('destination',$Destination),@('bundle',$Bundle),@('frontend-repo',$FrontendRepo),@('backend-repo',$BackendRepo),@('source-repo',$SourceRepo),@('report',$Report))) {
    if ($pair[1]) { $arguments += @(('--' + $pair[0]), $pair[1]) }
}
if ($Approve) { $arguments += '--approve' }
if ($ContinueOnError) { $arguments += '--continue-on-error' }
if ($WhatIfPreference) { $arguments += '--what-if' }
if ($Command -in @('fetch','sync','push','backup','restore','add','extract','promote','update','verify-branches','push-safe') -and -not $WhatIfPreference) {
    if (-not $PSCmdlet.ShouldProcess($Repository, $Command)) { return }
}
$oldEncoding = $env:PYTHONIOENCODING
try {
    $env:PYTHONIOENCODING = 'utf-8'
    & $python.Source @arguments
    if ($LASTEXITCODE -ne 0) { throw "Archive manager failed (exit $LASTEXITCODE). No automatic rollback or destructive retry was performed." }
} finally { $env:PYTHONIOENCODING = $oldEncoding }
