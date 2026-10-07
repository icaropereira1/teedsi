# %% [markdown]
# # 02 — Insights de volume e lote (WDO M1, somente exploração)
#
# **Objetivo:** gerar os gráficos da apresentação de insights e os números citados nela.
# Perguntas:
# 1. Onde está o volume, ao longo dos dias e dentro do pregão?
# 2. Volume bruto serve para achar fluxo anômalo, ou precisa normalizar por horário? Como normalizar?
# 3. O lote médio por negócio (`VOL/TICKVOL`) serve, sozinho, como proxy de lote grande?
#
# **Entrada:** `load_exploration()` (o hold-out não é tocado).
# **Saídas:** figuras em `reports/figures/02_*.png`, já no tamanho dos slides, e os números impressos.
#
# Fonte dos gráficos: IBM Plex Sans, se estiver instalada (é a fonte da apresentação);
# senão, a sans-serif padrão do sistema.

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import numpy as np
import pandas as pd

from src.ingestion.loader import load_exploration

FIG = BP / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 140)

# Tamanhos em px de slide (1920x1080): figsize = px/100 e dpi=200 (2x). 1 px de slide = 0,72 pt.
PX = 0.72
INK, BODY, MUTED = "#14202B", "#46505C", "#5F6672"
GRID, AXIS = "#E2E0D9", "#C3C2B7"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#C9CED6"
D_TEXT, D_MUTED, D_GRID, D_BLUE = "#F3F1EA", "#A9B6C4", "#263546", "#6da7ec"
LIGHT_BG, DARK_BG = "#F6F5F1", "#13202E"  # mesmas cores de fundo dos slides

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["IBM Plex Sans", "Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 24 * PX,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": MUTED,
    "axes.facecolor": "none",
    "axes.linewidth": 1.5 * PX,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelsize": 24 * PX,
    "ytick.labelsize": 24 * PX,
    "xtick.major.width": 1.5 * PX,
    "xtick.major.size": 6 * PX,
    "ytick.major.size": 0,
})


