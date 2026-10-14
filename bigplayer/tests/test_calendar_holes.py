import pandas as pd

from src.cleaning.calendar import (
    b3_holidays, roll_days, expected_trading_days, is_short_session, session_for, us_dst_range,
)
from src.cleaning.holes import find_holes, lookback_ok, mark_bars


def test_horario_de_verao_eua():
    assert us_dst_range(2021) == (pd.Timestamp("2021-03-14").date(), pd.Timestamp("2021-11-07").date())


def test_sessao_curta_so_ate_2023():
    assert is_short_session(pd.Timestamp("2021-06-01"))
    assert not is_short_session(pd.Timestamp("2021-12-01"))
    assert not is_short_session(pd.Timestamp("2024-06-03"))  # desde 2024, sempre longa


def test_fechamento_por_ativo():
    assert session_for(pd.Timestamp("2021-06-01"), "WIN").last_minute == 17 * 60 + 54
    assert session_for(pd.Timestamp("2021-06-01"), "WDO").last_minute == 17 * 60 + 59
    assert session_for(pd.Timestamp("2020-10-01"), "WDO").last_minute == 17 * 60 + 55
    assert session_for(pd.Timestamp("2025-01-06"), "WIN").last_minute == 18 * 60 + 24


def test_quarta_de_cinzas_abre_as_13h():
    s = session_for(pd.Timestamp("2024-02-14"), "WIN")
    assert s.open_minute == 13 * 60 and s.n_bars == 325


def test_feriados():
    h = b3_holidays(2023, 2024)
    assert pd.Timestamp("2023-12-29") in h        # 31/12 caiu no domingo
    assert pd.Timestamp("2024-11-20") in h and pd.Timestamp("2023-11-20") not in h
    assert pd.Timestamp("2024-03-29") in h        # sexta-feira santa
    assert pd.Timestamp("2024-02-14") not in h    # quarta de cinzas tem pregão


def test_buracos_e_trechos():
    days = expected_trading_days("2024-03-04", "2024-03-15")
    present = days.difference(pd.DatetimeIndex(["2024-03-07", "2024-03-08", "2024-03-12"]))
    holes = find_holes(present)
    assert list(holes["trading_days"]) == [2, 1]
    assert holes["start"].iloc[0] == pd.Timestamp("2024-03-07")

    rows = [pd.Timestamp(d) + pd.Timedelta(hours=10, minutes=m) for d in present for m in (0, 1)]
    marked = mark_bars(pd.DataFrame({"ts": rows}), "WIN")
    assert marked["segment"].nunique() == 3
    first = marked.groupby("session_date")["day_in_segment"].first()
    assert first.loc["2024-03-04"] == 1 and first.loc["2024-03-06"] == 3
    assert first.loc["2024-03-11"] == 1 and first.loc["2024-03-13"] == 1
    assert not lookback_ok(marked, 2).loc[marked["session_date"] == "2024-03-11"].any()


def test_usable_exclui_parcial_e_fora_da_sessao():
    d = pd.Timestamp("2024-03-04")
    ts = [d + pd.Timedelta(hours=9, minutes=m) for m in range(535)]   # sessão completa até 17:54
    ts.append(d + pd.Timedelta(hours=18, minutes=31))                 # fora da sessão
    ts += [pd.Timestamp("2024-03-05 10:00")]                          # pregão parcial (1 barra)
    m = mark_bars(pd.DataFrame({"ts": ts}), "WIN")
    assert m["usable"].iloc[:535].all()
    assert not m["usable"].iloc[535] and not m["usable"].iloc[536]


def test_dias_de_rolagem():
    win = roll_days("WIN", "2024-01-01", "2024-12-31")
    assert list(win.strftime("%m-%d")) == ["02-14", "04-17", "06-12", "08-14", "10-16", "12-18"]
    wdo = roll_days("WDO", "2024-01-01", "2024-12-31")
    assert len(wdo) == 12 and pd.Timestamp("2024-12-30") in wdo and pd.Timestamp("2024-11-29") in wdo
