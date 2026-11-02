# %% [markdown]
# # Parte 2 · 02 — Slide: o minuto antes dos picos
#
# Um slide 16:9 (2000 × 1125, o tamanho dos slides do grupo) com o minuto antes (T−1) dos 5 picos de volume
# que aparecem nos dois ativos: 9:30, 10:00, 10:30, 11:00 e 12:00.
#
# **Entrada:** `pt2/reports/picos_<ativo>.csv` (gerados por `pt2/01_picos.py`).
# **Saída:** `pt2/reports/figures/slide_minuto_antes.png`.

# %%
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
REPORTS = BP / "pt2" / "reports"

PEAKS = ["09:30", "10:00", "10:30", "11:00", "12:00"]
ASSETS = {"WDO": "mini dólar", "WIN": "mini índice"}
COLOR = {"WDO": "#7B57C8", "WIN": "#F0A030"}
SURFACE, INK, INK_2, GRID = "#F1EEE9", "#1A1A1A", "#5C5852", "#DAD5CD"

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})


def br(x: float, decimals: int) -> str:
    """Número no formato brasileiro, com sinal de menos tipográfico."""
    s = f"{x:.{decimals}f}".replace(".", ",")
    return s.replace("-", "−") if x < 0 else s


# %%
tables = {a: pd.read_csv(REPORTS / f"picos_{a.lower()}.csv").set_index("horario").loc[PEAKS] for a in ASSETS}

fig = plt.figure(figsize=(2000 / 150, 1125 / 150), dpi=150, facecolor=SURFACE)
fig.text(0.04, 0.905, "1 minuto antes do pico", fontsize=34, fontweight="bold")
fig.text(0.04, 0.855, "Variação do preço médio (máx + mín + fech) / 3 no minuto anterior aos 5 picos de volume, em pontos "
         "· 2020 a 2025 · ~1.000 pregões por horário", fontsize=12, color=INK_2)

for col, (asset, name) in enumerate(ASSETS.items()):
    t = tables[asset]
    left = 0.06 + col * 0.48
    decimals = 1 if asset == "WDO" else 0

    ax = fig.add_axes([left, 0.48, 0.40, 0.29], facecolor=SURFACE)
    x = range(len(t))
    ax.vlines(x, t["antes_min"], t["antes_max"], color=COLOR[asset], lw=2, alpha=0.55)
    ax.vlines(x, -t["antes_mediana_abs"], t["antes_mediana_abs"], color=COLOR[asset], lw=14)
    ax.scatter(x, t["antes_mediana"], s=45, color=SURFACE, edgecolor=INK, zorder=3)
    for i, (lo, hi) in enumerate(zip(t["antes_min"], t["antes_max"])):
        ax.text(i + 0.1, hi, f"máx {br(hi, decimals)}", fontsize=9, color=INK_2, va="center")
        ax.text(i + 0.1, lo, f"mín {br(lo, decimals)}", fontsize=9, color=INK_2, va="center")
    ax.axhline(0, color=INK, lw=1)
    ax.set_xticks(list(x), [f"antes das\n{h}" for h in t.index], fontsize=10)
    ax.set_xlim(-0.5, len(t) - 0.2)
    ax.set_ylabel("pontos", color=INK_2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.set_title(f"{asset} · {name}", loc="left", fontsize=16, fontweight="bold", pad=10)

    # tabela
    headers = ["pico", "mínima", "mediana", "máxima", "típico", "sobe", "cai"]
    xs = [left + f * 0.40 for f in (0.0, 0.17, 0.33, 0.49, 0.65, 0.81, 0.93)]
    top = 0.365
    for xi, h in zip(xs, headers):
        fig.text(xi, top, h, fontsize=10.5, fontweight="bold", color=INK_2)
    for r, (h, row) in enumerate(t.iterrows()):
        y = top - 0.037 * (r + 1)
        cells = [h, br(row["antes_min"], decimals), br(row["antes_mediana"], decimals), br(row["antes_max"], decimals),
                 "±" + br(row["antes_mediana_abs"], decimals),
                 f"{row['antes_sobe_pct']:.0f}%", f"{row['antes_cai_pct']:.0f}%"]
        for xi, c in zip(xs, cells):
            fig.text(xi, y, c, fontsize=10.5)

fig.text(0.04, 0.13, "Linha fina = da mínima à máxima · barra grossa = tamanho típico (mediana do |variação|) · "
         "ponto = mediana · sobe/cai = % dos dias (o resto ficou parado)", fontsize=10, color=INK_2)
fig.text(0.04, 0.035, "No minuto antes do pico, o preço não escolhe lado: sobe e cai em proporções parecidas e a "
         "mediana é ~0.\nO tamanho típico é pequeno; as pontas (mínima e máxima) são poucos dias atípicos.",
         fontsize=13, fontweight="bold", linespacing=1.4)

fig.savefig(REPORTS / "figures" / "slide_minuto_antes.png", dpi=150, facecolor=SURFACE)
plt.show()
