# QAgent 프로젝트 구조 설명

## 최신 구조 요약

현재 실행 구조는 Streamlit UI와 FastAPI API가 같은 Agent 실행 서비스를 공유하는 형태입니다.

- UI 진입점: `app.py`
- API 진입점: `api.py`
- 공통 Agent 실행: `qagent_core/agent/service.py`
- OpenAI loop: `qagent_core/agent/responses.py`, `qagent_core/agent/chat_completions.py`
- Tool schema/실행: `qagent_core/tool_registry.py`, `qagent_core/tool_executor.py`
- RAG: `qagent_core/rag.py`
- Guardrail: `qagent_core/guardrails.py`
- API 문서: `docs/API.md`
- RAG 문서: `docs/RAG_GUIDE.md`
- 보안 문서: `docs/SECURITY_NOTES.md`
- 아키텍처 판단 문서: `docs/AGENT_ARCHITECTURE.md`

RAG는 별도 벡터 DB 없이 repository 내부 문서와 데이터 설명 파일을 검색합니다. LangChain/LangGraph/MCP/A2A는 현재 코드에는 도입하지 않고, 적용 판단과 확장 후보를 문서화했습니다.

FastAPI 응답 metadata에는 `rag_status`, `rag_sources`, `guardrail_warnings`, `execution_nodes`가 포함됩니다.

## 루트 디렉토리

```
QAgent/
├── app.py                      # Streamlit 메인 애플리케이션
├── api.py                      # FastAPI 외부 호출 endpoint
├── requirements.txt            # Python 의존성 (pip install -r)
├── .env.example                # 환경변수 템플릿
├── .gitignore                  # Git 제외 설정
├── README.md                   # 최상위 프로젝트 안내서
├── qagent_core/                # 핵심 로직 (Agent, Tools, HITL, ...)
├── data/                       # 데이터 저장소
├── tests/                      # 자동 테스트
├── scripts/                    # 유틸리티 스크립트
├── docs/                       # 이 파일과 상세 문서
└── report/                     # 제출용 보고서 (PDF, PPT, DOCX)
```

### 루트 파일 설명

| 파일 | 목적 |
|------|------|
| `app.py` | Streamlit 웹 UI 진입점. `streamlit run app.py`로 실행 |
| `api.py` | FastAPI API 서버 진입점. `uvicorn api:app`으로 실행 |
| `requirements.txt` | Python 패키지 의존성. `pip install -r requirements.txt`로 설치 |
| `README.md` | 프로젝트 최상위 안내서. 빠른 실행, 폴더 구조, 주요 링크 포함 |
| `.env.example` | 환경변수 템플릿. 로컬에서 `.env`로 복사하여 설정 |
| `.gitignore` | Git 제외 설정 (`.env`, `venv/`, `__pycache__/`, 등) |

---

## qagent_core/ — 핵심 로직

```
qagent_core/
├── __init__.py
├── agent/                      # Agent 구현 (Tool calling, 프롬프트, 루프)
│   ├── service.py              # Agent 진입점 및 API 모드 선택
│   ├── chat_completions.py     # Chat Completions API 루프
│   ├── responses.py            # Responses API 루프
│   ├── prompts.py              # System prompt 및 user prompt 생성
│   ├── followup.py             # 가상 패치 필수 후속 정책
│   └── presentation.py         # Tool trace 표시명 및 결과 요약
├── tools/                      # 5개 분석 Tool 구현
│   ├── context.py              # AnalysisContext (모든 Tool이 사용)
│   ├── dataset.py              # Tool: 데이터 개요·성능 집계
│   ├── balance.py              # Tool: 이상 탐지·공식·조정 계산
│   ├── patch.py                # Tool: 패치 비교·관련 지식
│   ├── virtual_patch.py        # Tool: 가상 패치·시나리오·자기반성
│   ├── service.py              # Tool 이름 registry (안정된 계약)
│   └── __init__.py             # make_tool_functions() 및 build_tool_functions()
├── review/                     # HITL 기록 관리
│   ├── service.py              # HITL 기록 구성·조회·저장 orchestration
│   ├── models.py               # HITL 데이터 모델
│   └── sqlite_store.py         # SQLite 저장소 구현
├── data_pipeline/             # 데이터 정규화 파이프라인
│   ├── normalize_match.py      # Riot API 매치 데이터 정규화
│   └── ...
├── config.py                   # 설정값 및 기본값 (BALANCE_*, AGENT_*)
├── runtime.py                  # Agent 실행 시 생성되는 runtime 상태
├── data_io.py                  # 데이터 로딩·검증·캐싱
├── persistence.py              # 저장소 경로 관리
├── statistics.py               # 통계 계산 (Wilson 구간, 이상 탐지)
├── simulation.py               # 가상 패치 시나리오 시뮬레이션
├── risk.py                     # 위험 평가 및 재테스트 계획
├── evaluation.py               # Agent 평가 및 성능 분석
├── tool_registry.py            # Tool schema 선언 및 registry
├── tool_executor.py            # Tool 실행 envelop (timeout, 안전 처리)
├── utils.py                    # 유틸리티 함수
└── deadline.py                 # Deadline 추적 및 관리
```

