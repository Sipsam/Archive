# QAgent 리팩토링 및 개선 제안서

**분석 일자**: 2026-07-07  
**프로젝트**: Battle Balance Analyst Generative AI Agent v2.8.0

---

## 📋 Executive Summary

QAgent는 게임 밸런스 분석을 위한 잘 구조화된 AI Agent입니다. 주요 개선 기회:
1. **코드 중복 제거** (도구 빌더 패턴)
2. **타입 힌팅 강화** (런타임 안전성)
3. **에러 핸들링 표준화**
4. **성능 최적화** (캐싱, 배치 처리)
5. **테스트 커버리지 확대**

---

## 🎯 우선순위별 개선사항

### 1️⃣ **고우선 (High Priority)**

#### 1.1 도구 빌더 함수의 중복 제거

**현재 상황:**
```python
# qagent_core/tools/balance.py
def build_balance_tools(context: AnalysisContext) -> dict[str, Any]:
    battles = context.battles
    characters = context.characters
    skills = context.skills
    equipment_sets = context.equipment_sets
    patch_notes = context.patch_notes
    retrieve_related_knowledge = build_patch_tools(context)["retrieve_related_knowledge"]
    # ... 각 도구 함수 정의
```

**문제점:**
- 모든 도구 빌더(`balance.py`, `dataset.py`, `patch.py`, `virtual_patch.py`)가 동일한 boilerplate 사용
- 도구 함수 내 문맥 변수 추출 반복
- 유지보수 시 모든 빌더 수정 필요

**개선 방안:**
```python
# qagent_core/tools/base.py (신규)
from abc import ABC, abstractmethod
from typing import Any, Dict, Callable

class ToolBuilder(ABC):
    """모든 도구 빌더의 기본 추상 클래스."""
    
    def __init__(self, context: 'AnalysisContext'):
        self.context = context
        self.battles = context.battles
        self.characters = context.characters
        self.skills = context.skills
        self.equipment_sets = context.equipment_sets
        self.patch_notes = context.patch_notes
    
    @abstractmethod
    def build(self) -> Dict[str, Callable[[...], Any]]:
        """이 빌더가 제공하는 도구 함수 딕셔너리 반환."""
        pass

class BalanceToolBuilder(ToolBuilder):
    """밸런스 분석 도구 빌더."""
    
    def build(self) -> Dict[str, Callable]:
        return {
            "detect_anomalies": self.detect_anomalies,
            "analyze_segment_performance": self.analyze_segment_performance,
            # ...
        }
    
    def detect_anomalies(self, **kwargs) -> Dict[str, Any]:
        # 구현
        pass
```

**기대 효과:**
- 보일러플레이트 50% 감소
- 유지보수 난이도 ↓
- 도구 추가 시 프로세스 표준화

---

#### 1.2 타입 힌팅 강화

**현재 상황:**
```python
# qagent_core/tool_executor.py (일부 보완되어 있으나)
def execute(
    self,
    tool_name: str,
    arguments: Mapping[str, Any] | None,  # ✓ 좋음
    *,
    turn: int,
    forced_by_app: bool = False,
) -> dict[str, Any]:  # ✓ 좋음
```

하지만 많은 함수에서 누락:
```python
# qagent_core/statistics.py (예시)
def detect_balance_candidates(battles, min_samples=30, ...):  # ❌ 타입 없음
    # ...
    return overall_wr, anomalies  # ❌ 반환 타입 모호
```

