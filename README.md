# 월급잇다 (Wageitda)

근로계약서, 근무 기록, 급여명세서와 실제 입금 내역을 연결해 급여의 근거와 확인이 필요한 차이를 살펴보는 서비스의 프론트엔드입니다. 임금 확인에 필요한 자료를 모으고 검토하는 과정을 지원하며, 외국인 근로자를 위한 다국어 UI를 제공합니다.

## 프로젝트 개요

주요 사용자 흐름은 다음과 같습니다.

1. 회원가입·로그인 후 사업장을 등록하고 확인할 기간의 Case를 생성합니다.
2. 문서를 업로드하거나 기존 문서를 Case에 연결합니다.
3. 원본과 추출 필드를 대조·수정·확정하고, 근로 조건과 수기 기록을 보완합니다.
4. 서버에서 생성한 급여 계산·비교 결과와 근거, 입금 내역을 확인합니다.
5. 회사 문의 문안, 상담 준비 질문, 보고서 및 상담기관 안내를 이용합니다.

현재 화면에는 대시보드, 사업장·Case 관리, 문서 보관함·검토, 입금 등록·연결, 결과 이력 조회, 사업장 채팅, 계정 설정·비밀번호 재설정·탈퇴가 구현되어 있습니다. UI 언어는 한국어, 영어, 베트남어, 중국어, 크메르어를 지원합니다.

프론트엔드는 자료 입력·검토와 결과 시각화를 담당합니다. 공식 급여 계산과 문서 추출은 백엔드 책임이며, 입금 차이를 확정된 체불임금으로 표시하지 않습니다. 채팅 응답도 계산 결과를 대신하지 않습니다. 개발용 Mock에서 화면 흐름을 확인할 수 있으며, 실제 백엔드 연동은 별도 검증이 필요합니다.

## 기술 스택

버전은 `package.json`의 선언 기준입니다. 범위로 선언된 의존성의 설치 버전은 `package-lock.json`을 따릅니다.

| 분류 | 기술 | 역할 |
| --- | --- | --- |
| Framework | Next.js 16.4.5, React 19.3.0 | App Router, 공통 Layout, Server/Client Components |
| Language | TypeScript 5 | `strict` 타입 검사, `@/*` 경로 별칭 |
| Styling | Tailwind CSS 4, CSS Modules | 공통 스타일, 화면별 스타일, 반응형 레이아웃 |
| Server State | TanStack Query 5 | 조회 캐시, Mutation, 무효화, 상태 Polling |
| Client State | Zustand 5, React state/context | 상담 Case 선택·페이지 등 UI 상태, 앱 서비스 전달 |
| API Communication | Fetch API, ReadableStream | REST JSON, FormData 업로드, Blob 다운로드, SSE |
| Form Validation | React Hook Form 7, Zod 4, `@hookform/resolvers` | 폼 상태·검증, API 요청·응답 스키마 검증 |
| Internationalization | next-intl 4 | 언어별 메시지와 서버·클라이언트 번역 |
| Content / UI | PDF.js (`pdfjs-dist`), react-markdown, remark-gfm, lucide-react | PDF 미리보기, 채팅 Markdown, 아이콘 |
| Testing / Quality | Vitest 5, Testing Library, jsdom, MSW 3, Ajv, ESLint 9 | 단위·컴포넌트·계약 테스트, Mock API, 정적 검사 |

## 프로젝트 구조

```text
contracts/
  openapi.json          # API 구현·테스트의 기준 계약
src/
  app/                  # 페이지, Layout, 전역 Provider·오류 화면
    (marketing)/        # 서비스 소개
    (auth)/             # 로그인·회원가입
    (workspace)/        # 인증 후 사용하는 업무 화면
  features/             # 기능별 API·스키마·Query Hook·ViewModel·화면
    auth/               # 인증·세션·계정 관리
    workplaces/         # 사업장 관리
    cases/              # Case 관리·진행 단계
    documents/          # 문서 업로드·연결·원본/추출 필드 검토
    case-inputs/        # 근로 조건·수기 기록
    results/            # 계산·비교 결과·버전·근거
    payments/           # 입금 내역·Case 연결·비교
    case-support/       # 문의 문안·보고서·상담 준비·기관 안내
    chats/              # 채팅·SSE 처리
    dashboard/          # 업무 현황
  components/           # 공통 UI와 모바일/데스크톱 Layout
  hooks/                # 앱 서비스·세션 범위 등 공통 Hook
  lib/                  # API 클라이언트·오류·환경 설정·Query 공통 모듈
  types/                # 공통 API 타입
  i18n/                 # 언어 설정·번역 Provider·메시지 도구
  messages/             # ko, en, vi, zh, km 번역 리소스
  mocks/                # 브라우저 MSW와 개발 시나리오
  test/                 # 공통 테스트 도구·OpenAPI 계약 테스트
public/                 # 정적 리소스·MSW Service Worker
scripts/                # 번역 생성·검사 등 개발 스크립트
```

도메인 테스트는 해당 기능 옆의 `*.test.ts(x)`에도 배치합니다.

