# QAgent Guidance

이 문서는 QAgent를 실행, 검수, 제출할 때 참고하는 운영 가이드다. 발표 자료가 아니라 프로젝트 상태를 확인하고 재현하기 위한 제출용 기준 문서로 유지한다.

## 1. 현재 프로젝트 요약

QAgent는 게임 라이브 서비스 밸런스 분석을 보조하는 AI Agent PoC다. Streamlit UI와 FastAPI endpoint가 같은 Agent 실행 흐름을 사용하며, 사용자는 분석 질문을 입력하고 Agent는 데이터 분석 도구, RAG 근거, LLM 응답을 결합해 결과를 만든다.

현재 구현의 핵심은 다음과 같다.

- Streamlit UI: `app.py`
- 외부 호출 API: `api.py`
- Agent 실행 모듈: `qagent_core/agent/`
- 도구 등록 및 실행: `qagent_core/tool_registry.py`, `qagent_core/tool_executor.py`
- 데이터 로딩/분석: `qagent_core/data_io.py`, `qagent_core/statistics.py`, `qagent_core/simulation.py`, `qagent_core/evaluation.py`
- Guardrail: `qagent_core/guardrails.py`
- 파일 기반 RAG: `qagent_core/rag.py`
- 실행/보안/API 문서: `docs/`
- 제출 원본 문서: `submission/raw/`
- 생성 제출물: `submission/*_UPDATED.pdf`, `submission/FINAL_PRESENTATION_UPDATED.pptx`

## 2. 실행 진입점

### Streamlit UI

```bash
streamlit run app.py
```

UI는 서버의 `OPENAI_API_KEY` 값을 입력창 기본값으로 표시하지 않는다. OpenAI key는 서버 환경변수 또는 `.env`에서만 읽고, UI/API 응답/log에 원문을 노출하지 않는다.

### FastAPI Agent API

```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```

외부 프로그램은 다음 endpoint를 호출한다.

```http
POST /api/agent/run
```

인증은 `AGENT_API_KEY`를 사용한다. 이 값은 OpenAI 호출용 `OPENAI_API_KEY`와 반드시 분리한다.

```bash
curl.exe -X POST "http://127.0.0.1:8000/api/agent/run" ^
  -H "Authorization: Bearer %AGENT_API_KEY%" ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"패치노트 기반으로 밸런스 위험을 분석해줘\",\"model\":\"gpt-4.1-mini\",\"reasoning_effort\":\"medium\",\"context\":{},\"stream\":false}"
```

## 3. API 요청과 응답

요청 body 예시는 다음과 같다.

```json
{
  "query": "분석할 질문",
  "model": "gpt-4.1-mini",
  "reasoning_effort": "medium",
  "context": {},
  "stream": false
}
```

응답 body는 다음 구조를 따른다.

```json
{
  "answer": "...",
  "tool_trace": [],
  "metadata": {
    "model": "gpt-4.1-mini",
    "reasoning_effort": "medium",
    "elapsed_ms": 1234,
    "rag_status": "ok",
    "rag_sources": [],
    "guardrail_warnings": [],
    "execution_nodes": [
      "request_validation",
      "rag_search",
      "agent_run",
      "output_guardrail"
    ]
  }
}
```

주요 오류 응답은 다음과 같다.

- 인증 없음 또는 잘못된 `AGENT_API_KEY`: `401`
- 빈 query: `400`
- 너무 긴 query: `400`
- 서버 `OPENAI_API_KEY` 미설정: 명확한 설정 오류
- Agent 실행 실패: 민감정보를 제거한 안전한 오류 메시지

자세한 API 명세는 `docs/API.md`를 기준으로 한다.

## 4. 환경변수

`.env.example`을 복사해 `.env`를 만들고 필요한 값을 채운다. 실제 key는 저장소에 커밋하지 않는다.

