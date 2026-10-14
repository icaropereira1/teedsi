"""Auditoria do dado contra o calendário e marcação de buracos.

Convenção do projeto (decisão do grupo): os buracos NÃO são removidos nem preenchidos; são
**marcados**. Cada barra recebe:
- `session_date`   : data do pregão;
- `in_session`     : a barra está dentro da sessão do calendário (barras fora = leilão/pós-fechamento);
- `segment`        : id do trecho contínuo. Aumenta a cada buraco (dias úteis ausentes);
- `day_in_segment` : 1 no 1º pregão do trecho, 2 no seguinte etc.;
- `partial_day`    : pregão com menos de `min_fill` das barras esperadas (decisão do grupo: não entra);
- `usable`         : barra aproveitável nas features: `in_session & ~partial_day`
                     (decisão do grupo: pregão parcial e barra fora da sessão não entram);
- `after_intraday_gap`: a barra vem depois de uma pausa intradiária de `gap_minutes` ou mais;
- `roll_day`       : pregão em que o contínuo troca de contrato. O gap overnight desse dia inclui o
                     carry entre contratos: **nunca usar retorno que cruze essa abertura** (ver `calendar.roll_days`).

Uso em features com janela de N pregões: só valem as barras com `day_in_segment > N`
(ver `lookback_ok`), ou seja, quando os N pregões anteriores estão no mesmo trecho.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.cleaning.calendar import expected_trading_days, roll_days, session_for


def trading_day_table(df: pd.DataFrame, asset: str, min_fill: float = 0.6) -> pd.DataFrame:
    """Uma linha por pregão presente nos dados: barras, esperado, primeira/última barra, parcial."""
    day = df["ts"].dt.normalize()
    tod = df["ts"].dt.hour * 60 + df["ts"].dt.minute
    g = pd.DataFrame({"day": day, "tod": tod}).groupby("day")["tod"]
    t = pd.DataFrame({"n_bars": g.size(), "first_min": g.min(), "last_min": g.max()})
    sess = [session_for(d, asset) for d in t.index]
    t["session_open"] = [s.open_minute for s in sess]
    t["session_last"] = [s.last_minute for s in sess]
    t["expected_bars"] = [s.n_bars for s in sess]
    t["partial_day"] = t["n_bars"] < min_fill * t["expected_bars"]
    return t


def find_holes(days_present: pd.DatetimeIndex) -> pd.DataFrame:
    """Dias úteis esperados pelo calendário e ausentes nos dados, agrupados em trechos."""
    days_present = pd.DatetimeIndex(days_present).sort_values()
    exp = expected_trading_days(days_present.min(), days_present.max())
    missing = exp.difference(days_present)
    cols = ["start", "end", "trading_days", "calendar_days"]
    if len(missing) == 0:
        return pd.DataFrame(columns=cols)
    pos = exp.get_indexer(missing)               # posição entre os pregões esperados
    run = np.concatenate([[0], np.cumsum(np.diff(pos) > 1)])
    out = pd.DataFrame({"day": missing, "run": run}).groupby("run")["day"].agg(["min", "max", "size"])
    out.columns = ["start", "end", "trading_days"]
    out["calendar_days"] = (out["end"] - out["start"]).dt.days + 1
    return out.reset_index(drop=True)[cols]


def mark_bars(df: pd.DataFrame, asset: str, min_fill: float = 0.6, gap_minutes: int = 5) -> pd.DataFrame:
    """Devolve cópia de `df` (precisa de `ts`, ordenado) com as colunas de marcação."""
    if not df["ts"].is_monotonic_increasing:
        raise ValueError("df precisa estar ordenado por ts.")
    out = df.copy()
    out["session_date"] = out["ts"].dt.normalize()
    tod = out["ts"].dt.hour * 60 + out["ts"].dt.minute

    days = trading_day_table(out, asset, min_fill)
    out["in_session"] = tod.values <= out["session_date"].map(days["session_last"]).values
    out["partial_day"] = out["session_date"].map(days["partial_day"]).astype(bool)

    holes = find_holes(days.index)
    # trecho: conta quantos buracos terminaram antes do pregão
    ends = holes["end"].values
    seg_of_day = pd.Series(np.searchsorted(ends, days.index.values, side="left"), index=days.index)
    days["segment"] = seg_of_day
    days["day_in_segment"] = days.groupby("segment").cumcount() + 1
    out["roll_day"] = out["session_date"].isin(roll_days(asset, days.index.min(), days.index.max()))
    out["usable"] = out["in_session"] & ~out["partial_day"]
    out["segment"] = out["session_date"].map(days["segment"]).astype("int32")
    out["day_in_segment"] = out["session_date"].map(days["day_in_segment"]).astype("int32")

    dt = out["ts"].diff().dt.total_seconds() / 60
    same_day = out["session_date"] == out["session_date"].shift(1)
    out["after_intraday_gap"] = (same_day & (dt >= gap_minutes)).fillna(False)
    return out


def lookback_ok(marked: pd.DataFrame, n_days: int) -> pd.Series:
    """True onde os `n_days` pregões anteriores pertencem ao mesmo trecho (sem buraco no meio)."""
    return marked["day_in_segment"] > n_days
