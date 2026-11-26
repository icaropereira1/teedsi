"""Gera os gráficos da apresentação de 12/11 no padrão visual exato dos slides anteriores (Big Player).

Padrão visual (extraído dos slides do PDF e de pt2/):
- Fundo creme/off-white: #F1EEE9
- Tipografia escura: #1A1A1A (títulos/eixos) e #5C5852 (subtítulos/notas)
- Grade horizontal suave: #DAD5CD, sem bordas topo/direita/esquerda
- Paleta: Roxo (#7B57C8), Laranja (#F0A030), Cinza (#8E887F), Caixa de destaque verde-água (#BCECE6) com borda preta arredondada
"""
from __future__ import annotations

import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
BP = next(p for p in [HERE.parent, *HERE.parents] if (p / "configs" / "split.toml").exists())
DOC_DIR = BP / "docs" / "apresentacao-12-11"
MED_DIR = DOC_DIR / "dados" / "medianas_pico30"
FLUX_CSV = DOC_DIR / "dados" / "fluxo_investidores" / "fluxo_investidores.csv"
OUT_DIRS = [
    DOC_DIR / "graficos",
    BP / "reports" / "figures" / "apresentacao_12_11",
]
for d in OUT_DIRS:
    d.mkdir(parents=True, exist_ok=True)

# Paleta idêntica ao PDF da apresentação anterior
SURFACE = "#F1EEE9"
INK = "#1A1A1A"
INK_2 = "#5C5852"
GRID = "#DAD5CD"
PURPLE = "#7B57C8"      # Cor principal dos slides (WDO / Dias de alta / Estrangeiro)
ORANGE = "#F0A030"      # Cor secundária dos slides (WIN / Dias de baixa / Pessoa física)
MINT_BOX = "#BCECE6"    # Caixa de destaque dos slides 5, 6 e 7 do PDF
PINK = "#E06388"        # Rosa/coral dos slides 1, 3, 7 e 8
MUTED = "#8E887F"

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Segoe UI", "Arial"],
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.linewidth": 1.1,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.85,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.labelcolor": INK_2,
    "text.color": INK,
    "font.size": 11,
})


def br(x: float, decimals: int = 1, plus: bool = False) -> str:
    """Formata número no padrão brasileiro com sinal tipográfico (−)."""
    if abs(x) < 1e-9:
        x = 0.0
    s = f"{abs(x):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if round(x, decimals) < 0:
        return f"−{s}"
    if plus and round(x, decimals) > 0:
        return f"+{s}"
    return s