| 변수 | 용도 |
| --- | --- |
| `OPENAI_API_KEY` | 서버 내부 OpenAI 호출 전용 key |
| `AGENT_API_KEY` | 외부 Agent API 인증용 key |
| `OPENAI_MODEL` | 기본 Agent 모델 |
| `OPENAI_API_MODE` | `responses`, `chat_completions`, `auto` 중 선택 |
| `OPENAI_REASONING_EFFORT` | 기본 reasoning effort |
| `MAX_AGENT_ITERATIONS` | Agent loop 제한 |
| `MAX_TOOL_CALLS` | tool 호출 제한 |
| `AGENT_TIMEOUT_SECONDS` | Agent 실행 시간 제한 |
| `AGENT_CORS_ORIGINS` | 허용할 CORS origin 목록 |
| `AGENT_DATA_DIR` | 사용할 데이터셋 경로 |
| `ENABLE_RAG` | 파일 기반 RAG 활성화 여부 |
| `RAG_INCLUDE_DATA_DOCS` | `data/**` 문서와 patch note 검색 포함 여부 |
| `RAG_TOP_K` | RAG 검색 결과 개수 |
| `MAX_AGENT_QUERY_CHARS` | UI/API 공통 query 길이 제한 |
| `ENABLE_TOOL_TRACE` | tool trace 표시 여부 |
| `ENABLE_DEBUG_LOG` | 디버그 로그 여부 |
| `RIOT_API_KEY` | Riot 데이터 수집 또는 smoke test용 선택 key |

## 5. Agent 실행 흐름

UI와 API는 같은 실행 원칙을 따른다.

1. 요청 입력을 검증한다.
2. Guardrail이 빈 query, 너무 긴 query, 잘못된 model/reasoning 값을 차단한다.
3. RAG가 활성화되어 있으면 프로젝트 문서와 데이터 설명 문서를 검색한다.
4. 검색된 문서는 지시문이 아니라 비신뢰 근거로 prompt에 추가한다.
5. Agent가 LLM과 도구를 사용해 분석을 수행한다.
6. 출력 후처리에서 secret 패턴을 마스킹한다.
7. 응답 metadata에 RAG 상태, 출처, guardrail warning, 실행 node를 포함한다.

API metadata의 `execution_nodes`는 위 흐름을 검수하기 위한 trace다.

## 6. RAG 구조

현재 RAG는 벡터 DB 없이 파일 기반 lexical retriever로 구현되어 있다. 과제/데모 규모에서는 추가 인프라 없이 재현 가능하고, 검색 출처를 명확히 남기는 것이 더 중요하다고 판단했다.

검색 대상은 다음 범위다.

- `README.md`
- `docs/**/*.md`
- `data/**/README.md`
- `data/**/agent_prompt_v2.txt`
- `data/**/patch_notes.csv`

RAG 상태 값은 다음과 같다.

- `ok`: 관련 근거를 찾고 prompt에 첨부함
- `insufficient_evidence`: 검색은 수행했지만 충분한 근거가 없음
- `disabled`: `ENABLE_RAG=false` 또는 `RAG_TOP_K=0`

검색 출처는 `metadata.rag_sources`에 파일명, 섹션, 점수 형태로 들어간다. API 응답에는 문서 전체 내용이나 서버 secret을 반환하지 않는다.

자세한 내용은 `docs/RAG_GUIDE.md`를 기준으로 한다.

## 7. Guardrail 및 보안 기준

적용된 최소 보안 기준은 다음과 같다.

- `OPENAI_API_KEY`와 `AGENT_API_KEY` 분리
- 서버 key를 UI 기본값으로 주입하지 않음
- API 인증 필수
- request schema 검증
- 빈 query와 과도하게 긴 query 차단
- 허용되지 않은 파일 경로 접근 차단
- RAG 문서 내 prompt injection 의심 패턴 탐지
- tool 실행은 등록된 allowlist 기반
- LLM 출력에서 secret 패턴 마스킹
- 오류 메시지와 log에 민감정보가 섞이지 않도록 처리

OWASP LLM Top 10 관점의 점검 내용은 `docs/SECURITY_NOTES.md`에 정리되어 있다.

## 8. LangChain, LangGraph, MCP, A2A 판단

