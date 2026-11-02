from datetime import time

import pandas as pd
import pytest

from pt2.picos import (
    add_forward_change, add_minute_change, after_peak_table, after_stats, around_peaks, peak_window, price_path,
    summarize_peaks,
)


def _bars(rows):
    """rows: (timestamp, high, low, close)."""
    df = pd.DataFrame(rows, columns=["ts", "high", "low", "close"])
    df["ts"] = pd.to_datetime(df["ts"])
    df["session_date"] = df["ts"].dt.normalize()
    return df


def _flat(rows):
    """rows: (timestamp, preço) com máxima = mínima = fechamento."""
    return _bars([(ts, p, p, p) for ts, p in rows])


def test_variacao_do_preco_medio_e_do_fechamento_entre_minutos_seguidos():
    bars = add_minute_change(_bars([
        ("2024-03-04 10:00", 103, 97, 100),   # preço médio 100
        ("2024-03-04 10:01", 106, 100, 103),  # preço médio 103
    ]))
    assert bars["preco_medio"].tolist() == [100, 103]
    assert bars["variacao"].iloc[1] == 3
    assert bars["variacao_fech"].iloc[1] == 3
    assert bars[["variacao", "variacao_fech"]].iloc[0].isna().all()


def test_variacao_nao_existe_depois_de_minuto_sem_negocio_nem_entre_pregoes():
    bars = add_minute_change(_flat([
        ("2024-03-04 10:00", 100),
        ("2024-03-04 10:02", 110),  # 10:01 sem negócio
        ("2024-03-04 23:59", 120),
        ("2024-03-05 00:00", 130),  # 1 minuto depois, mas em outro pregão
    ]))
    assert bars["variacao"].isna().all()
    assert bars["variacao_fech"].isna().all()


def test_janela_do_pico_pega_os_dois_minutos_anteriores_e_o_minuto_do_pico():
    bars = add_minute_change(_flat([
        ("2024-03-04 09:57", 100),
        ("2024-03-04 09:58", 101),
        ("2024-03-04 09:59", 103),
        ("2024-03-04 10:00", 108),
        ("2024-03-05 09:58", 200),  # sem 09:57: dia fica de fora
        ("2024-03-05 09:59", 201),
        ("2024-03-05 10:00", 210),
    ]))
    window = peak_window(bars, times=[time(10, 0)])
    assert window[["horario", "var_antes2", "var_antes", "var_pico"]].values.tolist() == [["10:00", 1, 2, 5]]


def test_resumo_por_horario():
    window = pd.DataFrame({
        "session_date": pd.to_datetime(["2024-03-04", "2024-03-05", "2024-03-06", "2024-03-07"]),
        "horario": ["10:00"] * 4,
        "var_antes2": [1.0, 5.0, 2.0, 1.0],
        "var_antes": [-4.0, 1.0, 2.0, 3.0],
        "var_pico": [3.0, -6.0, 9.0, 3.0],
    })
    row = summarize_peaks(window).iloc[0]
    assert row["pregoes"] == 4
    assert (row["antes_min"], row["antes_mediana"], row["antes_max"], row["antes_mediana_abs"]) == (-4, 1.5, 3, 2.5)
    assert (row["pico_min"], row["pico_mediana"], row["pico_max"], row["pico_mediana_abs"]) == (-6, 3, 9, 4.5)
    assert (row["antes_sobe_pct"], row["antes_cai_pct"]) == (75, 25)
    # |T−1| contra |T−2|: 4>1, 1<5, 2=2 (empate fica fora), 3>1 → 2 de 3
    assert row["antes_maior_pct"] == pytest.approx(200 / 3)
    # |T| contra |T−1|: 3<4, 6>1, 9>2, 3=3 (empate fica fora) → 2 de 3
    assert row["pico_maior_pct"] == pytest.approx(200 / 3)
    assert row["pico_margem_pct"] == pytest.approx(100 * 1.96 * (0.25 / 3) ** 0.5)


def test_variacao_depois_compara_com_h_minutos_depois():
    bars = add_forward_change(add_minute_change(_bars([
        ("2024-03-04 10:00", 103, 97, 100),    # preço médio 100, fechamento 100
        ("2024-03-04 10:05", 110, 104, 108),   # preço médio 107,33, fechamento 108
        ("2024-03-04 10:06", 90, 90, 90),      # nada 5 minutos depois
    ])), horizons=[5])
    assert bars["depois_5"].iloc[0] == pytest.approx(22 / 3)
    assert bars["depois_fech_5"].iloc[0] == 8
    assert bars[["depois_5", "depois_fech_5"]].iloc[1:].isna().all().all()