## 기술 설계

### 라우팅과 화면 구성

Route Group은 URL에 포함되지 않습니다. `page.tsx`는 주로 기능 화면을 조합하고, 도메인 로직은 `features/`에 둡니다.

| 경로 | 용도 |
| --- | --- |
| `/` | 서비스 소개 |
| `/login`, `/signup` | 로그인·회원가입 |
| `/forgot-password`, `/reset-password`, `/account-deletion` | 비밀번호 복구·탈퇴 상태 안내 |
| `/dashboard`, `/settings` | 현황·계정 설정 |
| `/workplaces`, `/workplaces/new`, `/workplaces/[workplaceId]` | 사업장 목록·등록·상세 |
| `/workplaces/[workplaceId]/documents`, `/library` | 사업장 문서·전체 보관함 |
| `/workplaces/[workplaceId]/chats`, `/workplaces/[workplaceId]/chats/[chatId]` | 사업장 채팅 |
| `/cases`, `/cases/new`, `/cases/[caseId]` | Case 목록·생성·작업 공간 |
| `/cases/[caseId]/{upload,review,conditions,manual-records}` | 자료 등록·검토·입력 |
| `/cases/[caseId]/result` | 결과·입금 비교 (`/compare`는 이 경로로 이동) |
| `/cases/[caseId]/{questions,company-inquiry,reports}` | 상담 질문·문의 문안·보고서 |
| `/consultation`, `/consultation-centers` | 상담 준비·기관 안내 |

중괄호 표기는 같은 깊이에 있는 개별 경로를 묶은 것입니다. 루트 Layout에서 언어·앱 Provider를 제공하고, `(workspace)` Layout은 `AuthGate`와 공통 `AppShell`을 적용합니다. 모바일 탐색과 데스크톱 탐색, 화면별 반응형 스타일을 갖추고 있습니다.

### 상태와 도메인 경계

- TanStack Query로 서버 데이터를 관리합니다. 기본 자동 재시도는 비활성화하며, 기능별 Query Key와 Mutation 후 무효화를 사용합니다.
- Zustand는 상담 준비 화면의 Case 선택·페이지 같은 UI 상태에 사용합니다. API 응답을 별도 영속 저장하지 않습니다.
- 기능별 `api.ts`, `schemas.ts`, `queries.ts`, `view-models.ts`, 컴포넌트로 통신·검증·표현 책임을 나눕니다. 모듈별로 필요한 파일만 둡니다.
- Workplace, Case, Document, CaseDocumentLink를 구분합니다. 원본 문서는 여러 Case에서 참조할 수 있고, 처리 완료와 사용자 검토 확정은 별도 상태입니다.
- 미확인 값의 `null`과 `0`을 구분합니다. 결과의 입력 버전·스냅샷·최신성을 유지하며, 갱신 중에도 이전 결과를 표시합니다.

### API·비동기 처리

`src/lib/api/client.ts`의 Fetch 클라이언트를 기능별 API 모듈이 사용합니다. 브라우저에서 설정된 FastAPI API 주소로 직접 요청하며, JSON·204·202·Blob·다운로드·SSE 응답을 별도로 처리합니다. 기능별 Zod 스키마로 응답을 검증하고, OpenAPI 계약 테스트로 계약과의 일치를 검사합니다.

문서 처리와 재계산 작업은 활성 상태에서 Polling하고 종료 상태에서 중단합니다. 지원되는 변경 요청에 `expectedInputVersion`을 전달하고, 재계산 상태 API를 통해 결과 갱신을 관찰합니다. 채팅은 SSE 이벤트를 검증하며 완료·오류·취소·재시도 흐름을 처리합니다.

### 인증과 오류 처리

Access Token은 앱 트리별 메모리 세션에만 보관합니다. 요청에는 Bearer Token과 `credentials: 'include'`를 적용하고, 시작 시 세션 복원 및 401 발생 시 Refresh 요청을 공유하는 single-flight 방식으로 Token을 갱신합니다. 로그아웃·계정 전환 시 진행 요청을 취소하고 사용자 Query 캐시를 비웁니다.

`AuthGate`는 화면 접근과 로그인 이동을 담당하며, 실제 리소스 권한은 백엔드가 검증해야 합니다. `ApiError`는 401·403·404·409·422·429, 네트워크 오류와 응답 계약 오류를 구분합니다. 공통 상태 UI, 폼 필드 오류, App Router의 `loading.tsx`·`error.tsx`·`not-found.tsx`를 사용합니다.

## 로컬 실행

### 개발 환경

- **Node.js 24**: 기존 실행 기준과 `Dockerfile`의 `node:24-bookworm-slim`에 맞춥니다. Next.js 단독 최소 요구사항보다 테스트·Mock·PDF 의존성의 Node.js 요구사항이 높습니다.
- **npm**: `package-lock.json`을 사용하는 프로젝트입니다. npm 버전은 프로젝트 설정에서 고정하지 않습니다.
- **브라우저**: Mock Mode에는 Service Worker가 가능한 `localhost` 또는 HTTPS 환경이 필요합니다.

