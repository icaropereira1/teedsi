# %% [markdown]
# # 04 — Dataset limpo (exploração) com marcações
#
# **Objetivo:** gerar o dataset que a Fase 2 consome: exploração + colunas de calendário, buracos,
# rolagem e `usable` (ver `docs/DICIONARIO_DADOS.md`). **Nenhuma barra é removida.**
#
# O hold-out NÃO é tocado: a mesma função (`mark_bars`) será aplicada a ele na avaliação final.
#
# **Ativo:** `BIGPLAYER_ASSET`. **Entrada:** `load_exploration()`. **Saída:** `data/interim/<ativo>_m1_limpo.parquet`.

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import numpy as np
import pandas as pd

from src.cleaning.holes import mark_bars
from src.ingestion.loader import ASSET, CLEAN_FILE, load_exploration

raw = load_exploration()
clean = mark_bars(raw, ASSET).drop(columns=["spread"])   # SPREAD descartado (não confiável)
assert len(clean) == len(raw)
clean.to_parquet(CLEAN_FILE, index=False)
print(ASSET, "→", CLEAN_FILE.name, clean.shape)
print(clean.dtypes.to_string())

# %% [markdown]
# ## Conferências

# %%
u = clean["usable"]
print(f"usable: {u.mean():.4%} | descartadas: {int((~u).sum())}")
print("segmentos:", clean["segment"].nunique(), "| pregões:", clean["session_date"].nunique())

# O gap overnight dos dias de rolagem é de fato diferente? (mesmo trecho, só barras usáveis)
d = clean[u].groupby("session_date").agg(o=("open", "first"), c=("close", "last"),
                                         seg=("segment", "first"), roll=("roll_day", "first"))
d["gap"] = 100 * (d["o"] / d["c"].shift() - 1)
d = d[d["seg"] == d["seg"].shift()]
print(f"\nRolagem: {int(d['roll'].sum())} dias | gap overnight com sinal, mediana: "
      f"rolagem {d.loc[d['roll'], 'gap'].median():+.2f}% | demais {d.loc[~d['roll'], 'gap'].median():+.2f}%")
print(f"|gap| médio: rolagem {d.loc[d['roll'], 'gap'].abs().mean():.2f}% | demais {d.loc[~d['roll'], 'gap'].abs().mean():.2f}%")
