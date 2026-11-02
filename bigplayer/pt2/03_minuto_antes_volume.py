# %% [markdown]
# # Parte 2 · 03 — O minuto antes do pico: preço e contratos
#
# Nos 5 picos de volume que aparecem nos dois ativos (9:30, 10:00, 10:30, 11:00 e 12:00), compara o minuto
# antes do pico (T−1) com o minuto anterior a ele (T−2) e com o minuto do pico (T), em preço e em contratos,
# com mediana e média.
#
# - preço = variação do preço médio (máx + mín + fech) / 3 em relação ao minuto anterior, em pontos.
#   "Direção" usa o sinal; "tamanho" usa o valor sem sinal.
# - contratos = volume do minuto (coluna `vol`).
#
# **Entrada:** `data/interim/<ativo>_m1_limpo.parquet`. **Saídas:** `pt2/reports/antes_pico_<ativo>.csv` e
# `pt2/reports/figures/{volume_picos_anotado,antes_vs_pico_preco,antes_vs_pico_contratos,janela_picos_<ativo>}.png`.

# %%
import sys
from datetime import time
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from pt2.picos import add_minute_change, around_peaks
from src.ingestion.loader import INTERIM_DIR

REPORTS = BP / "pt2" / "reports"
FIGURES = REPORTS / "figures"

PEAKS = [time(9, 30), time(10, 0), time(10, 30), time(11, 0), time(12, 0)]
LABELS = [t.strftime("%H:%M") for t in PEAKS]
ASSETS = {"WDO": "mini dólar", "WIN": "mini índice"}
COLOR = {"WDO": "#7B57C8", "WIN": "#F0A030"}
MINUTE_COLOR = {-2: "#D6D1C9", -1: "#9C968D"}   # T−2 claro, T−1 escuro; T usa a cor do ativo
SURFACE, INK, INK_2, GRID = "#F1EEE9", "#1A1A1A", "#5C5852", "#DAD5CD"
MINUTE_NAME = {-2: "2 min antes (T−2)", -1: "1 min antes (T−1)", 0: "minuto do pico (T)"}

matplotlib.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": INK, "ytick.color": INK, "axes.labelcolor": INK_2, "font.size": 11,
})


def br(x: float, decimals: int) -> str:
    s = f"{x:.{decimals}f}".replace(".", ",")
    return s.replace("-", "−") if round(x, decimals) < 0 else s.lstrip("-")


def pct(x: float) -> str:
    r = round(x)
    return "0%" if r == 0 else f"{'+' if r > 0 else '−'}{abs(r)}%"


def thousands(x: float) -> str:
    return br(x / 1000, 1) + " mil"


def num_axis(v: float, _=None) -> str:
    return br(v, 2).rstrip("0").rstrip(",")


def mil_axis(v: float, _=None) -> str:
    return br(v / 1000, 0 if v % 1000 == 0 else 1) + " mil"


def minutes_since_nine(t: time) -> int:
    return (t.hour - 9) * 60 + t.minute


def minute_color(asset: str, k: int) -> str:
    return COLOR[asset] if k == 0 else MINUTE_COLOR[k]


# %% [markdown]
# ## 1. Números: mediana e média por pico e por minuto (de 5 minutos antes a 5 depois)

# %%
bars, stats = {}, {}
for asset in ASSETS:
    clean = pd.read_parquet(INTERIM_DIR / f"{asset.lower()}_m1_limpo.parquet")
    b = add_minute_change(clean[clean["usable"]])
    bars[asset] = b
    w = around_peaks(b, PEAKS)
    w["tamanho"] = w["variacao"].abs()
    s = w.groupby(["horario", "minuto_rel"]).agg(
        pregoes=("vol", "size"),
        preco_mediana=("variacao", "median"), preco_media=("variacao", "mean"),
        tamanho_mediana=("tamanho", "median"), tamanho_media=("tamanho", "mean"),
        contratos_mediana=("vol", "median"), contratos_media=("vol", "mean"),
    ).reset_index()
    stats[asset] = s
    s.round(2).to_csv(REPORTS / f"antes_pico_{asset.lower()}.csv", index=False)
    print(asset)
    print(s[s["minuto_rel"].between(-2, 0)].round(2).to_string(index=False))


def at(asset: str, horario: str, k: int) -> pd.Series:
    s = stats[asset]
    return s[(s["horario"] == horario) & (s["minuto_rel"] == k)].iloc[0]


# %% [markdown]
# ## 2. O gráfico de volume, com o minuto antes de cada pico anotado

