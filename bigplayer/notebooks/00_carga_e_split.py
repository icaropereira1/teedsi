# %% [markdown]
# # 00 — Carga e split exploração / hold-out
#
# **Objetivo:** carregar o CSV bruto do WDO, tipar as colunas e separar o **hold-out**
# (últimos 12 meses), que fica trancado até a avaliação final.
#
# **Entrada:** `data/raw/WDO$N_M1.csv`  ·  **Saídas:**
# - `data/interim/wdo_m1_exploracao.parquet` (usado em toda a EDA)
# - `data/holdout/wdo_m1_holdout.parquet` (TRANCADO)
# - `reports/split_manifest.json` (resumo versionado no git)
#
# **Outro ativo:** `BIGPLAYER_ASSET=WIN python notebooks/00_carga_e_split.py` (config em `configs/split_win.toml`).
#
# **Como rodar:** de dentro de `bigplayer/`, `python notebooks/00_carga_e_split.py`,
# ou célula a célula no VS Code / Jupyter (jupytext).

# %%
import json
import sys
from pathlib import Path

# Acha a pasta bigplayer/ mesmo rodando da raiz do repo ou de notebooks/
_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import pandas as pd

from src.ingestion.loader import (
    EXPLORATION_FILE, HOLDOUT_FILE, MANIFEST_FILE, REPO_DIR, load_config, read_raw_csv,
)
from src.ingestion.split import split_exploration_holdout

cfg = load_config()
print(cfg)

# %% [markdown]
# ## 1. Carga do CSV bruto

# %%
raw_path = REPO_DIR / "data" / "raw" / cfg["data"]["raw_file"]
df = read_raw_csv(raw_path)
print(df.shape)
print(df.dtypes)
df.head()

# %%
df.tail()

# %% [markdown]
# ## 2. Checagens mínimas antes de dividir
# (A análise profunda de qualidade está no notebook 01, e roda só sobre a exploração.)

# %%
assert df["ts"].is_monotonic_increasing, "CSV fora de ordem temporal"
print("Período total:", df["ts"].min(), "→", df["ts"].max())
print("Linhas:", len(df), "| nulos:", int(df.isna().sum().sum()))

# %% [markdown]
# ## 3. Split temporal
# Corte definido em `configs/split.toml`. Sem embaralhar: tudo antes do corte é exploração.

# %%
exploration, holdout = split_exploration_holdout(df, cfg["split"]["holdout_start"])

assert exploration["ts"].max() < holdout["ts"].min()
assert len(exploration) + len(holdout) == len(df)

for name, part in [("exploração", exploration), ("hold-out", holdout)]:
    print(f"{name:11s}: {len(part):>7,} linhas | {part['ts'].min()} → {part['ts'].max()} "
          f"| {part['ts'].dt.normalize().nunique()} dias")

# %% [markdown]
# ## 4. Gravação
# O hold-out é gravado em pasta separada e só é lido por `load_holdout(...)`, que exige
# confirmação explícita.

# %%
EXPLORATION_FILE.parent.mkdir(parents=True, exist_ok=True)
HOLDOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
exploration.to_parquet(EXPLORATION_FILE, index=False)
holdout.to_parquet(HOLDOUT_FILE, index=False)

manifest = {
    "asset": cfg["data"]["asset"],
    "raw_file": cfg["data"]["raw_file"],
    "holdout_start": cfg["split"]["holdout_start"],
    "total_rows": len(df),
    "exploration": {
        "rows": len(exploration),
        "start": str(exploration["ts"].min()),
        "end": str(exploration["ts"].max()),
        "days": int(exploration["ts"].dt.normalize().nunique()),
    },
    "holdout": {
        "rows": len(holdout),
        "start": str(holdout["ts"].min()),
        "end": str(holdout["ts"].max()),
        "days": int(holdout["ts"].dt.normalize().nunique()),
    },
}
MANIFEST_FILE.parent.mkdir(exist_ok=True)
MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(manifest, indent=2, ensure_ascii=False))

# %% [markdown]
# ## Conclusão
# - Dados carregados e tipados; hold-out separado e trancado.
# - **Daqui em diante, todo notebook usa `load_exploration()`.** Não ler o parquet do hold-out.
# - Próximo: `01_qualidade_dados.py`.
