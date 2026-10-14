# Resultado do Gate 1 — rodada 2 (WDO)

**Data:** 2026-10-14 · **Status:** concluído · **Veredito: nenhuma definição passa o Gate 1 (no-go para estas definições em M1)**
**Pré-registro:** `PRE_REGISTRO_GATE1_RODADA2.md` (congelado antes da execução)
**Código:** `notebooks/06_estudo_evento_r2.py`, `src/features/flow.py` · **Números:** `reports/estudo_evento_r2_wdo.csv`
**WIN:** não executado, de acordo com o pré-registro (só replica o que passar no WDO).

## 1. O que foi testado
Três definições novas, todas seguindo o fluxo, cinco horizontes cada (15 testes), no WDO, exploração.
Limite de Bonferroni sobre os 30 testes acumulados do WDO: **p < 0,0017**.

| Def. | Evento | Episódios |
|---|---|---|
| **A1** pausa com volume | `z_vol ≥ 1,5`, amplitude normal ou menor, em meio a um movimento de 15 barras; segue o movimento | 773 |
| **P1** fluxo persistente | ≥ 10 de 15 barras com `z_vol ≥ 1`, sem pico `≥ 3`; segue o movimento de 15 barras | 727 |
| **X1** pressão no extremo | 3 barras seguidas fechando perto da máxima/mínima com volume acima do normal | 772 |

## 2. Resultado
| Evento | Horizonte | N | A favor (bps) | Controle (bps) | **Efeito (bps)** | IC 95% | p | Acerto | Anos + |
|---|---|---|---|---|---|---|---|---|---|
| A1 | 1 min | 765 | +0,10 | -0,02 | **+0,12** | [-0,14; +0,38] | 0,366 | 41% | 3/6 |
| A1 | 5 min | 754 | +0,26 | -0,09 | **+0,35** | [-0,18; +0,88] | 0,202 | 47% | 4/6 |
| A1 | 15 min | 730 | +1,21 | -0,13 | **+1,34** | [+0,30; +2,36] | 0,015 | 49% | 6/6 |
| A1 | 30 min | 706 | +0,91 | -0,04 | **+0,94** | [-0,55; +2,40] | 0,208 | 47% | 5/6 |
| A1 | 60 min | 659 | +0,17 | +0,31 | **-0,14** | [-2,23; +1,98] | 0,904 | 48% | 3/6 |
| P1 | 1 min | 726 | -0,13 | -0,03 | **-0,10** | [-0,54; +0,36] | 0,678 | 41% | 2/6 |
| P1 | 5 min | 724 | -0,59 | -0,12 | **-0,46** | [-1,39; +0,40] | 0,304 | 44% | 0/6 |
| P1 | 15 min | 714 | -0,66 | -0,19 | **-0,47** | [-1,92; +0,93] | 0,498 | 48% | 2/6 |
| P1 | 30 min | 694 | -1,06 | -0,06 | **-1,00** | [-3,07; +1,02] | 0,340 | 48% | 2/6 |
| P1 | 60 min | 655 | -0,53 | +0,13 | **-0,65** | [-3,44; +2,07] | 0,629 | 46% | 2/6 |
| X1 | 1 min | 771 | -0,43 | -0,07 | **-0,36** | [-0,81; +0,10] | 0,124 | 39% | 2/6 |
| X1 | 5 min | 769 | -0,74 | -0,17 | **-0,57** | [-1,35; +0,22] | 0,153 | 42% | 3/6 |
| X1 | 15 min | 760 | -0,87 | -0,38 | **-0,49** | [-1,91; +0,95] | 0,473 | 44% | 3/6 |
| X1 | 30 min | 741 | -0,40 | -0,40 | **-0,00** | [-1,81; +1,87] | 0,998 | 46% | 3/6 |
| X1 | 60 min | 705 | -1,63 | -0,16 | **-1,47** | [-4,01; +0,98] | 0,261 | 47% | 1/6 |

**Critérios (todos obrigatórios):** efeito > 0 com p < 0,0017; mesmo sinal em ≥ 4 de 6 anos; N ≥ 300; efeito ≥ 1 tick (0,95 bps).

| | Resultado |
|---|---|
| Testes que passam o Gate 1 | **0 de 15** |
| Menor p | 0,0145 (A1, 15 min, efeito +1,34 bps) |
| Testes com efeito > 0 | 4 de 15 (todos de A1) |
| Efeito mediano de P1 / X1 (bps) | -0,47 / -0,49 |

## 3. Leitura por definição
- **P1 (fluxo persistente): sem sinal e sinal oposto.** Efeito negativo nos 5 horizontes, com acerto de 41% a 48%. A hipótese de "ordem fatiada, volume moderado e constante" não se sustenta com M1.
- **X1 (pressão no extremo): sem sinal.** Negativo ou nulo em todos os horizontes.
- **A1 (pausa com volume): a única com sinal na direção certa, mas não passa.**
  - Efeito de +1,34 bps em 15 min, IC 95% [+0,30; +2,37], p = 0,0145, positivo em 6 dos 6 anos.
  - Passaria o limite habitual de 0,05, mas **não o limite corrigido de 0,0017**. Entre os 15 testes desta rodada, um p tão baixo aparece por acaso em cerca de 20% das vezes (0,0145 × 15 ≈ 0,22 ajustado só pela rodada).
  - Os horizontes vizinhos são menos fortes (5 min: +0,35, p = 0,20; 30 min: +0,94, p = 0,21; 60 min: −0,14).
  - A taxa de acerto fica em 48,8%: o efeito vem de poucos ganhos grandes, não de acertar mais vezes. Isso costuma ser frágil.

## 4. Por que, de novo, não deu certo
Mesmos limites da rodada 1: candle de 1 minuto não identifica agressor, e a direção continua sendo inferida do preço.
As três definições novas mexeram no **filtro** do evento (absorção, persistência, fechamento), mas a **direção** e o
**dado** são os mesmos. Os testes agora dizem mais: o volume persistente (P1), que era a hipótese mais próxima de
"ordem grande fatiada", não mostrou nada, o que pesa contra a ideia com este nível de dado.

## 5. O que fazer com A1 (decisão do grupo)
- **Não é "go"** pelo critério pré-registrado, e este documento não deve ser lido como se fosse.
- É um **candidato** a confirmação. Uma confirmação limpa pede um teste novo, pré-registrado, **uma única
  definição e um único horizonte** (A1 em 15 min), em dado que não participou da escolha:
  - **WIN** (mesma lógica, outro ativo): 1 teste, limite 0,05.
  - **Hold-out do WDO**: só na Fase 6, não agora.
- Se o WIN também mostrar efeito positivo (e ≥ 1 tick, ~0,41 bps), A1 ganha peso. Se não, a rodada 2 fecha
  como no-go e a decisão passa a ser dado tick a tick ou encerrar.
- Nota de método: rodar A1 no WIN agora **foge do pré-registro** (que só replicava o que passasse), então só
  deve ser feito com aprovação explícita e registrado como confirmação exploratória.

## 6. Contador de testes (para o limite de Bonferroni)
| Rodada | Testes por ativo | Acumulado | Limite |
|---|---|---|---|
| 1 | 15 | 15 | 0,0033 |
| 2 | 15 | 30 | 0,0017 |
