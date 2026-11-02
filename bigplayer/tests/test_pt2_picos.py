from datetime import time

import pandas as pd
import pytest

from pt2.picos import add_forward_change, add_minute_change, after_stats, peak_window, summarize_peaks


def _bars(rows):
    """rows: (timestamp, high, low, close)."""
    df = pd.DataFrame(rows, columns=["ts", "high", "low", "close"])
    df["ts"] = pd.to_datetime(df["ts"])
    df["session_date"] = df["ts"].dt.normalize()
    return df


def test_variacao_e_diferenca_do_preco_medio_entre_minutos_seguidos():
    bars = add_minute_change(_bars([
        ("2024-03-04 10:00", 103, 97, 100),   # preço médio 100
        ("2024-03-04 10:01", 106, 100, 103),  # preço médio 103
    ]))
    assert bars["preco_medio"].tolist() == [100, 103]
    assert pd.isna(bars["variacao"].iloc[0])
    assert bars["variacao"].iloc[1] == 3


def test_variacao_nao_existe_depois_de_minuto_sem_negocio_nem_entre_pregoes():
    bars = add_minute_change(_bars([
        ("2024-03-04 10:00", 100, 100, 100),
        ("2024-03-04 10:02", 110, 110, 110),  # 10:01 sem negócio
        ("2024-03-04 18:29", 120, 120, 120),
        ("2024-03-05 09:00", 130, 130, 130),  # pregão seguinte
    ]))
    assert bars["variacao"].isna().all()


def test_janela_do_pico_pega_minuto_anterior_e_minuto_do_pico():
    bars = add_minute_change(_bars([
        ("2024-03-04 09:58", 100, 100, 100),
        ("2024-03-04 09:59", 102, 102, 102),
        ("2024-03-04 10:00", 107, 107, 107),
        ("2024-03-05 09:59", 200, 200, 200),  # sem 09:58: dia fica de fora
        ("2024-03-05 10:00", 210, 210, 210),
    ]))
    window = peak_window(bars, times=[time(10, 0)])
    assert window[["horario", "var_antes", "var_pico"]].values.tolist() == [["10:00", 2, 5]]


def test_resumo_por_horario_tem_minima_mediana_maxima_e_mediana_absoluta():
    window = pd.DataFrame({
        "session_date": pd.to_datetime(["2024-03-04", "2024-03-05", "2024-03-06"]),
        "horario": ["10:00"] * 3,
        "var_antes": [-4.0, 1.0, 2.0],
        "var_pico": [3.0, -6.0, 9.0],
    })
    row = summarize_peaks(window).iloc[0]
    assert row["pregoes"] == 3
    assert (row["antes_min"], row["antes_mediana"], row["antes_max"], row["antes_mediana_abs"]) == (-4, 1, 2, 2)
    assert (row["pico_min"], row["pico_mediana"], row["pico_max"], row["pico_mediana_abs"]) == (-6, 3, 9, 6)


def test_variacao_depois_compara_com_o_preco_medio_h_minutos_depois():
    bars = add_forward_change(add_minute_change(_bars([
        ("2024-03-04 10:00", 100, 100, 100),
        ("2024-03-04 10:05", 104, 104, 104),
        ("2024-03-04 10:06", 90, 90, 90),     # nada 5 minutos depois
    ])), horizons=[5])
    assert bars["depois_5"].iloc[0] == 4
    assert bars["depois_5"].iloc[1:].isna().all()


def test_estatisticas_depois_do_pico():
    minutes = pd.DataFrame({
        "variacao": [2.0, 2.0, -1.0, 0.0],
        "depois_15": [5.0, -3.0, -4.0, 1.0],
    })
    s = after_stats(minutes, 15)
    assert s["casos"] == 4
    assert (s["sobe_pct"], s["cai_pct"]) == (50, 50)
    assert s["mediana"] == -1
    # só os 3 casos em que o minuto mexeu: 2 continuam (+2→+5, −1→−4), 1 volta (+2→−3)
    assert s["continua_pct"] == pytest.approx(200 / 3)
    assert s["volta_pct"] == pytest.approx(100 / 3)
    assert s["margem_pct"] == pytest.approx(100 * 1.96 * (0.25 / 3) ** 0.5)
