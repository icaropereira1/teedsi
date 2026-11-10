"""Variação do preço em torno de um horário T (T-1, T, T+3, T+5, T+10, T+15).

Base de comparação: o fechamento do candle de T-1 (último preço antes de T). Para cada pregão e cada
horário-âncora T (ex.: 09:30, 10:00...), mede-se a variação em bps até o fechamento de T+h.
Só olha o MESMO pregão (o painel é pregão x minuto do dia), então nunca cruza rolagem/overnight.

As funções são genéricas: recebem um painel de preços (pregão x minuto), que pode ser o preço de um ativo
ou uma razão entre ativos (ex.: WIN/WDO), e um filtro opcional de pregões (ex.: só dias de alta).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

OFFSETS = (-1, 0, 3, 5, 10, 15)          # minutos relativos a T; -1 é a base
ANCHORS = tuple(h * 60 + m for h in range(9, 18) for m in (0, 30) if 9 * 60 + 30 <= h * 60 + m <= 17 * 60 + 30)


def price_panel(clean: pd.DataFrame, field: str = "close") -> pd.DataFrame:
    """Painel pregão x minuto-do-dia com o preço de `field`; só barras `usable`."""
    b = clean[clean["usable"]]
    tod = b["ts"].dt.hour * 60 + b["ts"].dt.minute
    return pd.DataFrame({"d": b["session_date"].values, "t": tod.values, "p": b[field].values}).pivot(
        index="d", columns="t", values="p"
    )


def tod_label(t: int) -> str:
    return f"{t // 60:02d}:{t % 60:02d}"


def changes_long(panel: pd.DataFrame, anchors=ANCHORS, offsets=OFFSETS, days=None) -> pd.DataFrame:
    """Formato longo: uma linha por (pregão, âncora, offset) com o nível de preço e a variação em bps vs T-1.
    Só entram pregões em que TODOS os offsets daquela âncora existem (mesma amostra em todas as colunas).
    `days`: índice de pregões a manter (None = todos)."""
    if days is not None:
        panel = panel.loc[panel.index.intersection(days)]
    rows = []
    for a in anchors:
        cols = [a + o for o in offsets]
        if any(c not in panel.columns for c in cols):
            continue
        sub = panel[cols].dropna()
        base = sub[a - 1]
        for o in offsets:
            p = sub[a + o]
            rows.append(
                pd.DataFrame(
                    {"d": sub.index, "anchor": a, "offset": o, "price": p.values, "bps": 1e4 * np.log(p.values / base.values)}
                )
            )
    return pd.concat(rows, ignore_index=True)


def day_direction(clean: pd.DataFrame) -> pd.Series:
    """Direção do pregão do PRÓPRIO ativo: +1 (alta) se o último fechamento > primeira abertura, -1 (baixa) se <,
    0 se igual. Usa só barras `usable`. Classificação feita olhando o dia inteiro (descritivo, não operável)."""
    b = clean[clean["usable"]].sort_values("ts")
    g = b.groupby("session_date")
    return np.sign(g["close"].last() - g["open"].first()).astype(int)


def summarize(long: pd.DataFrame, by=("anchor", "offset")) -> pd.DataFrame:
    """Por grupo: n (pregões), mediana do preço e mediana da variação vs T-1 (bps). Sempre mediana."""
    g = long.groupby(list(by))
    return g.agg(n=("bps", "size"), mediana_preco=("price", "median"), mediana_bps=("bps", "median")).reset_index()


# --- T = minuto de pico de volume (em pontos) -------------------------------------------------------------

def volume_peaks(clean: pd.DataFrame, field: str = "vol", window: int = 30, start: int = 9 * 60, end: int = 18 * 60) -> pd.DataFrame:
    """Minuto de pico de volume: um por (pregão, janela de `window` min) e um por pregão ('DIA').
    Colunas: d, grupo (início da janela, 'HH:MM'), T (minuto do dia do pico)."""
    b = clean[clean["usable"]].copy()
    b["T"] = b["ts"].dt.hour * 60 + b["ts"].dt.minute
    b["w"] = (b["T"] // window) * window
    win = b[(b["T"] >= start) & (b["T"] < end)]
    pw = win.loc[win.groupby(["session_date", "w"])[field].idxmax(), ["session_date", "w", "T"]]
    pw["grupo"] = pw["w"].map(tod_label)
    pdia = b.loc[b.groupby("session_date")[field].idxmax(), ["session_date", "T"]].assign(grupo="DIA")
    return pd.concat([pw[["session_date", "grupo", "T"]], pdia], ignore_index=True).rename(columns={"session_date": "d"})


def panel_direction(open_panel: pd.DataFrame, close_panel: pd.DataFrame) -> pd.Series:
    """Direção do pregão para um painel qualquer (ex.: razão WIN/WDO): sinal de (último close - primeira open),
    usando o primeiro minuto com open e o último com close disponíveis."""
    first = open_panel.apply(lambda r: r.dropna().iloc[0] if r.notna().any() else np.nan, axis=1)
    last = close_panel.apply(lambda r: r.dropna().iloc[-1] if r.notna().any() else np.nan, axis=1)
    return np.sign(last - first).dropna().astype(int)


def peak_changes(panel: pd.DataFrame, peaks: pd.DataFrame, offsets=OFFSETS, days=None) -> pd.DataFrame:
    """Para cada pico (pregão, grupo, T): preço de cada offset (em pontos) e variação em pontos vs T-1.
    Descarta o pico se faltar algum dos offsets (mesma amostra em todas as colunas)."""
    if days is not None:
        peaks = peaks[peaks["d"].isin(days)]
    pr = panel.reindex(peaks["d"].values)
    cols = {}
    for o in offsets:
        idx = peaks["T"].values + o
        vals = np.full(len(peaks), np.nan)
        ok = np.isin(idx, panel.columns)
        vals[ok] = pr.to_numpy()[np.where(ok)[0], panel.columns.get_indexer(idx[ok])]
        cols[o] = vals
    wide = pd.DataFrame(cols, index=peaks.index).join(peaks).dropna()
    long = wide.melt(id_vars=["d", "grupo", "T"], value_vars=list(offsets), var_name="offset", value_name="price")
    base = wide.set_index(["d", "grupo"])[-1]
    long["pts"] = long["price"].values - base.reindex(pd.MultiIndex.from_frame(long[["d", "grupo"]])).values
    return long


def summarize_peaks(long: pd.DataFrame) -> pd.DataFrame:
    """Por (grupo, offset): n, mediana do preço (pontos) e mediana da variação vs T-1 (pontos)."""
    return (long.groupby(["grupo", "offset"])
            .agg(n=("pts", "size"), mediana_preco=("price", "median"), mediana_pts=("pts", "median")).reset_index())
