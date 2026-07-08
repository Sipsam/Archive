from __future__ import annotations

from typing import Any, Dict, List

TOOL_DISPLAY_INFO = {
    "get_dataset_overview": {
        "label": "데이터셋 개요 확인",
        "analysis": "전체 전투 수, 패치 버전, 평균 승률, 평균 피해량, 로드된 컬럼을 확인합니다.",
    },
    "get_team_performance": {
        "label": "성능 집계",
        "analysis": "조합, 장비 세트, 딜러, 스킬, 유저 구간별 승률과 평균 피해량을 집계합니다.",
    },
    "detect_anomalies": {
        "label": "밸런스 검토 후보 탐지",
        "analysis": "최소 표본, 승률 차이, Wilson 구간과 FDR 기준으로 추가 검토 후보를 찾습니다.",
    },
    "compare_patch_performance": {
        "label": "패치 버전별 성능 비교",
        "analysis": "특정 조합의 패치 버전별 승률, 피해량, 전투 시간 변화를 비교합니다.",
    },
    "analyze_patch_impact": {
        "label": "패치 영향 분석",
        "analysis": "패치 전후 승률 변화량, 피해량 변화율, 전투 시간 변화율을 계산합니다.",
    },
    "analyze_segment_performance": {
        "label": "유저 구간별 영향 분석",
        "analysis": "beginner, mid, advanced 구간별로 이상 현상이 어디에 집중되는지 확인합니다.",
    },
    "retrieve_related_knowledge": {
        "label": "관련 지식 검색",
        "analysis": "캐릭터, 스킬, 장비 세트, 패치노트에서 이상 조합과 연결되는 근거를 검색합니다.",
    },
    "retrieve_lol_stat_knowledge": {
        "label": "LoL 스탯 공식 검색",
        "analysis": "체력, 방어력, 마법 저항력, 스킬 가속, 공격 속도 등 LoL 스탯 설명과 계산 공식을 검색합니다.",
    },
    "calculate_lol_stat_formulas": {
        "label": "LoL 스탯 공식 계산",
        "analysis": "방어력/마법 저항력 피해 감소, 유효 체력, 스킬 가속, 공격 속도 상한을 계산합니다.",
    },
    "simulate_stat_impact": {
        "label": "스탯 영향 시뮬레이션",
        "analysis": "공격력, 스킬 계수, 세트 보너스, 버프 효과를 이용해 예상 피해량 증가율을 근사 계산합니다.",
    },
    "calculate_adjustment_options": {
        "label": "밸런스 조정안 계산",
        "analysis": "패치 전후 수치를 바탕으로 완전 롤백이 아닌 부분 조정안을 계산합니다.",
    },
    "assess_balance_risk": {
        "label": "밸런스 리스크 평가",
        "analysis": "승률, 평균 대비 차이, 패치 영향, 예상 피해량 증가율을 바탕으로 리스크 등급을 산정합니다.",
    },
    "generate_virtual_patch_note": {
        "label": "가상 패치노트 생성",
        "analysis": "Agent 조정안을 현 버전 이후의 가상 패치 후보로 구조화하고, 승률/피해량 변화 가정을 기록합니다.",
    },
    "simulate_virtual_patch_impact": {
        "label": "가상 패치 시나리오 추정",
        "analysis": "가상 패치가 적용된 미래 버전을 가정해 승률, 평균 피해량, 게임 시간, 티어별 영향을 근사 추론합니다.",
    },
    "reflect_on_virtual_patch": {
        "label": "Agent 자기반성",
        "analysis": "Agent가 자신이 제안한 가상 패치의 과조정 위험, 표본 부족, 티어별 부작용을 비판적으로 검토합니다.",
    },
    "generate_retest_plan": {
        "label": "재테스트 계획 생성",
        "analysis": "리스크 수준에 맞춰 유저 구간별 재테스트 수와 Human Review 단계를 제안합니다.",
    },
}


def render_live_trace(trace: List[Dict[str, Any]], current_message: str = "") -> str:
    """Render the agent's live tool trace as Streamlit-compatible Markdown."""
    lines = []

    if current_message:
        lines.extend((f"**현재 상태:** {current_message}", ""))

    if not trace:
        lines.append("아직 실행된 Tool이 없습니다.")
        return "\n".join(lines)

    lines.append("### 실시간 Tool 실행 로그")
    if trace[0].get("run_id"):
        lines.append(f"- 실행 ID: `{trace[0]['run_id']}`")
    lines.append("")

    for idx, step in enumerate(trace, start=1):
        tool_name = step.get("tool", "unknown")
        info = TOOL_DISPLAY_INFO.get(tool_name, {"label": tool_name, "analysis": ""})
        status_icon = "✅" if step.get("finished") else "🔄"
        lines.append(f"{status_icon} **Step {idx}. {info['label']}** `{tool_name}`")

        if info.get("analysis"):
            lines.append(f"- 분석 내용: {info['analysis']}")
        if step.get("input_summary"):
            lines.append(f"- 입력 요약: `{step['input_summary']}`")
        if step.get("summary"):
            lines.append(f"- 결과 요약: {step['summary']}")
        if step.get("finished"):
            status = "성공" if step.get("success") else "실패"
            lines.append(
                f"- 상태: {status}, 실행 시간: "
                f"{float(step.get('duration_ms', 0)):.2f}ms"
            )
        lines.append("")

    return "\n".join(lines)