현재 프로젝트는 단순하고 재현 가능한 제출물이 중요하므로 다음과 같이 판단했다.

| 항목 | 적용 여부 | 이유 |
| --- | --- | --- |
| LangChain | 미적용 | 현재 RAG와 tool 연결은 자체 모듈로 충분하며 의존성 증가를 피함 |
| LangGraph | 미적용 | 실행 단계는 metadata trace로 표현 가능하고 그래프 런타임 도입 필요성이 낮음 |
| MCP | 미구현, 설계 문서화 | 외부 도구 표준화는 향후 확장 항목으로 적합 |
| A2A | 미구현, 설계 문서화 | 다중 Agent 협업은 현재 PoC 범위보다 큼 |

구체적인 판단 근거와 향후 확장 방향은 `docs/AGENT_ARCHITECTURE.md`를 기준으로 한다.

## 9. 테스트 및 검증

권장 검증 명령은 다음과 같다.

```bash
python -m ruff format app.py api.py qagent_core tests
python -m py_compile app.py api.py
python -m compileall -q qagent_core tests
python -m unittest discover -s tests -v
```

API smoke test가 필요한 경우 `AGENT_API_KEY`를 설정한 뒤 `scripts/smoke_test_api.py`를 사용한다.

검수할 핵심 항목은 다음과 같다.

- Streamlit UI가 정상 실행되는가
- UI에 서버 `OPENAI_API_KEY` 원문이 보이지 않는가
- 인증 없는 API 호출이 `401`을 반환하는가
- 잘못된 `AGENT_API_KEY`가 `401`을 반환하는가
- 빈 query와 너무 긴 query가 차단되는가
- 정상 API 호출 응답에 `rag_status`, `rag_sources`, `guardrail_warnings`, `execution_nodes`가 포함되는가
- RAG 검색 결과가 있을 때 출처가 metadata에 남는가
- 오류 응답과 log에 secret이 노출되지 않는가

## 10. 제출 산출물 생성

제출용 원본 문서는 `submission/raw/`에 둔다.

| 원본 | 생성물 |
| --- | --- |
| `submission/raw/PRESENTATION_10_15_SLIDES.md` | `submission/FINAL_PRESENTATION_UPDATED.pptx` |
| `submission/raw/AGENT_ARCHITECTURE.md` | `submission/AI_AGENT_ARCHITECTURE_UPDATED.pdf` |
| `submission/raw/DEMO_SCENARIO.md` | `submission/DEMO_SCENARIO_UPDATED.pdf` |
| `submission/raw/REFERENCES.md` | `submission/REFERENCES_UPDATED.pdf` |
| `submission/raw/FINAL_REPORT.md` | `submission/FINAL_REPORT_UPDATED.pdf` |
| `docs/guidance.md` | `submission/GUIDANCE_UPDATED.pdf` |

산출물은 다음 명령으로 재생성한다.

```bash
python scripts/build_submission_outputs.py
```

이 스크립트는 로컬 한글 폰트를 사용해 PDF/PPTX를 생성한다. 발표용 PPT는 `PRESENTATION_10_15_SLIDES.md`를 기준으로 만들지만, 제출의 핵심 문서는 `FINAL_REPORT.md`, `AGENT_ARCHITECTURE.md`, `DEMO_SCENARIO.md`, `REFERENCES.md`, `guidance.md`다.

## 11. 문서 기준

문서 간 우선순위는 다음과 같다.

1. API 동작과 오류 예시는 `docs/API.md`
2. RAG 구조와 metadata는 `docs/RAG_GUIDE.md`
3. 보안/OWASP 검토는 `docs/SECURITY_NOTES.md`
4. Agent 구조와 기술 적용 판단은 `docs/AGENT_ARCHITECTURE.md`
5. 제출물 구성과 재생성 방법은 `submission/raw/README_SUBMISSION.md`
6. 전체 운영 가이드는 이 문서 `docs/guidance.md`

서로 다른 문서의 환경변수 이름은 `.env.example`을 기준으로 맞춘다.
