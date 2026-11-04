"""Preço médio por minuto e o que o preço faz em volta dos horários de pico de volume.

Definições (as mesmas no código, nos gráficos e no relatório):
- preço médio do minuto = (máxima + mínima + fechamento) / 3
- variação do minuto = preço médio do minuto − preço médio do minuto anterior, em pontos.
  Só existe quando o minuto anterior é exatamente 1 minuto antes, no mesmo pregão.
- horários de pico = todo :00 e :30 de 9:00 a 17:30.
- variação depois do pico = preço médio h minutos depois − preço médio do minuto do pico, em pontos.
- direção ("continua" / "volta") usa o FECHAMENTO, não o preço médio. O preço médio de um minuto
  carrega parte do movimento do minuto anterior (máxima e mínima vêm de antes do fechamento), então
  com ele o movimento parece "continuar" sozinho, e mais ainda nos minutos que mexem muito, como os picos.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

PEAK_TIMES = [time(h, m) for h in range(9, 18) for m in (0, 30)]
AFTERNOON = (time(14, 0), time(17, 0))   # "volume típico da tarde": 14:00 a 16:59
HORIZONS = [5, 15, 30]                   # minutos depois do pico


def _shift(t: time, minutes: int) -> time:
    return (datetime.combine(date(2000, 1, 1), t) + timedelta(minutes=minutes)).time()


def _margin(n: int) -> float:
    """Margem de erro de 95% de uma porcentagem com n casos, em pontos percentuais: 1,96 × √(0,25 / n)."""
    return 100 * 1.96 * np.sqrt(0.25 / n) if n else np.nan


def add_minute_change(bars: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta `preco_medio`, `variacao` (preço médio) e `variacao_fech` (fechamento), em pontos."""
    out = bars.sort_values("ts").reset_index(drop=True)
    out["preco_medio"] = (out["high"] + out["low"] + out["close"]) / 3
    consecutive = (out["ts"].diff() == pd.Timedelta(minutes=1)) & (
        out["session_date"] == out["session_date"].shift()
    )
    out["variacao"] = out["preco_medio"].diff().where(consecutive)
    out["variacao_fech"] = out["close"].diff().where(consecutive)
    out["minuto"] = out["ts"].dt.time
    return out


def peak_window(bars: pd.DataFrame, times: list[time] = PEAK_TIMES) -> pd.DataFrame:
    """Uma linha por pregão e horário de pico T, com a variação nos minutos T−2 (`var_antes2`),
    T−1 (`var_antes`) e T (`var_pico`). Entram só os pregões que têm as três."""
    wide = bars.pivot(index="session_date", columns="minuto", values="variacao")
    rows = []
    for t in times:
        trio = (wide.reindex(columns=[_shift(t, -2), _shift(t, -1), t])
                .set_axis(["var_antes2", "var_antes", "var_pico"], axis=1)
                .dropna())
        trio["horario"] = t.strftime("%H:%M")
        rows.append(trio.reset_index())
    return pd.concat(rows, ignore_index=True)[["session_date", "horario", "var_antes2", "var_antes", "var_pico"]]


def around_peaks(bars: pd.DataFrame, times: list[time] = PEAK_TIMES,
                 offsets: range = range(-5, 6)) -> pd.DataFrame:
    """Uma linha por pregão, horário de pico e minuto relativo (`minuto_rel`: −1 = 1 minuto antes do pico,
    0 = o minuto do pico), com a variação do preço médio (pontos) e o volume (contratos) daquele minuto.
    Cada minuto usa todos os pregões que têm barra nele."""
    by_minute = {m: g for m, g in bars.groupby("minuto")}
    rows = []
    for t in times:
        for k in offsets:
            g = by_minute.get(_shift(t, k))
            if g is not None:
                rows.append(g[["session_date", "variacao", "vol"]].assign(horario=t.strftime("%H:%M"), minuto_rel=k))
    return pd.concat(rows, ignore_index=True)


