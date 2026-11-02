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
# `pt2/reports/figures/{volume_picos_anotado,antes_vs_pico_preco,antes_vs_pico_contratos,janela_picos_<ativo>,zoom_picos_<ativo>}.png`
# e `pt2/reports/{zoom_picos,x_y_picos}_<ativo>.csv`, `x_y_picos.png` e `x_y_comparacao.png`.

# %%
import sys
from datetime import date, datetime, time, timedelta
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

# %% [markdown]
# ## 6. Zoom nos picos: de 10 minutos antes a 10 minutos depois, com o horário real
# Só os 5 picos; a tarde e os horários sem pico ficam de fora.

# %%
ZOOM = range(-10, 11)
for asset, name in ASSETS.items():
    w = around_peaks(bars[asset], PEAKS, ZOOM)
    w["tamanho"] = w["variacao"].abs()
    z = w.groupby(["horario", "minuto_rel"]).agg(
        contratos_mediana=("vol", "median"), contratos_media=("vol", "mean"),
        tamanho_mediana=("tamanho", "median"), tamanho_media=("tamanho", "mean"),
        preco_mediana=("variacao", "median"), preco_media=("variacao", "mean"),
    ).reset_index()
    z.round(2).to_csv(REPORTS / f"zoom_picos_{asset.lower()}.csv", index=False)

    rows = (("contratos", "contratos no minuto", mil_axis),
            ("tamanho", "tamanho da variação\ndo preço (pontos)", num_axis),
            ("preco", "direção da variação\ndo preço (pontos)", num_axis))
    fig, axes = plt.subplots(len(rows), len(PEAKS), figsize=(20, 11), sharey="row",
                             gridspec_kw={"hspace": 0.5, "wspace": 0.08})
    for col, (t, h) in enumerate(zip(PEAKS, LABELS)):
        d = z[z["horario"] == h].sort_values("minuto_rel")
        colors = [COLOR[asset] if k == 0 else (MINUTE_COLOR[-1] if k == -1 else MINUTE_COLOR[-2])
                  for k in d["minuto_rel"]]
        ticks = [-10, -5, 0, 5, 10]
        tick_labels = []
        for k in ticks:
            m = minutes_since_nine(t) + k
            tick_labels.append(f"{9 + m // 60}:{m % 60:02d}")
        for row, (kind, ylabel, fmt) in enumerate(rows):
            ax = axes[row, col]
            ax.bar(d["minuto_rel"], d[f"{kind}_mediana"], color=colors, edgecolor=INK, lw=0.5, width=0.8)
            ax.scatter(d["minuto_rel"], d[f"{kind}_media"], marker="D", s=14, color=SURFACE, edgecolor=INK, zorder=3)
            if kind == "preco":
                ax.axhline(0, color=INK, lw=1)
            ax.set_xticks(ticks, tick_labels, fontsize=9.5)
            if col == 0:
                ax.yaxis.set_major_formatter(fmt)
                ax.set_ylabel(ylabel)
        axes[0, col].set_title(f"pico das {h}", fontsize=13, fontweight="bold")
    fig.suptitle(f"{asset} · {name}: zoom nos 5 picos, minuto a minuto (10 antes, 10 depois)", x=0.125, y=0.99,
                 ha="left", fontsize=17, fontweight="bold")
    fig.text(0.125, 0.945, "barra = mediana dos pregões · losango = média · 1 minuto antes em cinza escuro, minuto do "
             "pico colorido · preço = variação do preço médio (máx + mín + fech) / 3 em relação ao minuto anterior",
             fontsize=10.5, color=INK_2)
    fig.savefig(FIGURES / f"zoom_picos_{asset.lower()}.png", dpi=150, bbox_inches="tight")
    plt.show()

# %% [markdown]
# ## 7. x e y em cada pico: mediana do preço no pico (x) e no minuto antes (y)
# - nível: mediana do preço médio naquele minuto, entre todos os pregões;
# - desde a abertura: o mesmo, mas medido em relação ao 1º minuto do mesmo pregão;
# - diferença dia a dia: mediana de (preço no pico − preço no minuto antes) dentro de cada pregão.
# Atenção: "x − y" com níveis NÃO é a mediana da diferença dia a dia, e pode até ter o sinal trocado.

# %%
def br_level(x: float) -> str:
    return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


