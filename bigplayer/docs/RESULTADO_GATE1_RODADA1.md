# Resultado do Gate 1 — rodada 1 (estudo de evento, WDO e WIN)

**Data:** 2026-10-14 · **Status:** concluído · **Veredito: sem sinal (no-go) nas 3 definições pré-registradas**
**Código:** `notebooks/05_estudo_evento.py`, `src/features/flow.py`, `src/evaluation/event_study.py`
**Números brutos:** `reports/estudo_evento_wdo.csv`, `reports/estudo_evento_win.csv` (congelados nesta rodada; a rodada 2 deve gravar em arquivos novos)

> Este documento registra um resultado **negativo** de propósito. Ele conta como resultado do projeto:
> mostra o que foi testado, como, e por que não funcionou, para que as próximas rodadas não repitam o
> mesmo teste nem inflem os falsos positivos.

## 1. Pergunta
Quando aparece um minuto de fluxo anômalo (compatível com um operador grande executando ordem), o preço
continua na direção desse fluxo nos minutos seguintes, mais do que continuaria em um minuto comum parecido?

Se a resposta fosse sim, seguir o fluxo teria base. Se for não, as camadas seguintes (detector, estratégia,
simulação) não devem ser construídas (Gate 1 do `ARCHITECTURE.md`).

## 2. Desenho (pré-registrado antes de olhar os resultados)
| Item | Definição |
|---|---|
| Dados | `<ativo>_m1_limpo.parquet`, só exploração, só barras `usable`; hold-out intocado |
| Período | WDO: 2020-09 → 2025-04-01 · WIN: 2020-10 → 2025-09-25 (buracos marcados; janelas não os atravessam) |
| `z_vol` | z-score do log do volume contra o **mesmo minuto** dos 20 pregões anteriores (só passado, mesmo trecho sem buraco) |
| `z_lot` | idem para o lote médio por negócio (`VOL/TICKVOL`) |
| **E1** | `z_vol ≥ 3`; direção = sinal de `close − open` da barra |
| **E2** | `z_vol ≥ 3` **e** `z_lot ≥ 1`; mesma direção |
| **E3** | média de `z_vol` nas 5 últimas barras `≥ 2`; direção = sinal do retorno de 5 barras |
| Episódio | depois de um evento, ignora novos por 30 min no mesmo pregão (sem sobreposição) |
| Execução | entra na **abertura da barra seguinte**, sai no **fechamento de t+h**, h ∈ {1, 5, 15, 30, 60} min, mesmo pregão (nunca cruza `roll_day`) |
| Controle | barras comuns (`z < 1`) da mesma hora e do mesmo quintil de |retorno|, com a mesma regra de direção |
| Efeito | retorno a favor da direção do evento **menos** o do controle pareado, em bps (1 bp = 0,01%) |
| Incerteza | bootstrap por dia (4000), pois minutos do mesmo dia não são independentes |
| Múltiplos testes | 15 testes por ativo → **limite de Bonferroni p < 0,0033** |
| Critério do Gate 1 | efeito > 0 com p < 0,0033 em algum horizonte **e** mesmo sinal na maioria dos anos |

## 3. Resultado

### 3.1 Resumo
| | WDO | WIN |
|---|---|---|
| Episódios E1 / E2 / E3 | 1.619 / 655 / 849 | 2.140 / 795 / 925 |
| Testes que passam o critério | **0 de 15** | **0 de 15** |
| Menor p-valor | 0,069 | 0,065 |
| Maior efeito positivo (bps) | +0,29 (p = 0,70) | +1,46 (p = 0,15) |
| Efeito mediano entre os 15 testes (bps) | -0,35 | -0,27 |
| Testes com efeito negativo | 13 de 15 | 10 de 15 |
| Taxa de acerto (faixa) | 38% a 48% | 43% a 49% |
| Meia-largura mediana do IC 95% (bps) | 1,2 | 1,3 |
| Custo de 1 tick (bps) | ~0,95 | ~0,41 |

