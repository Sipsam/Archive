# Archive

개인 및 팀 프로젝트의 소스 코드와 개발 이력을 통합 보관하는 아카이브 저장소입니다. 수업·스터디·해커톤·개인 실험에서 만든 독립 프로젝트를 한곳에서 찾아보고, 원본 저장소가 없어도 보관된 코드와 브랜치를 열람하기 위해 만들었습니다.

공통 빌드·배포 체계를 사용하는 단일 애플리케이션 모노레포가 아닙니다. 프로젝트마다 실행 환경과 완성도가 다르며, 현재 서비스 운영보다 기록 보존을 중심으로 관리합니다.

## 저장소 특징

- 프로젝트별 디렉터리(prefix)와 브랜치 네임스페이스로 독립 프로젝트를 구분합니다.
- subtree 통합과 추가 브랜치 스냅샷으로 코드 및 도달 가능한 개발 이력을 보관합니다.
- 원본 접근 없이 Archive에서 브랜치 조회와 파일 추출이 가능합니다.
- [통합 관리 도구](scripts/archive-manager.ps1)로 상태 확인·후보 검증·동기화·개별 Push·선택적 백업과 복원을 지원합니다.
- **main의 폴더만으로 전체 구현을 판단하지 마세요.** 브랜치마다 파일 구조와 보관 시점이 다릅니다.

## 프로젝트 목록

main의 Git 트리 기준으로 독립 프로젝트는 11개입니다. 기술은 실제 설정·의존성 또는 소스 import에서 확인한 항목이며 실행 성공을 보증하지 않습니다.

| 프로젝트 | 분류 | 설명 | 주요 기술 | main 코드·자료 |
| --- | --- | --- | --- | --- |
| 2025-01-OpenSWBasicProject | 공공데이터 웹 | 국회 의안과 산업·기업·주가 정보를 조회하는 NAStock | Django, Python, pandas, HTML/JS | [코드](2025-01-OpenSWBasicProject/) |
| 2025-02-OpenSWDevProject | 수업·공동구매 웹 | Java 실습과 별도 브랜치의 공동구매·커뮤니티 서비스 | Java, Spring, JPA, WebSocket, HTML/JS | [실습](2025-02-OpenSWDevProject/) |
| 2026_01_OpenSWWebProject | 건강 기록·AI 웹 | 운동·식단·수면과 AI 코칭을 연결하는 Hill | React, Vite, Flask, SQLAlchemy | [코드](2026_01_OpenSWWebProject/) |
| 2026_04_animal_league | 실험형 학습 웹 | 학습 계획과 집중 방해 설계를 결합한 Utopia Planner | Java 21, Spring Boot, MySQL, Vite | [코드](2026_04_animal_league/) |
| 2026_14th_final_study_BE | 협업 과제 API | 프론트·백 협업용 베이스와 인증·사용자 구현 브랜치 | Java 25, Spring Boot, JPA, JWT | [베이스](2026_14th_final_study_BE/) |
| 2026_KIT_Vibe | 발표 훈련·AI 웹 | 영상 분석 → 음성 Q&A → 코칭 리포트 | React, TypeScript, FastAPI, Gemini, gTTS | [소개·자료](2026_KIT_Vibe/) |
| 2026_likelion_study | 백엔드 스터디 | 회원·게시글 API와 응답·예외 처리 학습 | Java 21, Spring Boot, JPA, MySQL | [코드](2026_likelion_study/) |
| QAgent | 게임 데이터·AI PoC | 전투 로그 기반 밸런스 후보·가상 패치 검토 자료 | Streamlit, pandas, FastAPI, OpenAI SDK | [코드](QAgent/) |
| Remory | 기억 기록·AI 웹 | 기억 자료 기반 페르소나·대화·사진 기억·스토리북 | React, TypeScript, FastAPI, MySQL | [코드](Remory/) |
| WOOWANGTHON_TEAM_49 | 급여 문서·AI 웹 | 근로 문서와 입금 기록을 검토·대조하는 월급잇다 | Next.js, FastAPI, SQLite, LangGraph, PDF/OCR | [코드](WOOWANGTHON_TEAM_49/) |
| legwork_backend | 패션 서비스 API | 상품·주문·OCR·가상 착용·수선 관리 Atelier Lens | Python 3.12, FastAPI, PostgreSQL, PaddleOCR | [코드](legwork_backend/) |