# %%
fig, axes = plt.subplots(2, 1, figsize=(16, 13), gridspec_kw={"hspace": 0.55})
for ax, (asset, name) in zip(axes, ASSETS.items()):
    b = bars[asset]
    g = b.groupby("minuto")["vol"]
    med, mean = g.median(), g.mean()
    x = [minutes_since_nine(t) for t in med.index]
    ax.plot(x, mean.values, color=COLOR[asset], lw=1.2, ls="--", alpha=0.8, label="média")
    ax.plot(x, med.values, color=COLOR[asset], lw=2, label="mediana")
    decimals = 2 if asset == "WDO" else 1
    top = mean.max()
    for i, (t, label) in enumerate(zip(PEAKS, LABELS)):
        before, peak = at(asset, label, -1), at(asset, label, 0)
        xb, xp = minutes_since_nine(t) - 1, minutes_since_nine(t)
        ax.scatter([xb], [before["contratos_mediana"]], s=70, color=MINUTE_COLOR[-1], edgecolor=INK, zorder=4)
        ax.scatter([xp], [peak["contratos_mediana"]], s=70, color=COLOR[asset], edgecolor=INK, zorder=4)
        box_x = 5 + i * 113
        text = (f"{(xb // 60) + 9}:{xb % 60:02d} · 1 min antes das {label}\n"
                f"preço: mediana {br(before['preco_mediana'], decimals)} · média {br(before['preco_media'], decimals)} pt\n"
                f"tamanho: mediana {br(before['tamanho_mediana'], decimals)} · média {br(before['tamanho_media'], decimals)} pt\n"
                f"contratos: mediana {thousands(before['contratos_mediana'])} · média {thousands(before['contratos_media'])}")
        ax.annotate(text, xy=(xb, before["contratos_mediana"]), xytext=(box_x, top * (1.45 if i % 2 == 0 else 1.08)), fontsize=8.6,
                    va="bottom", ha="left", color=INK,
                    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRID),
                    arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.7, shrinkB=4))
    hours = range(9, 19)
    ax.set_xticks([(h - 9) * 60 for h in hours], [f"{h}h" for h in hours])
    ax.set_xlim(-5, max(x) + 5)
    ax.set_ylim(0, top * 1.85)
    ax.yaxis.set_major_formatter(mil_axis)
    ax.set_ylabel("contratos por minuto")
    ax.scatter([], [], s=70, color=MINUTE_COLOR[-1], edgecolor=INK, label="1 min antes do pico (mediana)")
    ax.scatter([], [], s=70, color=COLOR[asset], edgecolor=INK, label="minuto do pico (mediana)")
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncols=4, fontsize=10)
    ax.set_title(f"{asset} · {name}", loc="left", fontsize=15, fontweight="bold", pad=34)
fig.subplots_adjust(top=0.88)
fig.suptitle("Volume em cada minuto do pregão, com o minuto antes dos 5 picos", x=0.125, y=0.975, ha="left",
             fontsize=18, fontweight="bold")
fig.text(0.125, 0.948, "linha cheia = mediana dos pregões, tracejada = média · nas caixas: o minuto antes do pico · "
         "preço = variação do preço médio (máx + mín + fech) / 3 em relação ao minuto anterior, em pontos",
         fontsize=10.5, color=INK_2)
