# 최종 검증 — 2026-11-17 2차

## 적용 결과

- SendGrid 영향 19개 로컬 커밋과 5개 참조 정리. origin의 기존 이력은 보존했다.
- 이전 일반 병합 11개는 부모/트리 검증만 수행했고 다시 병합하지 않았다.
- 백업 브랜치의 `.gitignore` 충돌을 임시 worktree에서 해결했다. 최종 파일 tree는 기존 로컬과 동일하며 양쪽 고유 커밋이 모두 도달 가능하다.
- 프로젝트 브랜치 **13개 일반 Push 성공**, 실패 0. 각 대상의 전체 도달 이력 검사와 최신 원격 tip 확인 후 개별 OID refspec을 사용했다. [브랜치별 결과](archive-push-results.json).
- 프로젝트 Push 후 48개 동일, diverged 0, 원격 전용 0, 로컬 전용 4개. [참조 스냅샷](archive-final-inventory.json)은 이 문서의 main 커밋 직전 기준이다. main 관리 파일 커밋도 검사 후 일반 Push하며, 최종 live 검증 기록은 외부 `D:\Archive-backups\finish-20261117`에 보존한다.
- 로컬 전용: backup/* 3개와 security/openswdev-backend-env 1개. 의도적으로 원격 업로드하지 않았다. 수동 승인이 필요한 원격 조작은 수행하지 않았으며 남은 동기화 실패는 없다.
- main 프로젝트 파일 및 WOOWANGTHON 트리/브랜치 OID는 유지했다. 변경은 관리 코드·설정·문서에 한정한다.

## 복구 및 LFS

기존 bundle 2개 verify, SHA256 대조, `.git` 사본 fsck, 새 mirror 복원 후 참조 동일성을 검증했다. 외부 새 checkpoint와 미커밋 파일 사본도 보존했다. [감사 보고서](archive-audit-report.md).

13개 LFS payload는 사용자가 의도적으로 삭제한 것으로 확인했다. 포인터와 Git 이력은 보존하고 다운로드하지 않았다. `KNOWN_MISSING`으로 경고하며 새로운 누락은 `UNEXPECTED_MISSING`으로 구분한다. 과거 커밋의 실제 LFS 파일은 복구하지 못할 수 있다. **Git 객체 복원 성공은 LFS를 포함한 완전 복구 성공을 뜻하지 않는다.**

## 도구 및 테스트

기존 11개 명령과 promote/update/verify-branches/push-safe를 제공한다. 기본 승격은 검토만 하며 명시적 -Approve로 적용한다. 업데이트는 source 등록이 있는 프로젝트에만 가능하고, source 불명/접근 불가는 SOURCE_UNAVAILABLE이다. 기존 프로젝트 source URL은 추측해 등록하지 않았다.

격리 테스트 17개 통과. add → promote → source 새 커밋 → update → promote, 기존 브랜치 ancestry 보존, 다른 프로젝트 불변, stale 후보 거부, 후보 비밀정보 차단, 캐시 무효화, 알려진/새 LFS 누락, 한글 파일/브랜치, backup/restore, 원본 없는 추출, 네트워크 실패 후 재실행, 서버 GH013 모의 거절을 포함한다. Windows PowerShell 5.1에서 15개 명령의 WhatIf를 실제 실행하여 ref/원격/외부 목적지 보존을 확인했다. 실제 GitHub GH013은 이번 Push에서 발생하지 않았다. git fsck 및 diff 공백 검사도 수행했다.

프로젝트별 애플리케이션 빌드와 실제 메일 전송, SendGrid 키 인증 테스트는 수행하지 않았다. PowerShell 7은 별도 검증하지 않았다. 제한된 정규식 검사의 한계는 보안 보고서를 따른다.

## 보안 잔존 및 운영 제한

키는 **폐기 여부 미확인**이다. 현재 모든 참조의 도달 이력에서는 제거했지만 원본 외부 백업과 로컬 reflog에는 남아 있다. 자동 gc/삭제를 수행하지 않았다. backup/security 작업 참조는 일반 자동 Push에서 제외한다. 원본 source remote를 다시 fetch하면 옛 객체가 재유입될 수 있다.

승격 도중 main 반영과 나머지 참조 트랜잭션 사이의 디스크/프로세스 장애는 외부 복구 지점으로 대응하며 파괴적 자동 롤백을 하지 않는다. 승격 후 메타데이터 커밋과 원격 Push는 가이드의 명시적 명령으로 수행한다. 기존 감사용 일회성 스크립트는 오실행을 막기 위해 외부 historical-scripts에 보존하고 운영 배포에는 포함하지 않았다. 과거 감사 JSON은 당시 증거이며 현재 상태는 최신 summary와 status를 따른다.

일상 운영 명령은 [가이드](archive-manager-guide.md)를 참조한다.