## 프로젝트 상세

### 2025-01-OpenSWBasicProject — NAStock

열린국회 API의 의안 정보를 산업·기업 정보와 함께 탐색하는 웹 프로젝트입니다. 의안 목록·상세·댓글, 공포 법안, 업종별 기업과 주가 조회 API가 있으며 의안 수집·KoBERT 업종 분류 학습 명령도 보관합니다.

- 구성: [frontend](2025-01-OpenSWBasicProject/frontend/)의 HTML/CSS/JavaScript와 [backend](2025-01-OpenSWBasicProject/backend/)의 Django API.
- 기술: requirements의 Django·pandas·PyTorch, 소스 import의 Django REST Framework·FinanceDataReader·Groq·Transformers. requirements가 모든 import를 포함하지 않아 환경 보완이 필요할 수 있습니다.
- 브랜치: `2025-01-OpenSWBasicProject/front`, `2025-01-OpenSWBasicProject/back`.
- 근거: backend README, `nastock/urls.py`, `api/views.py`, `api/management/commands/`.

### 2025-02-OpenSWDevProject — Java 실습·공동구매 서비스

main에는 주차별 Java 실습이 보관됩니다. 별도 frontend/backend 브랜치에는 공동구매 모집·참여, 상품, 커뮤니티, 채팅, 결제·포인트, 문의 메일 구현이 있습니다. 수업 실습과 서비스 스냅샷을 구분해서 열람해야 합니다.

- main 위치: [프로젝트 폴더](2025-02-OpenSWDevProject/).
- 프론트: `2025-02-OpenSWDevProject/frontend` 브랜치의 `2025-02-OpenSWDevProject/frontend/` HTML/CSS/JavaScript.
- 백엔드: `2025-02-OpenSWDevProject/backend` 브랜치의 `2025-02-OpenSWDevProject/src/main/java/`. 소스에서 Spring·JPA·WebSocket·SendGrid를 확인했습니다. 빌드 명세가 보관 트리에 없어 정확한 의존성 버전은 확인되지 않았습니다.
- 추가 브랜치: `2025-02-OpenSWDevProject/main`.
- 근거: 실습 README, 서비스 브랜치 controller/service/repository와 프론트 화면 파일.

### 2026_01_OpenSWWebProject — Hill / No Sweat, No Sweet

분리된 운동·식단·수면 기록을 모아 개인별 코칭을 제공하려는 웹 프로젝트입니다. 운동 세션·즐겨찾기, 음식 사진 분석·영양 목표, 수면·Fitbit 연동, 통계·프로필 화면을 보관합니다.

- 구성: [frontend](2026_01_OpenSWWebProject/frontend/)의 React 18·Vite·Axios와 [backend](2026_01_OpenSWWebProject/backend/)의 Flask·SQLAlchemy·JWT·PyMySQL.
- AI: OpenAI·Anthropic·Google 생성형 AI SDK 의존성과 코칭 서비스 코드. 외부 API 설정이 별도로 필요합니다.
- 브랜치: `2026_01_OpenSWWebProject/main`.
- 근거: README, package.json, requirements.txt, backend `app/services/`, frontend `src/pages/`.

### 2026_04_animal_league — Utopia Planner

시험 과목·난이도·이해도를 입력하고 학습 일정을 관리하는 실험형 웹 프로젝트입니다. 계획 UI에 유동적인 일정과 미디어·게임 팝업 같은 집중 방해 요소를 결합해 시험 기간의 심리적 역설을 표현합니다.

- 기능: 회원가입·JWT 로그인, 사용자별 시험·캘린더, 프로필·학습 통계.
- 구성: [프로젝트 루트](2026_04_animal_league/)의 HTML·assets·pages와 Java `src/`를 함께 보관합니다.
- 기술: Vite, Java 21·Spring Boot 3.5·Security·JPA·MySQL.
- 브랜치: `2026_04_animal_league/main`, `2026_04_animal_league/frontend`, `2026_04_animal_league/backend`.
- 근거: README, Backend_README, package.json, build.gradle, controller/service 코드.

### 2026_14th_final_study_BE — 프론트·백 협업 과제

