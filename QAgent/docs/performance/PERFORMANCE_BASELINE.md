# Core 성능 기준값

- 측정 시각(UTC): 2026-07-07T07:17:27+00:00
- Python: 3.12.10
- OS: Windows-11-10.0.26200-SP0
- 데이터: `D:\IdeaProjects\QAgent\data\lol_assignment_dataset` (10,420 rows)
- 측정 방식: 각 항목 1회 wall-clock 측정, 외부 API 호출 없음

| 구간 | 실행 시간(초) | 상태 | 비고 |
|---|---:|---|---|
| CSV 데이터 로딩 | 0.720293 | SUCCESS | 필수 CSV 5개 |
| 데이터 정규화 | 0.016605 | SUCCESS | 컬럼/BOM, 숫자형, 결과값 정리 |
| 이상 후보 탐지 | 6.129911 | SUCCESS | Wilson + 이항검정 + FDR |
| 패치 전후 비교 | 0.028372 | SUCCESS | 최빈 entity의 패치별 집계 |
| 세그먼트 분석 | 0.045829 | SUCCESS | 패치 × user_segment 집계 |
| 가상 패치 영향 추정 | 0.002383 | SUCCESS | 휴리스틱 시나리오 계산 |
| HITL 저장 | 0.065516 | SUCCESS | 임시 SQLite + CSV + JSON |
| Agent Tool 1회 실행 | 0.000013 | SUCCESS | 외부 API 없는 순수 Tool 호출 |
| Streamlit 초기 렌더링 | 1.675983 | SUCCESS | AppTest, 기본 데이터 로딩 포함 |
| 전체 실행 | 8.685048 | SUCCESS | battle rows=10420 |

## 해석 주의사항

- 이번 실행에서 가장 느린 독립 측정 항목은 `이상 후보 탐지` (6.129911초)입니다.
- 각 항목은 워밍업 없이 1회 측정했으므로 작은 값의 순위는 반복 실행 시 달라질 수 있습니다.
- Streamlit 초기 렌더링은 데이터 로딩을 다시 포함하므로 위 항목을 단순 합산해 비율을 계산하면 안 됩니다.
- OpenAI/Riot 네트워크 지연과 LLM 응답 시간은 측정하지 않았습니다.
- 이 문서는 해당 실행의 측정값이며 성능 보증 수치가 아닙니다.
