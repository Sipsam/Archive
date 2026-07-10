# Riot 수집기 구조 개선 계획

## 현재 책임 분포

`fetchMatch.py`는 약 2,500줄이며 설정·플레이어 목록, 정규화, rate limit,
HTTP client, match 변환, checkpoint/cache, CSV 병합, 수집 orchestration과 CLI를
한 프로세스에 포함한다.

| 책임 | 현재 위치 | 다음 분리 대상 |
|---|---|---|
| 순수 ID·패치·큐·룬 정규화 | 기존 421~591, 997~1017행 | `data_pipeline/normalize_match.py`로 분리 완료 |
| rate limit | `RiotRateLimiter` | clock/sleep 주입 후 `rate_limit.py` |
| Riot HTTP와 재시도 | `RiotApiClient` | Session·limiter 주입 후 `riot_client.py` |
| checkpoint/cache·병합 | 1630~1794행 및 `collect_dataset` | atomic write 계약을 만든 뒤 `checkpoint.py` |
| match detail → row | `build_battle_log_rows` | fixture 계약을 만든 뒤 `normalize_match.py` |
| app-ready DataFrame 변환 | 1181~1626행 | 현재 CSV 출력 golden test 후 별도 transformer |
| 수집 orchestration | `collect_dataset` 424행 | 위 계층 분리 후 service로 축소 |
| CLI | `main` 201행 | `build_parser()`와 `run(args)`로 나눈 뒤 `cli.py` |

## 단계별 이전 순서

1. 순수 정규화 함수와 기존 결과 계약을 고정한다. 현재 완료된 단계다.
2. `RiotRateLimiter`에 clock과 sleeper를 주입해 실제 대기 없는 단위 테스트를 만든다.
3. `RiotApiClient`에 Session과 limiter를 주입하고 200/429/5xx/4xx 응답을 Fake로 검증한다.
4. checkpoint 파일의 임시 파일·원자적 replace·resume 규칙을 테스트로 고정한다.
5. 익명화된 match fixture로 `build_battle_log_rows`와 app-ready CSV 컬럼을 고정한다.
6. 마지막에 CLI parser와 orchestration을 이동하고 `fetchMatch.py`는 호환 진입점으로 남긴다.

이번 단계에서는 API 호출, rate limit, checkpoint와 CSV 출력 경로를 변경하지 않았다.
기존 수집 결과 형식과 `python fetchMatch.py ...` 실행 방식도 유지한다.