def test_estatisticas_depois_ignoram_dias_sem_dado():
    minutes = pd.DataFrame({
        "depois_15": [5.0, -3.0, -4.0, 1.0, None],
        "variacao_fech": [2.0, 2.0, -1.0, 0.0, 1.0],
        "depois_fech_15": [5.0, -3.0, -4.0, 1.0, None],
    })
    s = after_stats(minutes, 15)
    assert s["casos"] == 4
    assert (s["sobe_pct"], s["cai_pct"]) == (50, 50)
    assert s["mediana"] == -1
    # direção só onde o fechamento mexeu e há dado depois: 2 continuam (+2→+5, −1→−4), 1 volta (+2→−3)
    assert s["casos_direcao"] == 3
    assert s["continua_pct"] == pytest.approx(200 / 3)
    assert s["volta_pct"] == pytest.approx(100 / 3)
    assert s["margem_pct"] == pytest.approx(100 * 1.96 * (0.25 / 3) ** 0.5)


def test_direcao_usa_o_fechamento_e_nao_o_preco_medio():
    minutes = pd.DataFrame({
        "depois_5": [1.0],
        "variacao_fech": [-1.0],      # fechamento caiu no minuto do pico...
        "depois_fech_5": [-2.0],      # ...e continuou caindo
    })
    assert after_stats(minutes, 5)["continua_pct"] == 100


def test_sem_minuto_anterior_ainda_tem_expectativa_mas_nao_tem_direcao():
    minutes = pd.DataFrame({"depois_5": [3.0, -1.0], "variacao_fech": [None, None], "depois_fech_5": [3.0, -1.0]})
    s = after_stats(minutes, 5)
    assert (s["casos"], s["sobe_pct"], s["casos_direcao"]) == (2, 50, 0)
    assert pd.isna(s["continua_pct"]) and pd.isna(s["margem_pct"])


def test_tabela_depois_do_pico_compara_com_minutos_comuns_da_mesma_hora():
    # sobe 1 ponto por minuto das 10:00 às 10:59 e cai 1 ponto por minuto das 11:00 às 11:59
    minutes = pd.date_range("2024-03-04 10:00", "2024-03-04 11:59", freq="min")
    prices = [m if m < 60 else 118 - m for m in range(len(minutes))]
    bars = add_forward_change(add_minute_change(_flat(zip(minutes.astype(str), prices))), horizons=[1])
    peaks = [time(10, 0), time(10, 30), time(11, 0), time(11, 30)]
    table = after_peak_table(bars, times=peaks, horizons=[1]).set_index("horario")

    assert table.loc["10:00", "sobe_pct"] == 100
    assert table.loc["11:00", "sobe_pct"] == 0
    # minutos comuns das 10h: 10:01 a 10:59 sem 10:30 = 58; só 10:59 → 11:00 cai
    assert table.loc["10:30", "normal_sobe_pct"] == pytest.approx(100 * 57 / 58)
    # minutos comuns das 11h: todos caem (11:59 não tem minuto seguinte)
    assert table.loc["11:00", "normal_sobe_pct"] == 0


def test_caminho_do_preco_e_medido_contra_a_abertura_do_mesmo_pregao():
    bars = add_minute_change(_flat([
        ("2024-03-04 09:00", 100),
        ("2024-03-04 09:01", 104),
        ("2024-03-05 09:01", 500),   # 1º negócio do dia às 9:01: vira a referência
        ("2024-03-05 09:02", 490),
    ]))
    path = price_path(bars)
    assert path.loc[time(9, 0), "mediana"] == 0
    assert path.loc[time(9, 1), "mediana"] == 2          # dias: +4 e 0
    assert path.loc[time(9, 1), "pregoes"] == 2
    assert path.loc[time(9, 2), "mediana"] == -10


def test_janela_em_volta_do_pico_marca_o_minuto_relativo():
    bars = _flat([("2024-03-04 09:58", 100), ("2024-03-04 09:59", 102), ("2024-03-04 10:00", 107)])
    bars["vol"] = [10, 20, 90]
    window = around_peaks(add_minute_change(bars), times=[time(10, 0)], offsets=range(-2, 2))
    rows = window.sort_values("minuto_rel")[["minuto_rel", "variacao", "vol"]].values.tolist()
    assert rows[0][0] == -2 and pd.isna(rows[0][1]) and rows[0][2] == 10
    assert rows[1:] == [[-1, 2, 20], [0, 5, 90]]          # 10:01 não existe: fica de fora
    assert set(window["horario"]) == {"10:00"}
