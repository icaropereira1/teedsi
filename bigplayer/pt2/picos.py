"""Preço médio por minuto e quanto ele varia em volta dos horários de pico de volume.

Definições (as mesmas no código, nos gráficos e no relatório):
- preço médio do minuto = (máxima + mínima + fechamento) / 3
- variação do minuto = preço médio do minuto − preço médio do minuto anterior, em pontos.
  Só existe quando o minuto anterior é exatamente 1 minuto antes, no mesmo pregão.
- horários de pico = todo :00 e :30 de 9:00 a 17:30.
- variação depois do pico = preço médio h minutos depois − preço médio do minuto do pico, em pontos.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta

import numpy as np
import pandas as pd

PEAK_TIMES = [time(h, m) for h in range(9, 18) for m in (0, 30)]
AFTERNOON = (time(14, 0), time(17, 0))   # "volume típico da tarde": 14:00 a 16:59
HORIZONS = [5, 15, 30]                   # minutos depois do pico


def _minus_one_minute(t: time) -> time:
    return (datetime.combine(datetime.min, t) - timedelta(minutes=1)).time()


def add_minute_change(bars: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta `preco_medio` e `variacao` (pontos) a barras de um único ativo."""
    out = bars.sort_values("ts").reset_index(drop=True)
    out["preco_medio"] = (out["high"] + out["low"] + out["close"]) / 3
    consecutive = (out["ts"].diff() == pd.Timedelta(minutes=1)) & (
        out["session_date"] == out["session_date"].shift()
    )
    out["variacao"] = out["preco_medio"].diff().where(consecutive)
    out["minuto"] = out["ts"].dt.time
    return out


def peak_window(bars: pd.DataFrame, times: list[time] = PEAK_TIMES) -> pd.DataFrame:
    """Uma linha por pregão e horário de pico T, com a variação no minuto T−1 (`var_antes`)
    e no minuto T (`var_pico`). Entram só os pregões que têm as duas variações."""
    wide = bars.pivot(index="session_date", columns="minuto", values="variacao")
    rows = []
    for t in times:
        pair = (wide.reindex(columns=[_minus_one_minute(t), t])
                .set_axis(["var_antes", "var_pico"], axis=1)
                .dropna())
        pair["horario"] = t.strftime("%H:%M")
        rows.append(pair.reset_index())
    return pd.concat(rows, ignore_index=True)[["session_date", "horario", "var_antes", "var_pico"]]


def summarize_peaks(window: pd.DataFrame) -> pd.DataFrame:
    """Por horário de pico: nº de pregões e, para T−1 e T, mínima, mediana, máxima e mediana do |variação|."""
    g = window.groupby("horario")
    table = pd.DataFrame({"pregoes": g.size()})
    for col, label in (("var_antes", "antes"), ("var_pico", "pico")):
        table[f"{label}_min"] = g[col].min()
        table[f"{label}_mediana"] = g[col].median()
        table[f"{label}_max"] = g[col].max()
        table[f"{label}_mediana_abs"] = g[col].apply(lambda s: s.abs().median())
    return table.reset_index()


def volume_profile(bars: pd.DataFrame) -> pd.Series:
    """Volume mediano de cada minuto do dia, dividido pelo volume típico da tarde
    (mediana dos volumes medianos dos minutos de 14:00 a 16:59)."""
    median_by_minute = bars.groupby("minuto")["vol"].median()
    afternoon = median_by_minute[(median_by_minute.index >= AFTERNOON[0]) & (median_by_minute.index < AFTERNOON[1])]
    return median_by_minute / afternoon.median()


def change_profile(bars: pd.DataFrame) -> pd.Series:
    """Mediana do |variação| (pontos) de cada minuto do dia."""
    return bars.groupby("minuto")["variacao"].apply(lambda s: s.abs().median())


def add_forward_change(bars: pd.DataFrame, horizons: list[int] = HORIZONS) -> pd.DataFrame:
    """Acrescenta `depois_<h>` = preço médio h minutos depois − preço médio do minuto, em pontos.
    Fica vazio quando não há barra exatamente h minutos depois (o pregão nunca vira a meia-noite)."""
    out = bars.copy()
    price = out.set_index("ts")["preco_medio"]
    for h in horizons:
        later = price.reindex(out["ts"] + pd.Timedelta(minutes=h)).to_numpy()
        out[f"depois_{h}"] = later - out["preco_medio"].to_numpy()
    return out


def after_stats(minutes: pd.DataFrame, h: int) -> dict:
    """O que o preço médio fez de T até T+h, num conjunto de minutos T.

    `continua_pct` e `volta_pct` contam só os casos em que o minuto T mexeu (variação ≠ 0):
    continua = T+h ficou do mesmo lado que o movimento de T; volta = ficou do lado oposto.
    `margem_pct` = margem de erro de 95% das porcentagens: 1,96 × √(0,25 / casos em que T mexeu)."""
    d = minutes[["variacao", f"depois_{h}"]].dropna()
    move, after = d["variacao"], d[f"depois_{h}"]
    moved = move != 0
    return {
        "casos": len(d),
        "sobe_pct": 100 * (after > 0).mean(),
        "cai_pct": 100 * (after < 0).mean(),
        "mediana": after.median(),
        "p10": after.quantile(0.10),
        "p90": after.quantile(0.90),
        "continua_pct": 100 * (np.sign(after[moved]) == np.sign(move[moved])).mean(),
        "volta_pct": 100 * (np.sign(after[moved]) == -np.sign(move[moved])).mean(),
        "margem_pct": 100 * 1.96 * np.sqrt(0.25 / moved.sum()),
    }


def after_table(bars: pd.DataFrame, by: pd.Series, horizons: list[int] = HORIZONS) -> pd.DataFrame:
    """`after_stats` para cada grupo de `by` (ex.: horário do pico, ou hora do dia) e cada horizonte."""
    rows = [{"grupo": key, "minutos_depois": h, **after_stats(g, h)}
            for key, g in bars.groupby(by) for h in horizons]
    return pd.DataFrame(rows)