def save_all(fig: plt.Figure, filename: str) -> None:
    for out in OUT_DIRS:
        fig.savefig(out / filename, dpi=180, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def load_med(serie: str, tipo: str) -> pd.DataFrame:
    return pd.read_csv(MED_DIR / f"pico30_{serie}_{tipo}.csv")


# ==============================================================================
# GRÁFICO 1: Por que separar Alta e Baixa? Trajetória T-1 a T+15 no pico do DIA
# ==============================================================================
def plot_01_todos_vs_alta_baixa_dia() -> None:
    series_cfg = [
        ("wdo", "WDO · mini dólar", "pontos (1 pt = R$ 10/contrato)", 2, (-6.2, 4.0)),
        ("win", "WIN · mini índice", "pontos (1 pt = R$ 0,20/contrato)", 1, (-135, 138)),
        ("dolarizado", "WIN/WDO · índice dolarizado", "pontos em US$ (1000 × WIN ÷ WDO)", 1, (-35, 34)),
    ]
    offsets = [-1, 0, 3, 5, 10, 15]
    x_pos = list(range(len(offsets)))
    x_labels = ["T−1\n(base)", "T\n(pico)", "T+3", "T+5", "T+10", "T+15"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.4), gridspec_kw={"wspace": 0.22})

    for ax, (s_key, title, unit, dec, ylim) in zip(axes, series_cfg):
        df_all = load_med(s_key, "todos").query("grupo == 'DIA'").set_index("offset").reindex(offsets)
        df_up = load_med(s_key, "alta").query("grupo == 'DIA'").set_index("offset").reindex(offsets)
        df_dn = load_med(s_key, "baixa").query("grupo == 'DIA'").set_index("offset").reindex(offsets)

        n_up = int(df_up["n"].iloc[0])
        n_dn = int(df_dn["n"].iloc[0])
        n_all = int(df_all["n"].iloc[0])

        ax.axhline(0, color=INK, lw=1.1, zorder=1)

        # Todos os dias (misturado)
        ax.plot(x_pos, df_all["mediana_pts"], color=MUTED, lw=2.0, ls="--", marker="o", ms=6,
                mec=INK, mew=0.8, label=f"todos os dias ({n_all})", zorder=2)

        # Dias de alta
        ax.plot(x_pos, df_up["mediana_pts"], color=PURPLE, lw=2.8, marker="o", ms=8,
                mec=INK, mew=1.0, label=f"dias de alta ({n_up})", zorder=4)

        # Dias de baixa
        ax.plot(x_pos, df_dn["mediana_pts"], color=ORANGE, lw=2.8, marker="o", ms=8,
                mec=INK, mew=1.0, label=f"dias de baixa ({n_dn})", zorder=4)

        # Rótulos nos pontos de alta e baixa
        for idx_i in (1, 2, 3, 4, 5):
            v_up = df_up["mediana_pts"].iloc[idx_i]
            v_dn = df_dn["mediana_pts"].iloc[idx_i]
            dy_up = (ylim[1] - ylim[0]) * 0.042
            dy_dn = -(ylim[1] - ylim[0]) * 0.055
            ax.text(idx_i, v_up + dy_up, br(v_up, dec, plus=True), ha="center", va="bottom",
                    fontsize=9.5, fontweight="bold", color=PURPLE)
            ax.text(idx_i, v_dn + dy_dn, br(v_dn, dec, plus=True), ha="center", va="top",
                    fontsize=9.5, fontweight="bold", color="#B86808")

        ax.set_xticks(x_pos, x_labels, fontsize=10)
        ax.set_ylim(*ylim)
        ax.set_xlim(-0.35, 5.45)
        ax.set_ylabel(unit, fontsize=10)
        ax.set_title(title, loc="left", fontsize=14, fontweight="bold", pad=28)
        # Legenda horizontal logo abaixo do título de cada painel, sem cobrir pontos
        ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), ncols=3, frameon=False,
                  fontsize=8.6, handlelength=1.4, columnspacing=0.9, borderaxespad=0)

    # Callout no painel do Dolarizado posicionado na faixa central livre
    axes[2].text(
        0.52, 0.34,
        "No dolarizado, o preço continua\nandando até T+15 (+27,0 / −28,7 pt)",
        transform=axes[2].transAxes, ha="center", va="center", fontsize=9.5, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.45", fc=MINT_BOX, ec=INK, lw=1.1),
    )

    fig.subplots_adjust(top=0.80)
    fig.suptitle(
        "Pico de volume do pregão (DIA): separar alta e baixa revela o movimento até T+15",
        x=0.06, y=0.98, ha="left", fontsize=17, fontweight="bold", color=INK,
    )
    fig.text(
        0.06, 0.915,
        "mediana da variação do fechamento contra T−1 (1 minuto antes do pico), em pontos · misturando todos os dias, alta e baixa se anulam (~0)",
        fontsize=11, color=INK_2,
    )
    save_all(fig, "01_todos_vs_alta_baixa_dia.png")


