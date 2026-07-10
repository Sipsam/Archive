# Security Notes

## 적용된 Guardrail

- API key 분리: `OPENAI_API_KEY`는 OpenAI 호출 전용, `AGENT_API_KEY`는 외부 API 인증 전용.
- API 인증: `Authorization: Bearer <AGENT_API_KEY>` 또는 `X-API-Key`.
- 입력 검증: 빈 query, 너무 긴 query, 잘못된 model 문자열, 잘못된 `reasoning_effort` 차단.
- 출력 마스킹: OpenAI/Riot/Bearer key 형태와 현재 환경변수 secret 값은 API/UI 출력 전 `[REDACTED]` 처리.
- 로그/trace 마스킹: tool 입력/출력 trace는 `safe_for_log()`를 거친다.
- API metadata: `rag_status`, `rag_sources`, `guardrail_warnings`, `execution_nodes`를 반환하되 secret, system prompt, raw internal message는 반환하지 않는다.
- Tool allowlist: Agent는 `build_tool_functions()`가 등록한 tool 이름만 실행할 수 있다.
- 파일 경로 제한: RAG는 repository root 내부의 문서/데이터 설명 파일만 읽고, 요청 body에서 임의 경로를 받지 않는다.
- RAG prompt injection 완화: 검색 문서는 “비신뢰 근거”로 prompt에 주입되고, 문서 내 지시문 패턴은 metadata에 표시한다.

## OWASP LLM Top 10 2025 점검

OWASP GenAI Security Project의 2025 분류를 기준으로 점검했다.

| 항목 | 현재 위험 | 대응 |
| --- | --- | --- |
| LLM01 Prompt Injection | 사용자 query와 RAG 문서가 모델 지시를 교란할 수 있음 | 의심 패턴 탐지, RAG 비신뢰 컨텍스트 래핑, system prompt와 문서 분리 |
| LLM02 Sensitive Information Disclosure | API key, system prompt, 내부 trace 노출 위험 | secret UI 미노출, output masking, safe trace, API metadata 제한 |
| LLM03 Supply Chain Vulnerabilities | 외부 패키지와 OpenAI SDK 의존 | 의존성 최소 유지. LangChain/LangGraph 미도입으로 공격면 증가 억제 |
| LLM04 Data and Model Poisoning | `docs/`, `data/` 문서가 오염되면 RAG 근거 오염 가능 | RAG 출처 metadata 제공, 문서 지시문 비신뢰 처리. 문서 변경 리뷰 필요 |
| LLM05 Improper Output Handling | Streamlit `st.markdown()`이 LLM output을 렌더링 | HTML 직접 삽입은 하지 않음. 외부 HTML 렌더링 기능 추가 시 escape 필요 |
| LLM06 Excessive Agency | Agent가 tool을 반복 호출하며 비용/시간 증가 가능 | `MAX_AGENT_ITERATIONS`, `MAX_TOOL_CALLS`, `AGENT_TIMEOUT_SECONDS` 제한 |
| LLM07 System Prompt Leakage | 사용자가 system prompt 공개를 요청할 수 있음 | prompt leakage 패턴 탐지, system prompt/API key를 API 응답에 포함하지 않음 |
| LLM08 Vector and Embedding Weaknesses | 벡터 DB는 없지만 RAG 검색 오염 가능 | 파일 기반 allowlist 검색, source metadata, 임의 경로 차단 |
| LLM09 Misinformation | 모델이 tool 근거 없는 수치를 만들 수 있음 | system prompt와 평가 테스트에서 tool grounding 요구, RAG는 근거 부족 상태 표시 |
| LLM10 Unbounded Consumption | 긴 query, 무제한 tool loop, 큰 문서 검색 위험 | query 길이 제한, RAG top-k/파일 크기 제한, tool/time limit |

## 보류 항목

- Secret scanner 또는 dependency vulnerability scanner는 CI가 없어 문서화만 했다. 제출 전 `pip-audit` 또는 GitHub Dependabot 도입을 권장한다.
- RAG 문서 무결성 서명은 과제 규모에서는 과하다. 대신 문서 변경 리뷰와 metadata 출처 표시를 사용한다.
- 별도 LLM guard model은 비용과 의존성이 커서 제외했다.

## 운영 주의

- `.env`, `.streamlit/secrets.toml`, API key 파일은 커밋하지 않는다.
- 외부에 API를 공개할 때는 HTTPS reverse proxy와 rate limit을 추가한다.
- `st.markdown()`에 LLM output을 표시하므로, `unsafe_allow_html=True`를 사용하지 않는다.

## 관련 환경변수

- `OPENAI_API_KEY`: 서버 내부 OpenAI 호출 전용.
- `AGENT_API_KEY`: 외부 API 인증 전용.
- `ENABLE_RAG`: 파일 기반 RAG 활성화 여부.
- `RAG_INCLUDE_DATA_DOCS`: 데이터셋 README/prompt/patch-note 검색 포함 여부.
- `RAG_TOP_K`: RAG 검색 결과 개수 제한.
- `MAX_AGENT_QUERY_CHARS`: UI/API query 길이 제한.
