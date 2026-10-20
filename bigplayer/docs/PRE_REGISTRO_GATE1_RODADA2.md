# Pré-registro do Gate 1 — rodada 2 (APROVADO e CONGELADO em 2026-10-14)

**Status:** aprovado pelo grupo. A partir daqui, nenhum limite ou definição muda olhando o resultado.
**Rodada anterior:** `RESULTADO_GATE1_RODADA1.md` (sem sinal; 15 testes por ativo já gastos).
**Execução:** `notebooks/06_estudo_evento_r2.py`. Resultado em `reports/estudo_evento_r2_<ativo>.csv`.

## 0. Decisões do grupo incorporadas
1. **Só a favor:** p-valor bilateral (como na rodada 1), mas **só efeito positivo conta como passe**. Efeito negativo robusto é anotado como achado, não como Gate 1.
2. **Seguir o fluxo, por enquanto:** nenhuma definição opera contra o movimento. Por isso o A1 original (direção contrária) foi trocado por uma versão de continuação (ver seção 2). A versão contrária fica para uma rodada futura.
3. **Cinco horizontes** {1, 5, 15, 30, 60} min para as 3 definições.
4. **Replicação no WIN só se passar no WDO.** WIN é confirmação, não busca.

## 1. O que muda em relação à rodada 1
A rodada 1 testou **pico de volume** e seguiu a direção do preço. Não deu sinal. Cada definição abaixo ataca uma hipótese do porquê (seção 4 do resultado da rodada 1):

| Def. | Ideia | Hipótese que ataca |
|---|---|---|
| **A1 — Pausa com volume** | muito volume e preço quase parado, no meio de um movimento; o movimento continua | 5 (esforço × resultado) |
| **P1 — Fluxo persistente** | volume moderado e sustentado por 15 barras, sem pico único | 2 (ordem fatiada ≠ notícia) |
| **X1 — Pressão no extremo** | 3 barras seguidas fechando perto da máxima (ou da mínima) com volume acima do normal | 1 e 5 (direção por onde a barra fecha) |

## 2. Definições exatas
Só passado e só barras `usable` com `lb_ok` (20 pregões anteriores no mesmo trecho). "Mesmo minuto" = mesma hora:minuto nos 20 pregões anteriores. "N barras" = N barras com negócio no mesmo pregão (minutos sem negócio não existem).

Variáveis:
- `z_vol`: como na rodada 1.
- `z_rng`: z-score do log de `max(high − low, 1 tick)` contra o mesmo minuto dos 20 pregões anteriores.
- `clv = (2·close − high − low) / (high − low)`, de −1 (fechou na mínima) a +1 (fechou na máxima); 0 se `high = low`.
- `r15`: retorno em bps de `close` contra o `close` 15 barras antes, no mesmo pregão. `ret3`: idem, 3 barras.
- `lim15`: média, nos 20 pregões anteriores, da mediana de `|r15|` da mesma hora (só passado).

| Def. | Condição do evento | Direção da posição |
|---|---|---|
| **A1** | `z_vol ≥ 1,5` **e** `z_rng ≤ 0` **e** `|r15| ≥ lim15` | sinal de `r15` (**continuação**) |
| **P1** | em pelo menos 10 das últimas 15 barras `z_vol ≥ 1`, **e** nenhuma delas com `z_vol ≥ 3` | sinal de `r15` |
| **X1** | nas 3 últimas barras: `z_vol ≥ 1`, `clv` com o mesmo sinal e `|clv| ≥ 0,5` | sinal de `clv` |

**Execução e estatística:** iguais à rodada 1 (entrada na abertura da barra seguinte, saída no fechamento de `t + h` no mesmo pregão, cooldown de 30 min, bootstrap por dia com 4000 repetições).

**Controle pareado** (esclarecimento feito antes de rodar): barras comuns da **mesma hora** e do **mesmo quintil** de |retorno|, com a mesma regra de direção:
- A1 e P1: quintil de `|r15|`; controle = barras com `z_vol < 1`, direção = sinal de `r15`.
- X1: quintil de `|ret3|`; controle = barras com `z_vol < 1` e `|clv| ≥ 0,5`, direção = sinal de `clv`.

## 3. Tamanho da amostra (contagem prévia, sem olhar retorno)
Episódios depois do cooldown, exploração (a contagem usou a mediana da amostra toda para `lim15`; a regra final usa só o passado e pode mudar o número um pouco):

| Def. | WDO | WIN |
|---|---|---|
| A1 | ~780 | ~680 |
| P1 | ~730 | ~735 |
| X1 | ~770 | ~940 |

A versão mais restrita de A1 (`z_vol ≥ 2`, `|r15| ≥ P75`) teve só ~110 episódios e foi descartada **pelo tamanho**. Regra: com **menos de 300 episódios** na execução, o resultado é *inconclusivo*, não negativo.

## 4. Múltiplos testes
- Por definição: 3 × 5 horizontes = 15 testes por ativo.
- Acumulado no WDO: 15 (rodada 1) + 15 (rodada 2) = **30 testes → limite de Bonferroni p < 0,0017**.
- WIN: só replica o que passar no WDO. Uma replicação por definição aprovada, com efeito no mesmo sinal e p < 0,05.

## 5. Critério do Gate 1 (todos obrigatórios, por definição)
1. Efeito **> 0** com **p < 0,0017** no WDO, em pelo menos um horizonte.
2. Mesmo sinal do efeito em **4 ou mais dos 6 anos** da exploração (WDO) naquele horizonte.
3. Mínimo de 300 episódios.
4. Efeito ≥ **1 tick** (0,95 bps no WDO) para seguir ao Gate 2. Abaixo disso, o sinal pode ser real, mas sem uso prático.
5. Replicação no WIN: mesmo sinal e p < 0,05.

Se **nenhuma** definição cumprir 1 a 3 no WDO: Gate 1 = *no-go* para dado M1, e a decisão do grupo passa a ser sobre mudança de dado (tick a tick) ou encerramento, não sobre mais definições.

## 6. O que NÃO será feito
- Mudar `z`, janelas ou limites depois de ver resultados.
- Usar o hold-out.
- Adicionar uma 4ª definição sem novo pré-registro e novo cálculo do limite.
- Tratar efeito negativo significativo como "go".
