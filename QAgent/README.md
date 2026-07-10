# QAgent

## Recent Agent API/RAG/Security Updates

### Agent API

FastAPI endpoint:

```http
POST /api/agent/run
```

External callers must authenticate with either header:

```http
Authorization: Bearer <AGENT_API_KEY>
X-API-Key: <AGENT_API_KEY>
```

Request example:

```json
{
  "query": "패치노트 기반으로 밸런스 후보를 분석해줘",
  "model": "gpt-4.1-mini",
  "reasoning_effort": "medium",
  "context": {},
  "stream": false
}
```

Response metadata includes `rag_status`, `rag_sources`, `guardrail_warnings`, and `execution_nodes`.

### Server-side Secret Handling

`OPENAI_API_KEY` is used only on the server to create the OpenAI client. The Streamlit UI does not provide an API-key input field, and UI/API responses/log traces must not expose the raw server key. External API authentication uses a separate `AGENT_API_KEY`.

### RAG

QAgent uses lightweight file-based RAG without a vector database. It searches:

- `README.md`
- `docs/**/*.md`
- `data/**/README.md`
- `data/**/agent_prompt_v2.txt`
- `data/**/patch_notes.csv`

Retrieved text is appended to the Agent prompt as untrusted reference evidence, not as instructions.

### Guardrails

Shared UI/API guardrails block examples such as:

- empty `query`
- `query` longer than `MAX_AGENT_QUERY_CHARS`
- invalid model names containing unsupported characters
- unsupported `reasoning_effort`
- oversized `context`

Prompt-injection-like patterns are flagged in `guardrail_warnings`; secret-looking output is masked before UI/API return.

### Security Notes

See:

- `docs/SECURITY_NOTES.md`
- `docs/RAG_GUIDE.md`
- `docs/AGENT_ARCHITECTURE.md`
- `docs/API.md`

### Run Commands

```powershell
pip install -r requirements.txt
streamlit run app.py
uvicorn api:app --host 127.0.0.1 --port 8000
python -m unittest discover -s tests -v
```

### Environment Variables

| Name | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Server-side OpenAI client key. Never expose in UI/API/logs. |
| `AGENT_API_KEY` | External API caller authentication key. Keep separate from OpenAI key. |
| `ENABLE_RAG` | Enable file-based RAG. |
| `RAG_INCLUDE_DATA_DOCS` | Include dataset README/prompt/patch-note files in RAG. |
| `RAG_TOP_K` | Maximum retrieved RAG snippets. |
| `MAX_AGENT_QUERY_CHARS` | Shared UI/API query length limit. |

QAgent는 게임 전투 로그 CSV를 분석해 밸런스 이상 후보를 찾고, OpenAI tool-calling Agent가 근거 조회, 가상 패치 후보, 영향 시나리오, HITL 검토 자료를 생성하는 PoC입니다.

## 실행 준비

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에 서버 내부용 `OPENAI_API_KEY`를 설정합니다. 이 키는 Streamlit UI나 외부 API 응답에 표시되지 않으며, UI 입력값으로도 받지 않습니다.

외부 프로그램에서 API를 호출하려면 `AGENT_API_KEY`도 별도로 설정합니다. `AGENT_API_KEY`는 QAgent API 인증용이며 `OPENAI_API_KEY`와 반드시 분리해서 관리합니다.

## Streamlit UI 실행

```powershell
streamlit run app.py
```

UI 사이드바에는 OpenAI 키 원문이 표시되지 않고 `configured` 또는 `missing` 상태만 표시됩니다. Agent 실행은 서버 환경에 `OPENAI_API_KEY`가 있을 때만 가능합니다.

## API 서버 실행

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

기본 endpoint:

- `GET /health`
- `POST /api/agent/run`

`POST /api/agent/run`은 `Authorization: Bearer <AGENT_API_KEY>` 또는 `X-API-Key: <AGENT_API_KEY>` 헤더가 필요합니다.

요청 예시:

```json
{
  "query": "분석할 질문",
  "model": "gpt-4.1-mini",
  "reasoning_effort": "medium",
  "context": {},
  "stream": false
}
```

응답 예시:

```json
{
  "answer": "...",
  "tool_trace": [],
  "metadata": {
    "model": "gpt-4.1-mini",
    "reasoning_effort": "medium",
    "api_mode": "responses",
    "elapsed_ms": 1234,
    "data_dir": "D:\\IdeaProjects\\QAgent\\data\\lol_assignment_dataset"
  }
}
```

curl 예시:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/run" `
  -H "Authorization: Bearer $env:AGENT_API_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"승률 이상 후보를 요약해줘\",\"model\":\"gpt-4.1-mini\",\"reasoning_effort\":\"medium\",\"context\":{},\"stream\":false}"
```

에러 응답 예시:

```json
{
  "detail": {
    "error": "unauthorized",
    "message": "Invalid API key."
  }
}
```

```json
{
  "detail": {
    "error": "openai_api_key_missing",
    "message": "OPENAI_API_KEY is not configured."
  }
}
```

## 환경변수

| 이름 | 필수 | 설명 |
| --- | --- | --- |
| `OPENAI_API_KEY` | Agent 실행 필수 | 서버 내부 OpenAI 호출용 키. UI/API에 노출하지 않습니다. |
| `AGENT_API_KEY` | 외부 API 필수 | `/api/agent/run` 호출 인증용 키. OpenAI 키와 분리합니다. |
| `OPENAI_MODEL` | 선택 | 기본 모델명 |
| `OPENAI_API_MODE` | 선택 | `auto`, `responses`, `chat_completions` |
| `OPENAI_REASONING_EFFORT` | 선택 | `none`, `low`, `medium`, `high`, `xhigh` 등 |
| `AGENT_DATA_DIR` | 선택 | API 서버가 사용할 CSV 데이터셋 폴더. 기본값은 `data/lol_assignment_dataset` |
| `AGENT_CORS_ORIGINS` | 선택 | 허용할 CORS origin을 쉼표로 구분. 비어 있으면 CORS를 열지 않습니다. |

## 구조

Streamlit UI와 FastAPI endpoint는 같은 Agent 실행 로직을 공유합니다.

1. CSV 5개를 로드합니다.
2. `AnalysisContext`를 만듭니다.
3. `build_tool_functions()`로 tool registry를 구성합니다.
4. `run_generative_agent()`가 서버 환경의 `OPENAI_API_KEY`로 OpenAI client를 만들고 Agent loop를 실행합니다.

## 보안 메모

- `OPENAI_API_KEY`는 서버 내부에서만 읽습니다.
- 외부 API 인증은 `AGENT_API_KEY`로 처리합니다.
- tool trace와 내부 메시지는 `safe_for_log()`를 거쳐 키/토큰 패턴을 마스킹합니다.
- system prompt와 내부 메시지 배열은 API 응답에 포함하지 않습니다.
- 사용자 입력값은 API에서 파일 경로로 사용하지 않습니다. 데이터 폴더 변경은 서버 환경변수 `AGENT_DATA_DIR`로만 합니다.
- Agent 답변은 Markdown으로 표시될 수 있습니다. 신뢰할 수 없는 HTML을 직접 렌더링하지 말고, 외부 프론트엔드에서는 HTML sanitization 정책을 적용하세요.

## 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q qagent_core tests
python -m py_compile app.py api.py
```

API 인증 확인:

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
curl.exe -i -X POST "http://127.0.0.1:8000/api/agent/run" -H "X-API-Key: wrong" -H "Content-Type: application/json" -d "{\"query\":\"test\"}"
```

잘못된 `AGENT_API_KEY`는 `401`을 반환해야 합니다.
