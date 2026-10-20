"""Leitura do CSV bruto (export MT5) e acesso controlado aos dados já divididos.

Regra do projeto: a EDA e a modelagem só enxergam a parte de EXPLORAÇÃO.
O hold-out só é aberto na avaliação final, de forma explícita.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

import pandas as pd

BIGPLAYER_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BIGPLAYER_DIR.parent
INTERIM_DIR = BIGPLAYER_DIR / "data" / "interim"
HOLDOUT_DIR = BIGPLAYER_DIR / "data" / "holdout"

# Ativo escolhido pela variável de ambiente BIGPLAYER_ASSET (WDO por padrão; WIN para o mini índice).
ASSET = os.environ.get("BIGPLAYER_ASSET", "WDO").upper()
_CONFIGS = {"WDO": "split.toml", "WIN": "split_win.toml"}
CONFIG_PATH = BIGPLAYER_DIR / "configs" / _CONFIGS[ASSET]

EXPLORATION_FILE = INTERIM_DIR / f"{ASSET.lower()}_m1_exploracao.parquet"
HOLDOUT_FILE = HOLDOUT_DIR / f"{ASSET.lower()}_m1_holdout.parquet"
CLEAN_FILE = INTERIM_DIR / f"{ASSET.lower()}_m1_limpo.parquet"   # exploração + marcações (notebook 04)

# Figuras do WDO ficam na raiz de reports/figures (histórico); as dos demais ativos, em subpasta.
FIGURES_DIR = BIGPLAYER_DIR / "reports" / "figures" / ("" if ASSET == "WDO" else ASSET.lower())
MANIFEST_FILE = BIGPLAYER_DIR / "reports" / ("split_manifest.json" if ASSET == "WDO" else f"split_manifest_{ASSET.lower()}.json")


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def read_raw_csv(path: Path) -> pd.DataFrame:
    """Lê o CSV do MT5 (separado por tab, colunas <DATE> <TIME> ...) e devolve
    colunas em minúsculo com `ts` (datetime ingênuo, fuso ainda NÃO verificado)."""
    df = pd.read_csv(path, sep="\t")
    df.columns = [c.strip("<>").lower() for c in df.columns]
    df["ts"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y.%m.%d %H:%M:%S")
    df = df.drop(columns=["date", "time"])
    return df[["ts", "open", "high", "low", "close", "tickvol", "vol", "spread"]]


def load_exploration() -> pd.DataFrame:
    """Dados de exploração (tudo ANTES do hold-out). É a função padrão para a EDA."""
    if not EXPLORATION_FILE.exists():
        raise FileNotFoundError(
            f"{EXPLORATION_FILE} não existe. Rode notebooks/00_carga_e_split.py primeiro."
        )
    return pd.read_parquet(EXPLORATION_FILE)


def load_clean() -> pd.DataFrame:
    """Exploração já marcada (calendário, buracos, rolagem, `usable`). Use `usable` para filtrar."""
    if not CLEAN_FILE.exists():
        raise FileNotFoundError(f"{CLEAN_FILE} não existe. Rode notebooks/04_dataset_limpo.py primeiro.")
    return pd.read_parquet(CLEAN_FILE)


def load_holdout(*, i_understand_this_burns_the_holdout: bool = False) -> pd.DataFrame:
    """Abre o hold-out. Só deve ser chamado UMA vez, na avaliação final (Fase 6)."""
    if not i_understand_this_burns_the_holdout:
        raise PermissionError(
            "O hold-out está trancado. Ele só é aberto na avaliação final do projeto. "
            "Se for esse o caso, chame load_holdout(i_understand_this_burns_the_holdout=True)."
        )
    return pd.read_parquet(HOLDOUT_FILE)
