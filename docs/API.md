# QAgent 외부 API 명세

## 인증

`POST /api/agent/run`은 `AGENT_API_KEY` 인증이 필요합니다.

지원 헤더:

```http
Authorization: Bearer <AGENT_API_KEY>
```

또는

```http
X-API-Key: <AGENT_API_KEY>
```

`AGENT_API_KEY`는 외부 호출 인증용 키이며, OpenAI 호출용 `OPENAI_API_KEY`와 분리해야 합니다.

## POST /api/agent/run

QAgent를 실행하고 최종 답변과 tool trace를 반환합니다. Streamlit UI와 동일한 `run_generative_agent()` 실행 로직을 공유합니다.

요청:

```json
{
  "query": "분석할 질문",
  "model": "gpt-4.1-mini",
  "reasoning_effort": "medium",
  "context": {},
  "stream": false
}
```

필드:

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `query` | string | 예 | Agent에게 전달할 질문 또는 업무 지시 |
| `model` | string | 아니오 | OpenAI 모델명. 기본값은 `OPENAI_MODEL` |
| `reasoning_effort` | string | 아니오 | `none`, `low`, `medium`, `high`, `xhigh` 등 |
| `context` | object | 아니오 | 추가 호출 컨텍스트. 비밀값을 넣지 마세요. |
| `stream` | boolean | 아니오 | 현재 `false`만 지원 |

응답:

```json
{
  "answer": "...",
  "tool_trace": [],
  "metadata": {
    "model": "gpt-4.1-mini",
    "reasoning_effort": "medium",
    "api_mode": "responses",
    "elapsed_ms": 1234,
    "data_dir": "D:\\IdeaProjects\\QAgent\\data\\lol_assignment_dataset",
    "rag_status": "ok",
    "rag_sources": [
      {
        "source": "docs/API.md",
        "section": "POST /api/agent/run",
        "score": 0.42,
        "injection_signals": []
      }
    ],
    "guardrail_warnings": [],
    "execution_nodes": [
      "input_validation",
      "rag_search",
      "rag_context_attached",
      "dataset_load",
      "tool_registry_build",
      "agent_run",
      "output_guardrail"
    ]
  }
}
```

curl:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/run" `
  -H "Authorization: Bearer $env:AGENT_API_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"분석할 질문\",\"model\":\"gpt-4.1-mini\",\"reasoning_effort\":\"medium\",\"context\":{},\"stream\":false}"
```

## 에러 응답

잘못된 API 키:

```json
{
  "detail": {
    "error": "unauthorized",
    "message": "Invalid API key."
  }
}
```

서버에 `AGENT_API_KEY`가 없는 경우:

```json
{
  "detail": {
    "error": "agent_api_key_missing",
    "message": "AGENT_API_KEY is not configured."
  }
}
```

서버에 `OPENAI_API_KEY`가 없는 경우:

```json
{
  "detail": {
    "error": "openai_api_key_missing",
    "message": "OPENAI_API_KEY is not configured."
  }
}
```

`stream=true` 요청:

```json
{
  "detail": {
    "error": "stream_not_supported",
    "message": "Streaming is not implemented for this endpoint."
  }
}
```

## Guardrail and RAG Metadata

Guardrail validation failure:

```json
{
  "detail": {
    "error": "empty_query",
    "message": "query must not be empty."
  }
}
```

RAG is file-based and optional. When enabled, `metadata.rag_status` is `ok`, `insufficient_evidence`, or `disabled`. `rag_sources` contains source file and section names only; server secrets and system prompts are not returned.

## Environment Variables

| Name | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Server-side OpenAI key. Never returned to UI/API/logs. |
| `AGENT_API_KEY` | External API authentication key. |
| `ENABLE_RAG` | Enables file-based RAG. |
| `RAG_INCLUDE_DATA_DOCS` | Includes `data/**` README, prompt, and patch-note files in RAG. |
| `RAG_TOP_K` | Maximum number of RAG snippets. |
| `MAX_AGENT_QUERY_CHARS` | Query length guardrail for UI/API. |

## CORS

기본값은 CORS 미설정입니다. 브라우저 프론트엔드에서 직접 호출해야 하는 경우에만 `AGENT_CORS_ORIGINS`에 허용 origin을 쉼표로 구분해 넣습니다.

```dotenv
AGENT_CORS_ORIGINS=http://localhost:3000,https://example.com
```

## 보안 주의

- `OPENAI_API_KEY`는 서버 내부 OpenAI client 생성에만 사용됩니다.
- API 응답에는 system prompt, 내부 메시지 배열, API key가 포함되지 않습니다.
- tool trace는 마스킹된 값만 반환하도록 처리합니다.
- 사용자 입력값은 API에서 파일 경로, shell command, SQL에 직접 사용하지 않습니다.
- Markdown/HTML 렌더링을 외부 프론트엔드에서 수행할 때는 신뢰할 수 없는 HTML을 sanitize 하세요.
