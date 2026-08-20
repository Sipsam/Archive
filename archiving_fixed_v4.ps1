#requires -Version 5.1

<#
.SYNOPSIS
    여러 GitHub 저장소와 로컬 QAgent 저장소를 하나의 아카이브 저장소로 통합합니다.

.DESCRIPTION
    - 통합 저장소 main:
      각 프로젝트의 대표 브랜치를 프로젝트별 폴더에 배치합니다.

    - 통합 저장소의 추가 브랜치:
      특정 프로젝트 폴더만 원본 브랜치 상태로 교체하고,
      다른 프로젝트는 main 상태를 유지합니다.

    - Git LFS:
      원본 서버에 없는 LFS 객체가 있어도 실제 파일 다운로드를 시도하지 않고
      LFS 포인터 파일만 보존합니다.

    - 재실행:
      main에 이미 추가된 프로젝트 폴더는 건너뜁니다.
      추가 아카이브 브랜치는 기존 로컬 브랜치를 삭제하고 다시 만듭니다.

.NOTES
    실행 위치:
      D:\IdeaProjects\Archive

    로컬 QAgent 기본 경로:
      D:\IdeaProjects\QAgent
#>

$ErrorActionPreference = "Stop"

# --------------------------------------------------------------------
# 사용자 설정
# --------------------------------------------------------------------

$MainBranch = "main"

# 로컬 QAgent 저장소 경로
$QAgentPath = "D:/IdeaProjects/QAgent"

# true이면 기존에 생성된 로컬 아카이브 브랜치를 삭제하고 다시 만듭니다.
# 중간 실패 후 재실행할 때 필요합니다.
$RecreateArchiveBranches = $true

# true이면 실행 완료 후 자동으로 GitHub에 push합니다.
# 처음에는 false로 두고 검수 후 직접 push하는 것을 권장합니다.
$AutoPush = $false

# --------------------------------------------------------------------
# 콘솔 및 Git 인코딩
# --------------------------------------------------------------------

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$env:LANG = "ko_KR.UTF-8"
$env:LC_ALL = "ko_KR.UTF-8"

# Git LFS 실제 객체 다운로드를 건너뜁니다.
# 서버에서 사라진 LFS 객체가 있어도 포인터 파일은 보존됩니다.
$env:GIT_LFS_SKIP_SMUDGE = "1"

git config core.quotepath false
git config i18n.logOutputEncoding utf-8
git config i18n.commitEncoding utf-8

# --------------------------------------------------------------------
# 공통 함수
# --------------------------------------------------------------------

function Assert-GitSuccess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$Message (Git exit code: $LASTEXITCODE)"
    }
}

function Write-Section {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Title
    Write-Host "============================================================"
}

function Test-LocalBranchExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BranchName
    )

    git show-ref --verify --quiet "refs/heads/$BranchName"
    return ($LASTEXITCODE -eq 0)
}

function Test-RemoteBranchExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteName,

        [Parameter(Mandatory = $true)]
        [string]$BranchName
    )

    git show-ref --verify --quiet "refs/remotes/$RemoteName/$BranchName"
    return ($LASTEXITCODE -eq 0)
}

function Test-TrackedPathExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prefix
    )

    # git cat-file은 경로가 없을 때 stderr를 출력합니다.
    # Windows PowerShell 5.1 + ErrorActionPreference=Stop에서는
    # 이 정상적인 "없음" 확인도 NativeCommandError로 처리될 수 있습니다.
    # git ls-tree는 경로가 없으면 빈 결과와 종료 코드 0을 반환하므로
    # 예외 없이 추적 경로 존재 여부를 확인할 수 있습니다.
    $trackedEntries = @(git ls-tree --name-only HEAD -- "$Prefix")
    Assert-GitSuccess "추적 경로 확인 실패: $Prefix"

    return ($trackedEntries.Count -gt 0)
}

function Test-WorkingTreeClean {
    # 아카이빙 스크립트처럼 Git이 추적하지 않는 파일은 허용합니다.
    # 추적 중인 파일의 수정/삭제/스테이징 여부만 검사합니다.
    $status = git status --porcelain --untracked-files=no

    return [string]::IsNullOrWhiteSpace(
        ($status | Out-String)
    )
}

