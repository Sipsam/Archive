from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AnalysisContext:
    """Immutable references to the five frames shared by analysis Tools."""

    battles: pd.DataFrame
    characters: pd.DataFrame
    skills: pd.DataFrame
    equipment_sets: pd.DataFrame
    patch_notes: pd.DataFrame