### 3.2 WDO — mini dólar
| Evento | Horizonte | N | A favor (bps) | Controle (bps) | **Efeito (bps)** | IC 95% | p | Acerto |
|---|---|---|---|---|---|---|---|---|
| E1 | 1 min | 1.615 | -0,35 | -0,07 | **-0,28** | [-0,59; +0,02] | 0,069 | 39% |
| E1 | 5 min | 1.599 | -0,62 | -0,09 | **-0,53** | [-1,09; +0,05] | 0,074 | 43% |
| E1 | 15 min | 1.556 | -0,56 | -0,23 | **-0,34** | [-1,26; +0,60] | 0,474 | 45% |
| E1 | 30 min | 1.501 | -0,78 | -0,20 | **-0,58** | [-1,84; +0,60] | 0,360 | 45% |
| E1 | 60 min | 1.406 | -1,04 | -0,14 | **-0,90** | [-2,79; +0,99] | 0,321 | 46% |
| E2 | 1 min | 650 | -0,16 | -0,07 | **-0,08** | [-0,56; +0,42] | 0,720 | 38% |
| E2 | 5 min | 644 | -0,45 | -0,11 | **-0,35** | [-1,20; +0,51] | 0,427 | 43% |
| E2 | 15 min | 606 | -0,02 | -0,22 | **+0,20** | [-1,29; +1,66] | 0,794 | 48% |
| E2 | 30 min | 571 | -0,51 | -0,22 | **-0,30** | [-2,19; +1,56] | 0,757 | 46% |
| E2 | 60 min | 524 | -1,37 | -0,16 | **-1,21** | [-3,96; +1,60] | 0,414 | 47% |
| E3 | 1 min | 847 | -0,46 | -0,09 | **-0,37** | [-0,90; +0,15] | 0,152 | 41% |
| E3 | 5 min | 844 | -0,70 | -0,21 | **-0,49** | [-1,43; +0,45] | 0,290 | 42% |
| E3 | 15 min | 829 | -0,12 | -0,41 | **+0,29** | [-1,27; +1,80] | 0,697 | 46% |
| E3 | 30 min | 812 | -0,38 | -0,30 | **-0,08** | [-2,02; +1,81] | 0,978 | 46% |
| E3 | 60 min | 765 | -1,27 | -0,06 | **-1,21** | [-3,84; +1,41] | 0,347 | 47% |

### 3.3 WIN — mini índice
| Evento | Horizonte | N | A favor (bps) | Controle (bps) | **Efeito (bps)** | IC 95% | p | Acerto |
|---|---|---|---|---|---|---|---|---|
| E1 | 1 min | 2.137 | -0,11 | +0,05 | **-0,16** | [-0,48; +0,16] | 0,337 | 45% |
| E1 | 5 min | 2.119 | -0,17 | +0,03 | **-0,21** | [-0,85; +0,46] | 0,545 | 47% |
| E1 | 15 min | 2.071 | -0,78 | +0,01 | **-0,79** | [-1,80; +0,22] | 0,132 | 45% |
| E1 | 30 min | 1.995 | -0,89 | +0,15 | **-1,05** | [-2,36; +0,19] | 0,106 | 46% |
| E1 | 60 min | 1.901 | -1,37 | +0,12 | **-1,50** | [-3,19; +0,18] | 0,086 | 46% |
| E2 | 1 min | 791 | +0,05 | +0,04 | **+0,00** | [-0,52; +0,60] | 0,984 | 44% |
| E2 | 5 min | 780 | +0,56 | +0,01 | **+0,55** | [-0,54; +1,80] | 0,358 | 46% |
| E2 | 15 min | 755 | -0,27 | -0,00 | **-0,27** | [-1,74; +1,29] | 0,728 | 47% |
| E2 | 30 min | 727 | +1,60 | +0,14 | **+1,46** | [-0,53; +3,52] | 0,153 | 49% |
| E2 | 60 min | 680 | +1,03 | +0,15 | **+0,88** | [-2,02; +3,59] | 0,546 | 48% |
| E3 | 1 min | 921 | +0,10 | -0,03 | **+0,13** | [-0,46; +0,74] | 0,681 | 44% |
| E3 | 5 min | 913 | -1,04 | -0,16 | **-0,88** | [-2,08; +0,30] | 0,144 | 43% |
| E3 | 15 min | 899 | -1,76 | -0,12 | **-1,64** | [-3,42; +0,09] | 0,065 | 45% |
| E3 | 30 min | 876 | -2,17 | -0,16 | **-2,01** | [-4,24; +0,28] | 0,081 | 44% |
| E3 | 60 min | 828 | -2,57 | -0,28 | **-2,28** | [-5,46; +0,75] | 0,148 | 43% |