# ==============================================================================
# GRÁFICO 2: WDO e WIN nas 18 janelas de 30 min (Manhã x Tarde em T e T+15)
# ==============================================================================
def plot_02_wdo_win_janelas_30min() -> None:
    windows = [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in (0, 30)]
    x = np.arange(len(windows))
    w = 0.36

    fig, axes = plt.subplots(2, 1, figsize=(16, 10.6), sharex=True, gridspec_kw={"hspace": 0.34})

    configs = [
        ("wdo", "WDO · mini dólar: variação no pico (T) e 15 min depois (T+15) por janela de 30 min",
         "mediana da variação contra T−1, em pontos (tick = 0,5 pt) · 512 pregões de alta e 519 de baixa",
         1, (-3.2, 3.8)),
        ("win", "WIN · mini índice: variação no pico (T) e 15 min depois (T+15) por janela de 30 min",
         "mediana da variação contra T−1, em pontos (tick = 5 pt) · 584 pregões de alta e 531 de baixa",
         0, (-92, 75)),
    ]

    for ax, (s_key, title, subtitle, dec, ylim) in zip(axes, configs):
        up = load_med(s_key, "alta").set_index(["grupo", "offset"])
        dn = load_med(s_key, "baixa").set_index(["grupo", "offset"])

        up_t0 = [up.loc[(g, 0), "mediana_pts"] for g in windows]
        up_t15 = [up.loc[(g, 15), "mediana_pts"] for g in windows]
        dn_t0 = [dn.loc[(g, 0), "mediana_pts"] for g in windows]
        dn_t15 = [dn.loc[(g, 15), "mediana_pts"] for g in windows]

        # Faixa sutil destacando a manhã (09:00 a 12:00 -> índices 0 a 6)
        ax.axvspan(-0.5, 6.5, color="#E5E0D5", alpha=0.55, zorder=0)
        ax.axvline(6.5, color=INK_2, ls="--", lw=1.0, zorder=1)
        ax.text(3.0, ylim[1] * 0.88, "MANHÃ (maior volume)", ha="center", va="center",
                fontsize=9.5, fontweight="bold", color=INK_2)

        # Barras de Alta (acima de zero)
        ax.bar(x - w / 2, up_t0, width=w, color="#B79CED", edgecolor=INK, lw=0.8,
               label="Dias de alta · em T (pico)", zorder=3)
        ax.bar(x + w / 2, up_t15, width=w, color=PURPLE, edgecolor=INK, lw=0.9,
               label="Dias de alta · em T+15", zorder=3)

        # Barras de Baixa (abaixo de zero)
        ax.bar(x - w / 2, dn_t0, width=w, color="#FAD089", edgecolor=INK, lw=0.8,
               label="Dias de baixa · em T (pico)", zorder=3)
        ax.bar(x + w / 2, dn_t15, width=w, color=ORANGE, edgecolor=INK, lw=0.9,
               label="Dias de baixa · em T+15", zorder=3)

        ax.axhline(0, color=INK, lw=1.2, zorder=4)

        # Anotar os principais valores da manhã em T+15 (sem colidir com a barra T ao lado)
        highlight_idx = [0, 1, 2, 3, 5] if s_key == "wdo" else [0, 2, 3, 4]
        for idx_i in highlight_idx:
            vu = up_t15[idx_i]
            vd = dn_t15[idx_i]
            off_y = (ylim[1] - ylim[0]) * 0.025
            top_anchor = max(vu, up_t0[idx_i] if abs(vu - up_t0[idx_i]) < 1e-6 else vu)
            bot_anchor = min(vd, dn_t0[idx_i]) if abs(vd) < abs(dn_t0[idx_i]) else vd
            ax.text(idx_i + w / 2, top_anchor + off_y, br(vu, dec, plus=True), ha="center", va="bottom",
                    fontsize=8.8, fontweight="bold", color=INK)
            ax.text(idx_i + w / 2, bot_anchor - off_y, br(vd, dec, plus=True), ha="center", va="top",
                    fontsize=8.8, fontweight="bold", color=INK)

        ax.set_ylim(*ylim)
        ax.set_xlim(-0.6, len(windows) - 0.4)
        ax.set_ylabel("variação vs T−1 (pontos)", fontsize=10.5)
        ax.set_title(title, loc="left", fontsize=14.5, fontweight="bold", pad=22)
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10, color=INK_2)
        ax.legend(loc="upper right", ncols=2, frameon=True, facecolor=SURFACE, edgecolor=INK, fontsize=9.2)

    # Caixas de destaque no estilo do PDF
    axes[0].text(
        0.48, 0.72,
        "Manhã (9h–12h): até +3,0 pt na alta e −2,0 pt na baixa em T+15\nTarde (13h–17h): mediana trava em 0 a 0,5 pt (1 tick)",
        transform=axes[0].transAxes, ha="left", va="center", fontsize=9.8, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.45", fc=MINT_BOX, ec=INK, lw=1.1),
    )
    axes[1].text(
        0.48, 0.22,
        "10:00 e 10:30 lideram no WIN (abertura B3 + dados EUA):\n+40 a +50 pt na alta e −75 pt na baixa em T+15",
        transform=axes[1].transAxes, ha="left", va="center", fontsize=9.8, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.45", fc=MINT_BOX, ec=INK, lw=1.1),
    )

    axes[1].set_xticks(x, windows, rotation=0, fontsize=10)
    axes[1].set_xlabel("janela de 30 minutos do pico de volume", fontsize=10.5, labelpad=8)

    save_all(fig, "02_wdo_win_janelas_30min.png")