def _larger_pct(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    """Entre os pregões em que |a| ≠ |b|: % em que |a| > |b|, e a margem de erro dessa porcentagem."""
    a, b = a.abs(), b.abs()
    differ = a != b
    return 100 * (a[differ] > b[differ]).mean(), _margin(int(differ.sum()))


def summarize_peaks(window: pd.DataFrame) -> pd.DataFrame:
    """Por horário de pico:
    - para T−1 e T: mínima, mediana e máxima da variação (com sinal) e mediana do |variação|;
    - `antes_sobe_pct` / `antes_cai_pct`: % dos pregões em que o preço médio subiu / caiu no minuto T−1;
    - `antes_maior_pct`: % dos pregões em que o minuto T−1 mexeu mais que o T−2 (empates fora);
    - `pico_maior_pct`: % dos pregões em que o minuto T mexeu mais que o T−1 (empates fora);
    - margens de erro de 95% dessas duas porcentagens. 50% = os dois minutos mexem igual."""
    rows = []
    for horario, g in window.groupby("horario"):
        row = {"horario": horario, "pregoes": len(g)}
        for col, label in (("var_antes", "antes"), ("var_pico", "pico")):
            row[f"{label}_min"] = g[col].min()
            row[f"{label}_mediana"] = g[col].median()
            row[f"{label}_max"] = g[col].max()
            row[f"{label}_mediana_abs"] = g[col].abs().median()
        row["antes_sobe_pct"] = 100 * (g["var_antes"] > 0).mean()
        row["antes_cai_pct"] = 100 * (g["var_antes"] < 0).mean()
        row["antes_maior_pct"], row["antes_margem_pct"] = _larger_pct(g["var_antes"], g["var_antes2"])
        row["pico_maior_pct"], row["pico_margem_pct"] = _larger_pct(g["var_pico"], g["var_antes"])
        rows.append(row)
    return pd.DataFrame(rows)


def volume_profile(bars: pd.DataFrame) -> pd.Series:
    """Volume mediano de cada minuto do dia, dividido pelo volume típico da tarde
    (mediana dos volumes medianos dos minutos de 14:00 a 16:59)."""
    median_by_minute = bars.groupby("minuto")["vol"].median()
    afternoon = median_by_minute[(median_by_minute.index >= AFTERNOON[0]) & (median_by_minute.index < AFTERNOON[1])]
    return median_by_minute / afternoon.median()


def change_profile(bars: pd.DataFrame) -> pd.Series:
    """Mediana do |variação| (pontos) de cada minuto do dia que tem variação (9:00 não tem)."""
    return bars.dropna(subset=["variacao"]).groupby("minuto")["variacao"].apply(lambda s: s.abs().median())


def price_path(bars: pd.DataFrame) -> pd.DataFrame:
    """Para cada minuto do dia: onde está o preço médio em relação ao 1º minuto do mesmo pregão
    (preço médio do minuto − preço médio do 1º minuto com negócio), em pontos.
    Colunas: `mediana`, `p10`, `p90` sobre os pregões e `pregoes` (quantos têm aquele minuto)."""
    from_open = bars["preco_medio"] - bars.groupby("session_date")["preco_medio"].transform("first")
    g = from_open.groupby(bars["minuto"])
    return pd.DataFrame({"mediana": g.median(), "p10": g.quantile(0.10), "p90": g.quantile(0.90), "pregoes": g.size()})


def add_forward_change(bars: pd.DataFrame, horizons: list[int] = HORIZONS) -> pd.DataFrame:
    """Acrescenta, para cada h, `depois_<h>` (preço médio) e `depois_fech_<h>` (fechamento):
    valor h minutos depois − valor do minuto, em pontos. Fica vazio quando não há barra
    exatamente h minutos depois (o pregão nunca vira a meia-noite)."""
    out = bars.copy()
    by_ts = out.set_index("ts")[["preco_medio", "close"]]
    for h in horizons:
        later = by_ts.reindex(out["ts"] + pd.Timedelta(minutes=h))
        out[f"depois_{h}"] = later["preco_medio"].to_numpy() - out["preco_medio"].to_numpy()
        out[f"depois_fech_{h}"] = later["close"].to_numpy() - out["close"].to_numpy()
    return out


def after_stats(minutes: pd.DataFrame, h: int) -> dict:
    """O que o preço fez de T até T+h, num conjunto de minutos T.

    - `casos`, `sobe_pct`, `cai_pct`, `mediana`, `p10`, `p90`: variação do preço médio de T a T+h.
    - `continua_pct`, `volta_pct`: só nos `casos_direcao`, os pregões em que o fechamento de T mexeu em
      relação ao de T−1. Continua = o fechamento em T+h ficou do mesmo lado desse movimento;
      volta = do lado oposto. `margem_pct` é a margem de erro de 95% dessas porcentagens."""
    after = minutes[f"depois_{h}"].dropna()
    d = minutes[["variacao_fech", f"depois_fech_{h}"]].dropna()
    d = d[d["variacao_fech"] != 0]
    move, later = np.sign(d["variacao_fech"]), np.sign(d[f"depois_fech_{h}"])
    return {
        "casos": len(after),
        "sobe_pct": 100 * (after > 0).mean(),
        "cai_pct": 100 * (after < 0).mean(),
        "mediana": after.median(),
        "p10": after.quantile(0.10),
        "p90": after.quantile(0.90),
        "casos_direcao": len(d),
        "continua_pct": 100 * (later == move).mean() if len(d) else np.nan,
        "volta_pct": 100 * (later == -move).mean() if len(d) else np.nan,
        "margem_pct": _margin(len(d)),
    }


def after_table(bars: pd.DataFrame, by: pd.Series, horizons: list[int] = HORIZONS) -> pd.DataFrame:
    """`after_stats` para cada grupo de `by` e cada horizonte com dados."""
    rows = [{"grupo": key, "minutos_depois": h, **after_stats(g, h)}
            for key, g in bars.groupby(by) for h in horizons if g[f"depois_{h}"].notna().any()]
    return pd.DataFrame(rows)


def after_peak_table(bars: pd.DataFrame, times: list[time] = PEAK_TIMES,
                     horizons: list[int] = HORIZONS) -> pd.DataFrame:
    """Tabela do passo 2: `after_stats` por horário de pico e horizonte, mais as colunas `normal_*`,
    que são a mesma conta em todos os minutos comuns (fora de `times`) da mesma hora do pico."""
    is_peak = bars["minuto"].isin(times)
    peaks, common = bars[is_peak], bars[~is_peak]
    table = after_table(peaks, peaks["minuto"].map(lambda t: t.strftime("%H:%M")), horizons)
    table = table.rename(columns={"grupo": "horario"})
    normal = after_table(common, common["ts"].dt.hour, horizons).rename(columns={"grupo": "hora"})
    normal = normal[["hora", "minutos_depois", "sobe_pct", "mediana", "p10", "p90", "continua_pct"]]
    normal.columns = ["hora", "minutos_depois"] + [f"normal_{c}" for c in normal.columns[2:]]
    table["hora"] = table["horario"].str[:2].astype(int)
    return table.merge(normal, on=["hora", "minutos_depois"], how="left").drop(columns="hora")
