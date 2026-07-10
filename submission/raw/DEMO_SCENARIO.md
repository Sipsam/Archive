# Game Balance Insight Agent 제출 검수 시나리오

## 1. 제출 검수 목적

이 문서는 발표용 진행 대본이 아니라 제출 검수자가 로컬에서 QAgent의 핵심 기능을 확인하기 위한 실행 시나리오다. 핵심 확인 대상은 사용자 질문, Guardrail 입력 검증, RAG 근거 검색, Tool 선택, 수치 근거, 가상 패치 후보, 한계 자기반성, 사람 검토로 이어지는 흐름이다.

이 데모는 특정 게임의 정답을 맞히는 도구가 아니라, 게임 밸런스 담당자의 데이터 분석과 의사결정 과정을 AI Agent가 어떻게 보조할 수 있는지를 보여주는 프로토타입이다. 핵심 관찰 대상은 “질문 → Tool 선택 → 수치 근거 → 가상 패치 후보 → 한계 자기반성 → 사람 검토”의 연결이다.

실제 OpenAI 호출은 네트워크와 모델 권한에 따라 시간이 달라질 수 있다. 제출 검수에서는 Streamlit 초기 화면, API 인증/검증, RAG metadata, 테스트 결과를 우선 확인하고, 실제 LLM 실행은 제출자의 유효한 key와 사용 가능한 모델이 있을 때 수행한다.

## 2. 사전 준비

- Python과 인터넷 연결
- OpenAI API 사용 권한과 `OPENAI_API_KEY`
- 외부 API endpoint를 확인할 경우 `AGENT_API_KEY`
- 저장소의 `data/lol_assignment_dataset/` 아래 필수 CSV 5개
- 새 데이터를 수집할 때만 `RIOT_API_KEY`; 포함된 CSV로 데모할 때는 불필요

PowerShell 기준:

```powershell
cd D:\IdeaProjects\QAgent
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에서 최소 다음을 설정한다.

```dotenv
OPENAI_API_KEY=본인의_OpenAI_key
AGENT_API_KEY=제출검수용_API_key
OPENAI_MODEL=gpt-5.4
OPENAI_API_MODE=responses
OPENAI_REASONING_EFFORT=none
ENABLE_RAG=true
RAG_INCLUDE_DATA_DOCS=true
RAG_TOP_K=4
MAX_AGENT_QUERY_CHARS=12000
```

키를 Markdown, 소스 코드, 화면 캡처에 노출하지 않는다. 현재 UI에는 `OpenAI API Key` 원문 입력창이 없고, 서버 환경의 key 설정 상태만 표시한다. 모델명은 코드의 기본값이지만 실제 계정에서 사용할 수 있는 모델로 바꿀 수 있다.

## 3. 데이터 준비와 설명

`data/lol_assignment_dataset/`에는 다음 파일이 있어야 한다.

```text
battle_logs.csv
characters.csv
skills.csv
equipment_sets.csv
patch_notes.csv
```

제출 데이터 요약 기준으로 1,042개 경기, 10,420개 참가자 행, 캐릭터 175행, 스킬 845행, 아이템 333행, 패치노트 40,272행이다. 개인 식별용 원본 필드가 일부 데이터셋 컬럼에 남아 있으므로 공개 시연에서는 참가자 원본 행 대신 집계 결과를 중심으로 보여준다.

## 4. 실행

```powershell
streamlit run app.py
```

브라우저에 열린 로컬 Streamlit 주소로 접속한다. 앱 제목은 `Battle Balance Analyst Generative AI Agent v2.8.0`이다.

외부 API endpoint까지 검수할 경우 별도 터미널에서 다음을 실행한다.

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

인증 실패와 입력 Guardrail은 실제 OpenAI 호출 없이도 확인할 수 있다.

```powershell
curl.exe -i -X POST "http://127.0.0.1:8000/api/agent/run" `
  -H "X-API-Key: wrong" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"test\"}"
```

