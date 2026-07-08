
import os
import re
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from qagent_core.config import (
    AGENT_TIMEOUT_SECONDS, APP_NAME, APP_VERSION, DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT, ENABLE_DEBUG_LOG, ENABLE_TOOL_TRACE,
    MAX_AGENT_ITERATIONS, MAX_TOOL_CALLS, BALANCE_FDR_ALPHA,
    BALANCE_MIN_SAMPLES, BALANCE_MIN_WILSON_DIFF, BALANCE_MIN_WIN_RATE,
    BALANCE_MIN_WIN_RATE_DIFF, get_secret,
)
from qagent_core.runtime import (
    input_summary, new_run_id, output_summary, safe_error_message, safe_for_log,
)
from qagent_core.data_io import (
    EXPECTED_DATA_FILES as CORE_EXPECTED_DATA_FILES,
    load_data_folder as core_load_data_folder,
    load_csv as core_load_csv,
    file_signature as _file_cache_key,
    discover_data_folders as core_discover_data_folders,
    summarize_battle_metrics,
    validate_required_columns as core_validate_required_columns,
)
from qagent_core.persistence import (
    ReviewPersistenceError,
    SQLiteReviewRepository,
    export_json_record,
    save_review_with_mirrors,
)
from qagent_core.statistics import (
    analyze_balance_stages, detect_balance_candidates,
    win_rate,
)
from qagent_core.simulation import (
    SCENARIO_WARNINGS, project_patch_scenario, project_patch_scenario_range,
)
from qagent_core.risk import assess_balance_risk, generate_retest_plan
from qagent_core.utils import (
    LOL_STAT_KNOWLEDGE, apply_lol_patch_version_mapping, ensure_column,
    first_existing_column, format_value, get_latest_patch_version,
    get_previous_patch_version, map_game_version_to_patch_version,
    normalize_existing_patch_version, normalize_master_tables, normalize_text,
    parse_number, patch_sort_key, pct, search_lol_stat_knowledge, split_team,
    to_jsonable_df,
)
from qagent_core.tool_registry import TOOL_SCHEMAS
from qagent_core.tool_executor import ToolExecutor
from qagent_core.tools import AnalysisContext, build_tool_functions
from qagent_core.agent import (
    choose_effective_openai_api, normalize_api_mode, normalize_reasoning_effort,
    run_generative_agent,
)
from qagent_core.agent.followup import get_latest_tool_result
from qagent_core.agent.presentation import render_live_trace, summarize_tool_result
from qagent_core.agent.prompts import build_user_prompt
from qagent_core.review.service import (
    build_review_record, load_review_logs, now_kst_iso,
)


# =========================================================
# Battle Balance Analyst Generative AI Agent
# Assignment-oriented improved version
#
# 개선점:
# 1. Patch Impact Analyzer Tool
# 2. Segment Performance Analyzer Tool
# 3. Stat Simulator Tool
# 4. Balance Risk Assessment Tool
# 5. Retest Plan Generator Tool
# 6. Stronger tool-calling system prompt
# 7. Safer CSV column normalization
# =========================================================