# ==============================================================================
# GRÁFICO 3: Índice Dolarizado (1000 * WIN / WDO) — Visão do Investidor Estrangeiro
# ==============================================================================
def plot_03_indice_dolarizado(janelas: bool = True) -> None:
    """janelas=False: só a trajetória minuto a minuto (painel esquerdo), sem as 18 janelas."""
    windows = [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in (0, 30)]
    offsets = [-1, 0, 3, 5, 10, 15]
    x_off = list(range(len(offsets)))
    off_labels = ["T−1", "T\n(pico)", "T+3", "T+5", "T+10", "T+15"]

    up = load_med("dolarizado", "alta")
    dn = load_med("dolarizado", "baixa")

    if janelas:
        fig, (ax_left, ax_right) = plt.subplots(
            1, 2, figsize=(18.0, 6.8), gridspec_kw={"width_ratios": [1.08, 1.32], "wspace": 0.22}
        )
    else:
        fig, ax_left = plt.subplots(figsize=(12.0, 7.2))

    # --- Painel Esquerdo: Trajetória T-1 a T+15 nas janelas da manhã vs Tarde ---
    sel_windows = [
        ("09:00", "#5B37A8", "-", "o", "09:00 (abertura)"),
        ("10:00", PURPLE, "-", "s", "10:00 (ações B3)"),
        ("10:30", "#9E7BE0", "--", "^", "10:30 (dados EUA)"),
        ("14:00", MUTED, ":", "d", "14:00 (tarde)"),
    ]
    ax_left.axhline(0, color=INK, lw=1.2, zorder=1)

    for g, col, ls, mk, lab in sel_windows:
        u_vals = up.query("grupo == @g").set_index("offset").reindex(offsets)["mediana_pts"]
        d_vals = dn.query("grupo == @g").set_index("offset").reindex(offsets)["mediana_pts"]
        lw = 2.6 if g in ("09:00", "10:00", "10:30") else 1.8
        ax_left.plot(x_off, u_vals, color=col, ls=ls, lw=lw, marker=mk, ms=6.5, mec=INK, mew=0.7,
                     label=f"Alta · {lab}" if g != "14:00" else "Tarde (14:00 · alta/baixa)")
        col_dn = ORANGE if g == "10:00" else ("#D97218" if g == "09:00" else ("#F5B35D" if g == "10:30" else MUTED))
        ax_left.plot(x_off, d_vals, color=col_dn, ls=ls, lw=lw, marker=mk, ms=6.5, mec=INK, mew=0.7,
                     label=f"Baixa · {lab}" if g != "14:00" else None)

    # Rótulos limpos à direita de T+15 (x = 5.14) e acima/abaixo de T (x = 1)
    u_1000 = up.query("grupo == '10:00'").set_index("offset").reindex(offsets)["mediana_pts"]
    d_1000 = dn.query("grupo == '10:00'").set_index("offset").reindex(offsets)["mediana_pts"]
    u_0900 = up.query("grupo == '09:00'").set_index("offset").reindex(offsets)["mediana_pts"]
    d_0900 = dn.query("grupo == '09:00'").set_index("offset").reindex(offsets)["mediana_pts"]
    u_1030 = up.query("grupo == '10:30'").set_index("offset").reindex(offsets)["mediana_pts"]
    d_1030 = dn.query("grupo == '10:30'").set_index("offset").reindex(offsets)["mediana_pts"]

    ax_left.text(1.0, u_1000.loc[0] + 1.2, f"10h: +{br(u_1000.loc[0], 1)}", ha="center", fontsize=8.8, fontweight="bold", color=PURPLE)
    ax_left.text(1.0, d_1030.loc[0] - 2.3, f"10:30: {br(d_1030.loc[0], 1)}", ha="center", fontsize=8.8, fontweight="bold", color="#B86808")

    # Rótulos finais à direita de T+15 sem sobreposição
    ax_left.text(5.15, u_0900.loc[15] + 0.4, f"09h: +{br(u_0900.loc[15], 1)}", ha="left", va="center", fontsize=8.8, fontweight="bold", color="#5B37A8")
    ax_left.text(5.15, u_1000.loc[15] - 0.1, f"10h: +{br(u_1000.loc[15], 1)}", ha="left", va="center", fontsize=8.8, fontweight="bold", color=PURPLE)
    ax_left.text(5.15, u_1030.loc[15] - 0.6, f"10:30: +{br(u_1030.loc[15], 1)}", ha="left", va="center", fontsize=8.8, fontweight="bold", color="#7B57C8")

    ax_left.text(5.15, d_1030.loc[15] + 0.3, f"10:30: {br(d_1030.loc[15], 1)}", ha="left", va="center", fontsize=8.8, fontweight="bold", color="#B86808")
    ax_left.text(5.15, d_1000.loc[15] + 0.1, f"10h: {br(d_1000.loc[15], 1)}", ha="left", va="center", fontsize=8.8, fontweight="bold", color="#B86808")
    ax_left.text(5.15, d_0900.loc[15] - 0.5, f"09h: {br(d_0900.loc[15], 1)}", ha="left", va="center", fontsize=8.8, fontweight="bold", color="#D97218")

    ax_left.set_xticks(x_off, off_labels, fontsize=10)
    ax_left.set_ylim(-26, 26)
    ax_left.set_xlim(-0.3, 6.25)
    ax_left.set_ylabel("variação vs T−1 (pontos em US$)", fontsize=10.5)
    ax_left.set_title("Trajetória minuto a minuto (T−1 até T+15)", loc="left", fontsize=13.5, fontweight="bold", pad=10)
    ax_left.legend(loc="upper left", frameon=True, facecolor=SURFACE, edgecolor=INK, fontsize=8.3, ncols=2)

    if janelas:
        # --- Painel Direito: Todas as 18 janelas de 30 min (T vs T+15) ---
        up_idx = up.set_index(["grupo", "offset"])
        dn_idx = dn.set_index(["grupo", "offset"])
        x_w = np.arange(len(windows))
        bw = 0.36

        up_t0 = [up_idx.loc[(g, 0), "mediana_pts"] for g in windows]
        up_t15 = [up_idx.loc[(g, 15), "mediana_pts"] for g in windows]
        dn_t0 = [dn_idx.loc[(g, 0), "mediana_pts"] for g in windows]
        dn_t15 = [dn_idx.loc[(g, 15), "mediana_pts"] for g in windows]

        ax_right.axvspan(-0.5, 6.5, color="#E5E0D5", alpha=0.55, zorder=0)
        ax_right.axvline(6.5, color=INK_2, ls="--", lw=1.0, zorder=1)
        ax_right.axhline(0, color=INK, lw=1.2, zorder=4)

        ax_right.bar(x_w - bw / 2, up_t0, width=bw, color="#B79CED", edgecolor=INK, lw=0.8, label="Alta · em T (pico)", zorder=3)
        ax_right.bar(x_w + bw / 2, up_t15, width=bw, color=PURPLE, edgecolor=INK, lw=0.9, label="Alta · em T+15", zorder=3)
        ax_right.bar(x_w - bw / 2, dn_t0, width=bw, color="#FAD089", edgecolor=INK, lw=0.8, label="Baixa · em T (pico)", zorder=3)
        ax_right.bar(x_w + bw / 2, dn_t15, width=bw, color=ORANGE, edgecolor=INK, lw=0.9, label="Baixa · em T+15", zorder=3)

        for idx_i in (0, 2, 3, 4, 5):
            top_anchor = max(up_t15[idx_i], up_t0[idx_i])
            bot_anchor = min(dn_t15[idx_i], dn_t0[idx_i])
            ax_right.text(idx_i + bw / 2, top_anchor + 0.6, br(up_t15[idx_i], 1, plus=True),
                          ha="center", va="bottom", fontsize=8.3, fontweight="bold", color=INK)
            ax_right.text(idx_i + bw / 2, bot_anchor - 0.6, br(dn_t15[idx_i], 1, plus=True),
                          ha="center", va="top", fontsize=8.3, fontweight="bold", color=INK)

        ax_right.text(
            0.97, 0.14,
            "De manhã, T+15 supera T em quase\ntodas as janelas: o movimento continua!",
            transform=ax_right.transAxes, ha="right", va="bottom", fontsize=9.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.45", fc=MINT_BOX, ec=INK, lw=1.1),
        )

        ax_right.set_xticks(x_w, windows, rotation=45, fontsize=9.5)
        ax_right.set_ylim(-26, 26)
        ax_right.set_xlim(-0.6, len(windows) - 0.4)
        ax_right.set_title("As 18 janelas de 30 min: salto em T vs acumulação até T+15", loc="left", fontsize=13.5, fontweight="bold", pad=10)
        ax_right.legend(loc="upper right", ncols=2, frameon=True, facecolor=SURFACE, edgecolor=INK, fontsize=8.8)

    fig.suptitle(
        "WIN/WDO · Índice Dolarizado (Ibovespa em US$): na manhã, o preço segue andando após o pico",
        x=0.06, y=1.03, ha="left", fontsize=16.5, fontweight="bold", color=INK,
    )
    fig.text(
        0.06, 0.955,
        "série = 1000 × WIN ÷ WDO (~22.200 pts) · T pelo pico de volume do WIN · 993 pregões comuns (524 de alta, 469 de baixa)",
        fontsize=11, color=INK_2,
    )
    save_all(fig, "03_indice_dolarizado_manha_tarde.png" if janelas else "03_indice_dolarizado_trajetoria.png")


