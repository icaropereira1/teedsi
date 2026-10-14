# Resumo do que foi feito em 2026-10-14 (para quem vai continuar)

> Leia primeiro `STATUS.md`. Este arquivo conta **o que mudou nesta sessão** e **onde está cada coisa**.
> Branch: `feat/bigplayer-win-eda` (a partir da `main` com o PR #4 já mergeado).

## Em 5 linhas
1. Repetimos a análise inicial de dados para o **mini índice (WIN)**; o pipeline agora roda para WDO e WIN.
2. **Fase 1 (dados) concluída:** calendário B3, buracos marcados, rolagem marcada, dicionário de dados, dataset limpo.
3. **Fase 2 (sinal):** 6 definições de "evento de big player" testadas em 2 ativos. **Nenhuma passou.**
4. Um candidato (A1) foi confirmado em outro ativo e **não confirmou** (p = 0,176).
5. **Gate 1 em dados de 1 minuto: no-go.** A decisão sobre o que fazer agora é do grupo (seção 5).

## 1. Como rodar para cada ativo
O ativo é escolhido pela variável `BIGPLAYER_ASSET` (`WDO` por padrão, ou `WIN`). A partir de `bigplayer/`:
```bash
export BIGPLAYER_ASSET=WIN                       # ou WDO
../.venv/bin/python notebooks/00_carga_e_split.py
MPLBACKEND=Agg ../.venv/bin/python notebooks/01_qualidade_dados.py
../.venv/bin/python notebooks/03_calendario_buracos.py
../.venv/bin/python notebooks/04_dataset_limpo.py     # gera data/interim/<ativo>_m1_limpo.parquet
../.venv/bin/python notebooks/05_estudo_evento.py     # rodada 1
../.venv/bin/python notebooks/06_estudo_evento_r2.py  # rodada 2
../.venv/bin/python -m pytest                         # 15 testes
```
Os CSVs brutos ficam em `data/raw/` (fora do git). Os parquets em `bigplayer/data/` também não vão para o git:
regenere com os notebooks 00 e 04. O `notebooks/07_confirmacao_a1_win.py` força o WIN sozinho.

## 2. O que mudou no código
| Arquivo | O que faz |
|---|---|
| `configs/split_win.toml` | configuração do WIN (tick 5, hold-out a partir de 2025-09-26, **a confirmar pelo grupo**) |
| `src/ingestion/loader.py` | ativo por `BIGPLAYER_ASSET`; `load_clean()` |
| `src/cleaning/calendar.py` | sessão, feriados B3, quarta de cinzas, dias de rolagem |
| `src/cleaning/holes.py` | buracos, `usable`, `segment`, `roll_day`, `lookback_ok` |
| `src/features/flow.py` | `z_vol`, `z_lot`, `z_rng`, `clv`, `r15`... (só passado) |
| `src/evaluation/event_study.py` | retorno futuro sem look-ahead e bootstrap por dia |
| `notebooks/03` a `07` | calendário, dataset limpo, estudos de evento e confirmação |
| `tests/` | 15 testes (split, calendário, buracos, estudo de evento, features) |

## 3. Fase 1 — dados (resumo)
- **Buracos reais** (dias úteis sem dado), iguais nos dois ativos em local, diferentes em tamanho:
  WDO 6 + 10 + 75 pregões; WIN 12 + 9 + 93 pregões (o maior é jun–set/out de 2023). Marcados, não removidos.
- **Rolagem:** o contínuo tem um salto de carry na troca de contrato. WIN: +1,49% (quarta mais próxima do dia 15
  dos meses pares). WDO: +0,36% (último pregão do mês). **Nunca usar retorno que cruze a abertura de `roll_day`.**
- **Sessão:** abre 09:00; fecha 17:59/18:29 (WDO) ou 17:54/18:24 (WIN); curta no horário de verão dos EUA até 2023, longa desde 2024.
- **Descartados (`usable = False`):** barras fora da sessão e pregões parciais: 0,10% (WDO) e 0,01% (WIN).
- **`SPREAD` do CSV não serve.** Detalhes em `DICIONARIO_DADOS.md`.

## 4. Fase 2 — estudo de evento (resumo)
Pergunta: depois de um minuto de fluxo anômalo, o preço continua na direção dele mais que num minuto comum parecido?
Metodologia: entrada na abertura da barra seguinte, saída em 1/5/15/30/60 min, mesmo pregão, controle pareado
por hora e tamanho de movimento, bootstrap por dia, correção de Bonferroni. Tudo pré-registrado antes de rodar.

| Rodada | Definições | Testes passam | Menor p | Documento |
|---|---|---|---|---|
| 1 | E1 volume ≥ 3σ · E2 + lote alto · E3 volume sustentado 5 barras | 0 de 15 (WDO) e 0 de 15 (WIN) | 0,065 | `RESULTADO_GATE1_RODADA1.md` |
| 2 | A1 pausa com volume · P1 fluxo persistente · X1 pressão no extremo | 0 de 15 (WDO) | 0,0145 (A1, 15 min) | `RESULTADO_GATE1_RODADA2.md` |
| Confirmação | A1 em 15 min no WIN | **não confirma** (+0,95 bps, p = 0,176) | — | `RESULTADO_CONFIRMACAO_A1_WIN.md` |

**Por que não funcionou (hipóteses, não testadas):** o candle de 1 min não mostra quem negocia (a direção vem do preço),
o pico de volume costuma ser notícia e não ordem fatiada, entramos depois do movimento e os custos de 1 a 3 bps
já comem qualquer efeito pequeno.

## 5. Decisões e pendências para o grupo
1. **Dado tick a tick** (com agressor comprador/vendedor): é a continuação mais coerente com o plano. Falta descobrir fonte e custo.
2. **Nova rodada em M1:** só com hipótese nova de fundo. Cada teste extra piora o limite de Bonferroni (hoje p < 0,0017).
3. **Encerrar** e entregar o resultado negativo documentado.
4. **Confirmar** o corte do hold-out do WIN (2025-09-26).
5. O notebook 02 (gráficos de slide) ainda é só do WDO; as anotações são fixas.

## 6. Regras que valem daqui para frente
- Features só com passado; sinal da barra `t` executa no open de `t+1`.
- Filtrar por `usable`; janelas de N pregões só onde `day_in_segment > N`.
- Cada nova definição é escrita **antes** de rodar e soma testes ao limite de Bonferroni.
- Hold-out só na Fase 6, uma única vez.
