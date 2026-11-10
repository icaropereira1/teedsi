# %% [markdown]
# # 09 — Mediana da variação do preço em T-1, T, T+3, T+5, T+10, T+15
#
# Pedido do professor. Base = fechamento de T-1; valor = **mediana** entre pregões da variação (bps) até o
# fechamento de T+h, para âncoras de 30 em 30 min. **Só mediana, sem testes de hipótese.** Só exploração.
# - Etapa 1: todos os dias.
# - Etapa 2: dias de alta x dias de baixa. Cada ativo é classificado pelo PRÓPRIO movimento no dia
#   (último fechamento vs primeira abertura do pregão).
# - Etapa 3 (a fazer): índice dolarizado WIN/WDO.
#
# **Saídas:** `reports/horizontes_<ativo>_<todos|alta|baixa>.csv`.

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import pandas as pd

from src.evaluation.horizons import changes_long, day_direction, price_panel, summarize, tod_label
from src.ingestion.loader import INTERIM_DIR

pd.set_option("display.width", 200)
COLS = {-1: "T-1", 0: "T", 3: "T+3", 5: "T+5", 10: "T+10", 15: "T+15"}


def show(s, title):
    t = s.pivot(index="anchor", columns="offset", values="mediana_bps").rename(columns=COLS)
    t.index = [tod_label(a) for a in t.index]
    t["n_pregoes"] = s.groupby("anchor")["n"].first().values
    t.loc["TODOS (mediana das medianas)"] = list(t.drop(columns="n_pregoes").median()) + [int(t["n_pregoes"].sum())]
    print(f"\n=== {title}: mediana da variação vs T-1 (bps) ===")
    print(t.round(2).to_string())


for asset in ("WDO", "WIN"):
    clean = pd.read_parquet(INTERIM_DIR / f"{asset.lower()}_m1_limpo.parquet")
    panel, direc = price_panel(clean), day_direction(clean)
    print(f"\n######## {asset}: {int((direc > 0).sum())} dias de alta, {int((direc < 0).sum())} de baixa, {int((direc == 0).sum())} neutros")
    for nome, days in (("todos", direc.index), ("alta", direc.index[direc > 0]), ("baixa", direc.index[direc < 0])):
        s = summarize(changes_long(panel, days=days))
        s.to_csv(BP / "reports" / f"horizontes_{asset.lower()}_{nome}.csv", index=False)
        show(s, f"{asset} — dias de {nome}" if nome != "todos" else f"{asset} — todos os dias")