8주차 협업 과제용 백엔드 베이스입니다. main은 애플리케이션 골격과 빌드 설정 중심이며, `week8/issue-6-jangsungwon`에는 인증·사용자 컨트롤러, 서비스와 테스트가 별도로 있습니다. 최종 서비스 주제는 확인되지 않았습니다.

- 위치: [프로젝트 폴더](2026_14th_final_study_BE/), 주요 구현은 과제 브랜치의 같은 prefix.
- 기술: main build.gradle 기준 Java 25·Spring Boot 4.0.6·Security·JPA·JWT·Swagger, H2와 MySQL 드라이버.
- 브랜치: `2026_14th_final_study_BE/main`, `2026_14th_final_study_BE/week8/issue-6-jangsungwon`.
- 근거: README, build.gradle, main/과제 브랜치 Java 소스.

### 2026_KIT_Vibe — AI Pitch Master / AI Pitch-Perfect

영상 업로드에서 말하기 지표 분석, 음성 답변을 포함한 AI 질의응답, 최종 코칭 리포트로 이어지는 발표 훈련 프로젝트입니다. 세션별 분석·Q&A 이력을 연결하고 타이머·카메라 상태를 관리합니다.

- main 위치: [소개·영상 자료](2026_KIT_Vibe/). README와 테스트 영상 ZIP만 있으며 구현 코드는 별도 브랜치에 있습니다.
- 프론트: `2026_KIT_Vibe/frontend` 브랜치의 `2026_KIT_Vibe/`에 React·TypeScript·Vite·Zustand·TanStack Query·Tailwind CSS.
- 백엔드: `2026_KIT_Vibe/backend` 브랜치의 같은 prefix에 FastAPI·Uvicorn·Pydantic·Google 생성형 AI·gTTS.
- 추가 브랜치: `2026_KIT_Vibe/main`.
- 근거: main README, frontend package.json, backend requirements.txt 및 `main.py`.

### 2026_likelion_study — 백엔드 세션 실습

멋쟁이사자처럼 충북대 백엔드 세션의 학습 코드입니다. 회원 가입·로그인과 게시글 생성·조회·수정 API, JPA 엔티티·DTO·공통 응답·예외 처리 구조를 보관합니다. 독립 프론트엔드는 포함하지 않습니다.

- 위치: [프로젝트 폴더](2026_likelion_study/), `src/main/java/com/likelion/backend/`.
- 기술: Java 21·Spring Boot 4.0.5·Web MVC·JPA·Validation·AOP·Actuator·Swagger·MySQL 드라이버.
- 브랜치: `2026_likelion_study/develop`, `2026_likelion_study/week4/장성원`.
- 근거: README, build.gradle, member/article 컨트롤러·서비스.

### QAgent — 게임 밸런스 분석 에이전트

게임 전투 로그 CSV에서 밸런스 이상 후보를 찾고 사람이 검토할 가상 패치와 영향 시나리오를 만드는 PoC입니다. Streamlit UI·인증된 FastAPI API·OpenAI 도구 호출·파일 기반 RAG·HITL 검토 자료를 보관합니다. 실제 게임 밸런스를 자동 변경하는 서비스로 해석하지 않습니다.

- 위치: [QAgent](QAgent/). `app.py`는 UI, `api.py`는 API, `qagent_core/`는 분석·도구·검토 로직, `data/`는 시나리오 자료입니다.
- 기술: Python·Streamlit·pandas·OpenAI SDK·FastAPI·Uvicorn·requests. 벡터 DB 없이 문서·패치 노트를 검색합니다.
- 브랜치: `QAgent/main`. 공개 원본 URL은 확인되지 않았으며 Archive만으로 접근할 수 있습니다.
- 근거: README, requirements.txt, `qagent_core/`, 시나리오 README.

### Remory — 기억 자료 기반 대화·기록

기억 자료를 대상자 프로필과 AI 페르소나로 연결하는 프로젝트입니다. 대화·사진 기억·인터뷰·스토리북·공유·음성 기능과 검증 요청·동의 기록·삭제 요청을 다룹니다. 음성 제공자의 mock 기본값과 실제 제공자 연동을 구분해야 합니다.

