# Arquitetura — Seguidor de Big Players (Mini Dólar)

> Documento vivo. Os passos da seção 8 são marcados `[x]` conforme concluídos; sempre se trabalha no primeiro passo `[ ]` da fase atual.

## 1. Objetivo

Detectar a atuação de grandes operadores (muitos contratos) no mercado futuro e seguir a direção deles: se compram, compramos; se vendem, vendemos. Meta: obter resultado semelhante ao do big player usando capital menor. Capital-alvo: **não definido por ora**. Objetivo de realismo: **o mais real possível** (custos, latência e execução modelados; resultado de backtest deve ser transferível para operação real).

## 2. Ativo e dados

**Ativo escolhido: Mini Dólar (WDO).** Arquivo: `WDO$N_M1.csv` (candles de 1 min, 17/09/2020 → 01/04/2026, ~717 mil linhas).

Motivos:
- O fluxo do WDO é dominado por participantes institucionais (bancos, estrangeiros, gestoras). O sinal de "operador grande" tende a ser menos diluído por varejo do que no mini índice.
- Volume por minuto menor que o do WIN: um lote grande é mais visível em relação ao fluxo normal.
- Um único ativo reduz o escopo e a complexidade da primeira versão.

**Mini Índice (`WIN$N_M1.csv`, 15/10/2020 → 25/09/2026) fica reservado** como teste de replicação: se o método funcionar no WDO, rodamos o mesmo pipeline no WIN, sem mudar o código, só a configuração. Não entra no escopo inicial.

Dados com problemas conhecidos (verificar na Fase 1): fuso horário do servidor, coluna `SPREAD` inconsistente (500 → 0), rolagem de contrato no `$N`, definição exata de `VOL` vs `TICKVOL`.

Se os dados se mostrarem insuficientes ou inconsistentes, buscamos outras fontes (tick a tick, dados B3). A arquitetura abaixo não depende da fonte.

## 3. Premissa central

Com candles de 1 minuto, "big player" **não é observável; é uma hipótese inferida**. O que detectamos é um **evento de fluxo anômalo** compatível com execução fatiada de uma ordem grande. O resultado do projeto é medir quanto esse evento prevê o preço, não identificar um agente real.

## 4. Modelagem do problema

### Tese econômica
Um operador grande não executa tudo de uma vez (o preço andaria contra ele). Ele fatia a ordem ao longo de minutos ou horas, o que deixa rastro:
- fluxo direcional persistente (autocorrelação do fluxo de ordens);
- volume acima do normal para o horário;
- preço desproporcional ao esforço ou, ao contrário, muito volume com preço parado (absorção).

Seguir funciona se detectarmos o evento **antes** de a execução terminar. Capital pequeno entra e sai sem impacto, e essa é a vantagem do seguidor.

### Estado latente
```
Estado oculto:  intenção/posição do big player  S(t) ∈ {comprando, vendendo, ausente}
Observáveis:    preço (OHLC), VOL, TICKVOL
Tarefa 1  Detecção  : estimar P(S(t) | dados até t)
Tarefa 2  Decisão   : traduzir a estimativa em LONG / SHORT / FLAT, com tamanho e saída
Tarefa 3  Execução  : executar a um custo realista
```

### Três perguntas validáveis separadamente
1. **Detecção.** O evento de fluxo anômalo existe e prevê o retorno futuro? (estudo de evento, sem estratégia)
2. **Seguimento.** Qual o horizonte e o tamanho do movimento restante depois do evento?
3. **Viabilidade.** O movimento restante sobrevive a custos, slippage e latência?

Cada pergunta é um *gate*: se a resposta for não, não se constrói a camada seguinte.

## 5. Arquitetura computacional

### Princípio: o mesmo núcleo de decisão em pesquisa, backtest e produção
O sistema é **orientado a eventos** (uma barra fechada = um evento). O código que decide é idêntico em todos os modos; só mudam os componentes das bordas (fonte de dados e broker).

```
 ┌── Camada de dados (batch/offline) ──────────────────────────────┐
 │ CSV bruto → Ingestão → Validação → Limpeza/Calendário →          │
 │ Contrato contínuo → Parquet versionado                           │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │  stream de Bar
 ┌── Núcleo de decisão (idêntico em todos os modos) ───────────────┐
 │ FeatureEngine → Detector → SignalGenerator → RiskManager         │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │  Order
 ┌── Broker (interface única) ─────────────────────────────────────┐
 │  SimulatedBroker (backtest/paper)  |  LiveBroker (produção)      │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │  Fill, posição, PnL
 ┌── Avaliação / Monitoramento ────────────────────────────────────┐
 │ Métricas, comparação com benchmarks, drift, relatórios           │
 └─────────────────────────────────────────────────────────────────┘
```