기대 결과는 `401 Unauthorized`다. 빈 query 또는 너무 긴 query는 `400`을 반환해야 한다. 정상 응답에는 `rag_status`, `rag_sources`, `guardrail_warnings`, `execution_nodes` metadata가 포함된다.

## 5. 정상 데모 절차

### 단계 1. 설정 확인

왼쪽 `LLM Agent 설정`에서 다음을 확인한다.

- `Model`: 계정에서 사용 가능한 모델
- `Reasoning effort`: 빠른 데모는 `none`
- `OpenAI API 방식`: `Responses API` 또는 `자동`
- `권장 최소 표본 수`: 30
- `권장 검토 후보 승률 기준`: 0.75
- `권장 평균 대비 차이`: 0.20

UI에 표시되는 `실행 예정 API`를 말로 확인한다. reasoning을 높이면 자동 모드가 Responses API를 택할 수 있지만, 결과 품질이 항상 단조롭게 개선된다고 단정하지 않는다.

### 단계 2. 데이터 연결

`1. 데이터 입력`에서 `LoL 데이터`를 선택한다. 다음을 보여준다.

- 데이터셋 요약 JSON
- `데이터 로드 완료`
- `로드된 컬럼 확인`
- `전투 로그 미리보기`
- `현재 데이터 프로필: League of Legends`

이때 특정 캐릭터 공략을 설명하지 않는다. 공개되고 구조화된 경쟁형 게임 데이터로 업무 흐름을 검증한다는 점만 설명한다.

### 단계 3. Agent 목표 확인

`2. Agent 목표 입력`의 기본 프롬프트를 유지한다. 프롬프트에는 데이터 개요, 후보 탐지, 집계, 패치·세그먼트 분석, 관련 지식, 스탯 근사, 조정 후보, 위험, 재테스트, 가상 패치, 시나리오, 자기반성 순서가 명시되어 있다.

제출 검수 시 입력 예시는 다음과 같이 요약한다.

> 최소 30전, 승률 0.75 이상, 전체 평균 대비 0.20 이상인 조합을 추가 검토 후보로 찾고 패치·티어별 근거, 보수적 조정 후보와 재테스트 조건을 제시하라. 데이터에 없는 픽률·밴률은 만들지 말라.

### 단계 4. Agent 실행

`생성형 AI Agent 실행` 버튼을 누른다. `3. 실시간 Agent 실행 상태`에서 모델이 Tool을 선택하고 결과를 다시 읽는 과정을 보여준다. 기본 안전 제한은 반복 18회, Tool 30회, 180초다.

### 단계 5. Trace 확인

`4. Agent Tool Call Trace 상세`에서 2~3개 항목을 연다.

- 입력 요약
- 출력 요약
- 성공/실패 상태
- 실행 시간(ms)
- 안전 처리된 인자와 결과 JSON

특히 `get_dataset_overview`, `detect_anomalies`, `analyze_patch_impact`, `analyze_segment_performance`가 호출됐다면 “언어모델의 기억이 아니라 로컬 데이터 계산 결과를 근거로 사용한다”는 점을 강조한다. Tool 호출 순서는 모델과 데이터에 따라 달라질 수 있다.

### 단계 6. 최종 분석 해석

`5. 생성형 AI Agent 최종 분석`에서 다음을 확인한다.

- 후보가 “확정된 밸런스 오류”가 아니라 “추가 검토 후보”로 표현됐는가
- 표본 수와 승률·평균 차이가 Tool 결과와 일치하는가
- 패치 전후, 티어/세그먼트 차이가 제시됐는가
- 다중 비교, 표본, 교란변수 한계를 언급했는가
- 데이터에 없는 픽률·밴률을 생성하지 않았는가

후보가 없다는 결과도 정상이다. 임계값을 통과한 후보가 없음을 보여주는 것이 임의의 문제를 만드는 것보다 올바른 동작이다.

### 단계 7. 가상 패치 영향 추론

`6. Virtual Patch Scenario Estimate & HITL Review Gate`에서 다음을 확인한다.