### qagent_core 핵심 파일

| 파일 | 책임 |
|------|------|
| `tools/context.py` | `AnalysisContext`: 모든 Tool이 공유하는 5개 DataFrame과 메타데이터 |
| `agent/service.py` | Agent 진입점: API 모드(Chat Completions vs Responses) 선택 및 실행 |
| `agent/prompts.py` | System prompt 버전 관리 및 user prompt 동적 생성 |
| `review/service.py` | HITL 기록 저장·조회·변환 (SQLite ↔ CSV/JSON) |
| `statistics.py` | Wilson 95% 신뢰구간, FDR 보정, 이상 탐지 |
| `tool_registry.py` | Tool schema 선언 (Tool 이름, 입력, 출력 계약 유지) |

---

## data/ — 데이터 저장소

```
data/
├── lol_assignment_dataset/     # 기본 샘플 데이터 (필수 CSV 5개)
│   ├── battle_logs.csv         # 전투 기록 (필수)
│   ├── characters.csv          # 캐릭터 정보 (필수)
│   ├── skills.csv              # 스킬 정보 (필수)
│   ├── equipment_sets.csv      # 장비 세트 (필수)
│   ├── patch_notes.csv         # 패치 노트 (필수)
│   ├── dataset_summary.json    # 데이터 요약 메타데이터
│   └── app_conversion_summary.json  # 과거 변환 호환성 메타데이터
├── human_review/               # 실행 중 생성되는 HITL 기록 (.gitignore)
│   ├── reviews.sqlite3         # 기준 저장소 (SQLite)
│   ├── review_logs.csv         # CSV 호환 export (best-effort)
│   └── records/                # JSON 호환 export (best-effort)
├── riot_dataset/               # Riot API 수집 원본 및 중간 결과 (.gitignore)
├── lol_assignment_dataset/extras/ # 계정, 매치 ID 등 민감 데이터 (.gitignore)
└── scenario_*/                 # 가상 시나리오 데이터 (선택)
    ├── battle_logs.csv
    ├── characters.csv
    ├── skills.csv
    ├── equipment_sets.csv
    └── patch_notes.csv
```

### 데이터 폴더 정책

