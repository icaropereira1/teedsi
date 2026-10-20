"""Estudo de evento: retorno futuro condicional ao evento, com controle pareado e bootstrap por dia.

Regra de realismo: o sinal da barra fechada em `t` executa na ABERTURA da próxima barra com negócio
(`ts >= t + 1 min`) e sai no FECHAMENTO da última barra com `ts <= t + h min`, sempre no mesmo pregão.
Retornos nunca cruzam a abertura de um pregão (logo, nunca cruzam `roll_day`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _asof(left: pd.DataFrame, ref: pd.DataFrame, key: str, cols: list[str], direction: str) -> pd.DataFrame:
    """Para cada linha de `left`, a barra de `ref` (mesmo pregão) mais próxima de `left[key]`."""
    r = ref[["session_date", "ts", *cols]].rename(columns={"ts": "_ref_ts"})
    out = pd.merge_asof(left.sort_values(key), r, left_on=key, right_on="_ref_ts",
                        by="session_date", direction=direction)
    return out.sort_values("_i").reset_index(drop=True)


def forward_returns(bars: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    """Retorno futuro de uma posição COMPRADA, em bps, por barra e horizonte.
    NaN quando não há negócio para entrar dentro do horizonte ou o horizonte passa do fim do pregão."""
    ref = bars[["session_date", "ts", "open", "close"]].sort_values("ts").reset_index(drop=True)
    base = bars[["session_date", "ts"]].reset_index(drop=True)
    base["_i"] = np.arange(len(base))
    ent = _asof(base.assign(_k=base["ts"] + pd.Timedelta(minutes=1)), ref, "_k", ["open"], "forward")
    last_ts = bars.groupby("session_date")["ts"].transform("max").reset_index(drop=True)
    out = {}
    for h in horizons:
        ex = _asof(base.assign(_k=base["ts"] + pd.Timedelta(minutes=h)), ref, "_k", ["close"], "backward")
        ok = ex["_ref_ts"].notna() & ent["_ref_ts"].notna() & (ex["_ref_ts"] >= ent["_ref_ts"])
        ok &= base["ts"] + pd.Timedelta(minutes=h) <= last_ts   # o horizonte cabe no pregão
        out[f"fwd_{h}"] = np.where(ok, 1e4 * (ex["close"] / ent["open"] - 1), np.nan)
    return pd.DataFrame(out, index=bars.index)


def cluster_bootstrap_mean(values: np.ndarray, days: np.ndarray, n_boot: int = 4000, seed: int = 0):
    """Média e IC 95% por bootstrap de dias (as observações do mesmo pregão não são independentes)."""
    df = pd.DataFrame({"v": values, "d": days}).dropna()
    g = df.groupby("d")["v"].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(n_boot, len(g)))
    boot = s[idx].sum(1) / c[idx].sum(1)
    mean = s.sum() / c.sum()
    p = 2 * min((boot <= 0).mean(), (boot >= 0).mean())
    return mean, np.percentile(boot, 2.5), np.percentile(boot, 97.5), max(p, 1 / n_boot)
