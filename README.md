# QAgent — LoL 게임 밸런스 분석 AI Agent

게임 전투 로그를 분석해 밸런스 검토 후보를 찾고, 패치·세그먼트 근거와 가상 조정 시나리오를 Human-in-the-loop(HITL) 검토로 전달하는 PoC입니다.

**현재 버전**: v2.8.0

## 빠른 실행

### 준비

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 OPENAI_API_KEY 설정
```

### 실행

```powershell
streamlit run app.py
```

로컬 Streamlit 주소로 접속합니다.

## 주요 기능

- LoL 및 가상 RPG CSV 데이터 로딩·정규화
- 패치/챔피언/아이템/포지션 조합별 밸런스 검토 후보 탐지
- 95% Wilson 승률 신뢰구간 기반 통계 검증
- OpenAI Tool calling을 통한 Agent 흐름 실행 및 Trace 표시
- 가상 패치 후보, 가정 기반 영향 시나리오, Agent 자기반성 생성
- Human-in-the-loop 검토: 승인·반려·재테스트 기록 저장

## 폴더 구조

```
QAgent/
├── app.py                      # Streamlit 메인 진입점
├── qagent_core/                # 핵심 로직 (tools, agent, review, ...)
├── data/                       # 데이터 저장소
│   ├── lol_assignment_dataset/ # 기본 샘플 데이터 (CSV 5개)
│   └── human_review/           # 실행 중 생성되는 HITL 기록
├── tests/                      # 자동 테스트
├── scripts/                    # 유틸리티 스크립트
├── docs/                       # 상세 문서
├── report/                     # 제출용 보고서 (PDF, PPT, DOCX)
├── requirements.txt            # Python 의존성
├── .env.example                # 환경변수 템플릿
└── README.md                   # 이 파일
```

자세한 구조는 [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)를 참고하세요.

## 테스트

```powershell
# 자동 테스트
python -m unittest discover -s tests -v

# 문법 검사
python -m py_compile app.py generateDemoData.py build_lol_assignment_dataset.py
python -m compileall -q qagent_core tests

# 추가 검사
python scripts/check_encoding.py
python scripts/smoke_test_api.py
```

## 주요 문서

자세한 내용은 docs 폴더의 다음 파일들을 참고하세요:

| 문서 | 설명 |
|------|------|
| [docs/RUN.md](docs/RUN.md) | 상세 실행 가이드 및 환경 설정 |
| [docs/DELIVERY_CHECKLIST.md](docs/DELIVERY_CHECKLIST.md) | 납품 체크리스트 및 보안 확인 |
| [docs/SUBMISSION_NOTES.md](docs/SUBMISSION_NOTES.md) | 프로젝트 목적, 기능, 한계 |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 전체 디렉토리 구조 및 각 폴더 설명 |
| [docs/review/](docs/review/) | 코드 리뷰, 리팩토링 가이드 |
| [docs/evaluation/](docs/evaluation/) | Agent 평가 결과 |
| [docs/performance/](docs/performance/) | 성능 분석 및 벤치마크 |

## 보안 주의사항

- `.env` 파일은 절대 커밋하지 마세요. `.env.example`에서 로컬 설정합니다.
- `OPENAI_API_KEY`와 `RIOT_API_KEY`는 환경변수로만 관리합니다.
- `data/human_review/`, `data/riot_dataset/` 등 실행 결과는 `.gitignore` 대상입니다.
- 보고서(PDF, PPT, DOCX)는 코드와 별도 산출물입니다.

자세한 보안 정책은 [docs/DELIVERY_CHECKLIST.md](docs/DELIVERY_CHECKLIST.md#보안-확인-사항)를 참고하세요.

## 데이터 구조

기본 LoL 데이터는 `data/lol_assignment_dataset/`에 있으며 다음 파일 5개가 필수입니다:

```text
battle_logs.csv
characters.csv
skills.csv
equipment_sets.csv
patch_notes.csv
```

데이터 파이프라인의 정규화 순서와 상세 정보는 [docs/review/](docs/review/) 문서를 참고하세요.

## Agent 분석 흐름

1. 데이터 개요 및 품질 확인
2. 최소 표본·승률·95% Wilson 구간으로 검토 후보 탐지
3. 패치 전후 및 세그먼트 분석
4. 관련 캐릭터·아이템·패치 지식 조회
5. 조정 후보와 위험·재테스트 계획 작성
6. 가상 패치 및 가정 기반 영향 시나리오 산출
7. Agent 자기반성 후 사람 검토로 이관

Tool 출력은 근거를 제공하지만 통계적 밸런스 이상을 확정하지 않습니다.

## 현재 한계

- 가상 패치 영향은 휴리스틱 시나리오이며 게임 엔진 시뮬레이션이 아닙니다.
- Wilson 신뢰구간은 다중 비교, 픽률·밴률, 숙련도, 상대 조합을 모두 통제하지 않습니다.
- HITL 기록은 단일 서버 PoC용 SQLite이며 중앙 감사 저장소가 아닙니다.
- Agent 결과는 자동 패치 승인이나 라이브 적용에 사용하면 안 됩니다.

더 자세한 내용은 [docs/SUBMISSION_NOTES.md](docs/SUBMISSION_NOTES.md)를 참고하세요.

---

**시작하기**: [docs/RUN.md](docs/RUN.md)를 읽은 후 `streamlit run app.py`로 실행하세요.
