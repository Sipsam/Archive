# Archive 보안 처리 결과 — 2026-11-17 2차

SendGrid 키의 **폐기 여부 미확인**. 서비스는 운영되지 않으며 인증 시험/API 호출, 새 키 발급, 서비스 복구는 수행하지 않았다. 사용자의 폐기 확인은 별도 사항이다.

## 적용

`D:\Archive-backups\finish-20261117\sanitized.git` 격리 mirror에서 Git 객체를 변환했다. 원본 3개 blob의 Java 문자열 리터럴을 `System.getenv("SENDGRID_API_KEY")`로 대체했다. 파일 삭제 없이 영향 커밋 19개, 참조 5개를 정리했다. 작성자·날짜·메시지·부모 순서를 보존했으며 부모 해시는 필요한 범위만 변경했다. 기존 환경변수 후보의 검사 코드도 유지했다.

[전체 old/new 해시](archive-sanitization-results.json)에 커밋·blob·참조 매핑이 있다. 변경된 모든 커밋의 트리 차이는 해당 EmailService 파일과 대체 blob에 한정되는지 검증했다. origin의 기존 커밋은 재작성하지 않았다. 정리된 backend는 기존 origin/backend를 조상으로 포함하며 도달 이력 검사 후 일반 Push했다. Force Push, 원격 삭제, 보호 규칙 변경, GH013 예외 승인은 없었다.

로컬 backup 2개, security 후보 및 `repo-2025-02/backend` 추적 참조도 정리된 객체로 갱신했다. 원본 source remote를 다시 fetch하면 과거 비밀정보가 재유입될 수 있다. 일반 관리는 origin만 fetch한다. source 서버의 과거 이력 변경은 이번 범위 밖이다.

## 잔존 범위와 검사 한계

외부 백업, 격리 원본 객체 및 기존 작업 저장소 reflog에는 원래 객체가 남아 있다. 복구 가능성을 위해 자동 expire/gc/prune하지 않았다. 따라서 디스크 전체에서 비밀정보를 완전히 삭제한 것은 아니다. 이들 자료는 GitHub에 올리지 않는다. `security` 기본 검사는 reflog까지 포함하므로 기존 키를 계속 보고할 수 있다. Push 검사는 해당 tip의 **전체 도달 이력**을 별도로 검사한다.

정규식 v2의 HIGH(SendGrid, 토큰, 개인키 등)는 차단한다. 광범위한 credential assignment/URL REVIEW는 코드·예제·placeholder도 매칭하므로 진단으로 보고하며 차단 판정과 구분한다. REVIEW를 실제 키로 확정하거나 전부 수동 검토 완료했다고 주장하지 않는다. 제한된 정규식 검사는 모든 비밀정보 부재를 보장하지 않는다. GitHub가 거절하면 우회 없이 중단한다. Git stderr/소스/값을 보고서에 출력하지 않는다.

캐시는 `.git/archive-security-cache`에 값 없이 저장하며 도달 tip과 관리 코드 SHA256으로 무효화한다. 검사 정책이 바뀌거나 새 커밋이 생기면 다시 검사한다. 원격 tip은 캐시와 별개로 Push 직전 재확인한다.