**개선 방안:**
```python
# qagent_core/statistics.py
from typing import Tuple
import pandas as pd

def detect_balance_candidates(
    battles: pd.DataFrame,
    min_samples: int = 30,
    win_rate_threshold: float = 0.75,
    win_rate_gap_threshold: float = 0.20,
    wilson_lower_gap_threshold: float = 0.0,
    segment_by: str = "",
    fdr_alpha: float = 0.05,
) -> Tuple[float, pd.DataFrame]:
    """
    밸런스 이상 후보 탐지 (Wilson 신뢰구간 + FDR 보정).
    
    Args:
        battles: 전투 로그 DataFrame
        min_samples: 최소 샘플 수
        win_rate_threshold: 승률 하한
        win_rate_gap_threshold: 전체 대비 승률 차이
        wilson_lower_gap_threshold: Wilson 구간 하한 차이
        segment_by: 세그먼트 기준 ("user_segment", "battle_mode", "")
        fdr_alpha: 거짓 발견율 임계값
    
    Returns:
        (전체_평균_승률, 이상_후보_DataFrame)
    """
    # 구현
    overall_wr: float = battles["result"].mean()
    anomalies: pd.DataFrame = pd.DataFrame()
    return overall_wr, anomalies
```

**스크립트로 자동 검사:**
```bash
python -m pyright qagent_core --level basic
python -m mypy qagent_core --ignore-missing-imports
```

**기대 효과:**
- IDE 자동완성 개선 (VS Code, PyCharm)
- 런타임 타입 오류 사전 감지
- 문서 자동 생성 가능

---

#### 1.3 에러 핸들링 표준화

**현재 상황:**
```python
# qagent_core/persistence.py (일부 좋음)
except sqlite3.Error as error:
    raise ReviewPersistenceError(...) from error  # ✓

# qagent_core/data_io.py (일부 누락)
except OSError:
    continue  # ❌ 에러 무시, 로깅 없음
```

**개선 방안:**
```python
# qagent_core/errors.py (신규)
"""Unified error hierarchy for the agent."""

class QAgentError(Exception):
    """Base exception for all QAgent errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN",
        user_safe: bool = True,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.user_safe = user_safe
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict[str, Any]:
        """AI Agent 응답/로그용 직렬화."""
        return {
            "error_code": self.error_code,
            "message": self.message if self.user_safe else "[오류 세부 정보는 관리자에게 문의]",
            "details": self.details if self.user_safe else {},
        }

class DataLoadError(QAgentError):
    """Data loading or validation failure."""
    pass

class ReviewPersistenceError(QAgentError):
    """HITL record persistence failure."""
    pass

class ToolExecutionError(QAgentError):
    """Tool execution failure."""
    pass

class APIError(QAgentError):
    """External API call failure."""
    pass
```

사용 예:
```python
# qagent_core/data_io.py
def discover_data_folders(...) -> list[Path]:
    try:
        with os.scandir(candidate) as entries:
            children = sorted(...)
    except OSError as e:
        logger.warning(f"Failed to scan {candidate}: {e}")  # 로깅 추가
        # 에러 분류
        raise DataLoadError(
            f"데이터 폴더를 탐색할 수 없습니다: {candidate}",
            error_code="FOLDER_SCAN_FAILED",
            details={"path": str(candidate), "os_error": str(e)},
        ) from e
```

**기대 효과:**
- 체계적 에러 추적
- 사용자/개발자 메시지 분리
- 로깅/모니터링 개선

---

### 2️⃣ **중우선 (Medium Priority)**

#### 2.1 캐싱 전략 개선

**현재 상황:**
```python
# qagent_core/data_io.py
@lru_cache(maxsize=32)
def load_csv(file_path: Path | str) -> pd.DataFrame:
    # ...
```

문제점: 캐시 키가 경로 문자열만 사용 → 파일 내용 변경 감지 안 됨

**개선 방안:**
```python
# qagent_core/data_io.py
from functools import lru_cache
import hashlib
from pathlib import Path
import pandas as pd

def compute_file_signature(file_path: Path) -> str:
    """파일의 내용 기반 시그니처 (경로 아님)."""
    stat = file_path.stat()
    # 경로 + 수정 시간 + 크기 조합
    return f"{file_path}:{stat.st_mtime_ns}:{stat.st_size}"

_csv_cache: dict[str, pd.DataFrame] = {}

def load_csv_cached(file_path: Path | str) -> pd.DataFrame:
    """파일 서명 기반 캐싱."""
    path = Path(file_path)
    sig = compute_file_signature(path)
    
    if sig not in _csv_cache:
        _csv_cache[sig] = load_csv(path)
    
    return _csv_cache[sig].copy()  # 복사본 반환 (공유 금지)
```