- 구성: [frontend](Remory/frontend/)의 React 19·TypeScript·Vite와 [backend](Remory/backend/)의 FastAPI·SQLAlchemy·Alembic·MySQL·JWT.
- AI/음성: google-genai·faster-whisper 의존성과 speech 서비스 코드. 모든 음성 기능의 실제 운영 동작을 보장하지 않습니다.
- 브랜치: `Remory/main`, `Remory/demo`, `Remory/backend/feat-ai-service`, `Remory/backend/feat-ai-voice-pipeline`, `Remory/backend/feat-consent-log`, `Remory/backend/feat-target-verification`.
- 근거: backend README·requirements, frontend package.json·서비스 모듈. frontend README의 원본 충돌 표식은 보존하고 기능 설명에는 사용하지 않았습니다.

### WOOWANGTHON_TEAM_49 — 월급잇다

근로계약서·근무 기록·급여명세서·입금 내역을 모아 근거를 검토하고 급여 차이를 확인하는 서비스입니다. 다국어 화면, 문서 판독·추출 후 사용자 확정, 계산·대조, 문의 문안과 PDF·ZIP 보고서를 보관합니다. 법적 체불 판정이나 실제 연동·모델·OCR 품질을 보장하지 않습니다.

- 구성: [frontend](WOOWANGTHON_TEAM_49/frontend/)의 Next.js·React·TypeScript·Tailwind CSS·next-intl와 [backend](WOOWANGTHON_TEAM_49/backend/)의 Python 3.14·FastAPI·SQLite·LangGraph·LangChain OpenAI·PDF 처리.
- OCR에는 Tesseract 실행파일·언어 데이터가 필요합니다. frontend 개발용 Mock과 backend의 계산·추출 책임을 구분합니다.
- 브랜치: `WOOWANGTHON_TEAM_49/main`, `WOOWANGTHON_TEAM_49/frontend/*`, `WOOWANGTHON_TEAM_49/backend/fix/agent-review-regressions`. frontend에는 Frontv3·frontv2·통합·수정 스냅샷이 보존되어 있습니다.
- 근거: frontend/backend README, package.json, pyproject.toml, app/agent 소스 구조.

### legwork_backend — Atelier Lens

패션 상품 탐색·구매와 보유 상품 관리를 지원하는 해커톤 백엔드입니다. 인증·게스트·상품·장바구니·주문·모의 결제, 파일 작업·OCR·아바타·가상 착용·코디 추천·손상 진단·수선 예약 API를 보관합니다. 모의 기능과 실제 제공자 연동은 구분해서 확인해야 합니다.

- 위치: [legwork_backend](legwork_backend/), `app/modules/`의 도메인별 API·서비스. 프론트엔드는 포함하지 않습니다.
- 기술: Python 3.12·FastAPI·SQLAlchemy async·PostgreSQL/asyncpg·Alembic·PaddleOCR·OpenCV·OpenAI SDK·Docker Compose.
- 브랜치: `legwork_backend/main`, `legwork_backend/feature/*`, `legwork_backend/chore/*`. OCR·추천·착용·진단·배포·통합 스냅샷을 별도 보관합니다.
- 근거: README, pyproject.toml, requirements.txt, 도메인 모듈과 Docker 실행 설정.

## 디렉터리 구조

```text
Archive/
├── 2025-01-OpenSWBasicProject/  # frontend + backend
├── 2025-02-OpenSWDevProject/    # main: 실습 / 서비스: 별도 브랜치
├── 2026_01_OpenSWWebProject/   # frontend + backend
├── 2026_04_animal_league/      # 웹 화면 + Java src
├── 2026_14th_final_study_BE/   # 협업 과제 베이스
├── 2026_KIT_Vibe/             # main: 소개·자료 / 구현: 별도 브랜치
├── 2026_likelion_study/        # Java API 실습
├── QAgent/                    # UI + API + 분석 코어·데이터
├── Remory/                    # frontend + backend
├── WOOWANGTHON_TEAM_49/        # frontend + backend/agent
├── legwork_backend/           # Python API
├── docs/                      # 운영·감사·보안·검증 문서
├── scripts/                   # 통합 관리 도구·격리 테스트
└── README.md
```

루트의 `archiving_fixed_v4.ps1`, `archive_woowangthon_add.ps1`는 초기 통합 방식의 기록입니다. 일상 관리는 통합 도구와 가이드를 따릅니다.