st.set_page_config(
    page_title=f"Battle Balance Analyst Agent v{APP_VERSION}",
    page_icon="🎮",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "data"
SAMPLE_DATA_DIR = DATA_DIR
LOL_DATA_DIR = DATA_DIR / "lol_assignment_dataset"
HITL_DIR = DATA_DIR / "human_review"
REVIEW_LOG_PATH = HITL_DIR / "review_logs.csv"
REVIEW_RECORDS_DIR = HITL_DIR / "records"
REVIEW_DB_PATH = HITL_DIR / "reviews.sqlite3"

STATE_AGENT_RESULT = "last_agent_result"
STATE_REVIEW_LOG = "last_review_log"
EMPTY_RESULT_MESSAGE = "아직 실행 결과가 없습니다. Agent를 실행하면 이 영역에 결과가 표시됩니다."

REQUIRED_BATTLE_COLUMNS = [
    "battle_id", "patch_version", "player_team", "enemy_team", "result",
    "duration_sec", "main_dealer", "total_damage", "skill_used_most",
    "equipment_set", "user_segment", "battle_mode"
]


@st.cache_data(show_spinner=False)
def _load_csv_path_cached(path_text: str, modified_ns: int, file_size: int) -> pd.DataFrame:
    # modified_ns and file_size are cache-key inputs; path_text is the data source.
    _ = modified_ns, file_size
    return core_load_csv(path_text)


@st.cache_data(show_spinner=False)
def _load_data_folder_cached(
    folder_text: str,
    file_signature: tuple[tuple[str, int, int], ...],
) -> dict[str, pd.DataFrame]:
    # file_signature invalidates the cache when any required CSV changes.
    _ = file_signature
    loaded = core_load_data_folder(Path(folder_text))
    characters, skills, equipment_sets, patch_notes = normalize_master_tables(
        loaded["characters"], loaded["skills"], loaded["equipment_sets"], loaded["patch_notes"]
    )
    loaded.update({
        "battle_logs": apply_lol_patch_version_mapping(loaded["battle_logs"]),
        "characters": characters,
        "skills": skills,
        "equipment_sets": equipment_sets,
        "patch_notes": patch_notes,
    })
    return loaded



def load_csv(uploaded_file, sample_path: Path) -> pd.DataFrame:
    dataset_name = sample_path.stem if sample_path.stem in EXPECTED_DATA_FILES else None
    if uploaded_file is not None:
        return core_load_csv(uploaded_file, name=dataset_name)
    path_text, modified_ns, file_size = _file_cache_key(sample_path)
    frame = _load_csv_path_cached(path_text, modified_ns, file_size)
    # Cached reads and uploaded reads enforce the same dataset contract.
    if dataset_name is not None:
        core_validate_required_columns(dataset_name, frame)
    return frame


EXPECTED_DATA_FILES = CORE_EXPECTED_DATA_FILES


@st.cache_data(ttl=30, show_spinner=False)
def find_data_folders(search_roots: tuple[str, ...]) -> List[Path]:
    """명시적인 데이터 루트에서 최대 2단계까지만 자동 탐색."""
    return core_discover_data_folders(search_roots, max_depth=2)


def load_data_from_folder(folder: Path):
    """선택한 폴더에서 CSV 5개를 자동으로 연결."""
    resolved = folder.resolve()
    signature = tuple(_file_cache_key(resolved / filename) for filename in EXPECTED_DATA_FILES.values())
    loaded = _load_data_folder_cached(str(resolved), signature)
    return tuple(loaded[name] for name in EXPECTED_DATA_FILES)


# =========================================================
# Tool factory
# =========================================================

def make_tool_functions(
    battles: pd.DataFrame,
    characters: pd.DataFrame,
    skills: pd.DataFrame,
    equipment_sets: pd.DataFrame,
    patch_notes: pd.DataFrame,
):
    return build_tool_functions(AnalysisContext(
        battles=battles,
        characters=characters,
        skills=skills,
        equipment_sets=equipment_sets,
        patch_notes=patch_notes,
    ))







# =========================================================
# Live Tool Trace UI helpers
# =========================================================





# =========================================================
# Generative Agent Loop
# =========================================================



# =========================================================
# Dataset profile helpers
# =========================================================

def detect_dataset_profile(battles: pd.DataFrame) -> str:
    cols = set(battles.columns)
    if {"champion_name", "queue_id", "match_id"}.issubset(cols):
        return "League of Legends"
    return "Sample RPG"





# =========================================================
# HITL Review helpers
# =========================================================





















def render_review_logs_panel() -> None:
    with st.expander("저장된 HITL 검토 로그"):
        try:
            logs_df = load_review_logs()
        except ReviewPersistenceError as error:
            st.error(str(error))
            return
        if logs_df.empty:
            st.info("아직 저장된 Human Review 로그가 없습니다.")
            return
        st.dataframe(logs_df.tail(20).iloc[::-1], width="stretch")
        st.download_button(
            "review_logs.csv 다운로드",
            data=logs_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name="review_logs.csv",
            mime="text/csv",
        )

# =========================================================
# UI
# =========================================================

st.title(f"{APP_NAME} v{APP_VERSION}")
st.caption("가상 예제 및 LoL 데이터를 분석하고, 가상 패치 후보와 휴리스틱 기반 시나리오 추정, Agent 자기반성, HITL 검토 기록을 지원하는 PoC용 밸런스 분석 Agent")

with st.sidebar:
    st.header("LLM Agent 설정")
    api_key = st.text_input("OpenAI API Key", type="password", value=get_secret("OPENAI_API_KEY"))
    if not api_key:
        st.caption("OPENAI_API_KEY가 없습니다. 로컬 .env 또는 배포 환경의 Secret 저장소에 설정하세요. 키를 txt 파일에 저장하지 마세요.")

    model_options = [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.5",
        "gpt-5.5-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o-mini",
        "직접 입력",
    ]
    env_model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    default_model_choice = env_model if env_model in model_options else "직접 입력"
    model_choice = st.selectbox(
        "Model",
        model_options,
        index=model_options.index(default_model_choice),
        help="gpt-5.x reasoning 모델을 사용할 수 있습니다. 목록에 없으면 직접 입력을 선택하세요.",
    )
    if model_choice == "직접 입력":
        model = st.text_input("직접 입력 모델명", value=env_model)
    else:
        model = model_choice

    reasoning_options = ["none", "minimal", "low", "medium", "high", "xhigh"]
    env_reasoning = normalize_reasoning_effort(os.getenv("OPENAI_REASONING_EFFORT", DEFAULT_REASONING_EFFORT))
    if env_reasoning not in reasoning_options:
        env_reasoning = "none"
    reasoning_effort = st.selectbox(
        "Reasoning effort",
        reasoning_options,
        index=reasoning_options.index(env_reasoning),
        help="reasoning을 none이 아닌 값으로 선택하면 자동 모드에서 Responses API를 사용합니다.",
    )

    api_mode_options = ["자동", "Responses API", "Chat Completions"]
    env_api_mode = os.getenv("OPENAI_API_MODE", "자동")
    if normalize_api_mode(env_api_mode) == "responses":
        default_api_mode = "Responses API"
    elif normalize_api_mode(env_api_mode) == "chat_completions":
        default_api_mode = "Chat Completions"
    else:
        default_api_mode = "자동"
    api_mode_label = st.selectbox(
        "OpenAI API 방식",
        api_mode_options,
        index=api_mode_options.index(default_api_mode),
        help="자동: gpt-5 계열 또는 reasoning 사용 시 Responses API, 그 외에는 Chat Completions를 사용합니다.",
    )
    api_mode = normalize_api_mode(api_mode_label)
    effective_api_preview = choose_effective_openai_api(api_mode, reasoning_effort, model)
    st.caption(f"실행 예정 API: {effective_api_preview} / reasoning: {reasoning_effort}")

    st.divider()
    min_samples = st.slider("권장 최소 표본 수", 10, 200, BALANCE_MIN_SAMPLES, 1)
    win_rate_threshold = st.slider("권장 검토 후보 승률 기준", 0.50, 0.99, BALANCE_MIN_WIN_RATE, 0.01)
    win_rate_gap = st.slider("권장 평균 대비 차이", 0.01, 0.60, BALANCE_MIN_WIN_RATE_DIFF, 0.01)

st.subheader("1. 데이터 입력")

data_mode = st.radio(
    "데이터 연결 방식",
    ["기본 샘플 데이터", "LoL 데이터", "폴더에서 자동 연결", "CSV 직접 업로드"],
    horizontal=True,
)

selected_data_folder = None
battle_file = character_file = skill_file = equipment_file = patch_file = None

if data_mode == "기본 샘플 데이터":
    try:
        battles = load_csv(None, SAMPLE_DATA_DIR / "battle_logs.csv")
        characters = load_csv(None, SAMPLE_DATA_DIR / "characters.csv")
        skills = load_csv(None, SAMPLE_DATA_DIR / "skills.csv")
        equipment_sets = load_csv(None, SAMPLE_DATA_DIR / "equipment_sets.csv")
        patch_notes = load_csv(None, SAMPLE_DATA_DIR / "patch_notes.csv")
        selected_data_folder = SAMPLE_DATA_DIR
        st.success("기본 가상 예제 데이터를 불러왔습니다.")
    except Exception as e:
        st.error(f"기본 샘플 데이터를 불러오지 못했습니다: {e}")
        st.info("data 폴더에 battle_logs.csv, characters.csv, skills.csv, equipment_sets.csv, patch_notes.csv가 있는지 확인하세요.")
        st.stop()

elif data_mode == "LoL 데이터":
    try:
        battles, characters, skills, equipment_sets, patch_notes = load_data_from_folder(LOL_DATA_DIR)
        selected_data_folder = LOL_DATA_DIR
        st.success(f"League of Legends 데이터셋을 불러왔습니다: {LOL_DATA_DIR}")
        summary_path = LOL_DATA_DIR / "dataset_summary.json"
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                st.json(json.load(f))
    except Exception as e:
        st.error(f"LoL 데이터셋을 불러오지 못했습니다: {e}")
        st.info("data/lol_assignment_dataset 폴더에 필수 CSV 5개가 있는지 확인하세요.")
        st.stop()

elif data_mode == "폴더에서 자동 연결":
    st.markdown(
        """
        아래 방식 중 하나로 데이터 폴더를 선택하세요.  
        선택한 폴더 안에 CSV 5개가 있으면 자동으로 연결됩니다.
        """
    )

    # 자동 탐색은 프로젝트의 명시적 data 루트로 제한한다. 그 밖의
    # 위치는 아래의 직접 경로 입력으로 선택하고 동일한 검증을 받는다.
    search_roots = [DATA_DIR]
    auto_folders = find_data_folders(search_roots)

    folder_options = ["직접 경로 입력"] + [str(p) for p in auto_folders]

    folder_choice = st.selectbox(
        "자동 탐색된 데이터 폴더",
        folder_options,
        help="필수 CSV 5개가 들어 있는 폴더만 자동으로 표시됩니다.",
    )

    manual_folder = ""
    if folder_choice == "직접 경로 입력":
        manual_folder = st.text_input(
            "데이터 폴더 경로",
            value="",
            placeholder=r"예: D:\battle_balance_project\data\lol_assignment_dataset",
            help="battle_logs.csv, characters.csv, skills.csv, equipment_sets.csv, patch_notes.csv가 들어 있는 폴더 경로를 입력하세요.",
        )
        if manual_folder.strip():
            selected_data_folder = Path(manual_folder.strip().strip('"'))
    else:
        selected_data_folder = Path(folder_choice)

    with st.expander("필수 파일명 확인"):
        st.code(
            "\n".join(EXPECTED_DATA_FILES.values()),
            language="text",
        )

    if selected_data_folder is not None:
        try:
            battles, characters, skills, equipment_sets, patch_notes = load_data_from_folder(selected_data_folder)
            st.success(f"데이터 폴더 연결 완료: {selected_data_folder}")
        except Exception as e:
            st.error(f"데이터 폴더를 불러오지 못했습니다: {e}")
            st.stop()
    else:
        st.info("데이터 폴더를 선택하거나 경로를 입력하면 자동으로 CSV를 연결합니다.")
        st.stop()

elif data_mode == "CSV 직접 업로드":
    col1, col2 = st.columns(2)
    with col1:
        battle_file = st.file_uploader("전투 로그 CSV", type=["csv"])
        character_file = st.file_uploader("캐릭터/챔피언 정보 CSV", type=["csv"])
        skill_file = st.file_uploader("스킬 정보 CSV", type=["csv"])
    with col2:
        equipment_file = st.file_uploader("장비/아이템 CSV", type=["csv"])
        patch_file = st.file_uploader("패치노트 CSV", type=["csv"])

    fallback_folder = LOL_DATA_DIR if LOL_DATA_DIR.exists() else SAMPLE_DATA_DIR
    battles = load_csv(battle_file, fallback_folder / "battle_logs.csv")
    characters = load_csv(character_file, fallback_folder / "characters.csv")
    skills = load_csv(skill_file, fallback_folder / "skills.csv")
    equipment_sets = load_csv(equipment_file, fallback_folder / "equipment_sets.csv")
    patch_notes = load_csv(patch_file, fallback_folder / "patch_notes.csv")
    selected_data_folder = fallback_folder

characters, skills, equipment_sets, patch_notes = normalize_master_tables(
    characters, skills, equipment_sets, patch_notes
)

# LoL 데이터는 Riot gameVersion과 패치노트 version 표기가 다를 수 있어 앱 로드 시 정규화한다.
battles = apply_lol_patch_version_mapping(battles)

missing = [c for c in REQUIRED_BATTLE_COLUMNS if c not in battles.columns]
if missing:
    st.error(f"전투 로그 필수 컬럼이 누락되었습니다: {missing}")
    st.stop()

st.success("데이터 로드 완료")

with st.expander("로드된 컬럼 확인"):
    if selected_data_folder is not None:
        st.write("선택된 데이터 폴더:", str(selected_data_folder))
    st.write("battle_logs:", list(battles.columns))
    st.write("characters:", list(characters.columns))
    st.write("skills:", list(skills.columns))
    st.write("equipment_sets:", list(equipment_sets.columns))
    st.write("patch_notes:", list(patch_notes.columns))

with st.expander("전투 로그 미리보기"):
    st.dataframe(battles.head(20), width="stretch")

st.subheader("2. Agent 목표 입력")

data_profile = detect_dataset_profile(battles)
st.info(f"현재 데이터 프로필: {data_profile}")

if data_profile == "League of Legends":
    with st.expander("LoL 패치 버전 매핑 / 스탯 공식 지식 베이스"):
        st.markdown(
            """
            **패치 버전 매핑 규칙**
            - 게임버전 `1.x ~ 14.x` → 패치노트 버전 `1.x ~ 14.x` 그대로 사용
            - 게임버전 `15.x` → 패치노트 버전 `25.xx`
            - 게임버전 `16.x` → 패치노트 버전 `26.xx`
            - 예: `14.10.000` → `14.10`, `16.3.000` → `26.03`, `16.13.000` → `26.13`
            """
        )
        if "game_version" in battles.columns:
            preview_cols = [c for c in ["game_version", "original_patch_version", "patch_version"] if c in battles.columns]
            st.dataframe(
                battles[preview_cols].drop_duplicates().sort_values("patch_version", key=lambda s: s.map(patch_sort_key)).head(20),
                width="stretch",
            )
        st.markdown("**내장 LoL 스탯 공식 지식 베이스**")
        st.dataframe(pd.DataFrame(LOL_STAT_KNOWLEDGE), width="stretch")

default_goal = build_user_prompt(
    data_profile=data_profile,
    min_samples=min_samples,
    win_rate_threshold=win_rate_threshold,
    win_rate_gap=win_rate_gap,
)

user_goal = st.text_area("Agent에게 줄 업무 지시", value=default_goal, height=360)
run = st.button("생성형 AI Agent 실행", type="primary")

if run:
    if not api_key:
        st.error("생성형 AI Agent 모드는 OpenAI API Key가 필요합니다.")
        st.stop()

    tool_functions = make_tool_functions(battles, characters, skills, equipment_sets, patch_notes)

    st.subheader("3. 실시간 Agent 실행 상태")
    live_progress_placeholder = st.empty()
    live_log_placeholder = st.empty()
    live_log_placeholder.info("Agent 실행을 시작합니다.")

    with st.spinner("LLM Agent가 tool을 선택하고 분석 중입니다..."):
        try:
            final_answer, trace, messages = run_generative_agent(
                api_key=api_key,
                model=model,
                user_goal=user_goal,
                tool_functions=tool_functions,
                max_turns=MAX_AGENT_ITERATIONS,
                live_placeholder=live_log_placeholder,
                progress_placeholder=live_progress_placeholder,
                reasoning_effort=reasoning_effort,
                api_mode=api_mode,
            )
        except Exception as e:
            st.error(f"Agent 실행 실패: {e}")
            if ENABLE_DEBUG_LOG:
                st.code(type(e).__name__)
            st.stop()

    run_id = str(trace[0].get("run_id", "")) if trace else str(messages[0].get("run_id", new_run_id()))
    st.session_state["last_agent_result"] = {
        "run_id": run_id,
        "created_at_kst": now_kst_iso(),
        "model": model,
        "reasoning_effort": reasoning_effort,
        "api_mode": api_mode,
        "effective_api": choose_effective_openai_api(api_mode, reasoning_effort, model),
        "user_goal": "[USER_INPUT_REDACTED]",
        "data_profile": data_profile,
        "selected_data_folder": str(selected_data_folder) if selected_data_folder else "",
        "final_answer": final_answer,
        "trace": trace,
        "messages": messages,
    }

agent_state = st.session_state.get("last_agent_result")

if agent_state:
    trace = agent_state.get("trace", [])
    final_answer = agent_state.get("final_answer", "")
    messages = agent_state.get("messages", [])

    st.subheader("4. Agent Tool Call Trace 상세")
    st.caption(f"실행 ID: {agent_state.get('run_id', '')} / 제한: 반복 {MAX_AGENT_ITERATIONS}회, Tool {MAX_TOOL_CALLS}회, {AGENT_TIMEOUT_SECONDS}초")
    if trace:
        for i, step in enumerate(trace, start=1):
            with st.expander(f"{i}. {step['tool']}"):
                st.write("입력 요약:", step.get("input_summary", ""))
                st.write("출력 요약:", step.get("output_summary", step.get("summary", "")))
                st.write("상태:", "성공" if step.get("success") else "실패")
                st.write("실행 시간(ms):", step.get("duration_ms", 0))
                if ENABLE_TOOL_TRACE:
                    st.markdown("**안전 처리된 입력/결과**")
                    st.json({"arguments": step.get("arguments", {}), "result": step.get("result", {})})
    else:
        st.warning("Tool call이 발생하지 않았습니다. 지시문에 '반드시 tool을 호출'하도록 더 명확히 적어보세요.")

    st.subheader("5. 생성형 AI Agent 최종 분석")
    st.markdown(final_answer)

    st.subheader("6. Virtual Patch Scenario Estimate & HITL Review Gate")
    st.markdown(
        """
        이 단계는 **AI 제안을 바로 적용하지 않고 사람이 검토하는 Human-in-the-loop 단계**입니다.  
        Agent가 만든 가상 패치노트, 가상 적용 시나리오 추정, 자기반성 결과를 사람이 보고 승인/거절/수정요청/재테스트 여부를 기록합니다.  
        `Approve Virtual Patch`는 실제 게임 패치를 자동 적용한다는 뜻이 아니라, **가상 패치 후보를 사람이 검토 후 승인 기록**한다는 의미입니다.
        영향 수치는 **휴리스틱 기반 시나리오 추정**이며, 예측 모델이나 게임 엔진 시뮬레이션 결과가 아닙니다.
        """
    )

    review_cols = st.columns(4)
    review_cols[0].metric(
        "Tool 호출 수", sum(bool(step.get("executed")) for step in trace)
    )
    review_cols[1].metric("데이터 프로필", agent_state.get("data_profile", data_profile))
    review_cols[2].metric("실행 모델", agent_state.get("model", model))
    st.caption(
        f"OpenAI API: {agent_state.get('effective_api', choose_effective_openai_api(api_mode, reasoning_effort, model))} / "
        f"Reasoning effort: {agent_state.get('reasoning_effort', reasoning_effort)}"
    )
    review_cols[3].metric("검토 로그", "저장 가능")

    virtual_patch = get_latest_tool_result(trace, "generate_virtual_patch_note")
    virtual_simulation = get_latest_tool_result(trace, "simulate_virtual_patch_impact")
    virtual_reflection = get_latest_tool_result(trace, "reflect_on_virtual_patch")

    st.markdown("### Agent 가상 패치 검토 자료")
    if virtual_patch:
        note = virtual_patch.get("virtual_patch_note", {})
        st.markdown("**가상 패치노트 후보**")
        if virtual_patch.get("patch_note_markdown"):
            st.markdown(virtual_patch.get("patch_note_markdown"))
        with st.expander("가상 패치노트 구조화 데이터"):
            st.json(virtual_patch)
    else:
        st.warning("이번 실행에서 `generate_virtual_patch_note` Tool 결과가 없습니다. 기본 프롬프트를 유지하고 다시 실행하면 가상 패치노트 단계가 포함됩니다.")

    if virtual_simulation:
        st.markdown("**가정 기반 영향 시나리오 추정**")
        st.warning("아래 수치는 입력 가정에 따른 휴리스틱 시나리오 추정입니다. 실제 예측 모델이나 게임 엔진 시뮬레이션 결과가 아니며 실제 패치 전 QA 테스트가 필요합니다.")
        sim_cols = st.columns(4)
        before = virtual_simulation.get("before", {})
        after = virtual_simulation.get("projected_after", {})
        sim_cols[0].metric("현재 승률", f"{float(before.get('win_rate') or 0) * 100:.1f}%")
        sim_cols[1].metric("시나리오 승률", f"{float(after.get('win_rate') or 0) * 100:.1f}%")
        sim_cols[2].metric("현재 평균 피해량", f"{float(before.get('avg_damage') or 0):,.0f}")
        sim_cols[3].metric("시나리오 평균 피해량", f"{float(after.get('avg_damage') or 0):,.0f}")
        scenario_rows = []
        for scenario_name, scenario in virtual_simulation.get("scenarios", {}).items():
            scenario_rows.append({
                "시나리오": scenario_name,
                "효과 배수": scenario.get("assumed_effect_multiplier"),
                "시나리오 승률": scenario.get("scenario_win_rate"),
                "피해량 변화 가정": scenario.get("scenario_damage_change"),
                "리스크 안내": scenario.get("risk_note"),
            })
        if scenario_rows:
            st.dataframe(pd.DataFrame(scenario_rows), width="stretch")
        with st.expander("가상 패치 시나리오 추정 상세"):
            st.json(virtual_simulation)
    else:
        st.info("가정 기반 영향 시나리오 추정 결과가 없습니다. 가상 패치노트가 생성되도록 다시 실행해보세요.")

    if virtual_reflection:
        st.markdown("**Agent 자기반성**")
        reflection_body = virtual_reflection.get("self_reflection", {})
        st.write("Agent 권고:", reflection_body.get("agent_recommendation", ""))
        col_pos, col_con = st.columns(2)
        with col_pos:
            st.markdown("긍정 근거")
            for item in reflection_body.get("positives", []):
                st.write(f"- {item}")
        with col_con:
            st.markdown("우려/한계")
            for item in reflection_body.get("concerns", []):
                st.write(f"- {item}")
        with st.expander("Agent 자기반성 상세"):
            st.json(virtual_reflection)
    else:
        st.info("Agent 자기반성 결과가 아직 없습니다. 이번 버전에서는 가상 패치노트가 생성되면 앱이 이 단계를 자동 보완하도록 수정했습니다. 다시 실행해보세요.")

    with st.form("hitl_review_form"):
        st.markdown("### Human Review 입력")
        col1, col2 = st.columns(2)
        with col1:
            reviewer = st.text_input("검토자", value="QA/밸런스 담당자")
            review_status = st.selectbox(
                "검토 상태",
                ["Pending", "Approve Virtual Patch", "Reject Virtual Patch", "Needs Revision", "Retest Required", "Save as Candidate"],
                index=0,
            )
            human_risk_level = st.selectbox(
                "사람이 판단한 최종 리스크",
                ["Unconfirmed", "Low", "Medium", "High", "Critical"],
                index=0,
            )
        with col2:
            review_target = st.text_input(
                "검토 대상",
                value="Agent가 제시한 가상 패치노트 후보",
                help="예: 특정 챔피언, 아이템, 포지션, 패치 버전 조합",
            )
            next_action = st.selectbox(
                "후속 액션",
                [
                    "모니터링 유지",
                    "추가 데이터 수집",
                    "재테스트 진행",
                    "가상 패치 후보 승인 기록",
                    "가상 패치 후보 거절 기록",
                    "부분 조정안 재작성",
                    "분석 재실행",
                    "조치 없음",
                ],
                index=1,
            )
            followup_owner = st.text_input("후속 담당", value="QA / Balance Designer")

        human_comment = st.text_area(
            "검토 의견 / 승인·반려·재테스트 사유",
            value="가상 패치노트의 가정 기반 시나리오 변화, Agent 자기반성, 표본 수, 티어별 부작용, 패치노트 근거를 확인한 뒤 승인/거절/수정/재테스트 여부를 판단.",
            height=140,
        )

        save_review = st.form_submit_button("가상 패치 HITL 검토 로그 저장", type="primary")

    if save_review:
        try:
            log_row, artifact = build_review_record(
                agent_state=agent_state,
                data_profile=data_profile,
                selected_data_folder=selected_data_folder,
                reviewer=reviewer,
                review_status=review_status,
                human_risk_level=human_risk_level,
                review_target=review_target,
                human_comment=human_comment,
                next_action=next_action,
                followup_owner=followup_owner,
            )
            st.session_state["last_review_log"] = log_row
            storage_result = log_row.get("storage_result", {})
            if storage_result.get("status") == "saved":
                st.success(f"HITL 검토 로그와 호환 export 저장 완료: {log_row['review_id']}")
            else:
                st.warning(
                    f"HITL 검토 로그는 SQLite에 저장됐지만 일부 export가 실패했습니다: "
                    f"{log_row['review_id']}"
                )
                st.warning(storage_result.get("mirror_warning", "호환 export 상태를 확인하세요."))
            st.json(log_row)
        except ReviewPersistenceError as error:
            st.error(f"HITL 검토 기록을 저장하지 못했습니다: {error}")
            storage_result = getattr(error, "storage_result", None)
            if storage_result:
                st.json(storage_result)

    if st.session_state.get("last_review_log"):
        st.info(f"최근 저장된 검토 상태: {st.session_state['last_review_log'].get('review_status')}")

    render_review_logs_panel()

    with st.expander("Debug: 전체 메시지"):
        st.json(messages)
else:
    st.subheader("3. Virtual Patch Scenario Estimate & HITL Review Gate")
    st.info("Agent를 먼저 실행하면 Tool Trace, 가상 패치노트, 가정 기반 시나리오 추정, Agent 자기반성, Human Review 저장 폼이 표시됩니다.")
    render_review_logs_panel()