- `가상 패치노트 후보`
- `가정 기반 영향 시나리오 추정`
- 현재와 시나리오 승률·평균 피해량
- conservative/baseline/aggressive 민감도 행
- 시나리오 상세 JSON의 가정·경고

예시 설명:

> Agent는 현재 승률과 전체 평균 차이, 사람이 검토할 위험 수준과 조정 강도를 입력으로 제한된 승률·피해량 변화 가정을 만든다. 이 값은 인과 예측이나 게임 엔진 시뮬레이션이 아니라, 후보안의 방향과 민감도를 토론하기 위한 휴리스틱 시나리오다.

실제 수치는 실행 결과를 그대로 읽고, 사전에 고정된 수치를 암기해 말하지 않는다.

### 단계 8. 자기반성 확인

`Agent 자기반성`에서 다음을 확인한다.

- `Agent 권고`
- `긍정 근거`
- `우려/한계`
- 과조정, 표본 부족, 티어별 부작용, 추가 검증 필요성

가상 패치노트는 생성됐지만 시나리오나 자기반성 호출이 빠진 경우 앱이 두 Tool을 자동 보완한다. 가상 패치노트 자체가 없으면 UI는 결과 없음 경고를 표시하며 임의 후보를 자동 생성하지 않는다.

### 단계 9. Human Review 기록

`Human Review 입력`에서 다음 예시로 저장한다.

- 검토자: `QA/밸런스 담당자`
- 검토 상태: `Retest Required`
- 사람이 판단한 최종 리스크: 실행 결과에 따라 `Medium` 또는 `High`
- 후속 액션: `추가 데이터 수집` 또는 `재테스트 진행`
- 후속 담당: `QA / Balance Designer`
- 의견: 표본·티어·패치노트 근거를 더 확인해야 한다는 내용

`가상 패치 HITL 검토 로그 저장`을 누른다. SQLite가 기준 저장소이고 CSV/JSON은 호환 출력이다. `Approve Virtual Patch`를 선택해도 실제 게임 패치는 적용되지 않는다.

## 6. 실패 시나리오

| 상황 | 예상 UI/동작 | 제출 검수에서의 해석 |
|---|---|---|
| API 키 없음 | 실행 시 `OpenAI API Key가 필요` 오류 후 중단 | 비인가 LLM 호출 방지 |
| 필수 CSV 또는 컬럼 누락 | 로드 오류 또는 누락 컬럼 표시 후 중단 | schema validation 필요성 |
| 너무 좁은 필터·표본 부족 | Tool이 `empty` 또는 후보 없음 반환 | 억지 결론 대신 추가 수집 |
| Tool 미호출 | `Tool call이 발생하지 않았습니다` 경고 | 프롬프트 수정·재실행 필요 |
| Tool 인자 오류·제한 초과 | Trace에 안전한 오류/timeout | 실패를 근거처럼 사용하지 않음 |
| 가상 패치노트 없음 | 검토 자료 없음 경고 | 자동 창작하지 않고 재실행 판단 |
| API/네트워크 실패 | `Agent 실행 실패` 메시지 | 모델·권한·네트워크 확인 |
| CSV/JSON mirror 실패 | SQLite 저장 성공 여부와 mirror 경고 구분 | 기준 저장소와 부가 출력 분리 |

## 7. 데모에서 강조할 포인트

1. 주제는 특정 게임 분석이 아니라 라이브 서비스 밸런스 업무의 의사결정 지원이다.
2. LLM은 직접 수치를 계산하는 대신 Tool을 선택하고 구조화된 결과를 해석한다.
3. 현재 구현이 제공하지 않는 픽률·밴률·커뮤니티 감성은 결과로 만들지 않는다.
4. 가상 패치 영향은 경계가 있는 휴리스틱이며 실제 미래 예측이 아니다.
5. 자기반성과 Trace는 과신을 줄이지만 정확성을 보장하지 않는다.
6. 최종 판단과 실제 적용은 사람, QA, 내부 리뷰의 책임이다.
