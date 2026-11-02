# %% [markdown]
# # Parte 2 · 01 — Preço nos horários de pico de volume
#
# **Pergunta:** quanto o preço médio varia no minuto antes de cada horário de pico (T−1) e no minuto
# do pico (T)? Os horários de pico são todo :00 e :30 de 9:00 a 17:30.
#
# **Entrada:** `data/interim/<ativo>_m1_limpo.parquet` (só exploração; só barras `usable`).
# Gerar antes com `notebooks/00_carga_e_split.py` e `notebooks/04_dataset_limpo.py`.
# **Saídas:** `pt2/reports/picos_<ativo>.csv`, `pt2/reports/figures/{perfil,picos}_<ativo>.png`.
#
# Como cada número é calculado: `pt2/README.md`.

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from pt2.picos import PEAK_TIMES, add_minute_change, change_profile, peak_window, summarize_peaks, volume_profile
from src.ingestion.loader import INTERIM_DIR

REPORTS = BP / "pt2" / "reports"
FIGURES = REPORTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

ASSETS = {"WDO": "mini dólar", "WIN": "mini índice"}
COLOR = {"WDO": "#7B57C8", "WIN": "#F0A030"}   # mesmas cores dos slides
MUTED = "#B9B3AA"
SURFACE = "#F1EEE9"
INK, INK_2 = "#1A1A1A", "#5C5852"

matplotlib.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True, "grid.color": "#DAD5CD", "grid.linewidth": 0.8,
    "xtick.color": INK, "ytick.color": INK, "axes.labelcolor": INK_2, "font.size": 11,
})


def minutes_since_nine(t):
    return (t.hour - 9) * 60 + t.minute


def titles(ax, title, subtitle):
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color=INK, pad=26)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10.5, color=INK_2)


# %% [markdown]
# ## 1. Dados e tabela por horário de pico

# %%
bars, tables = {}, {}
for asset in ASSETS:
    clean = pd.read_parquet(INTERIM_DIR / f"{asset.lower()}_m1_limpo.parquet")
    b = add_minute_change(clean[clean["usable"]])
    bars[asset] = b

    table = summarize_peaks(peak_window(b))
    vol = volume_profile(b)
    by_hour = b.groupby(b["ts"].dt.hour)["variacao"].apply(lambda s: s.abs().median())
    peak_times = {t.strftime("%H:%M"): t for t in PEAK_TIMES}
    table["volume_x_tarde"] = [vol[peak_times[h]] for h in table["horario"]]
    table["hora_mediana_abs"] = [by_hour[peak_times[h].hour] for h in table["horario"]]
    tables[asset] = table
    table.round(2).to_csv(REPORTS / f"picos_{asset.lower()}.csv", index=False)

    print(f"\n{asset}: {b['session_date'].nunique()} pregões, "
          f"{b['session_date'].min():%Y-%m-%d} → {b['session_date'].max():%Y-%m-%d}")
    print(table.round(2).to_string(index=False))

# %% [markdown]
# ## 2. Volume e variação do preço médio ao longo do dia
# Em cima, o mesmo gráfico de volume dos slides; embaixo, quanto o preço médio se move em cada minuto.

# %%
for asset, name in ASSETS.items():
    b = bars[asset]
    vol, chg = volume_profile(b), change_profile(b)
    fig, (ax_v, ax_p) = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True, gridspec_kw={"hspace": 0.45})

    ax_v.plot([minutes_since_nine(t) for t in vol.index], vol.values, color=COLOR[asset], lw=2)
    ax_v.axhline(1, color=INK, ls="--", lw=1)
    titles(ax_v, f"{asset} · {name}: volume por minuto",
           "volume mediano de cada minuto, dividido pelo volume típico da tarde (14h–17h) · 1 = normal da tarde")
    ax_v.set_ylabel("× volume da tarde")

    ax_p.plot([minutes_since_nine(t) for t in chg.index], chg.values, color=COLOR[asset], lw=2)
    titles(ax_p, f"{asset} · {name}: quanto o preço médio varia por minuto",
           "mediana do |variação| do preço médio (máx + mín + fech) / 3 em relação ao minuto anterior, em pontos")
    ax_p.set_ylabel("pontos")
    ax_p.set_ylim(bottom=0)

    hours = range(9, 19)
    ax_p.set_xticks([(h - 9) * 60 for h in hours], [f"{h}h" for h in hours])
    for ax in (ax_v, ax_p):
        for t in PEAK_TIMES:
            ax.axvline(minutes_since_nine(t), color="#DAD5CD", lw=0.8, zorder=0)
        ax.set_xlim(-5, minutes_since_nine(vol.index.max()) + 5)
    fig.savefig(FIGURES / f"perfil_{asset.lower()}.png", dpi=160, bbox_inches="tight")
    plt.show()

# %% [markdown]
# ## 3. Minuto antes do pico × minuto do pico

# %%
for asset, name in ASSETS.items():
    t = tables[asset]
    x = range(len(t))
    fig, ax = plt.subplots(figsize=(13, 5.5))
    kw = dict(width=0.38, edgecolor=INK, linewidth=1)
    ax.bar([i - 0.2 for i in x], t["antes_mediana_abs"], color=MUTED, label="minuto antes do pico (T−1)", **kw)
    ax.bar([i + 0.2 for i in x], t["pico_mediana_abs"], color=COLOR[asset], label="minuto do pico (T)", **kw)
    ax.set_xticks(list(x), t["horario"], rotation=45)
    ax.set_ylabel("pontos")
    ax.legend(frameon=False, loc="upper right")
    ax.text(0, -0.2, "9:00 fica de fora: é a abertura e não existe minuto antes dela.",
            transform=ax.transAxes, fontsize=9.5, color=INK_2)
    titles(ax, f"{asset} · {name}: quanto o preço médio varia antes e no pico",
           f"mediana do |variação| do preço médio em relação ao minuto anterior, em pontos · "
           f"{t['pregoes'].min()} a {t['pregoes'].max()} pregões por horário")
    fig.savefig(FIGURES / f"picos_{asset.lower()}.png", dpi=160, bbox_inches="tight")
    plt.show()