function Restore-InterruptedRun {
    Write-Section "중단된 이전 실행 상태 확인"

    $currentBranch = git branch --show-current
    Assert-GitSuccess "현재 브랜치를 확인하지 못했습니다."

    if ([string]::IsNullOrWhiteSpace($currentBranch)) {
        throw "Detached HEAD 상태입니다. 일반 브랜치로 이동한 후 다시 실행하세요."
    }

    if (Test-WorkingTreeClean) {
        Write-Host "작업 디렉터리가 깨끗합니다."
    }
    elseif ($currentBranch -ne $MainBranch) {
        Write-Host "중단된 아카이브 브랜치 작업을 초기화합니다: $currentBranch"

        git reset --hard HEAD
        Assert-GitSuccess "중단된 작업의 reset에 실패했습니다."

        # untracked 파일에는 사용자 파일이나 현재 실행 중인 스크립트가
        # 포함될 수 있으므로 git clean은 실행하지 않습니다.
    }
    else {
        throw "main 브랜치에 커밋되지 않은 변경사항이 있습니다. git status로 확인한 뒤 commit 또는 stash하고 다시 실행하세요."
    }

    git switch $MainBranch
    Assert-GitSuccess "main 브랜치로 이동하지 못했습니다."
}

function Add-RemoteRepository {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteName,

        [Parameter(Mandatory = $true)]
        [string]$RepositoryUrl
    )

    Write-Host ""
    Write-Host "Remote: $RemoteName"
    Write-Host "Source: $RepositoryUrl"

    # 존재하지 않는 remote에 대해 `git remote get-url`을 바로 실행하면
    # Windows PowerShell 5.1 + ErrorActionPreference=Stop 환경에서
    # 확인용 stderr가 예외로 처리될 수 있으므로 먼저 이름 목록을 검사합니다.
    $remoteNames = @(git remote)
    Assert-GitSuccess "Remote 목록 조회 실패"

    if ($remoteNames -contains $RemoteName) {
        $existingRemoteUrl = git remote get-url $RemoteName
        Assert-GitSuccess "Remote URL 조회 실패: $RemoteName"

        if ($existingRemoteUrl -ne $RepositoryUrl) {
            Write-Host "기존 remote URL을 수정합니다."

            git remote set-url $RemoteName $RepositoryUrl
            Assert-GitSuccess "Remote URL 수정 실패: $RemoteName"
        }
        else {
            Write-Host "기존 remote를 사용합니다."
        }
    }
    else {
        Write-Host "새 remote를 추가합니다."

        git remote add $RemoteName $RepositoryUrl
        Assert-GitSuccess "Remote 추가 실패: $RemoteName"
    }

    # 태그 이름 충돌을 피하기 위해 --no-tags 사용
    git fetch $RemoteName --prune --no-tags
    Assert-GitSuccess "Remote fetch 실패: $RemoteName"
}

function Assert-SourceBranch {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteName,

        [Parameter(Mandatory = $true)]
        [string]$SourceBranch
    )

    if (-not (Test-RemoteBranchExists $RemoteName $SourceBranch)) {
        throw "원본 브랜치를 찾을 수 없습니다: $RemoteName/$SourceBranch"
    }
}

function Add-SubtreeToMain {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteName,

        [Parameter(Mandatory = $true)]
        [string]$SourceBranch,

        [Parameter(Mandatory = $true)]
        [string]$Prefix
    )

    Write-Host ""
    Write-Host "Main import"
    Write-Host "  Source: $RemoteName/$SourceBranch"
    Write-Host "  Path:   $Prefix"

    git switch $MainBranch
    Assert-GitSuccess "main 브랜치로 이동하지 못했습니다."

    Assert-SourceBranch $RemoteName $SourceBranch

    if (Test-TrackedPathExists $Prefix) {
        Write-Host "  Skip: 이미 main에 존재합니다."
        return
    }

    # LFS smudge를 비활성화하여 실제 LFS 객체 다운로드를 방지합니다.
    git `
        -c filter.lfs.smudge= `
        -c filter.lfs.required=false `
        subtree add `
        --prefix="$Prefix" `
        $RemoteName `
        $SourceBranch

    Assert-GitSuccess "Subtree 추가 실패: $RemoteName/$SourceBranch"
}