또는 Streamlit 캐시 활용:
```python
@st.cache_data(ttl=3600, show_spinner=False)
def load_csv_streamlit(file_path: str) -> pd.DataFrame:
    """Streamlit 캐시 (세션 간 공유, 파일 변경 감지)."""
    return clean_columns(pd.read_csv(file_path))
```

**기대 효과:**
- 파일 수정 시 자동 재로드
- 중복 로드 50% 감소
- 메모리 효율성 ↑

---

#### 2.2 도구 스키마 자동 생성

**현재 상황:**
```python
# qagent_core/tool_registry.py
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_dataset_overview",
            "description": "데이터셋의 전체 규모...",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False}
        }
    },
    # ... 수동으로 모두 작성 (15+ 항목)
]
```

**문제점:**
- 도구 함수와 스키마 이중 관리
- 스키마 수정 시 동기화 필요
- 매뉴얼 유지보수 오류 가능

**개선 방안:**
```python
# qagent_core/tools/__init__.py
from typing import get_type_hints
import inspect
from docstring_parser import parse

def generate_tool_schema(func: Callable) -> dict[str, Any]:
    """함수 시그니처와 docstring에서 OpenAI schema 자동 생성."""
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    doc = parse(func.__doc__ or "")
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "context"):
            continue
        
        param_doc = next((p for p in doc.params if p.arg_name == param_name), None)
        properties[param_name] = {
            "type": _python_to_json_type(hints.get(param_name, str)),
            "description": param_doc.description if param_doc else "",
        }
        
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": doc.short_description or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            }
        }
    }

def _python_to_json_type(python_type) -> str:
    """Python 타입 → JSON Schema 타입 변환."""
    mapping = {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    return mapping.get(python_type, "string")
```

사용:
```python
# qagent_core/tool_registry.py
from qagent_core.tools import generate_tool_schema, build_balance_tools, build_dataset_tools

def generate_all_tool_schemas(context: AnalysisContext) -> list[dict]:
    """모든 도구의 스키마를 동적으로 생성."""
    tool_functions = build_tool_functions(context)
    return [generate_tool_schema(func) for func in tool_functions.values()]

# app.py에서
TOOL_SCHEMAS = generate_all_tool_schemas(context)
```

**기대 효과:**
- 스키마 유지보수 자동화
- 함수 변경 시 스키마 자동 동기화
- 버그 감소

---

#### 2.3 배치 처리 및 진행률 표시

**현재 상황:**
```python
# qagent_core/tools/balance.py
def detect_anomalies(...):
    # 전체 데이터셋 한 번에 처리
    overall_wr, anomalies = detect_balance_candidates(battles, ...)
    # 진행률 없음
```

**개선 방안:**
```python
# qagent_core/tools/balance.py
from typing import Callable, Optional

def detect_anomalies(
    ...,
    on_progress: Optional[Callable[[float, str], None]] = None,  # 콜백 추가
) -> Dict[str, Any]:
    """
    Args:
        on_progress: (진행률_0_1, 메시지) 콜백
    """
    def report_progress(fraction: float, message: str):
        if on_progress:
            on_progress(fraction, message)
    
    report_progress(0.0, "데이터 준비 중...")
    # ... 준비 단계
    
    report_progress(0.3, "이상 탐지 중...")
    overall_wr, anomalies = detect_balance_candidates(battles, ...)
    
    report_progress(0.7, "결과 정렬 중...")
    # ... 정렬
    
    report_progress(1.0, "완료")
    return {...}
```

Streamlit 통합:
```python
# app.py
progress_bar = st.progress(0)
status_text = st.empty()

def on_progress(fraction: float, message: str):
    progress_bar.progress(fraction)
    status_text.text(message)

result = detect_anomalies(
    ...,
    on_progress=on_progress,
)
```

**기대 효과:**
- 사용자 경험 개선 (긴 작업 중 상태 표시)
- 타임아웃 감소
- 반응성 ↑

