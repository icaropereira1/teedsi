# %% [markdown]
# # 01 — Qualidade dos dados (WDO M1, somente exploração)
#
# **Objetivo:** descobrir problemas nos dados ANTES de qualquer feature ou modelo.
# Perguntas:
# 1. Schema, nulos, duplicatas e ordenação estão corretos?
# 2. Os candles são consistentes (OHLC)? Preços respeitam o tick?
# 3. O que são `VOL`, `TICKVOL` e `SPREAD`? Dá para confiar neles?
# 4. Qual o fuso horário real dos timestamps? Qual o horário do pregão?
# 5. Há buracos (minutos faltando, dias incompletos)?
# 6. Como se comportam as rolagens do contrato contínuo (`$N`)?
# 7. Há outliers que parecem erro de dado?
#
# **Entrada:** `load_exploration()` (o hold-out não é tocado).
# **Saídas:** figuras em `reports/figures/01_*.png` e resumo das conclusões ao final.

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.ingestion.loader import load_exploration

FIG = BP / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 30)

def savefig(name):
    plt.tight_layout()
    plt.savefig(FIG / f"{name}.png", dpi=110)
    if matplotlib.get_backend().lower() != "agg":
        plt.show()
    plt.close()

df = load_exploration()
df["date"] = df["ts"].dt.normalize()
df["tod"] = df["ts"].dt.strftime("%H:%M")      # hora do dia
print(df.shape, df["ts"].min(), "→", df["ts"].max())

# %% [markdown]
# ## 1. Schema, nulos, duplicatas, ordenação

# %%
print("Nulos por coluna:\n", df.isna().sum().to_string())
print("\nTimestamps duplicados:", int(df["ts"].duplicated().sum()))
print("Ordenado:", df["ts"].is_monotonic_increasing)
df.describe().T

# %% [markdown]
# ## 2. Consistência OHLC e tick de preço

