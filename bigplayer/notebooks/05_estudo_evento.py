# %% [markdown]
# # 05 — Estudo de evento (Fase 2, Gate 1) — somente exploração
#
# **Pergunta:** quando aparece um evento de fluxo anômalo, o preço continua na direção dele?
# (Seguir só faz sentido se o retorno futuro, no sentido do evento, for positivo e maior que o de
# barras comuns parecidas.)
#
# **Pré-registro (definido ANTES de olhar os resultados; não alterar depois):**
# - Eventos (3 definições, direção = sinal do movimento do preço):
#   - **E1** `z_vol >= 3`; direção = sinal de `close - open` da barra.
#   - **E2** `z_vol >= 3` e `z_lot >= 1`; mesma direção. (volume anômalo com lote acima do normal)
#   - **E3** média de `z_vol` nas 5 últimas barras `>= 2`; direção = sinal do retorno de 5 barras.
# - `z_vol`/`z_lot`: log do volume / do lote contra o mesmo minuto dos 20 pregões anteriores (sem look-ahead).
# - Episódios: após um evento, ignora novos eventos por 30 min no mesmo pregão (sem sobreposição).
# - Execução: entra na abertura da barra seguinte, sai no fechamento de `t + h`, h em {1, 5, 15, 30, 60} min,
#   mesmo pregão (nunca cruza `roll_day`).
# - Controle: barras comuns (`z < 1`) da mesma hora e do mesmo quintil de |retorno|, com a mesma regra de direção.
#   O efeito do evento é o retorno a favor da direção MENOS o do controle pareado.
# - Incerteza: bootstrap por dia (4000), 15 testes: **limite de Bonferroni p < 0,0033**.
# - Critério do Gate 1: efeito > 0 com p < 0,0033 em algum horizonte **e** mesmo sinal na maioria dos anos.
#
# **Entrada:** `load_clean()` (exploração). **Saída:** `reports/estudo_evento_<ativo>.csv`.

# %%
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import numpy as np
import pandas as pd

from src.evaluation.event_study import cluster_bootstrap_mean, forward_returns
from src.features.flow import flow_features
from src.ingestion.loader import ASSET, load_clean

pd.set_option("display.width", 160)
HORIZONS = (1, 5, 15, 30, 60)
COOLDOWN_MIN = 30

b = flow_features(load_clean())
fw = forward_returns(b, HORIZONS)
b = pd.concat([b, fw], axis=1)
b["hour"] = b["ts"].dt.hour
b["year"] = b["ts"].dt.year
print(ASSET, "| barras usáveis:", len(b), "| com lookback de 20 pregões:", int(b["lb_ok"].sum()))
tick_bps = 0.5 / b["close"].median() * 1e4 if ASSET == "WDO" else 5 / b["close"].median() * 1e4
print(f"1 tick ≈ {tick_bps:.2f} bps (referência de custo; custos reais entram no Gate 2)")

# %% [markdown]
# ## 1. Definição dos eventos e do controle

# %%
DEFS = {
    "E1": dict(is_event=lambda d: d["z_vol"] >= 3, ctrl=lambda d: d["z_vol"] < 1, ret="ret_bps"),
    "E2": dict(is_event=lambda d: (d["z_vol"] >= 3) & (d["z_lot"] >= 1), ctrl=lambda d: d["z_vol"] < 1, ret="ret_bps"),
    "E3": dict(is_event=lambda d: d["z_vol5"] >= 2, ctrl=lambda d: d["z_vol5"] < 1, ret="ret5_bps"),
}
base = b[b["lb_ok"] & b["z_vol"].notna()].copy()


def apply_cooldown(ev: pd.DataFrame) -> pd.DataFrame:
    keep, last = [], {}
    for i, d, t in zip(ev.index, ev["session_date"], ev["ts"]):
        if d not in last or (t - last[d]) >= pd.Timedelta(minutes=COOLDOWN_MIN):
            keep.append(i)
            last[d] = t
    return ev.loc[keep]


rows, by_year = [], []
for name, spec in DEFS.items():
    d = base[base[spec["ret"]].notna() & (base[spec["ret"]] != 0)].copy()
    d["dir"] = np.sign(d[spec["ret"]])
    d["abs_r"] = d[spec["ret"]].abs()
    d["q"] = pd.qcut(d["abs_r"], 5, labels=False, duplicates="drop")
    ev_all = d[spec["is_event"](d)]
    ev = apply_cooldown(ev_all.sort_values("ts"))
    ctrl = d[spec["ctrl"](d)]
    print(f"\n{name}: {len(ev_all)} barras-evento → {len(ev)} episódios (cooldown {COOLDOWN_MIN} min), "
          f"{ev['session_date'].nunique()} dias | controle: {len(ctrl)} barras")
    for h in HORIZONS:
        col = f"fwd_{h}"
        d["sig"] = d["dir"] * d[col]                        # retorno a favor da direção (bps)
        cmean = d[spec["ctrl"](d)].groupby(["hour", "q"])["sig"].mean()
        e = d.loc[ev.index].dropna(subset=["sig"]).copy()
        e["ctrl"] = [cmean.get((hh, qq), np.nan) for hh, qq in zip(e["hour"], e["q"])]
        e = e.dropna(subset=["ctrl"])
        e["excess"] = e["sig"] - e["ctrl"]
        m, lo, hi, p = cluster_bootstrap_mean(e["excess"].to_numpy(), e["session_date"].to_numpy())
        rows.append(dict(evento=name, h_min=h, n=len(e), a_favor_bps=e["sig"].mean(), controle_bps=e["ctrl"].mean(),
                         efeito_bps=m, ic95_inf=lo, ic95_sup=hi, p=p, acerto=(e["sig"] > 0).mean()))
        for y, g in e.groupby("year"):
            by_year.append(dict(evento=name, h_min=h, ano=y, n=len(g), efeito_bps=g["excess"].mean()))

res = pd.DataFrame(rows)
res.to_csv(BP / "reports" / f"estudo_evento_{ASSET.lower()}.csv", index=False)
print("\n", res.round(3).to_string(index=False))

# %% [markdown]
# ## 2. Estabilidade por ano (efeito em bps)

# %%
yr = pd.DataFrame(by_year).pivot_table(index=["evento", "h_min"], columns="ano", values="efeito_bps")
print(yr.round(2).to_string())
pos = (yr > 0).sum(axis=1)
print("\nanos com efeito positivo (de", yr.shape[1], "):")
print(pos.unstack().to_string())

# %% [markdown]
# ## 3. Veredito do critério pré-registrado

# %%
alpha = 0.05 / len(res)
res["passa"] = (res["efeito_bps"] > 0) & (res["p"] < alpha)
print(f"Limite de Bonferroni: p < {alpha:.4f}")
print(res.loc[res["passa"], ["evento", "h_min", "n", "efeito_bps", "p"]].round(4).to_string(index=False)
      if res["passa"].any() else "Nenhum teste passa o limite.")