### Contratos entre módulos

| Módulo | Entrada | Saída | Regra |
|---|---|---|---|
| `DataSource` | arquivo / feed | stream de `Bar` | mesmo tipo em backtest e live |
| `FeatureEngine` | `Bar` (somente passado) | vetor de features | proibido usar dado futuro; só barras fechadas |
| `Detector` | features | `P(comprando/vendendo/ausente)` + confiança | treino somente no passado (walk-forward) |
| `SignalGenerator` | saída do detector | `LONG / SHORT / FLAT` | sem lógica de tamanho |
| `RiskManager` | intenção + estado da conta | `Order` com tamanho e stop | único módulo que conhece capital |
| `Broker` | `Order` | `Fill` | `Simulated` e `Live` implementam a mesma interface |
| `Evaluator` | histórico de trades | métricas | sempre contra benchmarks (aleatório, buy&hold) |

Cada módulo é substituível sem alterar os demais (ex.: detector por regras → detector por ML), o que permite comparar versões lado a lado.

### Modos de execução
1. **Pesquisa/EDA:** notebooks sobre Parquet.
2. **Backtest:** `DataSource` histórico + `SimulatedBroker`.
3. **Paper trading:** `DataSource` ao vivo + `SimulatedBroker`.
4. **Live:** `DataSource` ao vivo + `LiveBroker`.

## 6. Regras de realismo (invariantes do projeto)

- **Sem look-ahead:** sinal da barra fechada em `t` executa no **open de `t+1`**, nunca no close de `t`.
- **Custos explícitos:** corretagem, emolumentos B3, slippage (função de volume e volatilidade), latência configurável. Não confiar na coluna `SPREAD` do CSV.
- **Contrato contínuo tratado:** saltos de rolagem ajustados ou barras de rolagem marcadas e excluídas.
- **Calendário B3:** pregão, leilões, feriados, horário de verão.
- **Validação walk-forward** + **hold-out final travado**, que não é tocado até a avaliação final.
- **Registro de todos os experimentos** (parâmetros, versão dos dados, resultado), para controlar múltiplos testes e falsos positivos.
- **Nada hardcoded:** parâmetros em `configs/`.

## 7. Estrutura no repositório

Projeto `bigplayer/` dentro do repositório `teedsi` (um projeto por pasta; ambiente Python compartilhado na raiz). Dados brutos em `data/raw/` na raiz (não versionados).

```
teedsi/
├── data/raw/            # WDO$N_M1.csv, WIN$N_M1.csv (fora do git)
└── bigplayer/
    ├── data/
    │   ├── interim/     # limpo, calendário, contrato contínuo
    │   └── processed/   # features / labels
    ├── src/
    │   ├── ingestion/
    │   ├── cleaning/
    │   ├── features/
    │   ├── detection/
    │   ├── signals/
    │   ├── risk/
    │   ├── execution/   # Broker (Simulated / Live)
    │   ├── backtest/
    │   └── evaluation/
    ├── notebooks/       # scripts .py com células "# %%"
    ├── configs/
    ├── tests/
    └── docs/            # este documento, decisões, dicionário de dados
```

## 8. Plano de passos

Regra: só se avança de fase quando os critérios de saída estão cumpridos. Os *gates* (🚦) exigem decisão explícita go / no-go registrada na seção 9.

### Fase 0 — Fundação
- [x] Definir objetivo e tese econômica
- [x] Modelar o problema (estado latente, três perguntas)
- [x] Escolher o ativo (WDO)
- [x] Documentar arquitetura inicial (este documento)
- [x] Inicializar repositório git, ambiente Python (venv) e dependências
- [x] Criar esqueleto de pastas (interfaces `Bar`/`Order`/`Fill`/`Broker` ficam para a Fase 5)

**Saída:** repositório rodando, interfaces definidas, equipe com o mesmo ambiente.

