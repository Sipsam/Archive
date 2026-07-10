# 실행 가이드

## 최신 Agent API/RAG/Guardrail 설정

이 문서는 현재 `app.py`, `api.py`, `qagent_core/guardrails.py`, `qagent_core/rag.py` 기준입니다.

서버 secret 원칙:

- `OPENAI_API_KEY`는 서버 내부 OpenAI client 생성에만 사용합니다.
- Streamlit UI에는 OpenAI key 입력창이 없고, UI/API/log에는 원문 key를 표시하지 않습니다.
- 외부 API 호출 인증은 `OPENAI_API_KEY`와 분리된 `AGENT_API_KEY`로 처리합니다.

RAG/Guardrail 환경변수:

```dotenv
ENABLE_RAG=true
RAG_INCLUDE_DATA_DOCS=true
RAG_TOP_K=4
MAX_AGENT_QUERY_CHARS=12000
```

RAG 검색 대상:

- `README.md`
- `docs/**/*.md`
- `data/**/README.md`
- `data/**/agent_prompt_v2.txt`
- `data/**/patch_notes.csv`

Guardrail은 빈 query, 너무 긴 query, 잘못된 model 이름, 지원하지 않는 `reasoning_effort`, 지나치게 큰 `context`를 차단합니다.

API 응답 metadata에는 다음 필드가 포함됩니다:

- `rag_status`
- `rag_sources`
- `guardrail_warnings`
- `execution_nodes`

## 설치

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에 다음 값을 설정합니다.

```dotenv
OPENAI_API_KEY=sk-...
AGENT_API_KEY=change-me
```

`OPENAI_API_KEY`는 서버 내부 OpenAI 호출에만 사용됩니다. Streamlit UI에는 키 입력창이 없고, 키 원문은 기본값으로 채워지거나 표시되지 않습니다.

`AGENT_API_KEY`는 외부 프로그램이 FastAPI endpoint를 호출할 때 사용하는 별도 인증 키입니다.

## Streamlit UI

```powershell
streamlit run app.py
```

브라우저에서 Streamlit이 출력한 로컬 주소로 접속합니다. 사이드바의 OpenAI API Key 상태가 `configured`이면 Agent 실행이 가능합니다.

## FastAPI 서버

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

기본 데이터셋은 `data/lol_assignment_dataset`입니다. API 서버가 다른 데이터셋을 사용해야 하면 서버 환경변수로만 지정합니다.

```dotenv
AGENT_DATA_DIR=D:\IdeaProjects\QAgent\data\scenario_01_burst_meta
```

기본 CORS는 열지 않습니다. 브라우저 기반 외부 프론트엔드에서 호출해야 할 때만 origin을 명시합니다.

```dotenv
AGENT_CORS_ORIGINS=http://localhost:3000
```

## API 호출

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/run" `
  -H "Authorization: Bearer $env:AGENT_API_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"분석할 질문\",\"model\":\"gpt-4.1-mini\",\"reasoning_effort\":\"medium\",\"context\":{},\"stream\":false}"
```

`X-API-Key` 헤더도 사용할 수 있습니다.

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/run" `
  -H "X-API-Key: $env:AGENT_API_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"승률 이상 후보를 요약해줘\"}"
```

## 검증

```powershell
python -m py_compile app.py api.py
python -m compileall -q qagent_core tests
python -m unittest discover -s tests -v
```

잘못된 API 키 검증:

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/api/agent/run" `
  -H "X-API-Key: wrong" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"test\"}"
```

기대 결과는 `401 Unauthorized`입니다.