## 코드 열람과 Git 아카이빙 방식

초기 통합은 `git subtree add --prefix=...`로 코드를 배치하고 원본 이력을 연결했습니다. 분리된 frontend/backend 원본은 하위 prefix로, 추가 브랜치는 프로젝트 네임스페이스의 병합·스냅샷 커밋으로 보관했습니다. 추가 브랜치 가져오기에는 원본 이력을 부모로 연결하는 ours 병합과 prefix 파일 배치도 사용했습니다.

원본 커밋의 루트와 Archive 경로는 다릅니다. Archive 전용 커밋이 추가되며 일부 보안 정리로 영향 커밋·부모 해시가 변경됐습니다. 모든 원본 해시·삭제된 원본 브랜치·LFS payload까지 완벽히 재현한다고 보장하지 않습니다. [감사](docs/archive-audit-report.md), [보안](docs/archive-security-report.md), [과거 최종 검증](docs/archive-final-verification.md)의 수치는 당시 기준입니다. 이번 결과는 [정리 기록](docs/archive-cleanup-report.md)을 참고하세요.

GitHub 브랜치 선택기로 프로젝트 브랜치를 고르면 main과 다른 스냅샷이 보입니다. 로컬에서는 다음과 같이 열람합니다.

```powershell
git clone https://github.com/Sipsam/Archive.git
cd Archive
git branch -a
git ls-tree --name-only origin/2026_KIT_Vibe/frontend -- 2026_KIT_Vibe/
git switch --track origin/2026_KIT_Vibe/frontend
# 작업 트리가 깨끗한 상태에서 돌아오기
git switch main
```

과거 LFS payload 다운로드가 불필요한 열람에서는 clone/checkout 전에 `$env:GIT_LFS_SKIP_SMUDGE='1'`을 설정할 수 있습니다. 이 경우 파일은 포인터로 남습니다.

### 과거 원본 참조

아래 URL은 현재 Git remote 또는 보관 문서에서 확인한 **과거 원본 참조**입니다. 현재 접근 가능 여부는 확인하지 않았습니다. 서로 다른 소유자의 참조는 같은 원본 상태를 뜻하지 않습니다.