fig.savefig(FIGURES / "volume_picos_anotado.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 3. Preço: 2 minutos antes, 1 minuto antes e o minuto do pico

# %%
fig, axes = plt.subplots(2, 2, figsize=(16, 10), gridspec_kw={"hspace": 0.55, "wspace": 0.18})
offsets = {-2: -0.25, -1: 0, 0: 0.25}
for row, (asset, name) in enumerate(ASSETS.items()):
    for col, (kind, title, unit) in enumerate((("preco", "direção: variação com sinal", "pontos"),
                                                ("tamanho", "tamanho: variação sem sinal", "pontos"))):
        ax = axes[row, col]
        for k, dx in offsets.items():
            xs = [i + dx for i in range(len(PEAKS))]
            med = [at(asset, h, k)[f"{kind}_mediana"] for h in LABELS]
            mean = [at(asset, h, k)[f"{kind}_media"] for h in LABELS]
            ax.bar(xs, med, width=0.23, color=minute_color(asset, k), edgecolor=INK, lw=0.8, label=MINUTE_NAME[k])
            ax.scatter(xs, mean, marker="D", s=34, color=SURFACE, edgecolor=INK, zorder=3,
                       label="média" if k == 0 else None)
        ax.axhline(0, color=INK, lw=1)
        ax.set_xticks(range(len(PEAKS)), LABELS)
        ax.set_xlabel("horário do pico")
        ax.yaxis.set_major_formatter(num_axis)
        ax.set_ylabel(unit)
        ax.set_title(f"{asset} · {title}", loc="left", fontsize=13, fontweight="bold")
        if row == 0 and col == 1:
            ax.legend(frameon=False, loc="upper right", fontsize=9.5)
fig.suptitle("Preço no minuto antes do pico, comparado com o minuto anterior e com o pico", x=0.125, y=0.975,
             ha="left", fontsize=17, fontweight="bold")
fig.text(0.125, 0.935, "barra = mediana dos pregões · losango = média · variação do preço médio em relação ao minuto "
         "anterior, em pontos · no minuto antes, a direção fica abaixo de meio tick (WDO: 0,25 ponto; WIN: 2,5 pontos)",
         fontsize=10.5, color=INK_2)
fig.savefig(FIGURES / "antes_vs_pico_preco.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 4. Contratos: 2 minutos antes, 1 minuto antes e o minuto do pico

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 6.5), gridspec_kw={"wspace": 0.18})
for ax, (asset, name) in zip(axes, ASSETS.items()):
    for k, dx in offsets.items():
        xs = [i + dx for i in range(len(PEAKS))]
        med = [at(asset, h, k)["contratos_mediana"] for h in LABELS]
        mean = [at(asset, h, k)["contratos_media"] for h in LABELS]
        ax.bar(xs, med, width=0.23, color=minute_color(asset, k), edgecolor=INK, lw=0.8, label=MINUTE_NAME[k])
        ax.scatter(xs, mean, marker="D", s=34, color=SURFACE, edgecolor=INK, zorder=3,
                   label="média" if k == 0 else None)
        if k in (-1, 0):
            for x_, h in zip(xs, LABELS):
                prev = at(asset, h, k - 1)["contratos_mediana"]
                cur = at(asset, h, k)["contratos_mediana"]
                ax.text(x_, max(cur, at(asset, h, k)["contratos_media"]) * 1.03, pct(100 * (cur / prev - 1)),
                        ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(PEAKS)), LABELS)
    ax.set_xlabel("horário do pico")
    ax.yaxis.set_major_formatter(mil_axis)
    ax.set_ylabel("contratos no minuto")
    ax.set_title(f"{asset} · {name}", loc="left", fontsize=13, fontweight="bold")
    ax.legend(frameon=False, loc="upper right", fontsize=9.5)
fig.suptitle("Contratos no minuto antes do pico, comparado com o minuto anterior e com o pico", x=0.125, y=1.02,
             ha="left", fontsize=17, fontweight="bold")
fig.text(0.125, 0.955, "barra = mediana dos pregões · losango = média · % = variação da mediana em relação ao minuto "
         "anterior", fontsize=10.5, color=INK_2)
fig.savefig(FIGURES / "antes_vs_pico_contratos.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 5. Minuto a minuto, de 5 minutos antes a 5 minutos depois de cada pico

# %%
for asset, name in ASSETS.items():
    s = stats[asset]
    fig, axes = plt.subplots(2, len(PEAKS), figsize=(17, 7.5), sharey="row", gridspec_kw={"hspace": 0.45})
    for col, h in enumerate(LABELS):
        d = s[s["horario"] == h].sort_values("minuto_rel")
        colors = [COLOR[asset] if k == 0 else (MINUTE_COLOR[-1] if k == -1 else MINUTE_COLOR[-2])
                  for k in d["minuto_rel"]]
        for ax, kind, unit in ((axes[0, col], "contratos", "contratos"), (axes[1, col], "tamanho", "pontos")):
            ax.bar(d["minuto_rel"], d[f"{kind}_mediana"], color=colors, edgecolor=INK, lw=0.6)
            ax.scatter(d["minuto_rel"], d[f"{kind}_media"], marker="D", s=18, color=SURFACE, edgecolor=INK, zorder=3)
            ax.set_xticks([-5, 0, 5], ["−5", "pico", "+5"])
        axes[0, col].set_title(f"pico das {h}", fontsize=12, fontweight="bold")
        axes[1, col].set_xlabel("minutos em relação ao pico")
    axes[0, 0].yaxis.set_major_formatter(mil_axis)
    axes[0, 0].set_ylabel("contratos no minuto")
    axes[1, 0].yaxis.set_major_formatter(num_axis)
    axes[1, 0].set_ylabel("tamanho da variação\ndo preço (pontos)")
    fig.suptitle(f"{asset} · {name}: contratos e preço minuto a minuto em volta dos picos", x=0.125, y=1.0,
                 ha="left", fontsize=16, fontweight="bold")
    fig.text(0.125, 0.94, "barra = mediana dos pregões · losango = média · 1 minuto antes em cinza escuro, minuto do pico "
             "colorido · tamanho = variação do preço médio sem sinal", fontsize=10.5, color=INK_2)
    fig.savefig(FIGURES / f"janela_picos_{asset.lower()}.png", dpi=150, bbox_inches="tight")
    plt.show()
