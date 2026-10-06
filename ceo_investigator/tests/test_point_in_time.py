"""_is_valid_date é a função mais crítica do repositório: se ela deixar passar
uma data futura, todo backtest a jusante fica contaminado sem aviso."""

import datetime

import pytest

from src.data.tools_search import SearchTools

CORTE = datetime.date(2021, 12, 31)


@pytest.fixture
def tools():
    return SearchTools()


@pytest.mark.parametrize(
    "data,esperado",
    [
        ("2020-01-15", True),
        ("2021-12-30", True),
        ("2021-12-31", True),  # o próprio dia do corte entra (ver nota abaixo)
        ("2022-01-01", False),
        ("2022-03-10", False),
    ],
)
def test_filtro_de_data(tools, data, esperado):
    assert tools._is_valid_date(data, CORTE) is esperado


@pytest.mark.parametrize(
    "data", ["", "15/01/2020", "ontem", "2020-13-45", None, 20200115]
)
def test_data_improvavel_e_descartada(tools, data):
    # Fail-closed: sem prova de quando a notícia saiu, a fonte não entra.
    assert tools._is_valid_date(data, CORTE) is False


def test_timestamp_iso_com_hora_e_aceito(tools):
    assert tools._is_valid_date("2020-01-15T23:59:00Z", CORTE) is True


def test_corte_e_inclusivo_no_dia(tools):
    """Documenta um vazamento intradiário conhecido.

    Uma notícia publicada às 23h do dia do corte é aceita, mesmo que uma
    decisão tomada na abertura daquele dia não pudesse conhecê-la. Enquanto o
    filtro trabalhar com date (e não datetime com fuso), isto continua valendo.
    """
    assert tools._is_valid_date("2021-12-31T23:59:59Z", CORTE) is True


def test_search_historical_news_remove_o_futuro(tools):
    noticias = tools.search_historical_news("Executivo Exemplo", "NovaTech S.A.", CORTE)
    assert noticias, "o stub deveria devolver ao menos uma notícia válida"
    assert all(n["date"] <= CORTE.isoformat() for n in noticias)
    assert not any("Resultados anuais" in n["title"] for n in noticias)


def test_fetch_sec_filings_respeita_o_corte(tools):
    filings = tools.fetch_sec_filings("NVTC", CORTE)
    assert all(f["filingDate"] <= CORTE.isoformat() for f in filings)


def test_corte_anterior_a_tudo_devolve_vazio(tools):
    corte_antigo = datetime.date(2018, 1, 1)
    assert tools.search_historical_news("Executivo Exemplo", "NovaTech S.A.", corte_antigo) == []
    assert tools.fetch_sec_filings("NVTC", corte_antigo) == []
