# TEEDSI — Tópicos em Engenharia de Sistemas de Informação

Repositório da disciplina **Tópicos em Engenharia de Sistemas de Informação**, cujo tema é
**Data Science aplicada ao mercado financeiro**: uso de técnicas de *machine learning* para apoiar
decisões e operações (compra, venda e gestão de posição) em ativos negociados em bolsa.

O objetivo aqui é **aprender construindo**: cada tópico é acompanhado de um notebook ou script
reprodutível, com dados, hipótese, experimento e conclusão registrados — inclusive quando o
resultado é negativo.

> ⚠️ **Aviso**
> Este repositório tem finalidade exclusivamente educacional e de pesquisa. Nada aqui é
> recomendação de investimento. Resultados de *backtest* não garantem desempenho futuro, e a maior
> parte das estratégias que parecem lucrativas em pesquisa não sobrevive a custos, *slippage* e
> mudança de regime de mercado.

---

## Status

🚧 **Em construção.** Este README descreve o escopo planejado e serve como roteiro de estudo.

---

## Escopo do estudo

### 1. Aquisição e tratamento de dados
- Fontes de dados de mercado (cotações OHLCV, dados fundamentalistas, macroeconômicos).
- Ajustes por proventos (dividendos, splits, bonificações) e por que ignorá-los invalida o estudo.
- Tratamento de séries temporais: buracos, feriados, *survivorship bias*, dados *point-in-time*.

### 2. Análise exploratória (EDA)
- Estatísticas de retornos: caudas pesadas, assimetria, curtose, agrupamento de volatilidade.
- Estacionariedade, autocorrelação e testes (ADF, KPSS, Ljung-Box).
- Correlação entre ativos e análise de regime.

### 3. Engenharia de *features*
- Indicadores técnicos (médias móveis, RSI, MACD, bandas de Bollinger, ATR) como *features*.
- Transformações que preservam memória (diferenciação fracionária).
- Normalização e escalonamento respeitando a ordem temporal.
- Definição do alvo (*labeling*): retorno futuro, classificação direcional, *triple-barrier method*.

### 4. Modelagem
- *Baselines* obrigatórios: *buy and hold*, movimento aleatório, regra técnica simples.
- Modelos clássicos: regressão logística, árvores, *random forest*, *gradient boosting*
  (XGBoost / LightGBM).
- Séries temporais: ARIMA, GARCH para volatilidade.
- *Deep learning*: LSTM, GRU e arquiteturas baseadas em atenção.
- *Meta-labeling*: usar ML para filtrar sinais de uma estratégia primária.

### 5. Validação (o ponto mais crítico)
- Por que *k-fold* aleatório é inválido em séries temporais.
- *Walk-forward validation*, *purged k-fold* e *embargo*.
- *Data leakage*: vazamento de informação futura, o erro que mais gera resultado falso-positivo.
- *Overfitting* de *backtest* e viés de múltiplos testes (*deflated Sharpe ratio*).

### 6. *Backtest* e execução
- Simulação com custos de corretagem, emolumentos, impostos e *slippage*.
- Dimensionamento de posição e alavancagem.
- Métricas: retorno acumulado, CAGR, Sharpe, Sortino, Calmar, *max drawdown*, *hit rate*,
  fator de lucro, tempo exposto.

### 7. Gestão de risco
- *Stop* e alvo, *drawdown* máximo tolerável.
- VaR e CVaR.
- Alocação de capital entre estratégias (*risk parity*, critério de Kelly e suas limitações).

---

## Estrutura

O repositório contém um projeto por pasta. Cada projeto tem seu próprio `src/`, `tests/` e
`pyproject.toml`; o ambiente Python (`requirements.txt`, `.venv`) é compartilhado na raiz.

```text
teedsi/
├── ceo_investigator/  # agente que investiga o histórico de CEOs (Gemini + grounding)
│   ├── src/
│   └── tests/
├── bigplayer/         # estudo da atuação de grandes players no mercado
│   ├── src/
│   └── data/
├── data/              # dados compartilhados (não versionados)
│   └── raw/           # WINN_M1, WDON_M1 (candles de 1 minuto de WIN e WDO)
├── requirements.txt
└── README.md
```

Para rodar os testes de um projeto, entre na pasta dele:

```bash
cd ceo_investigator
python -m pytest
```

---

## Stack pretendida

| Área | Ferramentas |
| --- | --- |
| Linguagem | Python 3.11+ |
| Manipulação de dados | `pandas`, `numpy`, `polars` |
| Dados de mercado | `yfinance`, `pandas-datareader`, APIs de corretoras |
| Estatística | `statsmodels`, `scipy`, `arch` |
| Machine learning | `scikit-learn`, `xgboost`, `lightgbm` |
| Deep learning | `pytorch` |
| Indicadores técnicos | `pandas-ta`, `ta-lib` |
| *Backtest* | `vectorbt`, `backtrader` |
| Visualização | `matplotlib`, `seaborn`, `plotly` |
| Ambiente | `jupyter`, `uv` ou `venv` |

---

## Como começar

```bash
git clone https://github.com/icaropereira1/teedsi.git
cd teedsi

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
jupyter lab
```

Para contribuir (branches, PR para a `main` e revisão), leia o [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Princípios de trabalho

1. **Reprodutibilidade** — semente fixa, versão de dados registrada, notebook que roda do início ao fim.
2. **Ceticismo** — todo resultado bom demais é tratado como bug até que se prove o contrário.
3. **Baseline sempre** — um modelo só é interessante se bater o *buy and hold* e o acaso.
4. **Custos desde o começo** — estratégia sem custo de transação não é estratégia.
5. **Registrar o que não funcionou** — experimento negativo também é resultado.

---

## Referências de estudo

**Livros**
- *Advances in Financial Machine Learning* — Marcos López de Prado
- *Machine Learning for Algorithmic Trading* — Stefan Jansen
- *Quantitative Trading* — Ernest P. Chan
- *Options, Futures, and Other Derivatives* — John C. Hull
- *Análise Técnica dos Mercados Financeiros* — John J. Murphy

**Artigos e recursos**
- "The Probability of Backtest Overfitting" — Bailey, Borwein, López de Prado, Zhu
- Documentação do `scikit-learn` sobre validação cruzada em séries temporais
- QuantConnect / Quantopian Lectures (arquivo público)

---

## Licença

Distribuído sob a [Licença Apache 2.0](LICENSE).
