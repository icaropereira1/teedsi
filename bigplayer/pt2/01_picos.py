# %% [markdown]
# # Parte 2 · 01 — Preço nos horários de pico de volume
#
# **Perguntas:** (1) quanto o preço médio varia no minuto antes de cada horário de pico (T−1) e no
# minuto do pico (T)? (2) o que o preço faz depois do pico, em T+5, T+15 e T+30 minutos?
# Os horários de pico são todo :00 e :30 de 9:00 a 17:30.
#
# **Entrada:** `data/interim/<ativo>_m1_limpo.parquet` (só exploração; só barras `usable`).
# Gerar antes com `notebooks/00_carga_e_split.py` e `notebooks/04_dataset_limpo.py`.
# **Saídas:** `pt2/reports/{picos,depois}_<ativo>.csv`, `pt2/reports/figures/{perfil,picos,continua,faixa}_<ativo>.png`.
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

from pt2.picos import (
    HORIZONS, PEAK_TIMES, add_forward_change, add_minute_change, after_peak_table, change_profile, peak_window,
    summarize_peaks, volume_profile,
)
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
    b = add_forward_change(add_minute_change(clean[clean["usable"]]))
    bars[asset] = b

    table = summarize_peaks(peak_window(b))
    vol = volume_profile(b)
    peak_times = {t.strftime("%H:%M"): t for t in PEAK_TIMES}
    table["volume_x_tarde"] = [vol[peak_times[h]] for h in table["horario"]]
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
# Em cima, quanto cada minuto costuma andar (mediana). Embaixo, a comparação dia a dia, que não sofre com os
# "degraus" da mediana: em que % dos pregões um minuto mexeu mais que o anterior (50% = igual).

# %%
for asset, name in ASSETS.items():
    t = tables[asset]
    x = list(range(len(t)))
    fig, (ax_m, ax_p) = plt.subplots(2, 1, figsize=(13, 10), sharex=True, gridspec_kw={"hspace": 0.45})
    kw = dict(width=0.38, edgecolor=INK, linewidth=1)
    ax_m.bar([i - 0.2 for i in x], t["antes_mediana_abs"], color=MUTED, label="minuto antes do pico (T−1)", **kw)
    ax_m.bar([i + 0.2 for i in x], t["pico_mediana_abs"], color=COLOR[asset], label="minuto do pico (T)", **kw)
    ax_m.set_ylabel("pontos")
    ax_m.legend(frameon=False, loc="upper right")
    titles(ax_m, f"{asset} · {name}: quanto o preço médio varia antes e no pico",
           f"mediana do |variação| do preço médio em relação ao minuto anterior, em pontos · "
           f"{t['pregoes'].min()} a {t['pregoes'].max()} pregões por horário")

    ax_p.axhline(50, color=INK, ls="--", lw=1)
    ax_p.errorbar([i - 0.15 for i in x], t["antes_maior_pct"], yerr=t["antes_margem_pct"], fmt="o", ms=7,
                  color=MUTED, mec=INK, mew=0.8, elinewidth=1.5, capsize=3, label="T−1 mexeu mais que T−2")
    ax_p.errorbar([i + 0.15 for i in x], t["pico_maior_pct"], yerr=t["pico_margem_pct"], fmt="o", ms=7,
                  color=COLOR[asset], mec=INK, mew=0.8, elinewidth=1.5, capsize=3, label="T mexeu mais que T−1")
    ax_p.set_ylabel("% dos pregões")
    ax_p.legend(frameon=False, loc="upper right", ncols=2)
    titles(ax_p, "Dia a dia: o minuto mexeu mais que o anterior?",
           "% dos pregões em que |variação| do minuto > |variação| do minuto anterior (empates fora), "
           "com margem de erro de 95% · 50% = igual")
    ax_p.set_xticks(x, t["horario"], rotation=45)
    ax_p.text(0, -0.25, "9:00 fica de fora: é a abertura e não existe minuto antes dela.",
              transform=ax_p.transAxes, fontsize=9.5, color=INK_2)
    fig.savefig(FIGURES / f"picos_{asset.lower()}.png", dpi=160, bbox_inches="tight")
    plt.show()

# %% [markdown]
# ## 4. Depois do pico: tabela de expectativa
# Para cada horário de pico e cada horizonte (5, 15 e 30 min): % de dias em que o preço médio sobe ou cai,
# mediana, faixa de 10% a 90%, e % de vezes que o fechamento continua na direção do minuto do pico.
# **Normal da hora:** a mesma conta em todos os minutos comuns (que não são :00 nem :30) da mesma hora.