function Remove-ArchiveBranchIfNeeded {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ArchiveBranch
    )

    if (-not (Test-LocalBranchExists $ArchiveBranch)) {
        return
    }

    if (-not $RecreateArchiveBranches) {
        Write-Host "기존 브랜치를 유지합니다: $ArchiveBranch"
        return
    }

    $currentBranch = git branch --show-current

    if ($currentBranch -eq $ArchiveBranch) {
        git switch $MainBranch
        Assert-GitSuccess "기존 브랜치를 삭제하기 위해 main으로 이동하지 못했습니다."
    }

    Write-Host "기존 로컬 브랜치를 다시 생성하기 위해 삭제합니다: $ArchiveBranch"

    git branch -D "$ArchiveBranch"
    Assert-GitSuccess "기존 브랜치 삭제 실패: $ArchiveBranch"
}

function New-MainSnapshotBranch {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ArchiveBranch
    )

    Write-Host ""
    Write-Host "Main snapshot branch: $ArchiveBranch"

    git switch $MainBranch
    Assert-GitSuccess "main 브랜치로 이동하지 못했습니다."

    if (Test-LocalBranchExists $ArchiveBranch) {
        if ($RecreateArchiveBranches) {
            git branch -f "$ArchiveBranch" $MainBranch
            Assert-GitSuccess "Main snapshot 브랜치 갱신 실패: $ArchiveBranch"

            Write-Host "  Updated"
        }
        else {
            Write-Host "  Skip: 이미 존재합니다."
        }

        return
    }

    git branch "$ArchiveBranch" $MainBranch
    Assert-GitSuccess "Main snapshot 브랜치 생성 실패: $ArchiveBranch"

    Write-Host "  Created"
}