# ==============================================================================
# GRÁFICO 4: Fluxo de Investidores (Estrangeiro x Pessoa Física) no padrão do PDF
# ==============================================================================
def plot_04_fluxo_investidores(correlacao: bool = True) -> None:
    """correlacao=False: só o fluxo acumulado, sem o painel da correlação móvel."""
    df = pd.read_csv(FLUX_CSV)
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data").reset_index(drop=True)

    est_cum = df["estrangeiro"].cumsum() / 1000.0
    pf_cum = df["pessoa_fisica"].cumsum() / 1000.0
    corr_daily = df["estrangeiro"].corr(df["pessoa_fisica"])
    roll20 = df["estrangeiro"].rolling(20).corr(df["pessoa_fisica"])
    pct_opostos = ((df["estrangeiro"] * df["pessoa_fisica"]) < 0).mean() * 100

    if correlacao:
        fig, (ax_top, ax_bot) = plt.subplots(
            2, 1, figsize=(14.5, 8.2), sharex=True, gridspec_kw={"height_ratios": [2.1, 1.0], "hspace": 0.22}
        )
    else:
        fig, ax_top = plt.subplots(figsize=(14.5, 6.0))
        ax_bot = ax_top

    # --- Painel Superior: Fluxo Acumulado (R$ bilhões) ---
    ax_top.axhline(0, color=INK, lw=1.1, zorder=1)
    ax_top.fill_between(df["data"], 0, est_cum, color=PURPLE, alpha=0.12, zorder=1)
    ax_top.fill_between(df["data"], 0, pf_cum, color=ORANGE, alpha=0.14, zorder=1)

    ax_top.plot(df["data"], est_cum, color=PURPLE, lw=2.8, label="Investidor estrangeiro (Big Player)", zorder=3)
    ax_top.plot(df["data"], pf_cum, color=ORANGE, lw=2.8, label="Pessoa física (varejo)", zorder=3)

    # Marcar pontos-chave: Pico de abril/2026, vale de agosto/2026 e fim em nov/2026
    idx_peak = int(est_cum.idxmax())
    idx_trough = int(est_cum.loc[idx_peak:].idxmin())
    idx_end = len(df) - 1

    for idx_pt in (idx_peak, idx_trough, idx_end):
        d_pt = df.loc[idx_pt, "data"]
        ax_top.scatter([d_pt], [est_cum.iloc[idx_pt]], s=60, color=PURPLE, edgecolor=INK, lw=1.0, zorder=5)
        ax_top.scatter([d_pt], [pf_cum.iloc[idx_pt]], s=60, color=ORANGE, edgecolor=INK, lw=1.0, zorder=5)

    # Rótulos nos pontos-chave (Pico posicionado bem à direita, em mai/jun, longe da caixa verde-água)
    d_pk = df.loc[idx_peak, "data"]
    ax_top.annotate(
        f"Pico (20/abr/26)\nEstrangeiro: +{br(est_cum.iloc[idx_peak], 1)} bi · PF: {br(pf_cum.iloc[idx_peak], 1)} bi",
        xy=(d_pk, est_cum.iloc[idx_peak]),
        xytext=(d_pk + pd.Timedelta(days=42), 58),
        fontsize=9.3, fontweight="bold", color=INK,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=INK, lw=0.9),
        arrowprops=dict(arrowstyle="->", color=INK, lw=1.1),
    )

    d_tr = df.loc[idx_trough, "data"]
    ax_top.annotate(
        f"Vale (ago/26)\nEstrangeiro: +{br(est_cum.iloc[idx_trough], 1)} bi\nPF: +{br(pf_cum.iloc[idx_trough], 1)} bi",
        xy=(d_tr, est_cum.iloc[idx_trough]),
        xytext=(d_tr - pd.Timedelta(days=72), 14),
        fontsize=9.3, fontweight="bold", color=INK,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=INK, lw=0.9),
        arrowprops=dict(arrowstyle="->", color=INK, lw=1.1),
    )

    d_end = df.loc[idx_end, "data"]
    ax_top.text(d_end + pd.Timedelta(days=3), est_cum.iloc[idx_end], f"+{br(est_cum.iloc[idx_end], 1)} bi",
                va="center", ha="left", fontsize=10, fontweight="bold", color=PURPLE)
    ax_top.text(d_end + pd.Timedelta(days=3), pf_cum.iloc[idx_end], f"+{br(pf_cum.iloc[idx_end], 1)} bi",
                va="center", ha="left", fontsize=10, fontweight="bold", color="#B86808")

    # Callout principal no canto superior esquerdo livre
    ax_top.text(
        0.015, 0.81,
        f"Em {pct_opostos:.0f}% dos pregões operam em lados opostos\nCorrelação diária = {br(corr_daily, 2)} (um compra, o outro vende)",
        transform=ax_top.transAxes, ha="left", va="center", fontsize=9.8, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.45", fc=MINT_BOX, ec=INK, lw=1.2),
    )

    ax_top.set_ylabel("saldo acumulado (R$ bilhões)", fontsize=10.5)
    ax_top.set_ylim(-14, 78)
    ax_top.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"R$ {br(v, 0)} bi" if v != 0 else "0"))
    ax_top.legend(loc="upper right", frameon=True, facecolor=SURFACE, edgecolor=INK, fontsize=10.5)
    ax_top.set_title(
        "B3 · Fluxo acumulado: investidor estrangeiro × pessoa física (nov/2025 a nov/2026)",
        loc="left", fontsize=15.5, fontweight="bold", pad=22,
    )
    ax_top.text(
        0, 1.02,
        "saldo diário líquido (compras − vendas) acumulado em R$ bilhões · 245 pregões · fonte: Dados de Mercado (página pública)",
        transform=ax_top.transAxes, fontsize=10.5, color=INK_2,
    )

    if correlacao:
        # --- Painel Inferior: Correlação Móvel de 20 pregões ---
        ax_bot.axhline(0, color=INK, lw=1.0, zorder=1)
        ax_bot.axhline(corr_daily, color=INK, ls="--", lw=1.2, zorder=2)
        ax_bot.text(df["data"].min() + pd.Timedelta(days=4), corr_daily - 0.16,
                    f"correlação geral = {br(corr_daily, 2)}", fontsize=9.5, fontweight="bold", color=INK)

        ax_bot.fill_between(df["data"], 0, roll20, where=(roll20 <= 0), color=PINK, alpha=0.25, interpolate=True)
        ax_bot.fill_between(df["data"], 0, roll20, where=(roll20 > 0), color=PURPLE, alpha=0.20, interpolate=True)
        ax_bot.plot(df["data"], roll20, color=INK, lw=1.8, label="Correlação móvel (20 pregões)")

        idx_min_corr = int(roll20.idxmin())
        d_min = df.loc[idx_min_corr, "data"]
        ax_bot.scatter([d_min], [roll20.iloc[idx_min_corr]], s=50, color=PINK, edgecolor=INK, zorder=5)
        ax_bot.annotate(
            f"mínima (out/26): {br(roll20.iloc[idx_min_corr], 2)}",
            xy=(d_min, roll20.iloc[idx_min_corr]),
            xytext=(d_min - pd.Timedelta(days=70), -0.32),
            fontsize=9.2, fontweight="bold", color=INK,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=INK, lw=0.8),
            arrowprops=dict(arrowstyle="->", color=INK, lw=1.0),
        )

        ax_bot.set_ylim(-1.08, 0.55)
        ax_bot.set_yticks([-1.0, -0.5, 0.0, 0.5])
        ax_bot.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: br(v, 1)))
        ax_bot.set_ylabel("correlação (20d)", fontsize=10.5)
        ax_bot.set_title("Correlação móvel em janelas de 20 pregões", loc="left", fontsize=12.5, fontweight="bold", pad=6)

    ax_bot.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    ax_bot.set_xlim(df["data"].min() - pd.Timedelta(days=6), df["data"].max() + pd.Timedelta(days=26))

    if not correlacao:
        save_all(fig, "04_fluxo_estrangeiro_x_pf_sem_correlacao.png")
        return
    save_all(fig, "04_fluxo_estrangeiro_x_pf.png")
    for dst in [
        DOC_DIR / "graficos" / "f1_estrangeiro_x_pf.png",
        BP / "reports" / "figures" / "fluxo" / "f1_estrangeiro_x_pf.png",
    ]:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DOC_DIR / "graficos" / "04_fluxo_estrangeiro_x_pf.png", dst)