### Fase 1 — Dados
- [x] Converter CSV para Parquet (ingestão com validação de schema) — `notebooks/00`
- [x] Perfilar os dados: período, gaps, duplicatas, outliers, barras sem negócio — `notebooks/01`
- [x] Determinar o fuso horário real do timestamp (alinhar com o pregão B3) — é horário de Brasília
- [x] Definir `VOL` vs `TICKVOL` e avaliar a utilidade de `SPREAD` — `SPREAD` descartado (não confiável)
- [ ] Construir o calendário de pregão B3 (sessões, feriados)
- [x] Tratamento dos buracos nos dados (jun–set/2023 etc.) — decidido: ignorar
- [ ] Tratar rolagem do contrato contínuo
- [ ] Escrever o dicionário de dados em `docs/`
- [x] Definir e **travar** a divisão exploração / hold-out (12 meses; `configs/split.toml`)

**Saída:** dataset limpo, versionado e documentado; hold-out separado.

### Fase 2 — Hipótese de sinal 🚦
- [ ] Definir features de fluxo institucional (volume anômalo por horário, tamanho médio do negócio `VOL/TICKVOL`, esforço × resultado, absorção, etc.)
- [ ] Definir operacionalmente o "evento de big player" (regra explícita e parametrizada)
- [ ] Estudo de evento: retorno futuro condicional ao evento, em vários horizontes
- [ ] Testar significância estatística e comparar com eventos aleatórios (baseline)
- [ ] **Gate 1:** há sinal? Se não, revisar features/definição ou decidir buscar outro dado (tick a tick)

**Saída:** evidência (ou ausência) de que o evento prevê o preço.

### Fase 3 — Detector
- [ ] Baseline por regras
- [ ] Modelo de ML (comparar com o baseline)
- [ ] Validação walk-forward
- [ ] Avaliar calibração e estabilidade ao longo do tempo (regimes)

**Saída:** detector com desempenho fora da amostra superior ao baseline.

### Fase 4 — Estratégia de seguimento
- [ ] Regra de entrada a partir do sinal
- [ ] Regra de saída (horizonte, stop, fim de execução inferido)
- [ ] Dimensionamento de posição (parametrizado, sem capital-alvo fixo)

### Fase 5 — Simulação realista 🚦
- [ ] Implementar a interface `Broker` e o `SimulatedBroker`
- [ ] Modelar custos, slippage e latência
- [ ] Motor de backtest orientado a eventos
- [ ] Testes unitários de no-look-ahead
- [ ] **Gate 2:** o edge sobrevive aos custos? Se não, rever horizonte e frequência

### Fase 6 — Avaliação e robustez
- [ ] Métricas: retorno, Sharpe, drawdown, hit-rate, turnover
- [ ] Benchmarks: aleatório e buy & hold
- [ ] Análise de sensibilidade (custos, latência, parâmetros)
- [ ] Avaliação final **uma única vez** no hold-out

### Fase 7 — Operação (opcional, quando o resultado justificar)
- [ ] `DataSource` ao vivo
- [ ] Paper trading
- [ ] `LiveBroker` e monitoramento

### Extensão futura
- [ ] Replicar o pipeline no Mini Índice (`WIN$N_M1.csv`) trocando apenas a configuração

## 9. Registro de decisões

| Data | Decisão | Motivo |
|---|---|---|
| 2026-10-07 | Ativo inicial: **WDO** (WIN reservado para replicação) | Fluxo mais institucional; lotes grandes mais visíveis; escopo menor |
| 2026-10-07 | "Big player" = evento de fluxo anômalo inferido (hipótese) | Candle M1 não identifica agentes |
| 2026-10-07 | Arquitetura orientada a eventos, mesmo núcleo em backtest e live | Realismo máximo; evitar divergência pesquisa/produção |
| 2026-10-07 | Sem divisão de tarefas por pessoa; avanço por checklist de fases | Definido pela equipe |
| 2026-10-07 | Dados atuais mantidos; outras fontes só se forem inconsistentes | Definido pela equipe |
| 2026-10-07 | Hold-out = últimos 12 meses (a partir de 2025-04-02), trancado até a Fase 6 | Teste final honesto; EDA só vê a exploração |
| 2026-10-07 | Buracos nos dados (jun–set/2023 etc.): ignorar | Decisão da equipe |
| 2026-10-07 | `SPREAD` do CSV não será usado; custos modelados por fora | Valores inconsistentes entre anos (500 → 0/1) |

## 10. Riscos

- Dado M1 pode não conter sinal suficiente → mitigação: Gate 1 e possibilidade de dados tick a tick.
- Overfitting e múltiplos testes → walk-forward, hold-out travado, registro de experimentos.
- Custos maiores que o edge → Gate 2.
- Rolagem e fuso horário mal tratados contaminam todo o resultado → Fase 1 antes de qualquer modelagem.
