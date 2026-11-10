# %% [markdown]
# # 11 — Fluxo de investidores na B3: pessoa física x estrangeiro (divergência)
# Fonte: Dados de Mercado (https://www.dadosdemercado.com.br/fluxo). Saldo diário (compras − vendas), R$ milhões.
#
# **Duas fontes:**
# - **API** (histórico longo): defina `DADOSDEMERCADO_TOKEN`. Endpoint `GET /v1/investors`
#   (campos `date`, `foreigners`, `individuals`, `institutional`, `financial_institutions`, `other`...).
#   Não testado com token real: o formato dos valores (R$ ou R$ mi) deve ser conferido na primeira execução.
# - **Página pública** (sem token): só ~1 ano de histórico (nov/2025 em diante).
#
# **Saídas:** `data/processed/fluxo_investidores.csv` e `reports/figures/fluxo/*.png`.

# %%
import os
import re
import sys
from pathlib import Path

_here = Path.cwd()
BP = next(p for p in [_here, _here / "bigplayer", *_here.parents] if (p / "configs" / "split.toml").exists())

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
import urllib.request

import pandas as pd

OUT_CSV = BP / "data" / "processed" / "fluxo_investidores.csv"
FIG = BP / "reports" / "figures" / "fluxo"
FIG.mkdir(parents=True, exist_ok=True)
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
COLS = ["estrangeiro", "institucional", "pessoa_fisica", "inst_financeira", "outros"]


def _get(url: str, headers: dict | None = None) -> str:
    req = urllib.request.Request(url, headers=UA | (headers or {}))
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def _num(s: str) -> float:
    s = s.replace("mi", "").replace(".", "").replace(",", ".").strip()
    return float(s)


def from_page() -> pd.DataFrame:
    html = _get("https://www.dadosdemercado.com.br/fluxo")
    body = html[html.index('id="flow"'):]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, flags=re.S):
        tds = [re.sub(r"<[^>]+>|\s+", " ", t).strip() for t in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
        if len(tds) == 6 and re.fullmatch(r"\d{2}/\d{2}/\d{4}", tds[0]):
            rows.append([pd.to_datetime(tds[0], dayfirst=True)] + [_num(x) for x in tds[1:]])
    return pd.DataFrame(rows, columns=["data"] + COLS)   # R$ milhões


def from_api(token: str) -> pd.DataFrame:
    d = pd.DataFrame(json.loads(_get("https://api.dadosdemercado.com.br/v1/investors", {"Authorization": f"Bearer {token}"})))
    d = d.rename(columns={"date": "data", "foreigners": "estrangeiro", "institutional": "institucional", "individuals": "pessoa_fisica",
                          "financial_institutions": "inst_financeira", "other": "outros"})
    d["data"] = pd.to_datetime(d["data"])
    print("CONFERIR UNIDADE (primeiras linhas):\n", d.head(3))
    return d[["data"] + COLS]


token = os.environ.get("DADOSDEMERCADO_TOKEN")
df = (from_api(token) if token else from_page()).sort_values("data").reset_index(drop=True)
df.to_csv(OUT_CSV, index=False)
print(f"fonte: {'API' if token else 'página pública'} | {len(df)} pregões | {df['data'].min().date()} → {df['data'].max().date()}")

# %% [markdown]
# ## Divergência estrangeiro x pessoa física

# %%
df["pf_menos_estr"] = df["pessoa_fisica"] - df["estrangeiro"]
corr = df["estrangeiro"].corr(df["pessoa_fisica"])
roll = df["estrangeiro"].rolling(20).corr(df["pessoa_fisica"])
opostos = ((df["estrangeiro"] * df["pessoa_fisica"]) < 0).mean() * 100
print(f"correlação diária estrangeiro x PF: {corr:.2f} | dias com sinais opostos: {opostos:.0f}%")
print(df[COLS].describe().round(1).to_string())

C_E, C_PF = "#1b6ca8", "#d95f02"
fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
ax[0].axhline(0, color="gray", lw=0.6)
ax[0].plot(df["data"], df["estrangeiro"].cumsum() / 1000, color=C_E, label="Estrangeiro")
ax[0].plot(df["data"], df["pessoa_fisica"].cumsum() / 1000, color=C_PF, label="Pessoa física")
ax[0].set_ylabel("saldo acumulado (R$ bi)")
ax[0].set_title(f"Fluxo acumulado: estrangeiro x pessoa física (correlação diária {corr:.2f}; sinais opostos em {opostos:.0f}% dos dias)")
ax[0].legend(frameon=False)
ax[1].plot(df["data"], roll, color="#444", lw=1)
ax[1].axhline(0, color="gray", lw=0.6)
ax[1].set_ylabel("correlação 20 pregões")
ax[1].set_ylim(-1, 1)
fig.tight_layout()
fig.savefig(FIG / "f1_estrangeiro_x_pf.png", dpi=130)
plt.close(fig)
