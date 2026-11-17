# Archive 감사 — 2026-11-17 2차

이전 전체 감사를 반복하지 않고 기존 보고서와 현재 참조를 대조했다. 시작 main은 `b96e651eada5b6883e5eb75a45841882a8a977b5`, 관리 파일만 미커밋이었다. 35 동일 / 12 로컬 선행 / 1 분기 / 4 로컬 전용을 재확인했다.

기존 11개 일반 병합의 양쪽 부모 도달성과 기존 로컬 tree 일치를 확인했다. 재병합하지 않았다. 과거 JSON의 `pushed:false` 및 이전 inventory는 당시 기록이며 현재 상태는 최종 보고서를 따른다.

## 복구 검증

기존 외부 백업 `D:\Archive-backups\audit-20261117-184602` 확인.

- archive.bundle SHA256: `2eab73fddedf5b84f693533c6418aa5daf7d7c05c896c18dc1465a3b2b12b794` — 기존 보고서와 일치.
- post-reconciliation.bundle SHA256: `86d64d5e80484c14eb7178b4fa079013a921b454e0a5052f32fc55c936efde7a`.
- 두 bundle verify 성공. git-metadata 및 기존 복원 mirror fsck 성공.
- post-reconciliation.bundle을 새 mirror로 복원하여 이전 복원 mirror와 모든 참조 일치 확인.
- 새 `D:\Archive-backups\finish-20261117\checkpoint`: 전체 bundle, git-metadata, SHA256 manifest. 미커밋 scripts/docs/.gitignore도 외부 별도 복사.

백업에는 과거 키가 남으므로 외부 경로에 보존하고 업로드하지 않는다. bundle은 LFS payload 및 미커밋 파일의 완전 복원을 보장하지 않는다.

## 충돌

[검증 기록](archive-conflict-resolution.json). 백업 브랜치의 양쪽 프로젝트 subtree는 동일했다. merge-tree가 보고한 유일한 충돌은 Archive 최상위 `.gitignore` 수정/삭제였다. 임시 detached worktree에서 정상 merge 후 로컬 ignore 규칙을 유지했다. 최종 tree는 기존 로컬과 완전히 같고 양쪽 tip 및 고유 커밋을 보존한다. 원격 스냅샷에 없는 legwork_backend 등 파일도 삭제하지 않았다. 기존 원격 백업 브랜치에만 일반 Push했다. 로컬 전용 백업은 업로드하지 않았다.

WOOWANGTHON 프로젝트 및 해당 브랜치는 변경하지 않았다.
