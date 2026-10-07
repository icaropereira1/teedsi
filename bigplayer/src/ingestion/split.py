"""Divisão temporal exploração / hold-out."""
from __future__ import annotations

import pandas as pd


def split_exploration_holdout(
    df: pd.DataFrame, holdout_start: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Divide por data de corte (sem embaralhar). Exploração: ts < corte; hold-out: ts >= corte."""
    cut = pd.Timestamp(holdout_start)
    if not df["ts"].is_monotonic_increasing:
        raise ValueError("df precisa estar ordenado por ts antes do split.")
    exploration = df[df["ts"] < cut].reset_index(drop=True)
    holdout = df[df["ts"] >= cut].reset_index(drop=True)
    if exploration.empty or holdout.empty:
        raise ValueError(f"Corte {holdout_start} gera uma das partes vazia.")
    return exploration, holdout
