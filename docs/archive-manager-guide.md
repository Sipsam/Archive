# Archive 운영 가이드

Windows PowerShell 5.1, Git for Windows, Python 3.9+가 필요하다. 외부 Python 패키지는 없다. JSON은 UTF-8이며 PowerShell에서는 `Get-Content -Raw -Encoding UTF8`로 읽는다.

```powershell
.\scripts\archive-manager.ps1 fetch
.\scripts\archive-manager.ps1 status
.\scripts\archive-manager.ps1 verify-branches -Report D:\Archive-reports\branches-new.json
.\scripts\archive-manager.ps1 validate -Report D:\Archive-reports\validate-new.json
.\scripts\archive-manager.ps1 sync -WhatIf
.\scripts\archive-manager.ps1 push-safe -WhatIf
.\scripts\archive-manager.ps1 push-safe -ContinueOnError -Report D:\Archive-reports\push-new.json
```

`status/plan`은 저장된 origin 추적 참조를 비교하므로 먼저 fetch한다. fetch는 origin만 사용하며 prune/tag 갱신을 하지 않는다. 원본 프로젝트 폴더나 source remote가 없어도 동작한다. `sync`는 원격 선행 브랜치만 fast-forward/create하고 사용 중인 worktree 브랜치, backup 경로 및 security/*를 제외한다. 보안 검사, 외부 복구 백업, 원격 재조회 후 비교 갱신한다. diverged 이력은 자동 병합하지 않는다. `push-safe`는 기존 원격이 있는 로컬 선행 브랜치만 대상으로 개별 refspec을 사용한다. `-ContinueOnError`는 실패 브랜치를 기록하고 나머지를 진행한다. 실패/보안 차단이 있으면 종료 코드는 2다. 동일 브랜치는 건너뛰므로 재실행해도 중복 병합하지 않는다.

```powershell
.\scripts\archive-manager.ps1 push -Branch 'Project/branch' -WhatIf
.\scripts\archive-manager.ps1 push -Branch 'Project/branch'
```

Push는 전체 도달 이력의 HIGH 검사 후 immutable OID를 일반 Push한다. 원격 변경은 다시 fetch/plan할 때까지 거부한다. 로컬 전용 일반 프로젝트 브랜치는 위 개별 명령으로만 업로드할 수 있다. backup/security는 자동 Push 대상이 아니다. 서버 거절은 종료 코드와 메타데이터만 표시하며 원문 stderr는 비밀정보 보호를 위해 출력하지 않는다. GH013이면 예외 승인 없이 원인을 별도 조사한다. 강제 Push, reset --hard, 원격 삭제는 없다.

## 신규 프로젝트

```powershell
.\scripts\archive-manager.ps1 add -Project ExampleProject -FrontendRepo https://github.com/example/frontend.git -BackendRepo https://github.com/example/backend.git
# 단일 저장소: -SourceRepo https://github.com/example/project.git
.\scripts\archive-manager.ps1 promote -Candidate '반환된 candidate 경로' -WhatIf
.\scripts\archive-manager.ps1 promote -Candidate '반환된 candidate 경로' -Approve
```

add는 외부 임시 디렉터리에 candidate, manifest.json, candidate.bundle을 만들고 live Archive 참조를 변경하지 않는다. source의 전체 이력과 각 브랜치를 namespaced branch로 보존한다. 기존 프로젝트 이름은 거부한다. credential-free HTTPS 또는 로컬 경로만 사용한다. 후보를 확인한 뒤 promote는 기본 Dry Run이며 `-Approve`가 있어야 적용한다. main에서 clean 작업 트리가 필요하다. 생성 후 로컬/원격 참조 변경, 후보 tip 변경, 비 fast-forward, 프로젝트 외 파일 변경, HIGH 탐지 시 거부한다. 실행 직전에 외부 백업을 만들고 검증된 객체만 가져온다.

main은 Git fast-forward merge로 index/파일과 함께 갱신하고 나머지 대상 refs는 비교 갱신 트랜잭션으로 적용한다. 두 단계 사이의 운영체제/디스크 장애에는 외부 백업과 manifest가 복구 지점이다. 자동 파괴적 롤백은 없다. 이 경우 status와 백업을 확인한 뒤 새 후보를 생성한다. 원래 작업 트리를 stash/reset하지 않는다.

승격 후 `docs/archive-projects.json`에 source URL을 기록한다. 이 메타데이터를 검토하여 main에 커밋하고 다음 명령으로 원격 반영한다. push-safe는 새 로컬 전용 브랜치를 자동 업로드하지 않으므로 반환된 신규 브랜치마다 개별 push를 실행한다.

```powershell
git add docs/archive-projects.json
git commit -m 'docs(archive): register project sources'
.\scripts\archive-manager.ps1 push -Branch main
.\scripts\archive-manager.ps1 push -Branch 'ExampleProject/frontend/main'
.\scripts\archive-manager.ps1 validate
```

## 증분 업데이트

```powershell
.\scripts\archive-manager.ps1 update -Project WOOWANGTHON_TEAM_49 -WhatIf
.\scripts\archive-manager.ps1 update -Project ExampleProject
# 반환된 candidate를 promote -WhatIf → promote -Approve → 메타데이터 커밋 → 개별 push
```

등록된 source가 있을 때만 접근을 확인하고 후보를 만든다. 초기 metadata는 빈 객체이며 기존 프로젝트의 원본 URL을 추측하지 않는다. source가 없거나 접근 불가하면 `SOURCE_UNAVAILABLE`이며 Archive 내 status/extract/backup은 계속 가능하다. source 조회 실패와 파일 I/O 오류는 숨겨서 성공 처리하지 않는다. subtree pull이 원본 commit ancestry를 사용하므로 중복 이력을 가져오지 않는다. 기존 namespaced branch를 부모로 유지하고 해당 prefix만 갱신한다. source에서 사라진 브랜치도 자동 삭제하지 않는다. source의 새 이력이 diverged되거나 subtree 충돌이면 후보 작업만 실패하고 live Archive는 유지한다. 보안 검사는 승격 시 다시 수행한다.

## LFS 및 보안

`docs/archive-lfs-known-missing.json`의 13개 OID는 사용자가 의도적으로 삭제했다고 확인한 payload다. 포인터와 과거 커밋은 보존하며 자동 다운로드/복원하지 않는다. validate의 `KNOWN_MISSING`은 경고, `UNEXPECTED_MISSING`은 새로운 이상으로 종료 코드 2를 반환한다. 새로운 누락을 자동 baseline에 추가하지 않는다. 과거 checkout/extract가 실제 LFS 파일을 복구하지 못할 수 있다. bundle만으로 완전 복구 가능하다고 해석하지 않는다.

`security`는 모든 refs와 reflog를 검사하므로 정리 전 객체를 계속 탐지할 수 있다. Push 검사는 대상 tip의 도달 이력만 검사한다. HIGH(키·토큰·개인키 등)는 Push를 차단하고, 광범위한 credential 할당·URL REVIEW는 추가 검토용 진단이다. 제한된 정규식 검사는 모든 비밀정보 부재를 보장하지 않는다. 원본 source를 다시 fetch하면 과거 민감정보가 재유입될 수 있으므로 일반 관리는 origin만 조회한다. 캐시는 Git 공통 디렉터리의 `archive-security-cache/`에 저장되고 검사 코드 해시와 대상 tip으로 무효화된다. 검사 결과에 민감한 원문을 출력하거나 공개하지 않는다.

## 백업·복원·추출

별도 상시 백업은 필수가 아니다. 다만 실제 `sync`는 적용할 변경이 있을 때 첫 참조 갱신 전에, `promote -Approve`는 적용 전에, `push`와 `push-safe`는 각 실제 Push 전에 외부 복구 백업을 자동 생성한다. 경로는 저장소 루트의 두 단계 상위 아래 `Archive-backups/<sync|promote|push>-<시각>`이다. 현재 `D:\IdeaProjects\Archive`에서는 `D:\Archive-backups`가 된다. 이는 앞으로 명령 실행 시 생성되는 경로이며 현재 존재하는 백업을 뜻하지 않는다. 자동 백업 생략 옵션은 없고 `-WhatIf`에서는 생성하지 않는다. add/update는 시스템 임시 디렉터리에 외부 후보 자료를 만든다. 안전장치는 유지하며, 생성 자료의 검토·보관·삭제는 운영자가 관리한다.

아래는 선택적 수동 백업 예시이며 실제 존재하는 경로가 아니다.

```powershell
.\scripts\archive-manager.ps1 backup -Destination E:\ArchiveRecovery\manual-new
.\scripts\archive-manager.ps1 restore -Bundle E:\ArchiveRecovery\manual-new\archive.bundle -Destination D:\RecoveredProjects\Archive.git -WhatIf
.\scripts\archive-manager.ps1 restore -Bundle E:\ArchiveRecovery\manual-new\archive.bundle -Destination D:\RecoveredProjects\Archive.git
git -C D:\RecoveredProjects\Archive.git fsck --full
.\scripts\archive-manager.ps1 extract -Project Remory -Branch Remory/main -Destination D:\RecoveredProjects\Remory -WhatIf
```

복원은 새 외부 bare mirror로, 추출은 새 외부 파일 스냅샷으로만 실행한다. 기존 파일을 덮어쓰지 않는다. extract 결과의 LFS는 포인터이며 독립 프로젝트 Git 이력 재구성 기능은 아니다. backup은 모든 ref bundle, Git 메타데이터 사본, SHA256 manifest를 보존한다. 미커밋 작업 파일은 별도 보존해야 한다. 백업 시 다른 Git 작업을 동시에 실행하지 않는다. 비밀정보 포함 백업의 접근 권한은 운영자가 관리하며 업로드하지 않는다.

모든 변경 명령은 `-WhatIf`에서 clone/fetch/ref 변경/백업/보고서 쓰기를 하지 않는다. 읽기 전용 원격 조회와 검사는 수행할 수 있다. `-Report`는 기존 파일을 덮어쓰지 않으므로 새 경로를 사용한다. 실행 단계에서 다른 작업이 개입하면 재계획한다. 원격과의 마지막 경합은 서버의 일반 fast-forward 검사로 보호한다.

```powershell
python -m unittest discover -s scripts/tests -v
```

테스트는 GitHub와 연결되지 않은 임시 Git/bare 저장소만 사용한다. 원본 서비스 빌드나 실제 외부 서비스 인증 시험은 포함하지 않는다.