xy = {}
for asset in ASSETS:
    b = bars[asset].copy()
    b["desde_abertura"] = b["preco_medio"] - b.groupby("session_date")["preco_medio"].transform("first")
    level = b.pivot(index="session_date", columns="minuto", values="preco_medio")
    rel = b.pivot(index="session_date", columns="minuto", values="desde_abertura")
    rows = []
    for t, h in zip(PEAKS, LABELS):
        before = (datetime.combine(date(2000, 1, 1), t) - timedelta(minutes=1)).time()
        d = pd.DataFrame({"x": level[t], "y": level[before], "xr": rel[t], "yr": rel[before]}).dropna()
        rows.append({"horario": h, "pregoes": len(d),
                     "x_nivel": d["x"].median(), "y_nivel": d["y"].median(),
                     "x_menos_y_nivel": d["x"].median() - d["y"].median(),
                     "x_desde_abertura": d["xr"].median(), "y_desde_abertura": d["yr"].median(),
                     "diferenca_dia_a_dia": (d["x"] - d["y"]).median()})
    xy[asset] = pd.DataFrame(rows)
    xy[asset].round(2).to_csv(REPORTS / f"x_y_picos_{asset.lower()}.csv", index=False)
    print(asset)
    print(xy[asset].round(2).to_string(index=False))

fig, axes = plt.subplots(2, 1, figsize=(16, 13), gridspec_kw={"hspace": 0.5})
for ax, (asset, name) in zip(axes, ASSETS.items()):
    med = bars[asset].groupby("minuto")["vol"].median()
    x = [minutes_since_nine(t) for t in med.index]
    ax.plot(x, med.values, color=COLOR[asset], lw=2, label="volume (mediana dos pregões)")
    top = med.max()
    decimals = 2 if asset == "WDO" else 1
    for i, (t, row) in enumerate(zip(PEAKS, xy[asset].itertuples())):
        xp = minutes_since_nine(t)
        yp = med[t]
        ax.annotate("", xy=(xp + 6, yp + top * 0.18), xytext=(xp, yp),
                    arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=1.8))
        ax.annotate("", xy=(xp - 1, yp + top * 0.22), xytext=(xp - 1, yp),
                    arrowprops=dict(arrowstyle="->", color="#66BB6A", lw=1.8))
        ax.text(xp + 7, yp + top * 0.19, "x", color="#2E7D32", fontsize=13, fontweight="bold")
        ax.text(xp - 4, yp + top * 0.24, "y", color="#66BB6A", fontsize=13, fontweight="bold")
        text = (f"pico das {row.horario}\n"
                f"nível: x = {br_level(row.x_nivel)} · y = {br_level(row.y_nivel)}\n"
                f"desde a abertura: x = {br(row.x_desde_abertura, decimals)} · y = {br(row.y_desde_abertura, decimals)}\n"
                f"diferença dia a dia (x − y): {br(row.diferenca_dia_a_dia, decimals)} pt")
        ax.text(5 + i * 113, top * (1.75 if i % 2 == 0 else 1.42), text, fontsize=8.6, va="bottom",
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRID))
    hours = range(9, 19)
    ax.set_xticks([(h - 9) * 60 for h in hours], [f"{h}h" for h in hours])
    ax.set_xlim(-5, max(x) + 5)
    ax.set_ylim(0, top * 2.15)
    ax.yaxis.set_major_formatter(mil_axis)
    ax.set_ylabel("contratos por minuto")
    ax.set_title(f"{asset} · {name}", loc="left", fontsize=15, fontweight="bold")
fig.subplots_adjust(top=0.9)
fig.suptitle("x = mediana do preço no pico · y = mediana do preço no minuto antes (t−1)", x=0.125, y=1.0,
             ha="left", fontsize=18, fontweight="bold")
fig.text(0.125, 0.95, "preço = preço médio (máx + mín + fech) / 3, em pontos · nível = preço em si; desde a abertura = "
         "preço − preço do 1º minuto do dia · diferença dia a dia = mediana de (x − y) dentro de cada pregão",
         fontsize=10.5, color=INK_2)
fig.savefig(FIGURES / "x_y_picos.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 8. Por que não subtrair as medianas dos níveis

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 6), gridspec_kw={"wspace": 0.2})
for ax, (asset, name) in zip(axes, ASSETS.items()):
    t = xy[asset]
    xs = range(len(t))
    ax.bar([i - 0.2 for i in xs], t["x_menos_y_nivel"], width=0.38, color=MINUTE_COLOR[-2], edgecolor=INK,
           label="mediana(x) − mediana(y), com níveis")
    ax.bar([i + 0.2 for i in xs], t["diferenca_dia_a_dia"], width=0.38, color=COLOR[asset], edgecolor=INK,
           label="mediana de (x − y) dentro de cada dia")
    ax.axhline(0, color=INK, lw=1)
    ax.set_xticks(list(xs), t["horario"])
    ax.set_xlabel("horário do pico")
    ax.yaxis.set_major_formatter(num_axis)
    ax.set_ylabel("pontos")
    ax.legend(frameon=False, loc="lower left", fontsize=9.5)
    ax.set_title(f"{asset} · {name}", loc="left", fontsize=13, fontweight="bold")