def br(x, nd=0):
    """Número no formato brasileiro (1.234,5)."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def new_fig(w, h):
    """Figura com w x h px de slide, só com o eixo de baixo e grade horizontal."""
    f, ax = plt.subplots(figsize=(w / 100, h / 100), dpi=200)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=1.2 * PX)
    ax.set_axisbelow(True)
    return f, ax


def savefig(f, name, bg=LIGHT_BG):
    f.savefig(FIG / f"{name}.png", dpi=200, facecolor=bg)
    if matplotlib.get_backend().lower() != "agg":
        plt.show()
    plt.close(f)


df = load_exploration()
df["date"] = df["ts"].dt.normalize()
df["tod"] = df["ts"].dt.hour * 60 + df["ts"].dt.minute   # minuto do dia
df["hour"] = df["ts"].dt.hour
df["lot"] = df["vol"] / df["tickvol"]                     # lote médio por negócio
df["ret"] = np.log(df["close"]).groupby(df["date"]).diff()  # retorno 1 min, só dentro do dia
df["lv"] = np.log(df["vol"])
print(df.shape, df["ts"].min(), "→", df["ts"].max())

# %% [markdown]
# ## 1. Volume por pregão e buracos nos dados
# Os buracos são os do notebook 01 (decisão do grupo: ignorar). O 1º dia começa às 14:08
# (parcial) e fica de fora do gráfico.

# %%
daily = df.groupby("date")["vol"].sum()
print("Contratos por pregão — mediana:", br(daily.median()))

daily_mi = daily.iloc[1:] / 1e6
f, ax = new_fig(1664, 360)
ax.grid(axis="y", color=D_GRID, linewidth=1.2 * PX)
ax.spines["bottom"].set_color("#3A4A5C")
ax.tick_params(colors=D_MUTED)
ax.vlines(daily_mi.index, 0, daily_mi.values, color=D_BLUE, linewidth=1.6 * PX)
gaps = [("2021-11-24", "2021-12-01", "6 dias"), ("2022-07-15", "2022-07-28", "10 dias"),
        ("2023-06-05", "2023-09-19", "77 dias úteis sem dados")]
for a, b, lab in gaps:
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    ax.axvspan(a, b + pd.Timedelta(days=1), color=D_TEXT, alpha=0.07, linewidth=0)
    ax.text(a + (b - a) / 2, 6.55, lab, color=D_TEXT, ha="center", va="bottom", fontsize=24 * PX,
            fontweight="medium")
ax.set_ylim(0, 7.6)
ax.set_yticks([0, 2, 4, 6])
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: "0" if v == 0 else f"{v:.0f} mi"))
ax.set_xlim(daily_mi.index.min() - pd.Timedelta(days=10), daily_mi.index.max() + pd.Timedelta(days=10))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
f.subplots_adjust(left=0.045, right=0.995, top=0.98, bottom=0.14)
savefig(f, "02_volume_diario", bg=DARK_BG)

# %% [markdown]
# ## 2. Perfil intradiário do volume
# Mediana, entre pregões, dos contratos negociados em cada minuto do dia.

# %%
share = df.groupby("hour")["vol"].sum() / df["vol"].sum()
print("Participação no volume por hora:\n", (100 * share).round(1).to_string())
print("Participação das 9h às 11h59:", br(100 * share.loc[9:11].sum(), 1), "%")
morning = df.loc[df["tod"].between(9 * 60, 11 * 60 - 1), "vol"].median()
afternoon = df.loc[df["tod"].between(14 * 60, 17 * 60 - 1), "vol"].median()
print(f"Volume/min mediano 09:00–10:59 = {morning:.0f} | 14:00–16:59 = {afternoon:.0f} "
      f"| razão = {morning / afternoon:.2f}")

prof = df.groupby("tod")["vol"].median() / 1e3
f, ax = new_fig(1000, 576)
ax.fill_between(prof.index, 0, prof.values, color=BLUE, alpha=0.10, linewidth=0)
ax.plot(prof.index, prof.values, color=BLUE, linewidth=3 * PX, solid_joinstyle="round")
peaks = {541: None, 570: "09:30", 600: "10:00", 630: "10:30", 660: "11:00", 720: "12:00"}
for t, lab in peaks.items():
    y = prof.loc[t]
    ax.plot(t, y, "o", ms=10 * PX, color=BLUE, mec=LIGHT_BG, mew=2 * PX)
    if lab is None:
        continue
    # 11:00 e 12:00 com rótulo à direita, para não colidir com 10:30
    dx, dy, ha, va = (14, 0, "left", "center") if t in (660, 720) else (0, 12, "center", "bottom")
    ax.annotate(lab, (t, y), xytext=(dx * PX, dy * PX), textcoords="offset points", ha=ha,
                va=va, color=INK, fontsize=24 * PX, fontweight="medium")
ax.annotate(f"09:01: {br(prof.loc[541] * 1e3)} contratos,\no minuto mais cheio do dia", (541, prof.loc[541]),
            xytext=(600, 16.4), color=BODY, fontsize=24 * PX, va="center", ha="left",
            arrowprops=dict(arrowstyle="-", color=AXIS, lw=1.5 * PX, shrinkA=4, shrinkB=8))
ax.set_xlim(538, 18 * 60 + 31)
ax.set_xticks(range(540, 18 * 60 + 1, 60))
ax.set_xticklabels([f"{h}h" for h in range(9, 19)])
ax.set_ylim(0, 19.5)
ax.set_yticks([0, 5, 10, 15])
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: "0" if v == 0 else f"{v:.0f} mil"))
f.subplots_adjust(left=0.09, right=0.99, top=0.97, bottom=0.09)
savefig(f, "02_perfil_intradia")

# %% [markdown]
# ## 3. Volume bruto × normalizado por horário
# Pegamos o 1% de minutos mais extremos por cada critério e contamos em que hora caem.
# Sem viés de horário, cada uma das 9 horas (09:00–17:59) teria ~11%.
#
# - **z-score:** `(log vol − média do log no mesmo minuto dos 20 pregões anteriores) / desvio`.
# - **Razão simples (RVOL):** `vol / mediana do mesmo minuto dos 20 pregões anteriores`.
#
# Os dois usam só o passado (`shift(1)`), sem look-ahead. A janela de 20 pregões atravessa
# os buracos dos dados; para esta comparação descritiva, isso foi aceito.

# %%
lv = df.pivot_table(index="date", columns="tod", values="lv")
past = lv.rolling(20, min_periods=10)
hist = pd.concat({
    "mu": past.mean().shift(1).stack(),
    "sd": past.std().shift(1).stack(),
    "med": past.median().shift(1).stack(),
}, axis=1).reset_index()
d = df.merge(hist, on=["date", "tod"])
d = d[d["tod"] < 18 * 60].copy()   # 09:00–17:59, horário comum a todos os anos
d["z"] = (d["lv"] - d["mu"]) / d["sd"]
d["rvol"] = np.exp(d["lv"] - d["med"])


def share_by_hour(mask):
    return 100 * d.loc[mask, "hour"].value_counts(normalize=True).reindex(range(9, 18), fill_value=0)


top = pd.DataFrame({
    "bruto": share_by_hour(d["vol"] >= d["vol"].quantile(.99)),
    "zscore": share_by_hour(d["z"] >= d["z"].quantile(.99)),
    "razao_simples": share_by_hour(d["rvol"] >= d["rvol"].quantile(.99)),
})
print("Onde caem os 1% de minutos mais extremos (% por hora):\n", top.round(1).to_string())
print("Bruto, 9h às 11h59:", br(top["bruto"].loc[9:11].sum(), 1), "%")
print("Desvio do log do volume por hora (mediana):\n",
      d.groupby("hour")["sd"].median().round(2).to_string())

r = d["ret"].abs() * 1e4
r_z = r[d["z"] >= d["z"].quantile(.99)].median()
print(f"|retorno| mediano (bps): geral = {r.median():.2f} | top 1% z-score = {r_z:.2f} "
      f"| razão = {r_z / r.median():.1f}x")

f, ax = new_fig(1000, 576)
x = np.arange(9)
w = 0.36
ax.bar(x - w / 2 - 0.01, top["bruto"].values, w, color=ORANGE, label="Volume bruto")
ax.bar(x + w / 2 + 0.01, top["zscore"].values, w, color=BLUE, label="Volume normalizado por horário")
ax.hlines(100 / 9, -0.6, 8.42, color=MUTED, linewidth=1.5 * PX)
ax.text(8.5, 100 / 9, "11%\nao acaso", ha="left", va="center", color=MUTED, fontsize=24 * PX, linespacing=1.1)
for i in (0, 1):
    v = top["bruto"].iloc[i]
    ax.text(x[i] - w / 2, v + 0.6, f"{br(v)}%", ha="center", va="bottom", color=INK,
            fontsize=24 * PX, fontweight="semibold")
ax.set_xticks(x)
ax.set_xticklabels([f"{h}h" for h in range(9, 18)])
ax.set_xlim(-0.6, 9.6)
ax.set_ylim(0, 38)
ax.set_yticks([0, 10, 20, 30])
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.legend(loc="upper right", frameon=False, fontsize=24 * PX, handlelength=1.0, handleheight=1.0,
          labelcolor=BODY, borderaxespad=0.2)
f.subplots_adjust(left=0.07, right=0.99, top=0.97, bottom=0.09)
savefig(f, "02_bruto_vs_normalizado")

# %% [markdown]
# ## 4. Lote médio por negócio (`VOL/TICKVOL`)

# %%
lot = df["lot"]
med, p99 = lot.median(), lot.quantile(.99)
print(f"Lote médio: mediana = {med:.2f} | p99 = {p99:.2f}")
print("Lote mediano por hora:\n", df.groupby("hour")["lot"].median().round(2).to_string())

f, ax = new_fig(800, 330)
bins = np.arange(1.5, 10.01, 0.1)
cnt, edges = np.histogram(lot.clip(upper=10), bins=bins)   # última barra = 10 ou mais
pct = 100 * cnt / len(lot)
ax.bar(edges[:-1], pct, width=0.1, align="edge", color=BLUE, edgecolor=LIGHT_BG, linewidth=0.8 * PX)
for v, lab in [(med, f"mediana {br(med, 1)}"), (p99, f"p99 {br(p99, 1)}")]:
    ax.axvline(v, color=INK, linewidth=1.5 * PX)
    ax.text(v + 0.15, pct.max() * 1.02, lab, color=INK, fontsize=24 * PX, fontweight="medium", va="top")
ax.annotate(f"1% dos minutos\nacima de {br(p99, 1)}", (8.8, 0.12), xytext=(7.9, pct.max() * 0.55),
            color=BODY, fontsize=24 * PX, ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color=AXIS, lw=1.5 * PX, shrinkA=4, shrinkB=2))
ax.set_xlim(1.5, 10.5)
ax.set_xticks([2, 4, 6, 8, 10])
ax.set_xticklabels(["2", "4", "6", "8", "10+"])
ax.set_ylim(0, pct.max() * 1.08)
ax.set_yticks([0, 2, 4, 6])
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
f.subplots_adjust(left=0.09, right=0.98, top=0.97, bottom=0.17)
savefig(f, "02_lote_distribuicao")

# %% [markdown]
# ### 4.1 Lote alto = big player?
# Dividimos os minutos em 10 faixas (decis) de lote e olhamos quantos negócios e quanto
# movimento de preço cada faixa tem.

# %%
df["lot_dec"] = pd.qcut(df["lot"], 10, labels=False)
by_dec = pd.DataFrame({
    "negocios_mediana": df.groupby("lot_dec")["tickvol"].median(),
    "abs_ret_bps_mediana": (df["ret"].abs() * 1e4).groupby(df["lot_dec"]).median(),
})
print(by_dec.round(2).to_string())
print("Geral: negócios/min =", df["tickvol"].median(),
      "| |retorno| bps =", round((df["ret"].abs() * 1e4).median(), 2))

neg = by_dec["negocios_mediana"]
f, ax = new_fig(800, 330)
ax.bar(np.arange(10), neg.values, 0.62, color=[GRAY] * 9 + [ORANGE])
for i in (int(neg.values.argmax()), 9):
    ax.text(i, neg.iloc[i] + 30, br(neg.iloc[i]), ha="center", va="bottom", color=INK,
            fontsize=24 * PX, fontweight="semibold")
ax.set_xticks(np.arange(10))
ax.set_xticklabels([f"D{i}" for i in range(1, 11)])
ax.set_ylim(0, 1850)
ax.set_yticks([0, 500, 1000, 1500])
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: br(v)))
f.subplots_adjust(left=0.11, right=0.98, top=0.97, bottom=0.17)
savefig(f, "02_negocios_por_decil_lote")

# %% [markdown]
# ## Conclusões
# Ver `docs/STATUS.md` (seção "Achados da análise de insights") e as figuras em
# `reports/figures/02_*.png`.
