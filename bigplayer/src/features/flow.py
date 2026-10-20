"""Features de fluxo por barra de 1 minuto. Só passado: a barra de `ts` usa dados até o fechamento
dela; as estatísticas de referência (mesmo minuto do dia) vêm dos N pregões ANTERIORES.

Entrada: dataset limpo (`load_clean()`), usando apenas barras `usable`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LOOKBACK_DAYS = 20
MIN_PERIODS = 15


def _zscore_same_minute(values: pd.Series, dates: pd.Series, tod: pd.Series, n: int = LOOKBACK_DAYS) -> pd.Series:
    """z-score de `values` contra o mesmo minuto do dia nos `n` pregões anteriores (shift(1))."""
    wide = pd.DataFrame({"d": dates.values, "t": tod.values, "v": values.values}).pivot(index="d", columns="t", values="v")
    roll = wide.rolling(n, min_periods=MIN_PERIODS)
    mu, sd = roll.mean().shift(1), roll.std().shift(1)
    z = (wide - mu) / sd.where(sd > 0)
    key = pd.MultiIndex.from_arrays([dates.values, tod.values])
    return pd.Series(z.stack(future_stack=True).reindex(key).values, index=values.index)


def flow_features(clean: pd.DataFrame, tick: float | None = None) -> pd.DataFrame:
    """Devolve as barras `usable` com as features. Colunas novas:
    `z_vol` (log do volume), `z_lot` (log do lote médio), `ret_bps` (close/open da barra),
    `z_vol5` (média de `z_vol` nas últimas 5 barras do dia), `ret5_bps` (close vs close 5 barras antes),
    `lb_ok` (os 20 pregões anteriores estão no mesmo trecho).
    Rodada 2 (precisa de `tick`): `z_rng` (log de max(high−low, tick)), `clv`, `r15_bps`, `ret3_bps`,
    `lim15` (média, nos 20 pregões anteriores, da mediana de |r15| da mesma hora), `n_z1_15`
    (barras com z_vol ≥ 1 entre as 15 últimas), `max_z15`, `clv_run3` (sinal se as 3 últimas barras
    cumprem z_vol ≥ 1 e |clv| ≥ 0,5 com o mesmo sinal; 0 caso contrário)."""
    b = clean[clean["usable"]].copy().reset_index(drop=True)
    b["tod"] = b["ts"].dt.hour * 60 + b["ts"].dt.minute
    b["lv"] = np.log(b["vol"])
    b["ll"] = np.log(b["vol"] / b["tickvol"])
    b["z_vol"] = _zscore_same_minute(b["lv"], b["session_date"], b["tod"])
    b["z_lot"] = _zscore_same_minute(b["ll"], b["session_date"], b["tod"])
    b["ret_bps"] = 1e4 * (b["close"] / b["open"] - 1)
    g = b.groupby("session_date")
    b["z_vol5"] = g["z_vol"].transform(lambda s: s.rolling(5, min_periods=5).mean())
    b["ret5_bps"] = 1e4 * (b["close"] / g["close"].shift(5) - 1)
    b["lb_ok"] = b["day_in_segment"] > LOOKBACK_DAYS
    if tick is not None:
        rng = (b["high"] - b["low"]).clip(lower=tick)
        b["z_rng"] = _zscore_same_minute(np.log(rng), b["session_date"], b["tod"])
        span = b["high"] - b["low"]
        b["clv"] = np.where(span > 0, (2 * b["close"] - b["high"] - b["low"]) / span.replace(0, np.nan), 0.0)
        b["r15_bps"] = 1e4 * (b["close"] / g["close"].shift(15) - 1)
        b["ret3_bps"] = 1e4 * (b["close"] / g["close"].shift(3) - 1)
        b["hour"] = b["ts"].dt.hour
        b["_a"] = b["r15_bps"].abs()
        daily = b.groupby(["session_date", "hour"])["_a"].median().unstack("hour")
        lim = daily.rolling(LOOKBACK_DAYS, min_periods=MIN_PERIODS).mean().shift(1)
        b["lim15"] = lim.stack(future_stack=True).reindex(pd.MultiIndex.from_arrays([b["session_date"], b["hour"]])).values
        zv = b["z_vol"]
        b["n_z1_15"] = (zv >= 1).astype(float).groupby(b["session_date"]).transform(lambda s: s.rolling(15, min_periods=15).sum())
        b["max_z15"] = zv.groupby(b["session_date"]).transform(lambda s: s.rolling(15, min_periods=15).max())
        pos = ((b["clv"] >= 0.5) & (zv >= 1)).astype(float)
        neg = ((b["clv"] <= -0.5) & (zv >= 1)).astype(float)
        roll3 = lambda x: x.groupby(b["session_date"]).transform(lambda s: s.rolling(3, min_periods=3).sum())
        b["clv_run3"] = np.where(roll3(pos) == 3, 1, np.where(roll3(neg) == 3, -1, 0))
        b = b.drop(columns=["hour", "_a"])
    return b.drop(columns=["lv", "ll"])