---

### 3️⃣ **저우선 (Low Priority) - 코드 스타일/최적화**

#### 3.1 상수 중앙 관리

**현재 상황:**
```python
# 여러 파일에 분산
# qagent_core/statistics.py
MIN_WILSON_SAMPLES = 30

# qagent_core/config.py
BALANCE_MIN_SAMPLES = 30

# qagent_core/tools/balance.py
top_n: int = 10
```

**개선 방안:**
```python
# qagent_core/constants.py (신규)
"""Application-wide constants."""

# Statistical thresholds
STAT_MIN_SAMPLES = 30
STAT_MIN_WIN_RATE = 0.75
STAT_WILSON_CONFIDENCE = 0.95
STAT_FDR_DEFAULT_ALPHA = 0.05

# Display defaults
DISPLAY_TOP_N_DEFAULT = 10
DISPLAY_TOP_N_MAX = 20
DISPLAY_ANOMALIES_TOP_N = 20

# Timeout and limits
TOOL_EXECUTION_TIMEOUT_MS = 30000
AGENT_ITERATION_LIMIT = 18
AGENT_TOOL_CALL_LIMIT = 30

# File handling
MAX_SEARCH_DEPTH = 2
MAX_DATAFRAME_ROWS_LOG = 1000
FILE_CACHE_TTL_SECONDS = 3600
```

사용:
```python
from qagent_core.constants import STAT_MIN_SAMPLES, DISPLAY_TOP_N_DEFAULT

def detect_anomalies(
    ...,
    min_samples: int = STAT_MIN_SAMPLES,
    top_n: int = DISPLAY_TOP_N_DEFAULT,
) -> Dict[str, Any]:
    ...
```

**기대 효과:**
- 하드코딩된 상수 제거
- 설정값 한 곳에서 관리
- 버전 관리 용이

---

#### 3.2 로깅 표준화

**현재 상황:**
```python
# 로깅 일관성 없음
# qagent_core/tool_executor.py
logger = logging.getLogger(__name__)  # 어딘가만 사용

# qagent_core/data_io.py
# print()나 raise만 사용
```

**개선 방안:**
```python
# qagent_core/logger.py (신규)
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 생성 (일관된 형식)."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

# 모든 모듈에서
from qagent_core.logger import get_logger

logger = get_logger(__name__)

# 사용
logger.info(f"Loaded {len(df)} battles")
logger.warning(f"Missing patch version for {missing_count} records")
logger.error(f"Failed to save review: {e}", exc_info=True)
```

**기대 효과:**
- 일관된 로그 형식
- 디버깅 용이
- 모니터링 통합 가능

---

#### 3.3 매직 숫자 제거

**현재 상황:**
```python
# qagent_core/statistics.py
if len(df) < 30:  # ❌ 매직 숫자

# qagent_core/tool_executor.py
if future.done():
    executor.shutdown(wait=False, cancel_futures=True)  # ❌ Boolean 명확도 낮음

# qagent_core/data_io.py
safe_depth = min(max(int(max_depth), 0), 3)  # ❌ 3은?
```

**개선 방안:**
```python
# qagent_core/constants.py
STAT_MIN_SAMPLES = 30
DEFAULT_MAX_SEARCH_DEPTH = 2

# 사용
if len(df) < STAT_MIN_SAMPLES:
    raise InsufficientDataError(...)

# Boolean 변수명 명확화
if future.done():
    executor.shutdown(wait=False, cancel_futures=True)
    # vs
    task_completed = future.done()
    if task_completed:
        _cleanup_executor(executor, force=True)
```

---

## 📊 개선 효과 요약

