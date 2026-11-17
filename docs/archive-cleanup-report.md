# Archive 정리 기록 — 2026-11-17

이번 작업 시작 main은 `f963cac96321c5b91887999dc3ead494b2c243b3`이며 origin/main과 동일하고 작업 트리는 clean이었다. 과거 감사 문서는 당시 결과로 유지한다. 이 문서와 [참조 메타데이터](archive-cleanup-refs.json)가 이번 작업의 기록이다. 프로젝트 소스와 정상 프로젝트 브랜치는 수정하지 않았다.

## 참조 정리

| 대상 | 처리 |
| --- | --- |
| backup/animal-league-backend-before-merge | 로컬 삭제. 정상 backend에서 커밋 도달 가능 |
| backup/openswdev-backend-after-merge | 로컬 삭제. 정상 backend와 동일 OID |
| backup/reconcile-2025-02-OpenSWDevProject-backend | 로컬 삭제. 정상 backend에서 커밋 도달 가능 |
| 2026_14th_final_study_BE/backup/week8-jangsungwon-before-merge | 원격 OID 재확인 및 해당 ref의 예상 OID lease로 원격 삭제 후 로컬 삭제·prune |
| security/openswdev-backend-env | 삭제 보류. 후보에만 빈 환경변수 검사 코드가 남음 |

처리 시 다른 worktree에 체크아웃된 대상 브랜치는 없었다. 마지막 백업 tip은 정상 브랜치의 조상이 아니며 삭제 후 정상 브랜치에서 도달하지 않는다. 사용자가 폐기 대상으로 지정한 백업 이력이며 정상 프로젝트 참조는 그대로 보존했다. Git 객체 자체를 prune하지 않았다.

보안 후보와 정상 backend의 차이는 EmailService.java 하나이며, 정상 backend는 환경변수를 사용하지만 후보의 `requireSendGridApiKey()` 및 빈 값 검사 8줄은 반영되어 있지 않다. 따라서 모든 수정 반영 조건을 충족하지 못해 후보를 보존했다. 정상 backend는 origin과 동일하며 10,899개 도달 객체에서 HIGH 및 SendGrid 탐지는 각각 0건이었다. 후보는 원격에 없고 자동 Push에서 제외된다.

삭제 전후 전체 ref/OID를 대조하여 지정된 로컬 4개·origin 추적 1개 외에는 변하지 않았고, 원격도 지정된 1개 외에는 동일했다. 정상 브랜치를 덮어쓰는 강제 Push는 수행하지 않았다.

## 외부 백업

정확한 대상 `D:\Archive-backups`를 조사했다. 루트·내부 reparse point는 발견되지 않았다. 재귀 파일 집계는 3,818개, 1,598,277,851바이트였다. 감사·검증 자료, bare 복원 사본, Git 메타데이터 사본 및 등록된 detached conflict-worktree가 확인됐다. 사용자가 추가로 이 Git 사본과 worktree 삭제를 승인했다. 임시 worktree는 미커밋 변경이 없었다.

그러나 디렉터리 삭제를 포함한 명령은 자동 승인 검토에서 `blocked by policy`로 실행 전 거절됐다. 따라서 외부 백업은 삭제되지 않았고 임시 worktree 등록도 유지된다. 새 백업은 생성하지 않았다. 실제 삭제와 등록 해제가 남아 있다. 일반 삭제는 물리적 안전 소거를 뜻하지 않으며 로컬 reflog·도달 불가능 객체도 정리하지 않았다.

## 문서 조사

main Git 트리의 프로젝트 11개와 README 목록을 대조했다. 프로젝트 README·의존성·빌드 설정·API 및 소스 구조, 추가 브랜치, 통합 스크립트·커밋 이력을 참고했다. OpenSWDevProject 서비스와 KIT Vibe 구현은 별도 브랜치에 있음을 명시했다. QAgent 공개 원본 URL, 과제의 구체적 서비스 주제, OpenSWDevProject의 정확한 빌드 의존성 버전은 확정하지 않았다. 원본 URL은 Git remote·기존 문서·package.json에서 확인한 과거 참조로 표시했다.

프로젝트 애플리케이션 전체 빌드·외부 AI·메일 인증 시험은 이번 문서 작업의 검증 범위에 포함하지 않는다. 정규식 검사는 모든 비밀정보 부재를 보장하지 않으며 키 폐기 여부는 확인하지 않았다.
## 이번 검증 결과

- README: main의 독립 프로젝트 11개와 상세 항목 일치, 내부 상대 링크 34개 존재, 명시한 브랜치 참조 존재, Markdown 표·코드 펜스 및 diff 공백 검사 통과.
- 보안: 현재 모든 참조의 도달 객체 18,392개 검사에서 HIGH 0건, SendGrid 0건. 광범위 REVIEW 937건은 진단이며 비밀정보로 확정하거나 모두 수동 검토했다고 주장하지 않는다. reflog는 이 검사 범위에서 제외했다.
- Git: `git fsck --full` 종료 코드 0. dangling tree 2개는 보존했으며 객체 정리 명령을 실행하지 않았다.
- 도구: Windows PowerShell의 fetch·status·sync WhatIf·push-safe WhatIf 종료 코드 0. 격리 테스트 17개 통과(112.745초). 테스트 중 임시 저장소에서만 backup/restore를 검증했으며 실제 Archive 백업은 새로 생성하지 않았다.
- 정상 프로젝트 파일·참조 OID는 유지됐다. 이후 main에는 문서만 커밋하고 전체 tip 도달 이력 검사 후 일반 fast-forward Push한다. 커밋 해시는 이 문서를 포함한 Git 커밋에서 확인할 수 있다.
- 추가 확인: 관리 도구 validate 종료 코드 0, Git 객체 정상·예상 밖 LFS 누락 없음. 기본 validate의 943건 securityFindings는 reflog를 포함한 전체 진단 수이며 현재 참조만의 HIGH 0건 판정과 범위가 다르다.
- 문서 커밋 직전 로컬·원격 동일 브랜치 47개, 로컬 전용 보안 후보 1개, diverged·원격 전용 0개. 지정 백업 브랜치는 남아 있지 않다.