**Como ler:** "A favor" é o retorno médio de quem seguiu a direção do evento. "Controle" é o que uma barra comum
parecida teria dado. "Efeito" é a diferença; é ele que mede se o evento tem informação. IC 95% que contém 0 e
p acima de 0,0033 significam que **não dá para distinguir o efeito de ruído**. Acerto abaixo de 50% quer dizer que
a posição a favor do evento perdeu mais vezes do que ganhou.

## 4. Por que não deu certo

Há fatos medidos e hipóteses. Mantemos separados.

### O que os números mostram (medido)
1. **Não há continuação.** A taxa de acerto fica abaixo de 50% em todos os 30 testes (máximo 49%), e a
   mediana do efeito é -0,35 bps no WDO e -0,27 no WIN. Seguir o evento não bateu barras comuns.
2. **Há um indício fraco de reversão no WDO em 1 a 5 min** (E1: -0,28 e -0,53 bps, p ≈ 0,07). Não passa a correção
   de múltiplos testes e não se repete no WIN com a mesma força.
3. **O sinal do efeito muda de ano para ano** (por exemplo WDO E1 em 60 min: +5,96 bps em 2020, −2,76 em 2021).
   Isso é o padrão esperado de ruído, não de um efeito estável.
4. **O poder estatístico é limitado.** Com 650 a 2.100 episódios, o IC 95% tem de 1 a 5 bps de meia-largura.
   Efeitos menores que isso não podem ser descartados. Mas o custo de ida e volta (2 a 3 ticks, 1 a 3 bps)
   já os tornaria inviáveis, então para o objetivo do projeto a falta de poder importa pouco.

### Hipóteses (não testadas)
1. **O candle de 1 minuto não mostra quem negocia.** A "direção do big player" é inferida só do movimento do
   preço. Se o movimento do minuto já tem a direção embutida, estamos seguindo o que o preço já mostrou, e a
   informação já foi absorvida quando entramos.
2. **Pico de volume costuma ser notícia, não ordem fatiada.** `z_vol ≥ 3` cai em horários de dado
   macroeconômico e abertura de mercados externos (ex.: pico às 10:30 no WIN). Ali o preço ajusta em segundos,
   por muitos participantes. Um operador grande fatiando ordem deixaria volume **persistente e moderado**, não um pico.
3. **Entramos tarde.** Executar na abertura da barra seguinte (regra de realismo) já perde o movimento do
   minuto do evento. Se o movimento é rápido, não sobra continuação para capturar.
4. **Reversão por liquidez.** Depois de um choque de volume, é comum o preço devolver parte do movimento
   (impacto temporário). É compatível com o sinal negativo em 1 a 5 min.
5. **Definições simples demais.** Só olhamos volume e lote. Não olhamos esforço × resultado, absorção
   (muito volume com preço parado) nem o contexto (horário, regime de volatilidade, dia de notícia).

## 5. O que este resultado NÃO diz
- **Não prova que seguir big player nunca funciona.** Diz que estas três definições, em candles de 1 min,
  em 2020–2025, não mostraram sinal detectável.
- Não testa dado tick a tick, que identifica agressor comprador/vendedor e é o dado natural para esta ideia.
- Não usa o hold-out, que continua trancado.

## 6. Controle de falsos positivos (importante para as próximas rodadas)
- Esta rodada gastou **15 testes por ativo**. Cada rodada nova com definições novas **soma** testes ao total
  (30 por ativo na rodada 2 se também tiver 15). O limite de Bonferroni deve ser recalculado sobre o total
  acumulado, e cada nova definição deve ser escrita **antes** de rodar.
- Não reajustar limites (por exemplo `z ≥ 3` para `z ≥ 2,5`) olhando o resultado desta rodada.
- Qualquer candidato que passar deve ser confirmado em dado não visto (hold-out, uma única vez, na Fase 6).

## 7. Próximo passo
Rodada 2: poucas definições novas, pré-registradas em documento antes da execução, atacando as hipóteses 2, 4 e 5
(absorção, esforço × resultado, fluxo persistente em janelas maiores, condicionamento por horário/regime).
Depois da rodada 2, o grupo decide entre continuar, buscar dado tick a tick ou encerrar.
