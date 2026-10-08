import pandas as pd
import pytest

from src.ingestion.loader import load_holdout
from src.ingestion.split import split_exploration_holdout


def _df():
    ts = pd.date_range("2025-03-30", periods=6, freq="D")
    return pd.DataFrame({"ts": ts, "close": range(6)})


def test_split_sem_sobreposicao_e_completo():
    df = _df()
    exp, hold = split_exploration_holdout(df, "2025-04-01")
    assert exp["ts"].max() < hold["ts"].min()
    assert len(exp) + len(hold) == len(df)
    assert hold["ts"].min() == pd.Timestamp("2025-04-01")


def test_split_exige_ordenacao():
    df = _df().iloc[::-1]
    with pytest.raises(ValueError):
        split_exploration_holdout(df, "2025-04-01")


def test_holdout_trancado_por_padrao():
    with pytest.raises(PermissionError):
        load_holdout()
