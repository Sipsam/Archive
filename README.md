# Archive

수업·스터디·해커톤·개인 실험에서 만든 11개 프로젝트의 코드와 개발 이력을 한곳에 보관합니다. 공공데이터 웹부터 AI 발표 코칭, 기억 기록, 급여 문서 검토까지 프로젝트별 목적과 구현을 살펴볼 수 있습니다.

## Projects

프로젝트 이름은 상세 소개로, 코드 링크는 Archive에 보관된 실제 구현으로 연결됩니다.

| 프로젝트 | 설명 | 주요 기술 | 코드 |
| --- | --- | --- | --- |
| [2025-01-OpenSWBasicProject — NAStock](#project-01) | 국회 의안과 산업·기업·주가 정보를 조회하는 NAStock | Django, Python, pandas, HTML/JS | [코드](https://github.com/Sipsam/Archive/tree/main/2025-01-OpenSWBasicProject/) |
| [2025-02-OpenSWDevProject](#project-02) | Java 실습과 별도 브랜치의 공동구매·커뮤니티 서비스 | Java, Spring, JPA, WebSocket, HTML/JS | [프론트엔드](https://github.com/Sipsam/Archive/tree/2025-02-OpenSWDevProject%2Ffrontend/2025-02-OpenSWDevProject/frontend/) · [백엔드](https://github.com/Sipsam/Archive/tree/2025-02-OpenSWDevProject%2Fbackend/2025-02-OpenSWDevProject/src/main/java/) |
| [2026_01_OpenSWWebProject — Hill / No Sweat, No Sweet](#project-03) | 운동·식단·수면과 AI 코칭을 연결하는 Hill | React, Vite, Flask, SQLAlchemy | [코드](https://github.com/Sipsam/Archive/tree/main/2026_01_OpenSWWebProject/) |
| [2026_04_animal_league — Utopia Planner](#project-04) | 학습 계획과 집중 방해 설계를 결합한 Utopia Planner | Java, Spring Boot, MySQL, Vite | [코드](https://github.com/Sipsam/Archive/tree/main/2026_04_animal_league/) |
| [2026_14th_final_study_BE](#project-05) | 프론트·백 협업용 베이스와 인증·사용자 구현 브랜치 | Java, Spring Boot, JPA, JWT | [인증·사용자 구현](https://github.com/Sipsam/Archive/tree/2026_14th_final_study_BE%2Fweek8%2Fissue-6-jangsungwon/2026_14th_final_study_BE/) |
| [2026_KIT_Vibe — AI Pitch Master / AI Pitch-Perfect](#project-06) | 영상 분석 → 음성 Q&A → 코칭 리포트 | React, TypeScript, FastAPI, Gemini, gTTS | [프론트엔드](https://github.com/Sipsam/Archive/tree/2026_KIT_Vibe%2Ffrontend/2026_KIT_Vibe/) · [백엔드](https://github.com/Sipsam/Archive/tree/2026_KIT_Vibe%2Fbackend/2026_KIT_Vibe/) |
| [2026_likelion_study](#project-07) | 회원·게시글 API와 응답·예외 처리 학습 | Java, Spring Boot, JPA, MySQL | [코드](https://github.com/Sipsam/Archive/tree/main/2026_likelion_study/) |
| [QAgent](#project-08) | 전투 로그 기반 밸런스 후보·가상 패치 검토 자료 | Streamlit, pandas, FastAPI, OpenAI SDK | [코드](https://github.com/Sipsam/Archive/tree/main/QAgent/) |
| [Remory](#project-09) | 기억 자료 기반 페르소나·대화·사진 기억·스토리북 | React, TypeScript, FastAPI, MySQL | [코드](https://github.com/Sipsam/Archive/tree/main/Remory/) |
| [WOOWANGTHON_TEAM_49 — 월급잇다](#project-10) | 근로 문서와 입금 기록을 검토·대조하는 월급잇다 | Next.js, FastAPI, SQLite, LangGraph, PDF/OCR | [코드](https://github.com/Sipsam/Archive/tree/main/WOOWANGTHON_TEAM_49/) |
| [legwork_backend — Atelier Lens](#project-11) | 상품·주문·OCR·가상 착용·수선 관리 Atelier Lens | Python, FastAPI, PostgreSQL, PaddleOCR | [코드](https://github.com/Sipsam/Archive/tree/main/legwork_backend/) |

## Project Highlights

<a id="project-01"></a>

### 2025-01-OpenSWBasicProject — NAStock

열린국회 API의 의안 정보를 산업·기업 정보와 함께 탐색하는 웹 프로젝트입니다. 의안 목록·상세·댓글, 공포 법안, 업종별 기업과 주가 조회 API가 있으며 의안 수집·KoBERT 업종 분류 학습 명령도 보관합니다.

- 기술: Django·Django REST Framework, pandas·FinanceDataReader, PyTorch·Transformers, HTML/CSS/JavaScript. 의안 수집·KoBERT 업종 분류 학습 코드도 포함합니다.
- 코드: [프론트엔드](https://github.com/Sipsam/Archive/tree/main/2025-01-OpenSWBasicProject/frontend/) · [백엔드](https://github.com/Sipsam/Archive/tree/main/2025-01-OpenSWBasicProject/backend/)

<a id="project-02"></a>

### 2025-02-OpenSWDevProject — Java 실습·공동구매 서비스

main에는 주차별 Java 실습이 보관됩니다. 별도 frontend/backend 브랜치에는 공동구매 모집·참여, 상품, 커뮤니티, 채팅, 결제·포인트, 문의 메일 구현이 있습니다. 수업 실습과 서비스 스냅샷을 구분해서 열람해야 합니다.

- 기술: Java, Spring, JPA, WebSocket, HTML/CSS/JavaScript. 백엔드 빌드 명세가 보관 트리에 없어 정확한 의존성 버전은 확인되지 않습니다.
- 코드: [프론트엔드](https://github.com/Sipsam/Archive/tree/2025-02-OpenSWDevProject%2Ffrontend/2025-02-OpenSWDevProject/frontend/) · [백엔드](https://github.com/Sipsam/Archive/tree/2025-02-OpenSWDevProject%2Fbackend/2025-02-OpenSWDevProject/src/main/java/)
- main 자료: [Java 실습](https://github.com/Sipsam/Archive/tree/main/2025-02-OpenSWDevProject/). 서비스 구현은 위 별도 브랜치 링크에서 확인합니다.

<a id="project-03"></a>

### 2026_01_OpenSWWebProject — Hill / No Sweat, No Sweet

분리된 운동·식단·수면 기록을 모아 개인별 코칭을 제공하려는 웹 프로젝트입니다. 운동 세션·즐겨찾기, 음식 사진 분석·영양 목표, 수면·Fitbit 연동, 통계·프로필 화면을 보관합니다.

- 기술: React·Vite·Axios, Flask·SQLAlchemy·JWT·PyMySQL, OpenAI·Anthropic·Google 생성형 AI SDK.
- 코드: [프론트엔드](https://github.com/Sipsam/Archive/tree/main/2026_01_OpenSWWebProject/frontend/) · [백엔드](https://github.com/Sipsam/Archive/tree/main/2026_01_OpenSWWebProject/backend/)

<a id="project-04"></a>

### 2026_04_animal_league — Utopia Planner

시험 과목·난이도·이해도를 입력하고 학습 일정을 관리하는 실험형 웹 프로젝트입니다. 계획 UI에 유동적인 일정과 미디어·게임 팝업 같은 집중 방해 요소를 결합해 시험 기간의 심리적 역설을 표현합니다. 회원가입·JWT 로그인, 사용자별 시험·캘린더, 프로필·학습 통계를 제공합니다.

- 기술: HTML/CSS/JavaScript·Vite, Java·Spring Boot·Security·JPA·MySQL.
- 코드: [코드](https://github.com/Sipsam/Archive/tree/main/2026_04_animal_league/)
- 추가 구현: [프론트엔드 스냅샷](https://github.com/Sipsam/Archive/tree/2026_04_animal_league%2Ffrontend/2026_04_animal_league/) · [백엔드 스냅샷](https://github.com/Sipsam/Archive/tree/2026_04_animal_league%2Fbackend/2026_04_animal_league/).

<a id="project-05"></a>

### 2026_14th_final_study_BE — 프론트·백 협업 과제

8주차 협업 과제용 백엔드 베이스입니다. main은 애플리케이션 골격과 빌드 설정 중심이며, 별도 과제 브랜치에는 인증·사용자 컨트롤러, 서비스와 테스트가 별도로 있습니다. 최종 서비스 주제는 확인되지 않았습니다.

- 기술: Java·Spring Boot·Security·JPA·JWT·Swagger, H2·MySQL.
- 코드: [인증·사용자 구현](https://github.com/Sipsam/Archive/tree/2026_14th_final_study_BE%2Fweek8%2Fissue-6-jangsungwon/2026_14th_final_study_BE/)
- main 자료: [협업 과제 베이스](https://github.com/Sipsam/Archive/tree/main/2026_14th_final_study_BE/). 서비스 구현은 위 별도 브랜치 링크에서 확인합니다.

<a id="project-06"></a>

### 2026_KIT_Vibe — AI Pitch Master / AI Pitch-Perfect

영상 업로드에서 말하기 지표 분석, 음성 답변을 포함한 AI 질의응답, 최종 코칭 리포트로 이어지는 발표 훈련 프로젝트입니다. 세션별 분석·Q&A 이력을 연결하고 타이머·카메라 상태를 관리합니다.

- 기술: React·TypeScript·Vite·Zustand·TanStack Query·Tailwind CSS, FastAPI·Pydantic·Google 생성형 AI·gTTS.
- 코드: [프론트엔드](https://github.com/Sipsam/Archive/tree/2026_KIT_Vibe%2Ffrontend/2026_KIT_Vibe/) · [백엔드](https://github.com/Sipsam/Archive/tree/2026_KIT_Vibe%2Fbackend/2026_KIT_Vibe/)
- main 자료: [소개·테스트 영상](https://github.com/Sipsam/Archive/tree/main/2026_KIT_Vibe/). 서비스 구현은 위 별도 브랜치 링크에서 확인합니다.

<a id="project-07"></a>

### 2026_likelion_study — 백엔드 세션 실습

멋쟁이사자처럼 충북대 백엔드 세션의 학습 코드입니다. 회원 가입·로그인과 게시글 생성·조회·수정 API, JPA 엔티티·DTO·공통 응답·예외 처리 구조를 보관합니다. 독립 프론트엔드는 포함하지 않습니다.

- 기술: Java·Spring Boot·Web MVC·JPA·Validation·Swagger·MySQL.
- 코드: [코드](https://github.com/Sipsam/Archive/tree/main/2026_likelion_study/)
- 추가 구현: [4주차 실습](https://github.com/Sipsam/Archive/tree/2026_likelion_study%2Fweek4%2F%EC%9E%A5%EC%84%B1%EC%9B%90/2026_likelion_study/).

<a id="project-08"></a>

### QAgent — 게임 밸런스 분석 에이전트

게임 전투 로그 CSV에서 밸런스 이상 후보를 찾고 사람이 검토할 가상 패치와 영향 시나리오를 만드는 PoC입니다. Streamlit UI·인증된 FastAPI API·OpenAI 도구 호출·파일 기반 RAG·HITL 검토 자료를 보관합니다. 실제 게임 밸런스를 자동 변경하는 서비스로 해석하지 않습니다.

- 기술: Python·Streamlit·pandas, FastAPI, OpenAI SDK. 벡터 DB 없이 문서·패치 노트를 검색합니다.
- 코드: [코드](https://github.com/Sipsam/Archive/tree/main/QAgent/)

<a id="project-09"></a>

### Remory — 기억 자료 기반 대화·기록

기억 자료를 대상자 프로필과 AI 페르소나로 연결하는 프로젝트입니다. 대화·사진 기억·인터뷰·스토리북·공유·음성 기능과 검증 요청·동의 기록·삭제 요청을 다룹니다. 음성 제공자의 mock 기본값과 실제 제공자 연동을 구분해야 합니다.

- 기술: React·TypeScript·Vite, FastAPI·SQLAlchemy·Alembic·MySQL·JWT, google-genai·faster-whisper.
- 코드: [프론트엔드](https://github.com/Sipsam/Archive/tree/main/Remory/frontend/) · [백엔드](https://github.com/Sipsam/Archive/tree/main/Remory/backend/)
- 추가 구현: [데모](https://github.com/Sipsam/Archive/tree/Remory%2Fdemo/Remory/frontend/) · [AI 서비스](https://github.com/Sipsam/Archive/tree/Remory%2Fbackend%2Ffeat-ai-service/Remory/backend/) · [음성 파이프라인](https://github.com/Sipsam/Archive/tree/Remory%2Fbackend%2Ffeat-ai-voice-pipeline/Remory/backend/) · [동의 기록](https://github.com/Sipsam/Archive/tree/Remory%2Fbackend%2Ffeat-consent-log/Remory/backend/) · [대상자 검증](https://github.com/Sipsam/Archive/tree/Remory%2Fbackend%2Ffeat-target-verification/Remory/backend/).

<a id="project-10"></a>

### WOOWANGTHON_TEAM_49 — 월급잇다

근로계약서·근무 기록·급여명세서·입금 내역을 모아 근거를 검토하고 급여 차이를 확인하는 서비스입니다. 다국어 화면, 문서 판독·추출 후 사용자 확정, 계산·대조, 문의 문안과 PDF·ZIP 보고서를 보관합니다. 법적 체불 판정이나 실제 연동·모델·OCR 품질을 보장하지 않습니다.

- 기술: Next.js·React·TypeScript·Tailwind CSS·next-intl, FastAPI·SQLite·LangGraph·LangChain OpenAI, PDF·Tesseract OCR.
- 코드: [프론트엔드](https://github.com/Sipsam/Archive/tree/main/WOOWANGTHON_TEAM_49/frontend/) · [백엔드](https://github.com/Sipsam/Archive/tree/main/WOOWANGTHON_TEAM_49/backend/)
- 추가 구현: [Frontv3](https://github.com/Sipsam/Archive/tree/WOOWANGTHON_TEAM_49%2Ffrontend%2FFrontv3/WOOWANGTHON_TEAM_49/frontend/) · [백엔드 검토 수정](https://github.com/Sipsam/Archive/tree/WOOWANGTHON_TEAM_49%2Fbackend%2Ffix%2Fagent-review-regressions/WOOWANGTHON_TEAM_49/backend/).

<a id="project-11"></a>

### legwork_backend — Atelier Lens

패션 상품 탐색·구매와 보유 상품 관리를 지원하는 해커톤 백엔드입니다. 인증·게스트·상품·장바구니·주문·모의 결제, 파일 작업·OCR·아바타·가상 착용·코디 추천·손상 진단·수선 예약 API를 보관합니다. 모의 기능과 실제 제공자 연동은 구분해서 확인해야 합니다.

- 기술: Python·FastAPI·SQLAlchemy async·PostgreSQL·Alembic, PaddleOCR·OpenCV·OpenAI SDK·Docker Compose.
- 코드: [코드](https://github.com/Sipsam/Archive/tree/main/legwork_backend/)
- 추가 구현: [OCR](https://github.com/Sipsam/Archive/tree/legwork_backend%2Ffeature%2Fbe-b-ocr/legwork_backend/) · [코디 추천](https://github.com/Sipsam/Archive/tree/legwork_backend%2Ffeature%2Fbe-b-recommendation-coordi/legwork_backend/) · [가상 착용](https://github.com/Sipsam/Archive/tree/legwork_backend%2Ffeature%2Ftryon-openai/legwork_backend/) · [진단·수선](https://github.com/Sipsam/Archive/tree/legwork_backend%2Ffeature%2Fbe-b-diagnosis-repair/legwork_backend/) · [최종 통합](https://github.com/Sipsam/Archive/tree/legwork_backend%2Fchore%2Ffinal-integration/legwork_backend/).

## Repository Structure

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
├── docs/                      # 운영 가이드·관리 설정
├── scripts/                   # 통합 관리 도구·격리 테스트
└── README.md
```

독립 프로젝트를 프로젝트별 디렉터리에 보관하며, 초기 통합에는 Git subtree를 사용했습니다. 주요 개발 브랜치는 프로젝트 이름을 네임스페이스로 보존합니다. 브랜치마다 스냅샷과 폴더 구조가 다를 수 있으며 원본 저장소 없이 Archive에서 코드를 열람할 수 있습니다.

## Archive Management

Windows PowerShell 5.1, Git for Windows, Python 3.9+ 환경에서 저장소 루트를 기준으로 실행합니다.

```powershell
.\scripts\archive-manager.ps1 fetch
.\scripts\archive-manager.ps1 status
.\scripts\archive-manager.ps1 validate
```

`status`는 저장된 origin 추적 참조를 비교하므로 먼저 `fetch`합니다. 추가·승격·갱신·추출·동기화·Push는 [운영 가이드](docs/archive-manager-guide.md)를 참고하세요.

## Notes

- 프로젝트별 실행 환경·완성도·외부 API 설정이 다릅니다. 실행 조건은 각 프로젝트 문서를 확인하세요.
- main에 실습·소개만 있는 프로젝트도 있습니다. 구현은 Projects 표와 상세 소개의 코드 링크로 이동하세요.
- [의도된 LFS 누락 목록](docs/archive-lfs-known-missing.json)의 payload는 자동 복원하지 않습니다. 과거 영상·모델 파일은 포인터만 남아 있을 수 있습니다.
- 관리 도구의 실제 `sync` 변경·`promote` 적용·`push`는 외부 복구 백업을 자동 생성합니다. 상시 백업 유지는 필수가 아니지만 자동 백업 생략 옵션은 없습니다. 자세한 위치와 조건은 운영 가이드를 확인하세요.