def summarize_tool_result(tool_name: str, result: Dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return "도구 실행 결과를 요약할 수 없습니다."

    status = result.get("status", "unknown")
    if status in {"error", "timeout"}:
        return f"오류 발생: {result.get('message', 'unknown error')}"
    if status == "empty":
        return result.get("message", "조건에 맞는 데이터가 없습니다.")

    if tool_name == "get_dataset_overview":
        return (
            f"전투 로그 {result.get('battle_rows', 0):,}건, "
            f"전체 승률 {float(result.get('overall_win_rate', 0))*100:.1f}%, "
            f"패치 버전 {result.get('patch_versions', [])} 확인"
        )

    if tool_name == "detect_anomalies":
        anomalies = result.get("anomalies", [])
        if anomalies:
            top = anomalies[0]
            return (
                f"검토 후보 {len(anomalies)}건 탐지. "
                f"최상위 후보: {top.get('player_team')} / 승률 {float(top.get('win_rate', 0))*100:.1f}%"
            )
        return "현재 통계 기준을 모두 통과한 추가 검토 후보가 없습니다."

    if tool_name == "analyze_patch_impact":
        impact = result.get("impact", {})
        if impact:
            return (
                f"패치 전후 승률 변화 {float(impact.get('win_rate_change', 0))*100:.1f}%p, "
                f"피해량 변화 {float(impact.get('damage_change_rate', 0))*100:.1f}% 계산"
            )
        return "패치 전후 비교가 가능한 충분한 데이터가 없습니다."

    if tool_name == "analyze_segment_performance":
        rows = result.get("rows", [])
        return f"유저 구간별 성능 행 {len(rows)}건 분석"

    if tool_name == "retrieve_related_knowledge":
        return (
            f"캐릭터 {len(result.get('characters', []))}건, "
            f"스킬 {len(result.get('skills', []))}건, "
            f"장비 {len(result.get('equipment_sets', []))}건, "
            f"패치 근거 {len(result.get('patch_matches', []))}건 검색"
        )

    if tool_name == "retrieve_lol_stat_knowledge":
        return f"LoL 스탯 공식 {len(result.get('rows', []))}건 검색"

    if tool_name == "calculate_lol_stat_formulas":
        defense = result.get("defense", {})
        haste = result.get("haste", {})
        return (
            f"물리 피해 감소 {float(defense.get('physical_damage_reduction', 0))*100:.1f}%, "
            f"마법 피해 감소 {float(defense.get('magic_damage_reduction', 0))*100:.1f}%, "
            f"스킬 가속 쿨감 {float(haste.get('cooldown_reduction', 0))*100:.1f}% 계산"
        )

    if tool_name == "simulate_stat_impact":
        return f"예상 피해량 증가율 {float(result.get('estimated_increase_rate', 0))*100:.1f}% 계산"

    if tool_name == "calculate_adjustment_options":
        return f"조정안 {len(result.get('actions', []))}건 생성"

    if tool_name == "assess_balance_risk":
        return (
            f"리스크 등급 {result.get('risk_level', 'unknown')}, "
            f"점수 {result.get('risk_score', 0)}점 산정"
        )

    if tool_name == "generate_virtual_patch_note":
        note = result.get("virtual_patch_note", {})
        return (
            f"가상 패치 {note.get('virtual_patch_version', '')} 후보 생성. "
            f"대상 {note.get('target', '')}, 방향 {note.get('action', '')}"
        )

    if tool_name == "simulate_virtual_patch_impact":
        after = result.get("projected_after", {})
        return (
            f"가상 적용 시나리오 승률 {float(after.get('win_rate', 0))*100:.1f}%, "
            f"시나리오 평균 피해량 {float(after.get('avg_damage', 0)):,.0f}, "
            f"신뢰도 {result.get('confidence', 'unknown')}"
        )

    if tool_name == "reflect_on_virtual_patch":
        reflection = result.get("self_reflection", {})
        return (
            f"자기반성 완료. Agent 권고: {reflection.get('agent_recommendation', 'unknown')}, "
            f"우려 {len(reflection.get('concerns', []))}건"
        )

    if tool_name == "generate_retest_plan":
        return f"총 재테스트 {result.get('total_required_battles', 0):,}전 계획 생성"

    if tool_name == "get_team_performance":
        return f"{result.get('group_by', '')} 기준 성능 {len(result.get('rows', []))}건 집계"

    if tool_name == "compare_patch_performance":
        return f"패치 버전별 성능 {len(result.get('rows', []))}건 비교"

    return f"도구 실행 완료: status={status}"
