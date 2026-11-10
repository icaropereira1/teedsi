# %% [markdown]
# # 10 — Pontos em T-1, T, T+3, T+5, T+10, T+15, com T = pico de volume (janelas de 30 min) — WDO, WIN e WIN/WDO
# Mediana entre pregões do PREÇO EM PONTOS (fechamento do candle) e da variação em pontos vs T-1.
# T = minuto de maior `vol` em cada janela de 30 min (09:00, 09:30, ..., 17:30) e no pregão inteiro ('DIA').
# Alta/baixa: movimento do próprio ativo/série no dia (último close vs primeira open). Só exploração.
#
# **Dolarizado (visão do investidor estrangeiro):** série = 1000 * WIN / WDO = Ibovespa em dólares
# (WIN em pontos do índice; WDO = R$ por US$ 1.000). T = pico de volume do WIN (volume do índice).
# Só pregões em que os dois ativos existem.
#
# **Saídas:** `reports/pico30_<serie>_<alta|baixa|todos>.csv` (medianas) e
# `data/processed/pico30_<serie>_eventos.parquet` (um registro por pico e offset, com o rótulo do dia).

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import pandas as pd

from src.evaluation.horizons import (day_direction, panel_direction, peak_changes, price_panel, summarize_peaks,
                                     tod_label, volume_peaks)
from src.ingestion.loader import INTERIM_DIR

pd.set_option("display.width", 220)
NAMES = {-1: "T-1", 0: "T", 3: "T+3", 5: "T+5", 10: "T+10", 15: "T+15"}
OUT = BP / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


def load(a):
    return pd.read_parquet(INTERIM_DIR / f"{a.lower()}_m1_limpo.parquet")


wdo, win = load("WDO"), load("WIN")
cw, cwin = price_panel(wdo), price_panel(win)
ow, owin = price_panel(wdo, "open"), price_panel(win, "open")
days_both = cw.index.intersection(cwin.index)
cols = cw.columns.intersection(cwin.columns)
ratio_c = 1000 * cwin.loc[days_both, cols] / cw.loc[days_both, cols]
ratio_o = 1000 * owin.loc[days_both, cols] / ow.loc[days_both, cols]

SERIES = {
    "wdo": (cw, day_direction(wdo), volume_peaks(wdo)),
    "win": (cwin, day_direction(win), volume_peaks(win)),
    # dolarizado: T pelo volume do WIN, restrito aos pregões comuns
    "dolarizado": (ratio_c, panel_direction(ratio_o, ratio_c), volume_peaks(win).query("d in @days_both")),
}
ORDER = [tod_label(m) for m in range(9 * 60, 18 * 60, 30)] + ["DIA"]

for nome_s, (panel, direc, peaks) in SERIES.items():
    eventos = []
    for nome, days in (("todos", direc.index), ("alta", direc.index[direc > 0]), ("baixa", direc.index[direc < 0])):
        long = peak_changes(panel, peaks, days=days)
        s = summarize_peaks(long)
        s.to_csv(BP / "reports" / f"pico30_{nome_s}_{nome}.csv", index=False)
        if nome != "todos":
            eventos.append(long.assign(dia=nome))
        n = s.groupby("grupo")["n"].first().reindex(ORDER)
        p = s.pivot(index="grupo", columns="offset", values="mediana_preco").rename(columns=NAMES).reindex(ORDER)
        d = s.pivot(index="grupo", columns="offset", values="mediana_pts").rename(columns=NAMES).reindex(ORDER).drop(columns="T-1")
        print(f"\n=== {nome_s.upper()} — dias de {nome} — MEDIANA DO PREÇO (pontos) ===")
        print(p.assign(n_picos=n).round(2).to_string())
        print(f"--- {nome_s.upper()} — dias de {nome} — MEDIANA da variação vs T-1 (pontos) ---")
        print(d.round(2).to_string())
    pd.concat(eventos, ignore_index=True).to_parquet(OUT / f"pico30_{nome_s}_eventos.parquet", index=False)
    print(f"\n[{nome_s}] pregões: {len(direc)} | alta {(direc > 0).sum()} | baixa {(direc < 0).sum()} | neutros {(direc == 0).sum()}")
