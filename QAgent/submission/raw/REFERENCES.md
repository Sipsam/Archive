# 참고문헌 및 출처

최종 확인일: 2026-07-08. 외부 사례는 공급자·연구조직·표준기관의 1차 자료를 우선하였다. 공급자의 효과 주장은 독립 검증 결과가 아니므로 보고서에서는 기능과 활용 방향 중심으로 해석했다.

## 1. 게임 산업 및 라이브 서비스·AI 활용

1. **[G1]** Electronic Arts SEED, “SEED Applies Machine Learning Research to the Growing Demands of AAA Game Testing.” 강화학습·모방학습을 활용한 게임 테스트 연구와 적용상의 난점을 설명한다.  
   <https://www.ea.com/seed/news/seed-ml-research-aaa-game-testing>
2. **[G2]** Ubisoft Montreal La Forge, “Ubisoft La Forge presents: the Commit-Assistant.” 과거 버그 패턴으로 신규 결함 가능성을 식별하는 연구 프로토타입 사례다.  
   <https://montreal.ubisoft.com/en/ubisoft-la-forge-presents-the-commit-assistant/>
3. **[G3]** Microsoft Xbox, “Xbox Publishes Its Second Transparency Report.” AI와 사람을 결합한 Community Sift 기반 선제적 콘텐츠 모더레이션 사례를 설명한다.  
   <https://news.microsoft.com/es-es/2023/05/23/xbox-publica-su-segundo-informe-de-transparencia-que-muestra-el-papel-fundamental-de-la-moderacion-de-contenido-de-cara-a-una-experiencia-de-juego-mas-saludable/>
4. **[G4]** NVIDIA Developer, “NVIDIA ACE for Games.” 음성·언어·애니메이션 모델을 이용한 대화형 게임 캐릭터 개발 플랫폼과 안전장치 방향을 설명한다.  
   <https://developer.nvidia.com/ace>
5. **[G5]** NVIDIA, “NVIDIA ACE Autonomous Game Characters Debut…,” 2025. 실제 게임에 적용되는 자율 캐릭터 사례를 소개한다. 공급자 발표 자료이므로 효과 수치는 독립 검증으로 간주하지 않았다.  
   <https://www.nvidia.com/en-eu/geforce/news/nvidia-ace-naraka-bladepoint-inzoi-launch-this-month/>

## 2. AI Agent·LLM·위험 관리

1. **[A1]** OpenAI, “Function Calling in the OpenAI API.” 모델이 외부 데이터·계산 기능을 구조화된 호출로 사용하는 방식의 공식 설명이다.  
   <https://help.openai.com/en/articles/8555517-function-calling-in-the-openai-api>
2. **[A2]** NIST, “AI Risk Management Framework.” AI 시스템의 설계·개발·사용·평가에서 신뢰성 위험을 관리하기 위한 자발적 프레임워크다.  
   <https://www.nist.gov/itl/ai-risk-management-framework>
3. **[A3]** NIST, “Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile,” NIST AI 600-1, 2024. 생성형 AI의 정보 무결성, 개인정보, 보안, Human-AI 구성 위험과 통제 방향을 제시한다.  
   <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>

## 3. 사용 API 및 기술 문서

1. **[T1]** Riot Games Developer Portal, “Developer Portal.” API 키 유형, 보안, 호출 제한과 제품 등록 정책을 설명한다.  
   <https://developer.riotgames.com/docs/portal>
2. **[T2]** Riot Games Developer Portal, “League of Legends APIs.” 게임별 API 및 정책 진입점이다.  
   <https://developer.riotgames.com/docs/lol>
3. **[T3]** Streamlit, “Run your Streamlit app.” `streamlit run` 기반 로컬 앱 실행의 공식 문서다.  
   <https://docs.streamlit.io/develop/concepts/architecture/run-your-app>
4. **[T4]** pandas documentation. CSV 기반 표 데이터 로딩·집계에 사용한 라이브러리 문서다.  
   <https://pandas.pydata.org/docs/>
5. **[T5]** Python documentation. 프로젝트 실행 언어의 공식 문서다.  
   <https://docs.python.org/3/>