# ==============================================================================
# GRÁFICO 5: Painel Resumo (Manhã vs Tarde vs Pico do Dia nos 3 Ativos)
# ==============================================================================
def plot_05_resumo_comparativo_ativos() -> None:
    grupos = ["09:00", "10:00", "10:30", "14:00", "16:00", "DIA"]
    labels_g = ["09:00\n(abertura)", "10:00\n(ações)", "10:30\n(EUA)", "14:00\n(tarde)", "16:00\n(tarde)", "DIA\n(pico)"]
    x = np.arange(len(grupos))
    w = 0.35

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.3), gridspec_kw={"wspace": 0.22})
    cfg = [
        ("wdo", "WDO · mini dólar (em T+15)", "pontos vs T−1", 1, (-5.2, 3.6)),
        ("win", "WIN · mini índice (em T+15)", "pontos vs T−1", 0, (-128, 120)),
        ("dolarizado", "WIN/WDO · dolarizado (em T+15)", "pontos US$ vs T−1", 1, (-34, 33)),
    ]

    for ax, (s_key, title, ylabel, dec, ylim) in zip(axes, cfg):
        up = load_med(s_key, "alta").query("offset == 15").set_index("grupo").reindex(grupos)
        dn = load_med(s_key, "baixa").query("offset == 15").set_index("grupo").reindex(grupos)
        al = load_med(s_key, "todos").query("offset == 15").set_index("grupo").reindex(grupos)

        ax.axvspan(4.5, 5.5, color="#E5E0D5", alpha=0.7, zorder=0)
        ax.axvline(4.5, color=INK_2, ls="--", lw=1.0, zorder=1)
        ax.axhline(0, color=INK, lw=1.2, zorder=3)

        ax.bar(x - w / 2, up["mediana_pts"], width=w, color=PURPLE, edgecolor=INK, lw=0.9, label="Dias de alta", zorder=4)
        ax.bar(x + w / 2, dn["mediana_pts"], width=w, color=ORANGE, edgecolor=INK, lw=0.9, label="Dias de baixa", zorder=4)
        ax.scatter(x, al["mediana_pts"], color=SURFACE, edgecolor=INK, s=42, lw=1.3, zorder=5, label="Todos os dias")

        off_y = (ylim[1] - ylim[0]) * 0.025
        for i, (vu, vd) in enumerate(zip(up["mediana_pts"], dn["mediana_pts"])):
            ax.text(i - w / 2, max(vu, 0) + off_y, br(vu, dec, plus=True), ha="center", va="bottom",
                    fontsize=8.8, fontweight="bold", color=INK)
            ax.text(i + w / 2, min(vd, 0) - off_y, br(vd, dec, plus=True), ha="center", va="top",
                    fontsize=8.8, fontweight="bold", color=INK)

        ax.set_xticks(x, labels_g, fontsize=9.2)
        ax.set_ylim(*ylim)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, loc="left", fontsize=13.5, fontweight="bold", pad=28)
        ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), ncols=3, frameon=False,
                  fontsize=8.6, handlelength=1.3, columnspacing=0.9, borderaxespad=0)

    fig.subplots_adjust(top=0.80)
    fig.suptitle(
        "Resumo em T+15: manhã forte, tarde parada e pico do dia dominante nos três ativos",
        x=0.06, y=0.98, ha="left", fontsize=16.5, fontweight="bold", color=INK,
    )
    fig.text(
        0.06, 0.915,
        "mediana da variação em T+15 contra T−1, em pontos · círculos claros mostram que misturar todos os dias esconde o movimento perto de zero",
        fontsize=11, color=INK_2,
    )
    save_all(fig, "05_resumo_comparativo_t15.png")


if __name__ == "__main__":
    plot_01_todos_vs_alta_baixa_dia()
    plot_02_wdo_win_janelas_30min()
    plot_03_indice_dolarizado()
    plot_03_indice_dolarizado(janelas=False)
    plot_04_fluxo_investidores()
    plot_04_fluxo_investidores(correlacao=False)
    plot_05_resumo_comparativo_ativos()
    print("Gráficos atualizados com sucesso!")