function New-ArchiveBranch {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ArchiveBranch,

        [Parameter(Mandatory = $true)]
        [string]$RemoteName,

        [Parameter(Mandatory = $true)]
        [string]$SourceBranch,

        [Parameter(Mandatory = $true)]
        [string]$Prefix
    )

    Write-Host ""
    Write-Host "Archive branch"
    Write-Host "  Branch: $ArchiveBranch"
    Write-Host "  Source: $RemoteName/$SourceBranch"
    Write-Host "  Path:   $Prefix"

    Assert-SourceBranch $RemoteName $SourceBranch

    git switch $MainBranch
    Assert-GitSuccess "main 브랜치로 이동하지 못했습니다."

    Remove-ArchiveBranchIfNeeded $ArchiveBranch

    if (Test-LocalBranchExists $ArchiveBranch) {
        Write-Host "  Skip: 기존 브랜치를 유지합니다."
        return
    }

    git switch -c "$ArchiveBranch" $MainBranch
    Assert-GitSuccess "Archive 브랜치 생성 실패: $ArchiveBranch"

    try {
        # 원본 브랜치의 커밋 이력을 현재 아카이브 브랜치 기록에 연결합니다.
        # 파일 상태는 ours 전략으로 main 상태를 유지합니다.
        git merge `
            --strategy=ours `
            --allow-unrelated-histories `
            --no-edit `
            "$RemoteName/$SourceBranch"

        Assert-GitSuccess "원본 커밋 이력 병합 실패: $RemoteName/$SourceBranch"

        # 기존 프로젝트 폴더를 제거합니다.
        # -q를 사용하여 수천 개 파일의 rm 출력을 억제합니다.
        git rm `
            -r `
            -q `
            --ignore-unmatch `
            -- "$Prefix"

        Assert-GitSuccess "기존 프로젝트 폴더 제거 실패: $Prefix"

        # 지정한 원본 브랜치의 파일 트리를 해당 하위 폴더에 배치합니다.
        # LFS 실제 파일 다운로드는 건너뜁니다.
        git `
            -c filter.lfs.smudge= `
            -c filter.lfs.required=false `
            read-tree `
            --prefix="$Prefix/" `
            -u `
            "$RemoteName/$SourceBranch"

        Assert-GitSuccess "원본 파일 트리 배치 실패: $RemoteName/$SourceBranch"

        # 실제 파일 차이가 있는 경우에만 별도 커밋합니다.
        git diff --cached --quiet
        $hasNoStagedChanges = ($LASTEXITCODE -eq 0)

        if ($hasNoStagedChanges) {
            Write-Host "  파일 상태가 main과 동일하여 추가 파일 커밋은 생략합니다."
        }
        else {
            git commit `
                -m "archive: import $RemoteName/$SourceBranch into $Prefix"

            Assert-GitSuccess "Archive 파일 커밋 실패: $ArchiveBranch"
        }

        Write-Host "  Completed"
    }
    catch {
        Write-Host ""
        Write-Host "Archive 브랜치 생성 중 오류가 발생했습니다."
        Write-Host "부분 변경사항을 정리하고 main으로 돌아갑니다."

        git reset --hard HEAD 2>$null
        git switch $MainBranch 2>$null

        throw
    }
}

function Get-RemoteBranchNames {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteName
    )

    $branches = git for-each-ref `
        --format="%(refname:strip=3)" `
        "refs/remotes/$RemoteName"

    Assert-GitSuccess "Remote 브랜치 목록 조회 실패: $RemoteName"

    return @(
        $branches |
        Where-Object {
            -not [string]::IsNullOrWhiteSpace($_) -and
            $_ -ne "HEAD"
        }
    )
}

function Import-AllAdditionalBranches {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteName,

        [Parameter(Mandatory = $true)]
        [string]$DefaultBranch,

        [Parameter(Mandatory = $true)]
        [string]$ArchiveNamespace,

        [Parameter(Mandatory = $true)]
        [string]$Prefix
    )

    $branches = Get-RemoteBranchNames $RemoteName

    foreach ($sourceBranch in $branches) {
        if ($sourceBranch -eq $DefaultBranch) {
            continue
        }

        $archiveBranch = "$ArchiveNamespace/$sourceBranch"

        New-ArchiveBranch `
            -ArchiveBranch $archiveBranch `
            -RemoteName $RemoteName `
            -SourceBranch $sourceBranch `
            -Prefix $Prefix
    }
}

# --------------------------------------------------------------------
# 실행 전 검증 및 중단 상태 복구
# --------------------------------------------------------------------

Write-Section "아카이브 통합 시작"

git rev-parse --is-inside-work-tree *> $null
Assert-GitSuccess "현재 폴더는 Git 저장소가 아닙니다."

git show-ref --verify --quiet "refs/heads/$MainBranch"

if ($LASTEXITCODE -ne 0) {
    throw "통합 저장소에 '$MainBranch' 브랜치가 없습니다."
}

Restore-InterruptedRun

# --------------------------------------------------------------------
# 원본 저장소 등록
# --------------------------------------------------------------------

Write-Section "원본 저장소 등록"

Add-RemoteRepository `
    -RemoteName "repo-2025-01" `
    -RepositoryUrl "https://github.com/Sipsam/2025-01-OpenSWBasicProject.git"

Add-RemoteRepository `
    -RemoteName "repo-2025-02" `
    -RepositoryUrl "https://github.com/Sipsam/2025-02-OpenSWDevProject.git"

Add-RemoteRepository `
    -RemoteName "repo-animal-league" `
    -RepositoryUrl "https://github.com/Sipsam/2026_04_animal_league.git"

Add-RemoteRepository `
    -RemoteName "repo-kit-vibe" `
    -RepositoryUrl "https://github.com/Sipsam/2026_KIT_Vibe.git"

Add-RemoteRepository `
    -RemoteName "repo-likelion-study" `
    -RepositoryUrl "https://github.com/Sipsam/2026_likelion_study.git"

Add-RemoteRepository `
    -RemoteName "repo-web-project" `
    -RepositoryUrl "https://github.com/Sipsam/2026_01_OpenSWWebProject.git"

Add-RemoteRepository `
    -RemoteName "repo-final-study-be" `
    -RepositoryUrl "https://github.com/Sipsam/2026_14th_final_study_BE.git"

Add-RemoteRepository `
    -RemoteName "repo-remory-fe" `
    -RepositoryUrl "https://github.com/Sipsam/remoryFE.git"

Add-RemoteRepository `
    -RemoteName "repo-remory-be" `
    -RepositoryUrl "https://github.com/Sipsam/remoryBE.git"

Add-RemoteRepository `
    -RemoteName "repo-legwork-backend" `
    -RepositoryUrl "https://github.com/legworkteam/legwork_backend.git"

$QAgentEnabled = Test-Path -LiteralPath $QAgentPath

if ($QAgentEnabled) {
    Add-RemoteRepository `
        -RemoteName "repo-qagent" `
        -RepositoryUrl $QAgentPath
}
else {
    Write-Host ""
    Write-Warning "QAgent 경로가 없어 QAgent 통합을 건너뜁니다: $QAgentPath"
}

# --------------------------------------------------------------------
# main 브랜치 프로젝트 구조 생성
# --------------------------------------------------------------------

Write-Section "통합 main 브랜치 구성"

git switch $MainBranch
Assert-GitSuccess "main 브랜치로 이동하지 못했습니다."

# 2025-01 프로젝트는 front와 back을 각각 별도 하위 폴더로 배치
Add-SubtreeToMain `
    -RemoteName "repo-2025-01" `
    -SourceBranch "front" `
    -Prefix "2025-01-OpenSWBasicProject/frontend"

Add-SubtreeToMain `
    -RemoteName "repo-2025-01" `
    -SourceBranch "back" `
    -Prefix "2025-01-OpenSWBasicProject/backend"

Add-SubtreeToMain `
    -RemoteName "repo-2025-02" `
    -SourceBranch "main" `
    -Prefix "2025-02-OpenSWDevProject"

Add-SubtreeToMain `
    -RemoteName "repo-animal-league" `
    -SourceBranch "main" `
    -Prefix "2026_04_animal_league"

Add-SubtreeToMain `
    -RemoteName "repo-kit-vibe" `
    -SourceBranch "main" `
    -Prefix "2026_KIT_Vibe"

Add-SubtreeToMain `
    -RemoteName "repo-likelion-study" `
    -SourceBranch "develop" `
    -Prefix "2026_likelion_study"

Add-SubtreeToMain `
    -RemoteName "repo-web-project" `
    -SourceBranch "main" `
    -Prefix "2026_01_OpenSWWebProject"

Add-SubtreeToMain `
    -RemoteName "repo-final-study-be" `
    -SourceBranch "main" `
    -Prefix "2026_14th_final_study_BE"

# Remory FE/BE를 하나의 Remory 폴더에 배치
Add-SubtreeToMain `
    -RemoteName "repo-remory-fe" `
    -SourceBranch "main" `
    -Prefix "Remory/frontend"

Add-SubtreeToMain `
    -RemoteName "repo-remory-be" `
    -SourceBranch "main" `
    -Prefix "Remory/backend"

Add-SubtreeToMain `
    -RemoteName "repo-legwork-backend" `
    -SourceBranch "main" `
    -Prefix "legwork_backend"

if ($QAgentEnabled) {
    Add-SubtreeToMain `
        -RemoteName "repo-qagent" `
        -SourceBranch "main" `
        -Prefix "QAgent"
}

# --------------------------------------------------------------------
# 대표 브랜치 별칭 생성
# --------------------------------------------------------------------

Write-Section "대표 브랜치 생성"

# 해당 브랜치의 파일 상태가 이미 main에 반영되어 있으므로
# main을 가리키는 스냅샷 브랜치로 생성합니다.

New-MainSnapshotBranch "2025-01-OpenSWBasicProject/front"
New-MainSnapshotBranch "2025-01-OpenSWBasicProject/back"

New-MainSnapshotBranch "2025-02-OpenSWDevProject/main"

New-MainSnapshotBranch "2026_04_animal_league/main"

New-MainSnapshotBranch "2026_KIT_Vibe/main"

New-MainSnapshotBranch "2026_likelion_study/develop"

New-MainSnapshotBranch "2026_01_OpenSWWebProject/main"

New-MainSnapshotBranch "2026_14th_final_study_BE/main"

New-MainSnapshotBranch "Remory/main"

New-MainSnapshotBranch "legwork_backend/main"

if ($QAgentEnabled) {
    New-MainSnapshotBranch "QAgent/main"
}

# --------------------------------------------------------------------
# 2025-02-OpenSWDevProject 추가 브랜치
# --------------------------------------------------------------------

Write-Section "2025-02-OpenSWDevProject 브랜치"

New-ArchiveBranch `
    -ArchiveBranch "2025-02-OpenSWDevProject/backend" `
    -RemoteName "repo-2025-02" `
    -SourceBranch "backend" `
    -Prefix "2025-02-OpenSWDevProject"

New-ArchiveBranch `
    -ArchiveBranch "2025-02-OpenSWDevProject/frontend" `
    -RemoteName "repo-2025-02" `
    -SourceBranch "frontend" `
    -Prefix "2025-02-OpenSWDevProject"

# --------------------------------------------------------------------
# 2026_04_animal_league 추가 브랜치
# --------------------------------------------------------------------

Write-Section "2026_04_animal_league 브랜치"

New-ArchiveBranch `
    -ArchiveBranch "2026_04_animal_league/backend" `
    -RemoteName "repo-animal-league" `
    -SourceBranch "backend" `
    -Prefix "2026_04_animal_league"

New-ArchiveBranch `
    -ArchiveBranch "2026_04_animal_league/frontend" `
    -RemoteName "repo-animal-league" `
    -SourceBranch "frontend" `
    -Prefix "2026_04_animal_league"

# --------------------------------------------------------------------
# 2026_KIT_Vibe 추가 브랜치
# --------------------------------------------------------------------

Write-Section "2026_KIT_Vibe 브랜치"

New-ArchiveBranch `
    -ArchiveBranch "2026_KIT_Vibe/backend" `
    -RemoteName "repo-kit-vibe" `
    -SourceBranch "backend" `
    -Prefix "2026_KIT_Vibe"

New-ArchiveBranch `
    -ArchiveBranch "2026_KIT_Vibe/frontend" `
    -RemoteName "repo-kit-vibe" `
    -SourceBranch "frontend" `
    -Prefix "2026_KIT_Vibe"

# --------------------------------------------------------------------
# 2026_likelion_study 추가 브랜치
# --------------------------------------------------------------------

Write-Section "2026_likelion_study 브랜치"

New-ArchiveBranch `
    -ArchiveBranch "2026_likelion_study/week4/장성원" `
    -RemoteName "repo-likelion-study" `
    -SourceBranch "week4/장성원" `
    -Prefix "2026_likelion_study"

# --------------------------------------------------------------------
# 2026_14th_final_study_BE 추가 브랜치
# --------------------------------------------------------------------

Write-Section "2026_14th_final_study_BE 브랜치"

# 원본 브랜치의 # 문자는 URL/셸에서 불편하므로
# 통합 브랜치 이름에서는 issue-6으로 변경합니다.
New-ArchiveBranch `
    -ArchiveBranch "2026_14th_final_study_BE/week8/issue-6-jangsungwon" `
    -RemoteName "repo-final-study-be" `
    -SourceBranch "week8/#6-jangsungwon" `
    -Prefix "2026_14th_final_study_BE"

New-ArchiveBranch `
    -ArchiveBranch "2026_14th_final_study_BE/backup/week8-jangsungwon-before-merge" `
    -RemoteName "repo-final-study-be" `
    -SourceBranch "backup/week8-jangsungwon-before-merge" `
    -Prefix "2026_14th_final_study_BE"

# --------------------------------------------------------------------
# Remory 추가 브랜치
# --------------------------------------------------------------------

Write-Section "Remory 브랜치"

# FE demo 브랜치:
# frontend만 demo 상태이며 backend는 main 상태를 유지합니다.
New-ArchiveBranch `
    -ArchiveBranch "Remory/demo" `
    -RemoteName "repo-remory-fe" `
    -SourceBranch "demo" `
    -Prefix "Remory/frontend"

# BE feature 브랜치:
# backend만 feature 상태이며 frontend는 main 상태를 유지합니다.
New-ArchiveBranch `
    -ArchiveBranch "Remory/backend/feat-target-verification" `
    -RemoteName "repo-remory-be" `
    -SourceBranch "feat/target-verification" `
    -Prefix "Remory/backend"

New-ArchiveBranch `
    -ArchiveBranch "Remory/backend/feat-consent-log" `
    -RemoteName "repo-remory-be" `
    -SourceBranch "feat/consent-log" `
    -Prefix "Remory/backend"

New-ArchiveBranch `
    -ArchiveBranch "Remory/backend/feat-ai-voice-pipeline" `
    -RemoteName "repo-remory-be" `
    -SourceBranch "feat/ai-voice-pipeline" `
    -Prefix "Remory/backend"

New-ArchiveBranch `
    -ArchiveBranch "Remory/backend/feat-ai-service" `
    -RemoteName "repo-remory-be" `
    -SourceBranch "feat/ai-service" `
    -Prefix "Remory/backend"

# --------------------------------------------------------------------
# legwork_backend 추가 브랜치
# --------------------------------------------------------------------

Write-Section "legwork_backend 브랜치"

Import-AllAdditionalBranches `
    -RemoteName "repo-legwork-backend" `
    -DefaultBranch "main" `
    -ArchiveNamespace "legwork_backend" `
    -Prefix "legwork_backend"

# --------------------------------------------------------------------
# QAgent의 모든 추가 로컬 브랜치 자동 통합
# --------------------------------------------------------------------

if ($QAgentEnabled) {
    Write-Section "QAgent 추가 브랜치"

    Import-AllAdditionalBranches `
        -RemoteName "repo-qagent" `
        -DefaultBranch "main" `
        -ArchiveNamespace "QAgent" `
        -Prefix "QAgent"
}

# --------------------------------------------------------------------
# 완료 및 검증
# --------------------------------------------------------------------

Write-Section "최종 검증"

git switch $MainBranch
Assert-GitSuccess "최종 main 브랜치 복귀 실패"

if (-not (Test-WorkingTreeClean)) {
    Write-Host ""
    git status

    throw "작업 완료 후 커밋되지 않은 변경사항이 남아 있습니다."
}

Write-Host ""
Write-Host "현재 main 상태:"
git status --short --branch
Assert-GitSuccess "Git 상태 확인 실패"

Write-Host ""
Write-Host "생성된 로컬 브랜치:"
git branch --list
Assert-GitSuccess "브랜치 목록 확인 실패"

Write-Host ""
Write-Host "최근 커밋 그래프:"
git log --oneline --graph --decorate --all -30
Assert-GitSuccess "커밋 그래프 확인 실패"

# --------------------------------------------------------------------
# 선택적 자동 push
# --------------------------------------------------------------------

if ($AutoPush) {
    Write-Section "GitHub Push"

    git push origin $MainBranch
    Assert-GitSuccess "main push 실패"ㅇ:
    # 재실행으로 기존 아카이브 브랜치를 다시 만든 경우를 고려하여
    # force-with-lease를 사용합니다.
    git push origin --all --force-with-lease
    Assert-GitSuccess "전체 브랜치 push 실패"

    Write-Host ""
    Write-Host "GitHub push가 완료되었습니다."
}
else {
    Write-Section "통합 완료"

    Write-Host "아직 GitHub에는 push하지 않았습니다."
    Write-Host ""
    Write-Host "검수 명령:"
    Write-Host "  git status"
    Write-Host "  git branch"
    Write-Host "  git log --oneline --graph --decorate --all -50"
    Write-Host ""
    Write-Host "검수 후 최초 push:"
    Write-Host "  git push origin main"
    Write-Host "  git push origin --all"
    Write-Host ""
    Write-Host "이미 브랜치를 push한 뒤 스크립트를 재실행한 경우:"
    Write-Host "  git push origin main"
    Write-Host "  git push origin --all --force-with-lease"
}