6. **[T6]** FastAPI documentation. 외부 API endpoint, request validation, response model 구현의 공식 문서다.  
   <https://fastapi.tiangolo.com/>
7. **[T7]** Uvicorn documentation. ASGI 서버 실행과 로컬 API 서버 구동의 공식 문서다.  
   <https://www.uvicorn.org/>

## 4. 통계·평가 방법

1. **[S1]** Wilson, E. B. (1927), “Probable Inference, the Law of Succession, and Statistical Inference,” *Journal of the American Statistical Association*, 22(158), 209–212. 승률 비율의 신뢰구간 근거다.  
   <https://doi.org/10.1080/01621459.1927.10502953>
2. **[S2]** Benjamini, Y. and Hochberg, Y. (1995), “Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing,” *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300. 다중 비교에서 FDR 제어의 근거다.  
   <https://doi.org/10.1111/j.2517-6161.1995.tb02031.x>

## 5. 프로젝트 내부 문서 및 코드

- `README.md`: v2.8.0 기능, 빠른 실행, 한계.
- `.env.example`: 모델·API 방식·reasoning·안전 제한·탐지 임계값.
- `docs/RUN.md`: 실행 요약.
- `docs/API.md`: 외부 API endpoint, 인증, 요청/응답, error shape.
- `docs/RAG_GUIDE.md`: 파일 기반 RAG 검색 대상, status, metadata.
- `docs/SECURITY_NOTES.md`: OWASP LLM Top 10 기준 보안 점검과 대응.
- `docs/AGENT_ARCHITECTURE.md`: LangChain, LangGraph, MCP, A2A 적용 판단과 확장 설계.
- `docs/PROJECT_STRUCTURE.md`: 디렉터리와 모듈 책임.
- `docs/SUBMISSION_NOTES.md`: 제출 범위와 운영상 한계.
- `docs/STRUCTURE_REFACTORING_REPORT.md`, `docs/review/*`: 리팩터링 및 데이터 파이프라인 기록.
- `docs/evaluation/AGENT_EVALUATION.md`: fixture 기반 Agent 평가.
- `app.py`: Streamlit 화면, 모델 설정, 실행 및 HITL UI의 기준 구현.
- `qagent_core/agent/*`: 프롬프트, Responses/Chat Completions 루프, 필수 후속 단계.
- `qagent_core/guardrails.py`: UI/API 공통 입력 검증, prompt injection 신호 탐지, 출력 secret masking.
- `qagent_core/rag.py`: README/docs/data 문서 기반 lightweight retrieval.
- `qagent_core/tool_registry.py`, `qagent_core/tools/*`: 16개 호출 가능 Tool의 schema와 구현.
- `qagent_core/statistics.py`: Wilson 구간과 FDR 보정 기반 후보 탐지.
- `qagent_core/simulation.py`, `qagent_core/risk.py`: 휴리스틱 시나리오와 위험·재테스트 정책.
- `data/lol_assignment_dataset/dataset_summary.json`: 제출 데이터의 행 수, 컬럼, 품질 검사 결과.

## 6. 인용 해석 원칙

제출 패키지 실행과 보안 설정에서 반복 확인해야 할 환경변수는 `OPENAI_API_KEY`, `AGENT_API_KEY`, `ENABLE_RAG`, `RAG_INCLUDE_DATA_DOCS`, `RAG_TOP_K`, `MAX_AGENT_QUERY_CHARS`다. 실제 secret 값은 제출 문서와 압축본에 포함하지 않는다.

- EA, Ubisoft, Microsoft, NVIDIA 사례는 “AI가 이미 모든 업무를 대체했다”는 근거가 아니다. 확인 가능한 연구·제품 기능과 대표 활용 방향으로만 사용했다.
- 외부 사례의 성능·비용 절감 수치는 독립 검증되지 않은 경우 보고서의 정량 기대효과로 전용하지 않았다.
- 본 프로젝트의 구현 사실은 외부 문서가 아니라 저장소 코드와 테스트를 최우선 근거로 삼았다.
