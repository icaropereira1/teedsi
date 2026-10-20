# %% [markdown]
# # 06 — Estudo de evento, rodada 2 (Fase 2, Gate 1) — somente exploração
#
# Definições, critérios e limite estão **congelados** em `docs/PRE_REGISTRO_GATE1_RODADA2.md`.
# Não alterar este arquivo olhando o resultado. A replicação no WIN só roda se alguma definição
# passar no WDO (`BIGPLAYER_ASSET=WIN`, mesmo arquivo).
#
# **Saída:** `reports/estudo_evento_r2_<ativo>.csv`.

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
from src.ingestion.loader import ASSET, load_clean, load_config

pd.set_option("display.width", 170)
HORIZONS = (1, 5, 15, 30, 60)
COOLDOWN_MIN = 30
N_TESTS_TOTAL = 30                       # 15 da rodada 1 + 15 desta rodada (WDO)
ALPHA = 0.05 / N_TESTS_TOTAL
MIN_EPISODES = 300
TICK = load_config()["data"]["tick"]

b = flow_features(load_clean(), tick=TICK)
b = pd.concat([b, forward_returns(b, HORIZONS)], axis=1)
b["hour"] = b["ts"].dt.hour
b["year"] = b["ts"].dt.year
tick_bps = TICK / b["close"].median() * 1e4
print(f"{ASSET} | barras usáveis: {len(b)} | lb_ok: {int(b['lb_ok'].sum())} | 1 tick ≈ {tick_bps:.2f} bps | alpha = {ALPHA:.4f}")

base = b[b["lb_ok"] & b["z_vol"].notna() & b["z_rng"].notna()].copy()

# %% [markdown]
# ## Definições (ver pré-registro, seção 2)

# %%
A1_ev = (base["z_vol"] >= 1.5) & (base["z_rng"] <= 0) & (base["r15_bps"].abs() >= base["lim15"])
P1_ev = (base["n_z1_15"] >= 10) & (base["max_z15"] < 3)
X1_ev = base["clv_run3"] != 0
quint = lambda s: pd.qcut(s, 5, labels=False, duplicates="drop")

DEFS = {
    "A1": dict(ev=A1_ev, dir=np.sign(base["r15_bps"]), strat=base["r15_bps"].abs(),
               ctrl=base["z_vol"] < 1),
    "P1": dict(ev=P1_ev, dir=np.sign(base["r15_bps"]), strat=base["r15_bps"].abs(),
               ctrl=base["z_vol"] < 1),
    "X1": dict(ev=X1_ev, dir=base["clv_run3"].astype(float), strat=base["ret3_bps"].abs(),
               ctrl=(base["z_vol"] < 1) & (base["clv"].abs() >= 0.5)),
}
# X1: o controle usa a direção da própria barra (sinal de clv)
X1_ctrl_dir = np.sign(base["clv"])


def apply_cooldown(ev: pd.DataFrame) -> pd.Index:
    keep, last = [], {}
    for i, d, t in zip(ev.index, ev["session_date"], ev["ts"]):
        if d not in last or (t - last[d]) >= pd.Timedelta(minutes=COOLDOWN_MIN):
            keep.append(i)
            last[d] = t
    return pd.Index(keep)


rows, by_year = [], []
for name, spec in DEFS.items():
    d = base.copy()
    d["strat_q"] = quint(spec["strat"])
    valid = spec["strat"].notna() & (spec["strat"] > 0)
    ev_mask = spec["ev"] & valid
    ep = apply_cooldown(d[ev_mask].sort_values("ts"))
    ctrl_mask = spec["ctrl"] & valid
    n_all, n_ep = int(ev_mask.sum()), len(ep)
    print(f"\n{name}: {n_all} barras-evento → {n_ep} episódios | {d.loc[ep, 'session_date'].nunique()} dias | "
          f"controle: {int(ctrl_mask.sum())} barras" + ("  [INCONCLUSIVO: < 300]" if n_ep < MIN_EPISODES else ""))
    ctrl_dir = X1_ctrl_dir if name == "X1" else spec["dir"]
    for h in HORIZONS:
        fwd = d[f"fwd_{h}"]
        ctrl_sig = (ctrl_dir * fwd)[ctrl_mask]
        cmean = ctrl_sig.groupby([d.loc[ctrl_mask, "hour"], d.loc[ctrl_mask, "strat_q"]]).mean()
        e = d.loc[ep].copy()
        e["sig"] = spec["dir"].loc[ep] * e[f"fwd_{h}"]
        e = e.dropna(subset=["sig"])
        e["ctrl"] = [cmean.get((hh, qq), np.nan) for hh, qq in zip(e["hour"], e["strat_q"])]
        e = e.dropna(subset=["ctrl"])
        e["excess"] = e["sig"] - e["ctrl"]
        m, lo, hi, p = cluster_bootstrap_mean(e["excess"].to_numpy(), e["session_date"].to_numpy())
        yr = e.groupby("year")["excess"].mean()
        rows.append(dict(evento=name, h_min=h, n=len(e), a_favor_bps=e["sig"].mean(), controle_bps=e["ctrl"].mean(),
                         efeito_bps=m, ic95_inf=lo, ic95_sup=hi, p=p, acerto=(e["sig"] > 0).mean(),
                         anos_pos=int((yr > 0).sum()), anos=len(yr)))
        for y, v in yr.items():
            by_year.append(dict(evento=name, h_min=h, ano=y, efeito_bps=v))

res = pd.DataFrame(rows)
res.to_csv(BP / "reports" / f"estudo_evento_r2_{ASSET.lower()}.csv", index=False)
print("\n", res.round(3).to_string(index=False))

# %% [markdown]
# ## Veredito pelo critério pré-registrado

# %%
res["c1_p"] = (res["efeito_bps"] > 0) & (res["p"] < ALPHA)
res["c2_anos"] = res["anos_pos"] >= 4
res["c3_n"] = res["n"] >= MIN_EPISODES
res["c4_tick"] = res["efeito_bps"] >= tick_bps
res["passa_gate1"] = res["c1_p"] & res["c2_anos"] & res["c3_n"]
res["segue_gate2"] = res["passa_gate1"] & res["c4_tick"]
print(f"Limite: p < {ALPHA:.4f} | piso prático: {tick_bps:.2f} bps | mínimo de {MIN_EPISODES} episódios")
print(res[["evento", "h_min", "n", "efeito_bps", "p", "anos_pos", "c1_p", "c2_anos", "passa_gate1", "segue_gate2"]]
      .round(4).to_string(index=False))
print("\nPassam o Gate 1:", res.loc[res["passa_gate1"], ["evento", "h_min"]].values.tolist() or "nenhuma")
print("Menor p:", res.loc[res["p"].idxmin(), ["evento", "h_min", "efeito_bps", "p"]].to_dict())
