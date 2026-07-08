# 납품 체크리스트

이 문서는 내부 시연·과제용 PoC 납품 패키지를 만들고 실행할 때 사용하는 체크리스트입니다.

## 실행 전 준비사항

- Windows PowerShell 또는 동등한 명령 실행 환경
- Python 3.12 권장
- OpenAI API 사용 권한과 유효한 API 키
- Riot 데이터를 새로 수집할 경우에만 Riot API 키
- 외부 API 호출이 가능한 네트워크

## 패키지 설치

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

기존 개발자의 `venv/` 또는 `.venv/`를 복사하지 말고 수신 환경에서 새로 생성합니다.

## 환경변수 설정

```powershell
Copy-Item .env.example .env
```

로컬 `.env`에서 필요한 값을 설정합니다.

- `OPENAI_API_KEY`: Agent 실행에 필요
- `RIOT_API_KEY`: Riot API 신규 수집에만 필요
- `OPENAI_MODEL`: 기본 모델명
- `OPENAI_API_MODE`: `responses` 또는 지원되는 API 방식
- `OPENAI_REASONING_EFFORT`: 모델 추론 강도. 기본값은 `none`
- `MAX_AGENT_ITERATIONS`, `MAX_TOOL_CALLS`, `AGENT_TIMEOUT_SECONDS`: 실행 안전 제한
- `ENABLE_TOOL_TRACE`, `ENABLE_DEBUG_LOG`: 안전 처리된 Trace 및 오류 표시 설정

실제 키가 들어 있는 `.env`는 납품 압축파일, 저장소, 보고서에 포함하지 않습니다.

## 데이터 파일 위치

기본 실행 데이터는 `data/lol_assignment_dataset/`에 있으며 다음 파일 5개가 필요합니다.

- `battle_logs.csv`
- `characters.csv`
- `skills.csv`
- `equipment_sets.csv`
- `patch_notes.csv`

`dataset_summary.json`과 `app_conversion_summary.json`은 데이터 설명용으로 함께 전달합니다.

다음 데이터는 기본 앱 실행에 필요하지 않으며 납품에서 제외합니다.

- `data/riot_dataset/`: API 수집 원본 및 중간 결과
- `data/lol_assignment_dataset/extras/`: 계정, 매치 ID, 수집 로그 및 추가 집계
- `data/human_review/`: 개인 검토자 이름·의견을 포함할 수 있는 실행 결과

## 실행 명령어

```powershell
streamlit run app.py
```

브라우저에서 Streamlit이 안내하는 로컬 주소로 접속합니다. OpenAI 키가 없으면 데이터 미리보기는 가능하지만 Agent 실행은 할 수 없습니다.

## 테스트 명령어

```powershell
python -m unittest discover -s tests -v
python -m py_compile app.py fetchMatch.py fetchPatches.py build_lol_assignment_dataset.py generateDemoData.py scripts\refresh_dataset_summary.py
python -m compileall -q qagent_core tests
python scripts\refresh_dataset_summary.py
python scripts\smoke_test_api.py
```

마지막 명령은 현재 전달 CSV를 기준으로 데이터 요약을 다시 작성합니다.

## 보안 확인 사항

- `.env`, `OPENAI_API_KEYS.txt`, `.streamlit/secrets.toml`이 없는지 확인
- API 키와 토큰 형태의 문자열을 전체 납품 폴더에서 검색
- `venv/`, `.venv/`, `__pycache__/`, `.pytest_cache/` 제외
- `*.log`, `*.tmp`, `*.bak`, `*.lock` 제외
- `.idea/`, `.vscode/` 등 개인 IDE 설정 제외
- `data/human_review/` 및 `data/riot_dataset/` 제외
- `data/lol_assignment_dataset/extras/` 제외
- 노출 가능성이 있었던 기존 API 키는 폐기·재발급
- 압축파일을 별도 임시 위치에서 풀어 파일 목록을 다시 확인

## 현재 한계

- 가상 패치 영향은 예측 모델이나 게임 엔진 결과가 아니라 휴리스틱 기반 시나리오 추정입니다.
- Wilson 신뢰구간을 사용하지만 다중 비교, 픽률·밴률, 숙련도, 상대 조합을 모두 통제하지 않습니다.
- HITL 기록은 단일 서버 PoC용 SQLite와 CSV/JSON 호환 산출물이며 중앙 감사 저장소가 아닙니다.
- Agent 결과는 자동 패치 승인 또는 라이브 적용에 사용하면 안 됩니다.
- 실제 OpenAI/Riot API 연결은 수신자가 자신의 키와 네트워크 환경에서 확인해야 합니다.

## 납품 전 체크박스

- [ ] Python 3.12 신규 환경에서 설치 확인
- [ ] 자동 테스트 전체 통과
- [ ] `py_compile` 통과
- [ ] Streamlit 기본 화면 기동 확인
- [ ] 기본 데이터 CSV 5개 존재 확인
- [ ] `dataset_summary.json`과 실제 CSV 행 수 일치 확인
- [ ] `.env` 제외 확인
- [ ] `OPENAI_API_KEYS.txt` 제외 확인
- [ ] 가상환경·캐시·로그·임시 파일 제외 확인
- [ ] Riot 수집 원본·extras·HITL 기록 제외 확인
- [ ] 보고서/PDF/PPT가 현재 v2.8.0 코드와 일치하는지 별도 검토
- [ ] 압축 해제 후 최종 파일 목록 재검토
- [ ] 수신자에게 `.env.example` 기반 설정 방법 안내