# %%
after = {}
for asset in ASSETS:
    table = after_peak_table(bars[asset])
    after[asset] = table
    table.round(2).to_csv(REPORTS / f"depois_{asset.lower()}.csv", index=False)

    with_direction = table.dropna(subset=["continua_pct"])
    print(f"\n{asset}: {len(table)} combinações horário × horizonte ({len(with_direction)} com direção)")
    for h, g in with_direction.groupby("minutos_depois"):
        n = g["casos_direcao"]
        excess = ((g["continua_pct"] - g["normal_continua_pct"]) * n).sum() / n.sum()
        outside = int(((g["continua_pct"] - g["normal_continua_pct"]).abs() > g["margem_pct"]).sum())
        print(f"  {h:>2} min: continua no pico − normal da hora, somando os horários = {excess:+.2f} p.p. "
              f"(margem ±{100 * 1.96 * (0.25 / n.sum()) ** 0.5:.2f}) · horários fora da margem: {outside} de {len(g)}")

# %% [markdown]
# ## 5. Depois do pico: o preço continua na direção do minuto do pico?

# %%
for asset, name in ASSETS.items():
    fig, axes = plt.subplots(len(HORIZONS), 1, figsize=(13, 10), sharex=True, gridspec_kw={"hspace": 0.5})
    for ax, h in zip(axes, HORIZONS):
        t = after[asset][after[asset]["minutos_depois"] == h].reset_index(drop=True)
        x = range(len(t))
        t = t.dropna(subset=["continua_pct"]).reset_index(drop=True)
        x = range(len(t))
        ax.scatter(x, t["normal_continua_pct"], s=70, marker="_", linewidths=3, color=MUTED, zorder=2,
                   label="minutos comuns da mesma hora")
        ax.errorbar(x, t["continua_pct"], yerr=t["margem_pct"], fmt="o", ms=7, color=COLOR[asset],
                    mec=INK, mew=0.8, ecolor=COLOR[asset], elinewidth=1.5, capsize=3, zorder=3,
                    label="depois do pico (com margem de erro de 95%)")
        ax.set_xticks(list(x), t["horario"], rotation=45)
        ax.set_ylabel("% continua")
        ax.set_title(f"{h} minutos depois", loc="left", fontsize=12, fontweight="bold", color=INK)
    axes[0].legend(frameon=False, loc="upper right", ncols=2, fontsize=10)
    fig.suptitle(f"{asset} · {name}: depois do pico, o preço continua na direção do minuto do pico?",
                 x=0.125, ha="left", fontsize=15, fontweight="bold", color=INK)
    fig.text(0.125, 0.925, "% dos pregões em que o fechamento em T+h ficou do mesmo lado que o movimento do fechamento "
             "no minuto do pico · compare com o traço cinza, não com 50%", fontsize=10.5, color=INK_2)
    fig.savefig(FIGURES / f"continua_{asset.lower()}.png", dpi=160, bbox_inches="tight")
    plt.show()

# %% [markdown]
# ## 6. Depois do pico: faixa esperada em 15 minutos

# %%
for asset, name in ASSETS.items():
    t = after[asset][after[asset]["minutos_depois"] == 15].reset_index(drop=True)
    x = range(len(t))
    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.vlines([i - 0.12 for i in x], t["normal_p10"], t["normal_p90"], color=MUTED, lw=6,
              label="minutos comuns da mesma hora")
    ax.vlines([i + 0.12 for i in x], t["p10"], t["p90"], color=COLOR[asset], lw=6,
              label="depois do pico")
    ax.scatter([i + 0.12 for i in x], t["mediana"], s=36, color=SURFACE, edgecolor=INK, zorder=3, label="mediana")
    ax.axhline(0, color=INK, lw=1)
    ax.set_xticks(list(x), t["horario"], rotation=45)
    ax.set_ylabel("pontos")
    ax.legend(frameon=False, loc="upper right", ncols=3)
    ax.text(0, -0.2, "Faixa cinza: minutos comuns da mesma hora. Às 9h, ela inclui 9:01–9:29, logo depois da abertura.",
            transform=ax.transAxes, fontsize=9.5, color=INK_2)
    titles(ax, f"{asset} · {name}: onde o preço está 15 minutos depois do pico",
           "variação do preço médio de T a T+15, em pontos · cada barra vai de 10% a 90% dos dias "
           "(80% dos dias caem dentro dela)")
    fig.savefig(FIGURES / f"faixa_{asset.lower()}.png", dpi=160, bbox_inches="tight")
    plt.show()