- **lol_assignment_dataset/**: 기본 샘플 데이터. 제출물에 포함.
- **human_review/**: 실행 중 생성되는 HITL 기록. `.gitignore` 대상. 로컬에서만 유지.
- **riot_dataset/**, **extras/**: Riot API 수집 원본 및 민감 데이터. `.gitignore` 대상.
- **dataset_summary.json**: 현재 CSV 기준 메타데이터. 제출물에 포함.

---

## tests/ — 자동 테스트

```
tests/
├── __init__.py
├── fakes.py                    # Fake OpenAI client (테스트용)
├── fixtures/                   # 테스트 데이터 및 fixture
├── test_core.py                # 핵심 로직 테스트
├── test_data_pipeline.py       # 데이터 정규화 테스트
├── test_agent_loops.py         # Agent Tool loop 테스트
├── test_agent_evaluation.py    # Agent 평가 테스트
├── test_stabilization.py       # 안정화 테스트
├── test_prompts.py             # Prompt 정책 회귀 테스트
└── __pycache__/                # 캐시 (제외)
```

### 테스트 실행

```powershell
# 모든 테스트 실행
python -m unittest discover -s tests -v

# 특정 테스트 실행
python -m unittest tests.test_core -v
```

---

## scripts/ — 유틸리티 스크립트

```
scripts/
├── __pycache__/                # 캐시 (제외)
├── check_encoding.py           # 파일 인코딩 검사
├── smoke_test_api.py           # OpenAI/Riot API 연결 확인 (최소 요청)
├── refresh_dataset_summary.py  # 현재 CSV 기준 데이터 요약 재생성
└── profile_core.py             # 성능 벤치마크 측정
```

### 스크립트 설명

| 스크립트 | 목적 |
|---------|------|
| `check_encoding.py` | 파일 인코딩 검사 (BOM, UTF-8 등) |
| `smoke_test_api.py` | OpenAI 모델 메타데이터, Riot 플랫폼 상태 확인 (최소 요청) |
| `refresh_dataset_summary.py` | 현재 전달 CSV 기준으로 데이터 요약 재생성 |
| `profile_core.py` | 핵심 로직의 성능 벤치마크 측정 (wall-clock) |

### 실행 예

```powershell
python scripts/check_encoding.py
python scripts/smoke_test_api.py
python scripts/refresh_dataset_summary.py
python scripts/profile_core.py --output PERFORMANCE_BASELINE.md
```

---

## docs/ — 상세 문서

```
docs/
├── README.md (../README.md로 링크)
├── RUN.md                      # 상세 실행 가이드 및 환경 설정
├── API.md                      # 외부 API 인증, 요청/응답, 에러 명세
├── DELIVERY_CHECKLIST.md       # 납품 체크리스트 및 보안 확인
├── SUBMISSION_NOTES.md         # 프로젝트 목적, 기능, 한계, 주의사항
├── PROJECT_STRUCTURE.md        # 이 파일
├── review/                     # 코드 리뷰, 리팩토링, 데이터 파이프라인
│   ├── REFACTORING_GUIDE.md    # 리팩토링 가이드 및 구조 설명
│   ├── CODE_REVIEW_DETAILS.md  # 코드 리뷰 상세 내용
│   └── DATA_PIPELINE_REFACTOR.md  # 데이터 파이프라인 리팩토링 계획
├── evaluation/                 # Agent 평가 결과
│   └── AGENT_EVALUATION.md     # Agent 성능 평가 및 결과
└── performance/                # 성능 분석 및 벤치마크
    ├── PERFORMANCE_BASELINE.md # 기본 성능 벤치마크
    ├── PERFORMANCE_AFTER.md    # 최적화 후 성능 결과
    └── PERFORMANCE_NOTES.md    # 성능 최적화 내역 및 개선 사항
```

### 주요 문서 링크

| 문서 | 내용 |
|------|------|
| [RUN.md](RUN.md) | 상세 실행 가이드: 환경 설정, 데이터 구조, 테스트 명령어 |
| [API.md](API.md) | 외부 API endpoint 명세와 curl 예시 |
| [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md) | 납품용 체크리스트: 보안 확인, 필수 파일, 제외 파일 |
| [SUBMISSION_NOTES.md](SUBMISSION_NOTES.md) | 프로젝트 개요: 목적, 기능, 한계, 운영 전 필요사항 |
| [review/](review/) | 코드 구조, 리팩토링 내역, 데이터 정규화 |
| [evaluation/](evaluation/) | Agent 평가 결과 및 성능 지표 |
| [performance/](performance/) | 벤치마크 및 최적화 결과 |

---

## report/ — 제출용 보고서

```
report/
├── Battle_Balance_Analyst_AI_Agent_PPT_프리미엄_재디자인.pptx
├── Battle_Balance_Analyst_AI_Agent_보고서_제출용_확장수정본.docx
├── Battle_Balance_Analyst_AI_Agent_보고서_제출용_확장수정본.pdf
├── LoL_Balance_Agent_Final_Presentation.pptx
├── LoL_Balance_Agent_Final_Report.pdf
├── integration_profile.md
├── streamlit-smoke.err.log
└── streamlit-smoke.out.log
```

### 보고서 정책

- **PDF, PPT, DOCX**: 코드 구현과 별도 산출물. 제출물에 포함 시 현재 v2.8.0 코드와 일치하는지 사람이 검토.
- **.log**: 실행 로그. 제출물에서 제외 권장.
- **integration_profile.md**: 통합 시나리오 시연 프로필.

---

## 루트 레벨 레거시 파일

다음 파일들은 루트에 존재하는 레거시 수집기 및 데이터 생성 스크립트입니다. 코드 로직 변경 없이 legacy wrapper로 유지되며, 필요시 scripts/로 이동할 수 있습니다.

| 파일 | 목적 | 상태 |
|------|------|------|
| `fetchMatch.py` | Riot API 매치 데이터 수집 | Legacy wrapper (변경 안 함) |
| `fetchPatches.py` | Riot API 패치 데이터 수집 | Legacy wrapper (변경 안 함) |
| `build_lol_assignment_dataset.py` | CSV 데이터셋 생성 | Utility (선택적 이동 가능) |
| `generateDemoData.py` | 데모 데이터 생성 | Utility (선택적 이동 가능) |

### Legacy 파일 주의

- 현재 app.py에서 직접 import하지 않습니다.
- 필요시 `python fetchMatch.py` 또는 `python scripts/fetchMatch.py`로 별도 실행.
- 데이터 수집이나 데모 생성 시에만 사용.

---

## 환경변수 관리

### .env 파일 설정

```powershell
# 로컬에서만 사용
Copy-Item .env.example .env
```

### 필수 및 선택 변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `OPENAI_API_KEY` | 필수 | - | 서버 내부 OpenAI 호출용 키. UI/API에 원문 노출 금지 |
| `AGENT_API_KEY` | API 사용 시 필수 | - | 외부 API 호출 인증용 키. OpenAI 키와 분리 |
| `RIOT_API_KEY` | 선택 | - | Riot API 키 (신규 데이터 수집만) |
| `OPENAI_MODEL` | 선택 | `gpt-5.4` | 사용할 OpenAI 모델명 |
| `OPENAI_API_MODE` | 선택 | `responses` | API 모드 (Chat Completions 또는 Responses) |
| `OPENAI_REASONING_EFFORT` | 선택 | `none` | 추론 강도 (일부 모델) |
| `MAX_AGENT_ITERATIONS` | 선택 | 18 | 최대 Agent 반복 횟수 |
| `MAX_TOOL_CALLS` | 선택 | 30 | 최대 Tool 호출 횟수 |
| `AGENT_TIMEOUT_SECONDS` | 선택 | 180 | Agent 실행 제한 시간 (초) |
| `AGENT_DATA_DIR` | 선택 | `data/lol_assignment_dataset` | API 서버가 사용할 데이터셋 폴더 |
| `AGENT_CORS_ORIGINS` | 선택 | 빈 값 | 허용할 CORS origin 목록. 기본값은 열지 않음 |
| `ENABLE_RAG` | 선택 | `true` | 파일 기반 RAG 사용 여부 |
| `RAG_INCLUDE_DATA_DOCS` | 선택 | `true` | `data/**` README, prompt, patch note 파일을 RAG 검색에 포함 |
| `RAG_TOP_K` | 선택 | `4` | API/UI prompt에 첨부할 RAG 근거 개수 제한 |
| `MAX_AGENT_QUERY_CHARS` | 선택 | `12000` | UI/API query 길이 제한 |
| `ENABLE_TOOL_TRACE` | 선택 | `true` | Tool trace 표시 여부 |
| `ENABLE_DEBUG_LOG` | 선택 | `false` | 디버그 로그 표시 여부 |

---

## 제출물 체크리스트

제출 전 다음을 확인하세요:

- [ ] 루트에 `.env` 파일이 없음 (`.env.example`만 있음)
- [ ] 루트에 `OPENAI_API_KEYS.txt` 같은 민감 파일이 없음
- [ ] `venv/`, `.venv/`, `__pycache__/`, `.pytest_cache/` 제외됨
- [ ] `data/human_review/`, `data/riot_dataset/`, `data/lol_assignment_dataset/extras/` 제외됨
- [ ] `report/` 보고서가 현재 v2.8.0 코드와 일치하는지 검토됨
- [ ] `requirements.txt`로 신규 환경에서 설치 확인됨
- [ ] 모든 테스트 통과: `python -m unittest discover -s tests -v`
- [ ] `streamlit run app.py` 정상 기동 확인됨

---

## 빠른 참조

### 주요 명령어

```powershell
# 실행
streamlit run app.py

# API 서버 실행
uvicorn api:app --host 127.0.0.1 --port 8000

# 테스트
python -m unittest discover -s tests -v
python scripts/smoke_test_api.py

# 검증
python -m py_compile app.py generateDemoData.py build_lol_assignment_dataset.py
python -m compileall -q qagent_core tests
python scripts/check_encoding.py

# 성능 측정
python scripts/profile_core.py --output PERFORMANCE_BASELINE.md
```

### 중요 파일 경로

```
최상위 안내        → README.md
상세 실행 가이드   → docs/RUN.md
데이터 구조       → docs/review/DATA_PIPELINE_REFACTOR.md
코드 리뷰        → docs/review/CODE_REVIEW_DETAILS.md
기능 한계        → docs/SUBMISSION_NOTES.md
성능 벤치마크     → docs/performance/
```

---

**관련 문서**: [README.md](../README.md) | [docs/RUN.md](RUN.md) | [docs/DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md)