저장소 루트에서 실행합니다.

```sh
npm ci
```

### 환경 변수

PowerShell:

```powershell
Copy-Item .env.example .env.local
```

macOS / Linux:

```sh
cp .env.example .env.local
```

| 변수 | 예제 파일 기본값 | 설명 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000/api/v1` | API Origin과 버전 Prefix를 포함한 주소 |
| `NEXT_PUBLIC_MOCK_API` | `false` | 개발 서버에서 `true`일 때 MSW 활성화 |

`.env.local`은 Git 제외 대상입니다. `NEXT_PUBLIC_*`는 브라우저에 공개되므로 비밀값을 넣지 않습니다. 값을 바꾸면 개발 서버를 재시작하며, 프로덕션용 공개 변수는 빌드 전에 설정합니다.

### 백엔드 없이 실행: Mock Mode

`.env.local`을 다음과 같이 설정합니다.

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_MOCK_API=true
```

```sh
npm run dev
```

[http://localhost:3000](http://localhost:3000)에 접속합니다. 샘플 계정은 `worker@example.com` / `password1234`입니다.

- 샘플 계정에는 가상 사업장·Case·문서·결과가 제공됩니다. 신규 가입 계정은 독립적인 빈 업무 데이터로 시작합니다.
- 데이터 변경과 신규 계정은 페이지 전체 새로고침 시 초기화됩니다. 샘플 계정은 개발용 표식 Cookie로 세션을 복원할 수 있습니다.
- 업로드 문서의 추출값·계산·채팅은 가상 응답입니다. 실제 OCR·급여 계산·AI 연동 검증을 의미하지 않으므로 민감한 자료를 넣지 않습니다.
- 비밀번호 복구는 `LOCAL_OUTBOX_ONLY`로 동작하며 이메일을 발송하지 않습니다.
- 미등록 API는 `501 MOCK_NOT_IMPLEMENTED`로 차단하고 실제 서버로 전달하지 않습니다. Mock Mode는 프로덕션에서 비활성화됩니다.

### 실제 API 연동 조건

Mock을 끄면 별도로 제공되는 백엔드 API가 필요합니다. `NEXT_PUBLIC_MOCK_API=false`와 접근 가능한 `NEXT_PUBLIC_API_BASE_URL`을 설정합니다. 이 저장소에는 FastAPI 서버 실행 명령이나 백엔드 구현이 포함되어 있지 않습니다.

API 계약은 `contracts/openapi.json`을 기준으로 합니다. 브라우저가 API에 직접 접근하므로 백엔드는 프론트엔드 Origin에 대한 CORS·credentials 허용, Refresh Cookie 정책, SSE 응답을 지원해야 합니다. `localhost`와 `127.0.0.1`을 혼용할 때도 Cookie·Origin 조건을 확인해야 합니다. 실제 서버 연동은 별도 검증이 필요합니다.

### 빌드·프로덕션 실행

```sh
npm run build
npm start
```

프로덕션에서는 Mock이 동작하지 않으므로 업무 기능 사용에 실제 API가 필요합니다. `next.config.ts`는 `output: 'standalone'`을 사용합니다. Docker 이미지도 제공하며, `compose.yaml`은 프론트엔드만 빌드·실행합니다. API 주소는 Docker 빌드 인자로 전달됩니다.

### 검사 명령어

```sh
npm run lint
npm run typecheck
npm test
npm run build
```

| 명령어 | 역할 |
| --- | --- |
| `npm run lint` | ESLint 검사 |
| `npm run typecheck` | Next.js 라우트 타입 생성 후 `tsc --noEmit` |
| `npm test` | Vitest 전체 테스트 실행 |
| `npm run test:watch` | Vitest 감시 모드 |
| `npm run i18n:generate` | 번역 리소스 기반 카탈로그 생성 |
| `npm run i18n:check` | 번역 리소스·ICU 메시지·번역 사용 정책 검사 |

`dev`, `build`, `typecheck` 전에는 npm의 `pre*` 스크립트로 번역 카탈로그가 자동 생성됩니다. 테스트에는 MSW를 이용한 통신·오류 회귀 테스트와 OpenAPI 계약 검증이 포함되며, 실제 백엔드 실행을 요구하지 않습니다.

## 참고 자료

- [API 계약: contracts/openapi.json](contracts/openapi.json)
- [개발 규칙: AGENTS.md](AGENTS.md)
- [실행 스크립트와 의존성: package.json](package.json)
- [환경 변수 예제: .env.example](.env.example)
- [Next.js 설정: next.config.ts](next.config.ts)
- [OpenAPI 계약 테스트: src/test/openapi/](src/test/openapi/)
- [Docker 빌드: Dockerfile](Dockerfile), [로컬 Compose: compose.yaml](compose.yaml), [프로덕션 Compose: compose.prod.yaml](compose.prod.yaml)

로컬 참고문서 디렉터리 `docs/`는 Git 추적에서 제외되므로 저장소 이용에 필요한 문서 링크로 사용하지 않습니다.
