import numpy as np
import pandas as pd

from src.features.flow import flow_features


def _clean(n=30):
    ts = pd.date_range("2024-03-04 09:00", periods=n, freq="min")
    close = 100 + np.arange(n, dtype=float)
    return pd.DataFrame({
        "ts": ts, "session_date": ts.normalize(), "open": close - 1, "high": close, "low": close - 1,
        "close": close, "vol": 100, "tickvol": 50, "usable": True, "day_in_segment": 30,
    })


def test_clv_r15_e_run3():
    f = flow_features(_clean(), tick=0.5)
    # barra fecha na máxima: clv = +1
    assert np.allclose(f["clv"], 1.0)
    # r15 usa o close 15 barras antes, no mesmo pregão
    assert np.isclose(f["r15_bps"].iloc[20], 1e4 * (f["close"].iloc[20] / f["close"].iloc[5] - 1))
    assert f["r15_bps"].iloc[:15].isna().all()
    # sem histórico de 20 pregões, z_vol é NaN, então não há run3
    assert (f["clv_run3"] == 0).all()