fig.suptitle("Subtrair medianas de níveis engana: o sinal pode até trocar", x=0.125, y=1.03, ha="left",
             fontsize=17, fontweight="bold")
fig.text(0.125, 0.965, "a mediana do nível depende de quais anos e dias entram na conta; a diferença certa é a de cada "
         "dia (pico − minuto antes), e só depois a mediana", fontsize=10.5, color=INK_2)
fig.savefig(FIGURES / "x_y_comparacao.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 9. Só a manhã: os 5 picos até 12h, com mediana e média logo acima de cada pico
# Acima de cada pico: mediana do preço médio (o preço em si, em pontos) no minuto do pico e no minuto antes (t−1).

# %%
MORNING_END = time(12, 10)
fig, axes = plt.subplots(2, 1, figsize=(18, 12), gridspec_kw={"hspace": 0.35})
for ax, (asset, name) in zip(axes, ASSETS.items()):
    b = bars[asset]
    level = b.pivot(index="session_date", columns="minuto", values="preco_medio")
    morning = b[b["minuto"] <= MORNING_END]
    med = morning.groupby("minuto")["vol"].median()
    xs = [minutes_since_nine(t) for t in med.index]
    ax.plot(xs, med.values, color=COLOR[asset], lw=2)
    top = med.max()
    decimals = 2 if asset == "WDO" else 1
    before_color = "#4A4640"
    for t in PEAKS:
        before = (datetime.combine(date(2000, 1, 1), t) - timedelta(minutes=1)).time()
        d = pd.DataFrame({"x": level[t], "y": level[before]}).dropna()
        xp = minutes_since_nine(t)
        ax.scatter([xp - 1], [med[before]], s=55, color=before_color, edgecolor=INK, zorder=4)
        ax.scatter([xp], [med[t]], s=70, color=COLOR[asset], edgecolor=INK, zorder=4)
        ax.text(xp, med[t] + top * 0.22, br_level(d["x"].median()), ha="center", va="bottom",
                fontsize=12, fontweight="bold", color=COLOR[asset])
        ax.text(xp, med[t] + top * 0.08, br_level(d["y"].median()), ha="center", va="bottom",
                fontsize=12, color=before_color)
    ax.scatter([], [], s=70, color=COLOR[asset], edgecolor=INK, label="mediana do preço no minuto do pico")
    ax.scatter([], [], s=55, color=before_color, edgecolor=INK, label="mediana do preço no minuto antes (t−1)")
    ax.legend(frameon=False, loc="upper right", fontsize=10.5)
    ticks = list(range(0, 181, 30))
    ax.set_xticks(ticks, [f"{9 + m // 60}:{m % 60:02d}" for m in ticks])
    ax.set_xlim(-12, minutes_since_nine(MORNING_END) + 8)
    ax.set_ylim(0, top * 1.6)
    ax.yaxis.set_major_formatter(mil_axis)
    ax.set_ylabel("contratos por minuto (mediana)")
    ax.set_title(f"{asset} · {name}", loc="left", fontsize=15, fontweight="bold")
fig.suptitle("Os picos de volume da manhã: preço no pico e no minuto antes (t−1)", x=0.125, y=0.995, ha="left",
             fontsize=18, fontweight="bold")
fig.text(0.125, 0.94, "linha = volume mediano por minuto · números = mediana do preço médio (máx + mín + fech) / 3 "
         "entre os pregões, em pontos",
         fontsize=10.5, color=INK_2)
fig.savefig(FIGURES / "picos_manha.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 10. Dia inteiro: mediana do FECHAMENTO no pico e no minuto antes (t−1), e a diferença
# Todos os :00 e :30 de 9:30 a 17:30. Preço = fechamento do minuto (não o preço médio).
# - pico e t−1: mediana do fechamento entre os pregões que têm os dois minutos;
# - Δ: mediana do pico − mediana de t−1 (a subtração dos dois números mostrados). Não é a variação típica de um
#   dia: a mediana da diferença dentro de cada pregão fica em `x_y_picos_<ativo>.csv` e no gráfico x_y_comparacao.

# %%
ALL_PEAKS = [time(h, m) for h in range(9, 18) for m in (0, 30)][1:]
Y_AXIS = {"WDO": (19_500, range(0, 18_001, 3_000)), "WIN": (96_000, range(0, 80_001, 10_000))}


def draw_day_peaks(price_name: str, price_of, filename: str) -> None:
    """price_of(barras) devolve o preço de cada minuto; price_name entra no título e na legenda."""
    fig, axes = plt.subplots(2, 1, figsize=(22, 13), gridspec_kw={"hspace": 0.3})
    before_color = "#4A4640"
    for ax, (asset, name) in zip(axes, ASSETS.items()):
        b = bars[asset]
        close = b.assign(preco=price_of(b)).pivot(index="session_date", columns="minuto", values="preco")
        g = b.groupby("minuto")["vol"]
        med, mean = g.median(), g.mean()
        xs = [minutes_since_nine(t) for t in med.index]
        ax.plot(xs, mean.values, color=COLOR[asset], lw=1.1, ls="--", alpha=0.8, label="volume: média")
        ax.plot(xs, med.values, color=COLOR[asset], lw=1.8, label="volume: mediana")
        for t in ALL_PEAKS:
            before = (datetime.combine(date(2000, 1, 1), t) - timedelta(minutes=1)).time()
            d = pd.DataFrame({"x": close[t], "y": close[before]}).dropna()
            x_med, y_med = float(f"{d['x'].median():.1f}"), float(f"{d['y'].median():.1f}")
            diff = x_med - y_med                     # bate com os números mostrados
            xp = minutes_since_nine(t)
            ax.scatter([xp - 1], [med[before]], s=40, color=before_color, edgecolor=INK, zorder=4)
            ax.scatter([xp], [med[t]], s=55, color=COLOR[asset], edgecolor=INK, zorder=4)
            anchor = max(mean[t], mean[before], med[t])          # topo do pico, contando a linha da média
            for offset, text, color, weight in ((4, f"Δ {br(diff, 1)}", INK, "bold"),
                                                (17, br_level(y_med), before_color, "normal"),
                                                (30, br_level(x_med), COLOR[asset], "bold")):
                ax.annotate(text, xy=(xp, anchor), xytext=(0, offset), textcoords="offset points",
                            ha="center", va="bottom", fontsize=9.5, fontweight=weight, color=color)
        ax.scatter([], [], s=55, color=COLOR[asset], edgecolor=INK, label=f"mediana do {price_name} no minuto do pico (pontos)")
        ax.scatter([], [], s=40, color=before_color, edgecolor=INK, label=f"mediana do {price_name} no minuto antes, t−1 (pontos)")
        ax.plot([], [], " ", label="Δ = mediana do pico − mediana de t−1 (pontos)")
        ax.legend(frameon=False, loc="upper right", fontsize=10.5)
        hours = range(9, 19)
        ax.set_xticks([(h - 9) * 60 for h in hours], [f"{h}h" for h in hours])
        ax.set_xlim(-8, max(xs) + 8)
        ylim, yticks = Y_AXIS[asset]
        ax.set_ylim(0, ylim)
        ax.set_yticks(list(yticks))
        ax.yaxis.set_major_formatter(mil_axis)
        ax.set_ylabel("contratos por minuto")
        ax.set_title(f"{asset} · {name}", loc="left", fontsize=15, fontweight="bold")
    fig.suptitle(f"Volume negociado em cada minuto do pregão e o {price_name} nos picos", x=0.125, y=0.995,
                 ha="left", fontsize=19, fontweight="bold")
    fig.text(0.125, 0.947, "volume em contratos por minuto: mediana (linha cheia) e média (tracejada) dos pregões · "
             "todos os números acima dos picos estão em pontos · horários de pico = todo :00 e :30 de 9:30 a 17:30",
             fontsize=11, color=INK_2)
    fig.savefig(FIGURES / filename, dpi=150, bbox_inches="tight")
    plt.show()

draw_day_peaks("fechamento", lambda b: b["close"], "picos_dia_fechamento.png")

# %% [markdown]
# ## 11. O mesmo gráfico com o preço médio (mínima + máxima) / 2

# %%
draw_day_peaks("preço médio (mín + máx) / 2", lambda b: (b["low"] + b["high"]) / 2, "picos_dia_preco_medio.png")
