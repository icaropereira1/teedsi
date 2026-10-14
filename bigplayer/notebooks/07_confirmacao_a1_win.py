# %% [markdown]
# # 07 — Confirmação do A1 no WIN (um único teste)
# Critérios congelados em `docs/PRE_REGISTRO_CONFIRMACAO_A1_WIN.md`. Não alterar olhando o resultado.

# %%
import os
import sys
from pathlib import Path

os.environ["BIGPLAYER_ASSET"] = "WIN"
_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())
sys.path.insert(0, str(BP))

import numpy as np
import pandas as pd

from src.evaluation.event_study import cluster_bootstrap_mean, forward_returns
from src.features.flow import flow_features
from src.ingestion.loader import ASSET, load_clean, load_config

assert ASSET == "WIN"
H, COOLDOWN_MIN, ALPHA, MIN_EP = 15, 30, 0.05, 300
TICK = load_config()["data"]["tick"]

b = flow_features(load_clean(), tick=TICK)
b = pd.concat([b, forward_returns(b, (H,))], axis=1)
b["hour"] = b["ts"].dt.hour
b["year"] = b["ts"].dt.year
tick_bps = TICK / b["close"].median() * 1e4
d = b[b["lb_ok"] & b["z_vol"].notna() & b["z_rng"].notna()].copy()

valid = d["r15_bps"].abs() > 0
ev = (d["z_vol"] >= 1.5) & (d["z_rng"] <= 0) & (d["r15_bps"].abs() >= d["lim15"]) & valid
ctrl = (d["z_vol"] < 1) & valid
direction = np.sign(d["r15_bps"])
d["q"] = pd.qcut(d["r15_bps"].abs(), 5, labels=False, duplicates="drop")

keep, last = [], {}
for i, s, t in zip(d[ev].sort_values("ts").index, d[ev].sort_values("ts")["session_date"], d[ev].sort_values("ts")["ts"]):
    if s not in last or (t - last[s]) >= pd.Timedelta(minutes=COOLDOWN_MIN):
        keep.append(i)
        last[s] = t

sig = direction * d[f"fwd_{H}"]
cmean = sig[ctrl].groupby([d.loc[ctrl, "hour"], d.loc[ctrl, "q"]]).mean()
e = d.loc[keep].copy()
e["sig"] = sig.loc[keep]
e = e.dropna(subset=["sig"])
e["ctrl"] = [cmean.get((h, q), np.nan) for h, q in zip(e["hour"], e["q"])]
e = e.dropna(subset=["ctrl"])
e["excess"] = e["sig"] - e["ctrl"]
m, lo, hi, p = cluster_bootstrap_mean(e["excess"].to_numpy(), e["session_date"].to_numpy())
yr = e.groupby("year")["excess"].agg(["mean", "size"])

print(f"WIN A1 @ {H} min | episódios: {len(e)} | dias: {e['session_date'].nunique()} | 1 tick ≈ {tick_bps:.2f} bps")
print(f"a favor: {e['sig'].mean():+.2f} bps | controle: {e['ctrl'].mean():+.2f} | EFEITO: {m:+.2f} bps "
      f"IC95 [{lo:+.2f}; {hi:+.2f}] | p = {p:.4f} | acerto {100 * (e['sig'] > 0).mean():.1f}%")
print("\nPor ano (efeito em bps, n):\n", yr.round(2).to_string())
c1, c2, c3 = (m > 0 and p < ALPHA), len(e) >= MIN_EP, m >= tick_bps
c4 = int((yr["mean"] > 0).sum())
print(f"\nCritérios: 1) efeito>0 e p<0,05: {c1} | 2) N≥300: {c2} | 3) efeito≥1 tick: {c3} | 4) anos positivos: {c4}/{len(yr)}")
print("CONFIRMA A1 no WIN:", bool(c1 and c2 and c3))
pd.DataFrame([dict(ativo="WIN", evento="A1", h_min=H, n=len(e), a_favor_bps=e["sig"].mean(), controle_bps=e["ctrl"].mean(),
                   efeito_bps=m, ic95_inf=lo, ic95_sup=hi, p=p, acerto=(e["sig"] > 0).mean(), anos_pos=c4, anos=len(yr),
                   confirma=bool(c1 and c2 and c3))]).to_csv(BP / "reports" / "confirmacao_a1_win.csv", index=False)