| 프로젝트 | 확인된 과거 원본 참조 |
| --- | --- |
| 2025-01-OpenSWBasicProject | [Sipsam/2025-01-OpenSWBasicProject](https://github.com/Sipsam/2025-01-OpenSWBasicProject) |
| 2025-02-OpenSWDevProject | [Sipsam/2025-02-OpenSWDevProject](https://github.com/Sipsam/2025-02-OpenSWDevProject) |
| 2026_01_OpenSWWebProject | [Sipsam/2026_01_OpenSWWebProject](https://github.com/Sipsam/2026_01_OpenSWWebProject) |
| 2026_04_animal_league | [Sipsam](https://github.com/Sipsam/2026_04_animal_league), package.json의 [th0oel](https://github.com/th0oel/animal_league) |
| 2026_14th_final_study_BE | [Sipsam/2026_14th_final_study_BE](https://github.com/Sipsam/2026_14th_final_study_BE) |
| 2026_KIT_Vibe | [Sipsam](https://github.com/Sipsam/2026_KIT_Vibe), README의 [tronve](https://github.com/tronve/2026_KIT_Vibe) |
| 2026_likelion_study | [Sipsam/2026_likelion_study](https://github.com/Sipsam/2026_likelion_study) |
| Remory | [remoryFE](https://github.com/Sipsam/remoryFE), [remoryBE](https://github.com/Sipsam/remoryBE) |
| WOOWANGTHON_TEAM_49 | [frontend](https://github.com/woowangthon/WOOWANGTHON_TEAM_49_FE), [backend](https://github.com/woowangthon/WOOWANGTHON_TEAM_49_BE) |
| legwork_backend | [legworkteam/legwork_backend](https://github.com/legworkteam/legwork_backend) |

QAgent는 로컬 원본에서 가져왔고 공개 URL은 확인되지 않았습니다. 원본 URL 표와 도구의 업데이트 등록 정보는 별개입니다. 현재 [archive-projects.json](docs/archive-projects.json)은 빈 객체이므로 기존 프로젝트 update에는 검토된 source 등록이 먼저 필요합니다.

## 관리 방법과 보관 정책

Windows PowerShell 5.1, Git for Windows, Python 3.9+ 환경에서 루트 기준으로 실행합니다. 자세한 조건·인자는 [운영 가이드](docs/archive-manager-guide.md)를 따릅니다.

```powershell
.\scripts\archive-manager.ps1 fetch
.\scripts\archive-manager.ps1 status
.\scripts\archive-manager.ps1 validate
.\scripts\archive-manager.ps1 sync -WhatIf
.\scripts\archive-manager.ps1 push-safe -WhatIf
```

status는 저장된 origin 추적 참조를 비교하므로 fetch를 먼저 실행합니다. sync는 분기 이력을 자동 병합하지 않으며 push-safe는 기존 원격이 있는 로컬 선행 브랜치만 다룹니다. backup/security 참조는 자동 Push에서 제외됩니다.

1. **신규 추가:** `add -Project ExampleProject -SourceRepo <원본>` 또는 `-FrontendRepo`·`-BackendRepo`로 격리 후보를 만듭니다.
2. **검토·승격:** 반환된 후보를 확인하고 `promote -Candidate <경로> -WhatIf` 후 `-Approve`로 적용합니다. 프로젝트 외 파일·참조 변화·보안 검사를 통과해야 합니다.
3. **증분 갱신:** source 등록 후 `update -Project ExampleProject -WhatIf`로 확인하고 실제 update가 만든 후보를 같은 promote 흐름으로 반영합니다.
4. **원본 없는 추출:** `extract -Project Remory -Branch Remory/main -Destination <새 외부 폴더> -WhatIf`로 검토 후 실행합니다. 파일 스냅샷이며 독립 Git 이력 재구성이 아닙니다.
5. **원격 반영:** 메타데이터를 검토·커밋하고 `push -Branch main -WhatIf` 또는 개별 브랜치를 지정합니다. 신규 로컬 브랜치는 개별 Push가 필요합니다. 강제·mirror·일괄 Push를 사용하지 않습니다.
6. **선택적 백업·복원:** 필요할 때 `backup -Destination <새 외부 폴더>`, `restore -Bundle <bundle> -Destination <새 bare 저장소> -WhatIf`로 검토 후 실행합니다. bundle은 LFS payload·미커밋 파일을 완전히 보존하지 않습니다.

별도 로컬 백업의 상시 유지는 필수가 아닙니다. 다만 **현재 실제 sync 변경·promote 적용은 안전장치로 외부 백업을 자동 생성**하고 add/update도 외부 후보 자료를 만듭니다. 생성을 원하지 않으면 WhatIf와 조회·추출을 사용하고 실제 변경 전 해당 동작을 고려하세요. 백업 생략 인자는 없습니다.

새 프로젝트는 README 목록과 source 메타데이터를 함께 갱신합니다. 주요 브랜치를 보존하고 원본에서 사라진 브랜치를 자동 삭제하지 않습니다. 임시 참조는 정확한 이름·OID·worktree·보안·다른 브랜치와의 관계를 확인한 뒤 명시적으로 정리합니다.

## 주의사항

- 프로젝트마다 의존성·환경변수·DB·외부 API가 다릅니다. 루트에서 모든 앱을 한 번에 빌드하지 않습니다.
- 일부 원본은 접근할 수 없으며 문서의 개발 경로·상태는 과거 시점일 수 있습니다.
- [LFS 누락 목록](docs/archive-lfs-known-missing.json)의 13개 payload는 의도적으로 보존되지 않았습니다. 포인터·이력이 있어도 실제 파일 복원을 보장하지 않습니다.
- 보안상 일부 과거 이력을 정리했습니다. 원본 remote fetch는 옛 비밀정보를 재유입할 수 있어 일반 관리에서는 origin만 조회합니다.
- 제한된 패턴 검사는 모든 비밀정보 부재를 보장하지 않습니다. 기본 security/validate는 reflog의 과거 객체도 검사합니다. Push 전 대상 tip의 전체 도달 이력을 별도 검사합니다.
- 일반 백업 삭제는 물리적 안전 소거가 아닙니다. 로컬 reflog·도달 불가능 객체 잔존과 키 폐기 여부는 별도 사항입니다.