# %%
bad_high = df["high"] < df[["open", "close", "low"]].max(axis=1)
bad_low = df["low"] > df[["open", "close", "high"]].min(axis=1)
nonpos = (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
print("high < max(o,c,l):", int(bad_high.sum()))
print("low  > min(o,c,h):", int(bad_low.sum()))
print("preços <= 0     :", int(nonpos.sum()))

# tick do WDO: os preços são múltiplos de 0,5?
frac = ((df["close"] * 2) % 1).abs()
print("preços fora do múltiplo de 0,5:", int((frac > 1e-6).sum()))

# %% [markdown]
# ## 3. Volumes e spread
# `TICKVOL` = nº de negócios (ticks) no minuto; `VOL` = hipótese: contratos negociados.
# A razão `VOL/TICKVOL` é o **tamanho médio do negócio**, base do nosso proxy de lote grande.

# %%
print("tickvol == 0:", int((df["tickvol"] == 0).sum()), "| vol == 0:", int((df["vol"] == 0).sum()))
print("vol < tickvol:", int((df["vol"] < df["tickvol"]).sum()))
ratio = (df["vol"] / df["tickvol"].replace(0, np.nan))
print("\nVOL/TICKVOL (lote médio por negócio):")
print(ratio.describe(percentiles=[.01, .25, .5, .75, .99]).to_string())
print("\nCorrelação log(vol) × log(tickvol):",
      round(np.corrcoef(np.log1p(df["vol"]), np.log1p(df["tickvol"]))[0, 1], 4))

# %%
sp = df.groupby(df["ts"].dt.year)["spread"].agg(["min", "median", "max", lambda s: s.nunique()])
sp.columns = ["min", "mediana", "max", "valores_distintos"]
print("SPREAD por ano:\n", sp)

# %% [markdown]
# ## 4. Fuso horário e horário de pregão
# Vemos o perfil de volume por minuto do dia. A abertura (leilão/primeiros negócios) e o
# fechamento deixam picos reconhecíveis. O WDO opera aproximadamente das 09:00 às 18:00/18:30
# no horário de Brasília.

# %%
first = df.groupby("date")["tod"].min()
last = df.groupby("date")["tod"].max()
print("Primeira barra do dia — mais comuns:\n", first.value_counts().head(8).to_string())
print("\nÚltima barra do dia — mais comuns:\n", last.value_counts().head(8).to_string())

# %%
prof = df.groupby("tod")[["vol", "tickvol"]].mean()
fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
prof["vol"].plot(ax=ax[0], title="VOL médio por minuto do dia")
prof["tickvol"].plot(ax=ax[1], title="TICKVOL médio por minuto do dia")
ax[1].set_xticks(range(0, len(prof), 60))
ax[1].set_xticklabels(prof.index[::60], rotation=45)
savefig("01_perfil_volume_intradia")

# %%
# A faixa de horário muda ao longo dos anos? (horário de verão do servidor, mudança de pregão)
span = df.groupby("date").agg(first=("tod", "min"), last=("tod", "max"))
span["ano"] = span.index.year
print(span.groupby("ano").agg(primeira_mais_comum=("first", lambda s: s.mode()[0]),
                              ultima_mais_comum=("last", lambda s: s.mode()[0]),
                              dias=("first", "size")))

# %% [markdown]
# ## 5. Buracos: minutos faltando e dias incompletos

# %%
bars_per_day = df.groupby("date").size()
print(bars_per_day.describe().to_string())

fig, ax = plt.subplots(figsize=(12, 3.5))
bars_per_day.plot(ax=ax, lw=0.8, title="Barras por dia")
savefig("01_barras_por_dia")

# dias com pouquíssimas barras (pregão curto / dado faltando)
short = bars_per_day[bars_per_day < bars_per_day.median() * 0.6]
print(f"\nDias com < 60% da mediana de barras: {len(short)}")
print(short.head(15).to_string())

# %%
# Gaps intradia: diferença entre barras consecutivas DENTRO do mesmo dia
d = df.copy()
d["dt"] = d["ts"].diff().dt.total_seconds().div(60)
same_day = d["date"] == d["date"].shift(1)
gaps = d.loc[same_day & (d["dt"] > 1), "dt"]
print("Gaps intradia (>1 min):", len(gaps), "| em %:", round(100 * len(gaps) / same_day.sum(), 2))
print(gaps.describe(percentiles=[.5, .9, .99]).to_string())
print("\nMinutos 'sem barra' por ano (proxy de minutos sem negócio):")
print(d.loc[same_day & (d["dt"] > 1)].groupby(d["ts"].dt.year)["dt"].agg(["count", "sum"]).rename(columns={"count": "n_gaps", "sum": "min_faltantes"}))

# %% [markdown]
# ### 5.1 Dias úteis faltando
# O teste de gap intradia não vê dias inteiros ausentes. Comparamos com todos os dias
# seg–sex do período: faltas isoladas são, em geral, feriados; sequências longas são **buracos nos dados**.

# %%
days = pd.DatetimeIndex(df["date"].unique())
weekdays = pd.bdate_range(days.min(), days.max())
missing = pd.Series(weekdays.difference(days))
run = (missing.diff().dt.days > 3).cumsum()
runs = missing.groupby(run.values).agg(inicio="min", fim="max", dias="size")
print(f"Dias úteis (seg–sex) sem nenhuma barra: {len(missing)} de {len(weekdays)}")
print("\nBuracos com 3+ dias úteis seguidos (NÃO são feriado):")
print(runs[runs["dias"] >= 3].to_string(index=False))
print("\nFaltas isoladas (feriados prováveis):", int(runs[runs["dias"] < 3]["dias"].sum()))

fig, ax = plt.subplots(figsize=(12, 2.5))
ax.plot(days, np.ones(len(days)), "|", ms=18)
ax.set_yticks([]); ax.set_title("Dias com dado (cada traço = 1 dia). Espaços = buracos")
savefig("01_dias_com_dado")

# %%
# O horário de fechamento do pregão varia? (17:59 vs 18:29)
last_by_month = (df.groupby("date")["tod"].max()
                 .groupby([lambda d: d.year, lambda d: d.month]).agg(lambda s: s.mode()[0]).unstack())
print("Último minuto mais comum, por ano × mês:")
print(last_by_month.to_string())

# %% [markdown]
# ## 6. Rolagem do contrato contínuo (`$N`)
# O WDO vence todo mês. No contínuo, na troca de vencimento pode haver um **salto de preço**
# entre o último fechamento e a primeira abertura do dia seguinte que não é movimento de mercado.
# Medimos o gap overnight (open do dia − close do dia anterior).

# %%
daily = df.groupby("date").agg(open=("open", "first"), close=("close", "last"),
                               high=("high", "max"), low=("low", "min"), vol=("vol", "sum"))
daily["gap"] = daily["open"] - daily["close"].shift(1)
daily["gap_pct"] = 100 * daily["gap"] / daily["close"].shift(1)
print(daily["gap_pct"].describe(percentiles=[.01, .05, .5, .95, .99]).to_string())

# %%
big = daily["gap_pct"].abs().nlargest(15)
print("Maiores gaps overnight (% do preço):")
print(daily.loc[big.index, ["open", "close", "gap", "gap_pct"]].assign(
    dia_do_mes=lambda x: x.index.day, dia_semana=lambda x: x.index.day_name()).sort_index().to_string())

# %%
# Os maiores gaps se concentram no início do mês (troca de vencimento)?
daily["dia_util_no_mes"] = daily.groupby([daily.index.year, daily.index.month]).cumcount() + 1
g = daily.groupby("dia_util_no_mes")["gap_pct"].agg(lambda s: s.abs().mean())
fig, ax = plt.subplots(figsize=(10, 3.5))
g.head(23).plot.bar(ax=ax, title="|gap overnight| médio (%) por dia útil do mês")
savefig("01_gap_por_dia_util_mes")
print(g.head(6).round(3).to_string())

# %% [markdown]
# ## 7. Outliers

# %%
ret = np.log(df["close"]).diff()
same = df["date"] == df["date"].shift(1)
ret1m = ret.where(same)   # só retornos dentro do dia
print("Retorno 1 min (log):")
print(ret1m.describe(percentiles=[.001, .01, .5, .99, .999]).to_string())
z = (ret1m - ret1m.mean()) / ret1m.std()
print("\nBarras com |z| > 10:", int((z.abs() > 10).sum()))
print(df.loc[z.abs().nlargest(8).index, ["ts", "open", "high", "low", "close", "tickvol", "vol"]].to_string())

# %%
fig, ax = plt.subplots(1, 2, figsize=(12, 3.5))
ret1m.dropna().clip(-0.003, 0.003).hist(bins=120, ax=ax[0]); ax[0].set_title("Retorno 1 min (clip ±0,3%)")
np.log1p(df["vol"]).hist(bins=100, ax=ax[1]); ax[1].set_title("log(1+VOL)")
savefig("01_distribuicoes")

# %% [markdown]
# ## Conclusões
# Preenchido após a execução — ver `docs/STATUS.md` (seção "Achados da qualidade dos dados")
# e as figuras em `reports/figures/`. Decisões de limpeza que decorrem daqui serão aplicadas
# no pipeline da Fase 1 (`src/cleaning/`), valendo para exploração e hold-out.
