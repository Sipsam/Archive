from __future__ import annotations

from typing import Any

from qagent_core.risk import assess_balance_risk, generate_retest_plan

from .balance import build_balance_tools
from .context import AnalysisContext
from .dataset import build_dataset_tools
from .patch import build_patch_tools
from .virtual_patch import build_virtual_patch_tools


def build_tool_functions(context: AnalysisContext) -> dict[str, Any]:
    """Build the stable Tool-name registry for one loaded dataset."""
    tools: dict[str, Any] = {}
    for builder in (
        build_dataset_tools, build_balance_tools, build_patch_tools,
        build_virtual_patch_tools,
    ):
        tools.update(builder(context))
    tools.update({
        "assess_balance_risk": assess_balance_risk,
        "generate_retest_plan": generate_retest_plan,
    })
    return tools
