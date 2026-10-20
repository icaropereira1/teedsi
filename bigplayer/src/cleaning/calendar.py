"""Calendário de pregão B3 para o WDO e o WIN (candles M1).

Regras de sessão e feriados vêm daqui, não do dado, para que o dado possa ser
auditado contra o calendário (dias faltando, barras fora da sessão).

Horários são os do timestamp da ÚLTIMA barra (não do fechamento do leilão):
- WDO: abre 09:00; última barra 17:59 (horário de verão dos EUA) ou 18:29.
- WIN: abre 09:00; última barra 17:54 ou 18:24.
Observado nos dados (2020–2025): a sessão curta vale do 1º pregão após o início do horário de
verão dos EUA até o último pregão antes do fim; a partir de 2024 a sessão é sempre a longa.
Quarta-feira de Cinzas: o pregão abre às 13:00.

Feriados e fechamentos foram conferidos contra os CSVs do WDO e do WIN (exploração): com as regras
abaixo, todo dia útil ausente nos dados é um buraco real (ver `holes.py`). Os dois fechamentos
`OBSERVED_CLOSURES` não têm regra conhecida; foram inferidos por ausência nos dois ativos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
from dateutil.easter import easter

OPEN_MINUTE = 9 * 60
LAST_BAR = {  # (sessão curta, sessão longa), em minutos desde 00:00
    "WDO": (17 * 60 + 59, 18 * 60 + 29),
    "WIN": (17 * 60 + 54, 18 * 60 + 24),
}
LONG_ONLY_FROM = pd.Timestamp("2024-01-01")  # a partir daqui não há mais sessão curta
# O WDO fechava às 17:55 (e não 17:59) na sessão curta de set–out/2020.
WDO_SHORT_OLD = (pd.Timestamp("2020-11-01"), 17 * 60 + 55)
ASH_WEDNESDAY_OPEN = 13 * 60
NATIONAL_CONSCIENCE_DAY_FROM = 2024  # 20/11 só virou feriado da B3 em 2024 (aberto em 2023)
# Ausências inferidas dos dados (dia de semana, sem regra conhecida). Confirmar com a B3 se importar.
OBSERVED_CLOSURES = pd.DatetimeIndex(["2021-01-25", "2021-07-09"])


@dataclass(frozen=True)
class Session:
    open_minute: int
    last_minute: int

    @property
    def n_bars(self) -> int:
        return self.last_minute - self.open_minute + 1


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def us_dst_range(year: int) -> tuple[date, date]:
    """Início (2º domingo de março) e fim (1º domingo de novembro) do horário de verão dos EUA."""
    return _nth_weekday(year, 3, 6, 2), _nth_weekday(year, 11, 6, 1)


def is_short_session(day: pd.Timestamp) -> bool:
    """Pregão com fechamento antecipado (sessão curta)? Só até 2023."""
    day = pd.Timestamp(day).normalize()
    if day >= LONG_ONLY_FROM:
        return False
    start, end = us_dst_range(day.year)
    return pd.Timestamp(start) <= day < pd.Timestamp(end)


def session_for(day: pd.Timestamp, asset: str) -> Session:
    day = pd.Timestamp(day).normalize()
    asset = asset.upper()
    short, long_ = LAST_BAR[asset]
    if asset == "WDO" and day < WDO_SHORT_OLD[0]:
        short = WDO_SHORT_OLD[1]
    is_ash = day.date() == easter(day.year) - timedelta(days=46)
    return Session(ASH_WEDNESDAY_OPEN if is_ash else OPEN_MINUTE,
                   short if is_short_session(day) else long_)


def b3_holidays(first_year: int, last_year: int) -> pd.DatetimeIndex:
    """Feriados em que a B3 não opera (dias de semana). Móveis a partir da Páscoa."""
    days: list[date] = []
    for y in range(first_year, last_year + 1):
        e = easter(y)
        days += [
            e - timedelta(days=48),  # segunda de Carnaval
            e - timedelta(days=47),  # terça de Carnaval
            e - timedelta(days=2),   # sexta-feira santa
            e + timedelta(days=60),  # Corpus Christi
        ]
        days += [date(y, m, d) for m, d in
                 [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (12, 24), (12, 25)]]
        if y >= NATIONAL_CONSCIENCE_DAY_FROM:
            days.append(date(y, 11, 20))
        # 31/12 (ou o último dia útil do ano, se cair no fim de semana): sem pregão
        d = date(y, 12, 31)
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        days.append(d)
    idx = pd.DatetimeIndex(sorted(set(days)))
    idx = idx.union(OBSERVED_CLOSURES[(OBSERVED_CLOSURES.year >= first_year) & (OBSERVED_CLOSURES.year <= last_year)])
    return idx[idx.dayofweek < 5]


def expected_trading_days(start, end) -> pd.DatetimeIndex:
    """Dias de semana entre start e end (inclusive) que não são feriado da B3."""
    bdays = pd.bdate_range(pd.Timestamp(start), pd.Timestamp(end))
    hol = b3_holidays(bdays.min().year, bdays.max().year)
    return bdays.difference(hol)


def roll_days(asset: str, start, end) -> pd.DatetimeIndex:
    """Pregões em que o contínuo `$N` troca de contrato: a ABERTURA do dia traz o contrato novo,
    então o gap overnight desse dia inclui o carry entre contratos (não é movimento de mercado).

    Verificado nos dados (exploração): o gap é positivo em ~90% (WIN) e ~80% (WDO) das trocas e
    acompanha a Selic (WIN: 0,3% em 2020, ~2% em 2022 e 2025; WDO: ~0,4% mediano).
    - WIN: vencimento na quarta-feira mais próxima do dia 15 dos meses pares
      (se feriado, o pregão anterior). A troca aparece na abertura desse mesmo dia.
    - WDO: o último pregão de cada mês (o contrato vence no 1º dia útil do mês seguinte).
    """
    asset = asset.upper()
    trading = expected_trading_days(start, end)
    if asset == "WDO":
        s = pd.Series(trading, index=trading)
        days = s.groupby([trading.year, trading.month]).max().values
        return pd.DatetimeIndex(days)
    days = []
    for y in range(pd.Timestamp(start).year, pd.Timestamp(end).year + 1):
        for m in range(2, 13, 2):
            c = pd.Timestamp(y, m, 15)
            off = (2 - c.weekday() + 3) % 7 - 3          # quarta-feira mais próxima (-3..+3)
            wed = c + pd.Timedelta(days=off)
            prev = trading[trading <= wed]
            if len(prev):
                days.append(prev[-1])
    return pd.DatetimeIndex(sorted(set(days)))
