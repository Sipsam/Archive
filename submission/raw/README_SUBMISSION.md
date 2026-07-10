# 최종 제출물 안내

이 폴더는 발표 자료가 아니라 제출 패키지의 원본 문서 묶음이다. `PRESENTATION_10_15_SLIDES.md`는 과제 요구나 부속 설명이 필요할 때 참고할 수 있는 보조 원고이며, 제출물의 중심은 `FINAL_REPORT.md`, `AGENT_ARCHITECTURE.md`, `DEMO_SCENARIO.md`, `REFERENCES.md`, Mermaid 다이어그램 원본이다.

## 제출 주제

**게임 라이브 서비스 밸런스 분석을 위한 AI Agent 도입 전략 및 Delivery 설계**

QAgent는 게임 전투 로그와 패치 근거를 바탕으로 밸런스 검토 후보를 찾고, 통계 Tool, RAG 근거, 가상 패치 시나리오, 재테스트 계획, Human-in-the-loop(HITL) 검토 기록을 제공하는 PoC다. 최종 패치 판단과 실제 적용은 Agent가 아니라 사람이 수행한다.

## 제출 파일 역할

| 파일 | 제출 기준 역할 |
| --- | --- |
| `FINAL_REPORT.md` | 최종 제출 보고서 원고. 문제 정의, 후보 비교, MVP, 구현, 보안, 한계, 운영 전환 계획 포함 |
| `AGENT_ARCHITECTURE.md` | 실제 코드 기준 Agent/API/Tool/RAG/Guardrail/HITL 구조 설명 |
| `DEMO_SCENARIO.md` | 제출 검수자가 로컬에서 앱과 API를 확인할 때 쓰는 실행 시나리오 |
| `REFERENCES.md` | 외부 공식 문서와 프로젝트 내부 근거 목록 |
| `PRESENTATION_10_15_SLIDES.md` | 선택 부록. 발표가 필요한 경우에만 사용하는 보조 원고 |
| `diagrams/architecture.mmd` | 아키텍처 Mermaid 원본 |
| `diagrams/workflow.mmd` | Agent 실행 workflow Mermaid 원본 |

## 현재 코드 기준 최신 변경

- Streamlit UI와 FastAPI endpoint가 같은 `run_generative_agent()` 실행 흐름을 공유한다.
- 외부 API endpoint `POST /api/agent/run`이 추가되어 `AGENT_API_KEY` 인증으로 호출한다.
- `OPENAI_API_KEY`는 서버 내부 OpenAI client 생성에만 사용하고 UI/API/log에 원문을 노출하지 않는다.
- 파일 기반 RAG가 `README.md`, `docs/**/*.md`, `data/**/README.md`, `data/**/agent_prompt_v2.txt`, `data/**/patch_notes.csv`를 검색한다.
- 공통 Guardrail이 빈 query, 너무 긴 query, 잘못된 model/reasoning 값, 과도한 context를 차단한다.
- API 응답 metadata에는 `rag_status`, `rag_sources`, `guardrail_warnings`, `execution_nodes`가 포함된다.
- LangChain/LangGraph/MCP/A2A는 현재 코드에는 도입하지 않았고, 도입 판단과 확장 후보만 문서화했다.

## 실행 방법

```powershell
cd D:\IdeaProjects\QAgent
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에는 실제 키를 직접 넣되 제출 패키지에는 포함하지 않는다.

```dotenv
OPENAI_API_KEY=...
AGENT_API_KEY=...
ENABLE_RAG=true
RAG_INCLUDE_DATA_DOCS=true
RAG_TOP_K=4
MAX_AGENT_QUERY_CHARS=12000
```

Streamlit UI:

```powershell
streamlit run app.py
```

FastAPI:

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

API 호출 예시:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/run" `
  -H "Authorization: Bearer $env:AGENT_API_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"패치노트 기반으로 밸런스 후보를 분석해줘\",\"model\":\"gpt-4.1-mini\",\"reasoning_effort\":\"medium\",\"context\":{},\"stream\":false}"
```

## 제출 전 확인

- [x] `OPENAI_API_KEY`가 UI 입력값이나 API 응답에 노출되지 않도록 수정됨
- [x] 외부 API 인증용 `AGENT_API_KEY`가 OpenAI key와 분리됨
- [x] RAG/Guardrail/API metadata 문서가 `docs/`와 README에 반영됨
- [x] `qagent_core/guardrails.py`, `qagent_core/rag.py` 추가됨
- [x] API endpoint 보안/검증 테스트가 추가됨
- [x] 자동 테스트 107개 통과 이력 있음
- [ ] 제출 직전 `python -m unittest discover -s tests -v` 재실행
- [ ] 제출 압축본에 `.env`, `.streamlit/secrets.toml`, `OPENAI_API_KEYS.txt`, 실행 로그, 개인 HITL 기록 제외
- [ ] PDF 변환 시 한글 글꼴, 표 잘림, Mermaid 렌더링 육안 확인

## 주의사항

- 제출물은 “AI가 패치를 자동 승인/적용하는 시스템”이 아니라 “검토 후보와 근거를 줄여주는 HITL Agent PoC”로 설명해야 한다.
- 가상 패치 영향은 예측 모델이나 게임 엔진 시뮬레이션이 아니라 휴리스틱 기반 시나리오 추정이다.
- RAG 검색 결과는 근거 자료이며 시스템 지시문이 아니다.
- 실제 OpenAI end-to-end 실행은 제출자의 유효한 key와 모델 권한이 필요하다.
