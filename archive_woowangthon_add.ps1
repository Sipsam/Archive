#requires -Version 5.1
# Incremental import of WOOWANGTHON FE and BE into Sipsam/Archive.
# Run from a clean local clone of Sipsam/Archive.
$ErrorActionPreference = 'Stop'
$MainBranch = 'main'
$Namespace = 'WOOWANGTHON_TEAM_49'
$AutoPush = $false
$env:GIT_LFS_SKIP_SMUDGE = '1'

function Invoke-Git {
    param([Parameter(Mandatory=$true)][string[]]$Args)
    & git @Args
    if ($LASTEXITCODE -ne 0) { throw "Git failed ($LASTEXITCODE): git $($Args -join ' ')" }
}
function Test-Branch([string]$Name) {
    & git show-ref --verify --quiet "refs/heads/$Name"
    return ($LASTEXITCODE -eq 0)
}
function Test-TreePath([string]$Prefix) {
    $entries = @(& git ls-tree --name-only HEAD -- "$Prefix")
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect path: $Prefix" }
    return ($entries.Count -gt 0)
}
function Configure-Remote([string]$Name, [string]$Url) {
    $remoteNames = @(& git remote)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot list remotes' }
    if ($remoteNames -contains $Name) {
        $existing = (& git remote get-url $Name | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) { throw "Cannot inspect remote $Name" }
        if ($existing -ne $Url) { throw "Remote $Name exists with different URL: $existing" }
    } else { Invoke-Git @('remote','add',$Name,$Url) }
    Invoke-Git @('fetch',$Name,'--prune','--no-tags')
}
function Add-MainSubtree([string]$Remote, [string]$Prefix) {
    Invoke-Git @('switch',$MainBranch)
    if (Test-TreePath $Prefix) {
        Write-Host "SKIP already imported: $Prefix"
    } else {
        Invoke-Git @('-c','filter.lfs.smudge=','-c','filter.lfs.required=false','subtree','add',"--prefix=$Prefix",$Remote,'main')
    }
}
function Add-ArchiveBranch([string]$ArchiveBranch, [string]$Remote, [string]$SourceBranch, [string]$Prefix) {
    Invoke-Git @('switch',$MainBranch)
    if (Test-Branch $ArchiveBranch) {
        Write-Host "SKIP existing branch: $ArchiveBranch"
        return
    }
    Write-Host "Import branch $ArchiveBranch <= $Remote/$SourceBranch"
    Invoke-Git @('switch','-c',$ArchiveBranch,$MainBranch)
    Invoke-Git @('merge','--strategy=ours','--allow-unrelated-histories','--no-edit',"$Remote/$SourceBranch")
    Invoke-Git @('rm','-r','-q','--ignore-unmatch','--',$Prefix)
    Invoke-Git @('-c','filter.lfs.smudge=','-c','filter.lfs.required=false','read-tree',"--prefix=$Prefix/",'-u',"$Remote/$SourceBranch")
    & git diff --cached --quiet
    $diffExit = $LASTEXITCODE
    if ($diffExit -eq 1) {
        Invoke-Git @('commit','-m',"archive: import $Remote/$SourceBranch into $Prefix")
    } elseif ($diffExit -ne 0) {
        throw "Could not inspect staged changes for $ArchiveBranch"
    }
}

& git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) { throw 'Run inside the local Archive Git repository.' }
$current = (& git branch --show-current | Out-String).Trim()
if ($current -ne $MainBranch) { throw 'Switch to main before running.' }
$status = @(& git status --porcelain)
if ($LASTEXITCODE -ne 0 -or $status.Count -gt 0) { throw 'Working tree must be completely clean (including untracked files). Move the script outside the repository or commit changes first.' }

Configure-Remote 'repo-woowang-fe' 'https://github.com/woowangthon/WOOWANGTHON_TEAM_49_FE.git'
Configure-Remote 'repo-woowang-be' 'https://github.com/woowangthon/WOOWANGTHON_TEAM_49_BE.git'

Add-MainSubtree 'repo-woowang-fe' "$Namespace/frontend"
Add-MainSubtree 'repo-woowang-be' "$Namespace/backend"

# The representative branch is a snapshot of the combined main.
$representative = "$Namespace/main"
if (-not (Test-Branch $representative)) { Invoke-Git @('branch',$representative,$MainBranch) }
else { Write-Host "SKIP existing branch: $representative" }

# Discover all current source branches instead of hardcoding names.
$sourceRepos = @(
    @{ Remote='repo-woowang-fe'; Segment='frontend' },
    @{ Remote='repo-woowang-be'; Segment='backend' }
)
foreach ($source in $sourceRepos) {
    $remote = $source.Remote
    $segment = $source.Segment
    $branches = @(& git for-each-ref '--format=%(refname:strip=3)' "refs/remotes/$remote")
    if ($LASTEXITCODE -ne 0) { throw "Cannot list branches for $remote" }
    foreach ($branch in $branches) {
        if ([string]::IsNullOrWhiteSpace($branch) -or $branch -eq 'HEAD' -or $branch -eq 'main') { continue }
        Add-ArchiveBranch "$Namespace/$segment/$branch" $remote $branch "$Namespace/$segment"
    }
}
Invoke-Git @('switch',$MainBranch)
Write-Host "`nLocal archive completed. Review git status, git branch, and git log before pushing."
if ($AutoPush) {
    Invoke-Git @('push','origin','main')
    Invoke-Git @('push','origin','--all')
}
