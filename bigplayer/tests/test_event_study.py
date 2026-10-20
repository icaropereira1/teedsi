import numpy as np
import pandas as pd

from src.evaluation.event_study import cluster_bootstrap_mean, forward_returns


def _bars():
    ts = pd.date_range("2024-03-04 10:00", periods=10, freq="min")
    close = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109], float)
    open_ = close - 1
    return pd.DataFrame({"session_date": ts.normalize(), "ts": ts, "open": open_, "close": close})


def test_entrada_na_abertura_seguinte_e_saida_no_fechamento():
    b = _bars()
    r = forward_returns(b, (3,))
    # sinal na barra 0: entra no open da barra 1 (=100), sai no close da barra 3 (=103)
    assert np.isclose(r["fwd_3"].iloc[0], 1e4 * (103 / 100 - 1))


def test_nao_cruza_o_pregao():
    b = _bars()
    r = forward_returns(b, (30,))
    # horizonte maior que o pregão: NaN (nunca olha o dia seguinte nem trunca a saída)
    assert r["fwd_30"].isna().all()


def test_bootstrap_detecta_media_positiva():
    rng = np.random.default_rng(1)
    days = np.repeat(np.arange(200), 5)
    m, lo, hi, p = cluster_bootstrap_mean(rng.normal(0.5, 1, 1000), days)
    assert lo > 0 and p < 0.05