| 개선사항 | 난이도 | 예상 효과 | 소요 시간 |
|---------|------|---------|---------|
| 도구 빌더 기본 클래스 | ⭐⭐ | 코드량 ↓50%, 유지보수성 ↑ | 4-6시간 |
| 타입 힌팅 완성 | ⭐⭐ | IDE 자동완성, 오류 사전감지 | 3-4시간 |
| 에러 핸들링 표준화 | ⭐⭐ | 버그 감소, 디버깅 ↑ | 2-3시간 |
| 캐싱 개선 | ⭐ | 응답속도 ↑30-50% | 1-2시간 |
| 스키마 자동 생성 | ⭐⭐⭐ | 유지보수 자동화 | 5-7시간 |
| 진행률 표시 | ⭐ | UX 개선 | 1-2시간 |
| 상수 중앙화 | ⭐ | 관리 효율성 ↑ | 1-2시간 |
| 로깅 표준화 | ⭐⭐ | 모니터링, 디버깅 ↑ | 2-3시간 |

---

## 🔍 추가 제안

### 테스트 커버리지 강화
```python
# tests/test_refactored_tools.py (신규)
import unittest
from qagent_core.tools.base import ToolBuilder
from qagent_core.tools.balance import BalanceToolBuilder

class TestToolBuilderBase(unittest.TestCase):
    """도구 빌더 기본 클래스 테스트."""
    
    def test_context_propagation(self):
        """컨텍스트가 올바르게 빌더에 전파되는가."""
        context = create_mock_context()
        builder = BalanceToolBuilder(context)
        self.assertEqual(builder.battles.shape[0], len(context.battles))
    
    def test_tool_schema_consistency(self):
        """도구 함수와 스키마 매칭."""
        builder = BalanceToolBuilder(context)
        tools = builder.build()
        schemas = generate_all_tool_schemas(context)
        
        for schema in schemas:
            tool_name = schema["function"]["name"]
            self.assertIn(tool_name, tools)
```

### CI/CD 파이프라인
```yaml
# .github/workflows/quality.yml (신규)
name: Code Quality

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt pytest mypy

      - name: Type check
        run: mypy qagent_core --ignore-missing-imports

      - name: Run tests
        run: pytest tests/ -v

      - name: Code coverage
        run: pytest tests/ --cov=qagent_core --cov-report=term
```

### 성능 벤치마크
```python
# scripts/benchmark_tools.py (신규)
import time
import pandas as pd
from qagent_core.tools import build_tool_functions
from qagent_core.tools.context import AnalysisContext

def benchmark_tool(tool_func, *args, **kwargs):
    """단일 도구 벤치마크."""
    start = time.perf_counter()
    result = tool_func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, result

# 사용
context = AnalysisContext.from_data_folder("data/lol_assignment_dataset")
tools = build_tool_functions(context)

results = {}
for tool_name, tool_func in tools.items():
    elapsed, _ = benchmark_tool(tool_func)
    results[tool_name] = elapsed
    print(f"{tool_name}: {elapsed:.3f}s")
```

---

## 📋 구현 체크리스트

### Phase 1: 기초 (2주)
- [ ] `qagent_core/errors.py` 생성 (에러 계층)
- [ ] `qagent_core/tools/base.py` 생성 (도구 기본 클래스)
- [ ] `qagent_core/constants.py` 생성 (상수 중앙화)
- [ ] 기존 도구 마이그레이션 (1개 시작, 검증 후 확대)

### Phase 2: 품질 (2주)
- [ ] 전체 타입 힌팅 추가
- [ ] 로깅 표준화
- [ ] 테스트 커버리지 20% → 50%

### Phase 3: 최적화 (1주)
- [ ] 캐싱 개선
- [ ] 스키마 자동 생성
- [ ] 벤치마크 스크립트

---

## 🎓 결론

이 리팩토링은 QAgent를 **운영 환경으로 전환**하기 위한 기초 작업입니다:

1. **단계적 접근**: 고우선 항목부터 시작하여 점진적 개선
2. **하위호환성**: 스키마/API 유지로 기존 기능 영향 없음
3. **팀 확장성**: 타입 힌팅과 문서화로 새 기여자 온보딩 용이
4. **장기 운영**: 에러 처리/로깅으로 모니터링 및 장애 대응 가능

**권장 시작점**: 도구 기본 클래스 + 타입 힌팅 (가장 높은 ROI)

