# %% [markdown]
# # 03 — Calendário de pregão e marcação de buracos (somente exploração)
#
# **Objetivo:** auditar o dado contra o calendário B3 (`src/cleaning/calendar.py`) e marcar
# cada barra com trecho contínuo, sessão e dia parcial (`src/cleaning/holes.py`).
# Por decisão do grupo, os buracos **não** são removidos nem preenchidos, só marcados.
#
# **Ativo:** `BIGPLAYER_ASSET` (padrão WDO). **Entrada:** `load_exploration()`.
# **Saída:** `reports/buracos_<ativo>.csv` (buracos de dias úteis) e o resumo impresso.

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import pandas as pd

from src.cleaning.holes import find_holes, mark_bars, trading_day_table
from src.ingestion.loader import ASSET, load_exploration

pd.set_option("display.width", 140)
df = load_exploration()
days = trading_day_table(df, ASSET)
print(ASSET, "|", len(df), "barras |", len(days), "pregões |", df["ts"].min(), "→", df["ts"].max())

# %% [markdown]
# ## 1. Dias úteis esperados e ausentes
# Calendário: dias de semana menos feriados B3. Todo dia esperado e ausente é um buraco.

# %%
holes = find_holes(days.index)
print(f"{len(holes)} buracos | {int(holes['trading_days'].sum())} pregões ausentes")
print(holes.to_string(index=False))
(BP / "reports").mkdir(exist_ok=True)
holes.to_csv(BP / "reports" / f"buracos_{ASSET.lower()}.csv", index=False)

# %% [markdown]
# ## 2. Pregões parciais e barras fora da sessão

# %%
print("Pregões parciais (< 60% das barras esperadas):")
print(days.loc[days["partial_day"], ["n_bars", "expected_bars", "first_min", "last_min"]].assign(
    primeira=lambda x: x["first_min"].map(lambda m: f"{m // 60:02d}:{m % 60:02d}")).to_string())

marked = mark_bars(df, ASSET)
print("\nBarras fora da sessão:", int((~marked["in_session"]).sum()))
print(marked.loc[~marked["in_session"], ["ts", "tickvol", "vol"]].to_string(index=False))
print("\nBarras após pausa intradiária >= 5 min:", int(marked["after_intraday_gap"].sum()))

# %% [markdown]
# ## 3. Trechos contínuos
# `segment` muda a cada buraco. Uma feature com janela de N pregões só vale quando
# `day_in_segment > N` (`lookback_ok`).

# %%
seg = marked.groupby("segment").agg(inicio=("session_date", "min"), fim=("session_date", "max"),
                                    pregoes=("session_date", "nunique"), barras=("ts", "size"))
print(seg.to_string())
for n in (20, 60):
    from src.cleaning.holes import lookback_ok
    ok = lookback_ok(marked, n)
    print(f"\nJanela de {n} pregões: {100 * ok.mean():.1f}% das barras válidas")
