# Big Player · parte 2 — o preço nos horários de pico de volume

A parte 1 (pastas `notebooks/`, `src/`, `docs/` do `bigplayer`) montou os dados limpos e testou
estratégias com estudo de evento. A parte 2 recomeça a análise pelo que o professor pediu: olhar o
**preço** nos horários em que o volume tem pico, em **pontos**, com contas simples.

**Status (2026-11-02):** prontos o passo 1 (minuto antes do pico e minuto do pico) e o passo 2
(o que o preço faz depois do pico).

## Como rodar

```bash
cd bigplayer
# uma vez, para cada ativo (gera data/interim/<ativo>_m1_limpo.parquet)
BIGPLAYER_ASSET=WDO python notebooks/00_carga_e_split.py && BIGPLAYER_ASSET=WDO python notebooks/04_dataset_limpo.py
BIGPLAYER_ASSET=WIN python notebooks/00_carga_e_split.py && BIGPLAYER_ASSET=WIN python notebooks/04_dataset_limpo.py
# análise da parte 2 (WDO e WIN juntos)
python pt2/01_picos.py
python -m pytest tests/test_pt2_picos.py
```

Saídas: `pt2/reports/picos_<ativo>.csv` (passo 1), `pt2/reports/depois_<ativo>.csv` (passo 2) e as
figuras em `pt2/reports/figures/`.
O código das contas está em `pt2/picos.py`, e cada função tem a definição escrita.

## Como cada número é calculado

| O quê | Conta |
|---|---|
| **Dados** | Candles de 1 minuto, só o período de exploração (WDO: 18/09/2020 a 01/04/2025, 1.034 pregões; WIN: 15/10/2020 a 25/09/2025, 1.118 pregões). Só barras `usable` (dentro da sessão, sem pregão parcial). O último ano de cada ativo (hold-out) não é usado. |
| **Preço médio do minuto** | `(máxima + mínima + fechamento) / 3`. É o "preço típico" da barra. Com candle de 1 minuto não dá para ter o preço médio de cada negócio. |
| **Variação do minuto** | Preço médio do minuto **menos** o preço médio do minuto anterior, em **pontos**. Só é calculada quando o minuto anterior existe, é exatamente 1 minuto antes e é do mesmo pregão. Assim, nunca compara um dia com o outro. |
| **Horários de pico** | Todo :00 e :30 de 9:00 a 17:30. **9:00 fica de fora**: é a abertura e não existe minuto antes dela. |
| **T−1 e T** | Para o pico das 10:00: T−1 é a variação do minuto 9:59 (9:59 contra 9:58) e T é a variação do minuto 10:00 (10:00 contra 9:59). Só entram os pregões que têm as duas. |
| **Mínima, mediana e máxima** | Calculadas sobre todos os pregões daquele horário, **com sinal** (negativo = caiu). |
| **Mediana do \|variação\|** | Mediana do tamanho da variação, **sem o sinal**. Responde "quanto o preço costuma andar", sem que subidas e quedas se cancelem. |
| **Volume × tarde** | Volume mediano daquele minuto ao longo dos pregões, dividido pelo volume típico da tarde (mediana dos volumes medianos dos minutos de 14:00 a 16:59). É o gráfico de volume dos slides: 1 = normal da tarde. |
| **Normal da hora** (`hora_mediana_abs`) | Mediana do \|variação\| de todos os minutos da hora do pico. Exemplo: para 10:00 e 10:30, todos os minutos das 10:00 às 10:59. |
| **Variação depois do pico** (passo 2) | Preço médio em T+h **menos** o preço médio em T, em pontos, com h = 5, 15 e 30 minutos. Só existe se houve negócio exatamente h minutos depois. |
| **% sobe / % cai** | % dos pregões em que a variação depois do pico foi positiva ou negativa. O que falta para 100% é variação zero. |
| **Faixa de 10% a 90%** (`p10`, `p90`) | 10% dos pregões ficaram abaixo de `p10` e 10% acima de `p90`, ou seja, 80% dos pregões caem entre os dois. |
| **% continua / % volta** | Só nos pregões em que o minuto do pico mexeu (variação de T diferente de zero). Continua = em T+h o preço está do mesmo lado do movimento de T (subiu em T e está acima em T+h, ou caiu e está abaixo). Volta = do lado oposto. |
| **Normal da hora** (passo 2, colunas `normal_*`) | A mesma conta feita em **todos os minutos comuns** da mesma hora, ou seja, os que não são :00 nem :30. É a referência: o pico só tem algo de especial se ficar longe dela. |
| **Margem de erro** (`margem_pct`) | `1,96 × √(0,25 / casos)`, em pontos percentuais. É a margem de 95% de uma porcentagem. Com ~1.000 pregões, dá ±3 pontos percentuais: um 53% não se distingue de 50%. |

Por que **mediana** e não média: alguns dias de notícia têm variações enormes (veja os extremos abaixo).
A média ficaria puxada por esses poucos dias, e a mediana mostra o dia comum.

**Atenção ao "continua" dos minutos comuns:** ele fica em 51% a 53% em 5 minutos, e não em 50%. É
efeito da conta, não do mercado. O preço médio é uma média de três preços do minuto, então parte do
movimento de um minuto aparece também na média do minuto seguinte. Por isso a comparação certa é
**pico contra minuto comum**, e não pico contra 50%.

Unidades: no WDO o tick é 0,5 ponto (1 ponto = R$ 10 por contrato). No WIN o tick é 5 pontos
(1 ponto = R$ 0,20 por contrato). Como o preço médio é uma média de 3 preços, a variação anda em
"degraus" de 1/3 de tick (0,17 ponto no WDO e 1,67 ponto no WIN). Por isso a linha do gráfico do WDO
tem forma de escada. **Não compare pontos do WDO com pontos do WIN**: cada um tem a sua escala.

## Resultados

Figuras:
- `perfil_<ativo>.png`: em cima, o volume por minuto (o mesmo gráfico dos slides). Embaixo, quanto o
  preço médio anda em cada minuto do dia.
- `picos_<ativo>.png`: mediana do \|variação\| no minuto antes (T−1) e no minuto do pico (T), por horário.

### Mediana do |variação| em pontos: minuto antes × minuto do pico

| Horário | WDO T−1 | WDO T | WDO volume × tarde | WIN T−1 | WIN T | WIN volume × tarde |
|---|---|---|---|---|---|---|
| 09:30 | 1,17 | 1,50 | 3,7 | 21,7 | 28,3 | 1,9 |
| 10:00 | 1,50 | 1,67 | 4,2 | 23,3 | 38,3 | 3,0 |
| 10:30 | 1,00 | 1,17 | 3,4 | 31,7 | 41,7 | 3,9 |
| 11:00 | 1,00 | 1,33 | 3,5 | 30,0 | 40,0 | 2,9 |
| 11:30 | 1,00 | 1,00 | 2,6 | 28,3 | 31,7 | 2,6 |
| 12:00 | 1,00 | 1,00 | 3,1 | 25,0 | 28,3 | 2,0 |
| 13:00 | 0,83 | 0,83 | 2,1 | 18,3 | 21,7 | 1,3 |
| 15:00 | 0,67 | 0,83 | 1,4 | 18,3 | 23,3 | 1,4 |
| 17:00 | 0,50 | 0,50 | 0,9 | 18,3 | 25,0 | 1,3 |

Tabela completa (todos os horários, com mínima, mediana e máxima com sinal) nos CSVs.

### Leitura
1. **No minuto antes do pico, o preço não tem direção.** A mediana com sinal é praticamente 0 em
   todos os horários (WDO: −0,17 a +0,17 ponto; WIN: −1,67 a +1,67 ponto, ou seja, ±1/3 de tick).
   Somando todos os horários, o minuto antes sobe em 47% dos casos e cai em 47% no WDO (49% e 49% no WIN).
2. **Em tamanho, o minuto antes também é um minuto comum.** O \|variação\| em T−1 fica no nível normal
   daquela parte do dia. Não aparece uma "preparação" do preço antes do pico.
3. **O preço anda mais no minuto do pico do que no minuto antes.** No WIN isso vale para todos os
   horários: de 3 a 15 pontos a mais, com a maior diferença de manhã (10:00: de 23 para 38 pontos). No
   WDO aparece nos picos da manhã (11:00: de 1,00 para 1,33 ponto). À tarde, T−1 e T quase sempre ficam
   iguais (exceções: 14:00, 15:00 e 17:30).
4. **Os extremos são dias de notícia dos EUA.** As maiores variações no minuto do pico (WDO −36 pontos
   em 03/05/2024 às 9:30; WIN +1.047 pontos em 22/08/2025 às 11:00; WDO −32,5 e WIN +670 em 10/08/2022
   às 9:30) caem em datas que parecem ser de payroll, inflação (CPI) e discurso do presidente do Fed.
   *A coincidência com o calendário dos EUA ainda não foi conferida dia a dia.*

### O que isto NÃO diz (passo 1)
- Não diz quem negociou: o candle não mostra o agressor.
- Não olha a abertura (9:00), que é o maior pico do WDO.

## Passo 2 — o que o preço faz depois do pico

Figuras:
- `continua_<ativo>.png`: % de pregões em que o preço continua na direção do minuto do pico, em 5, 15 e
  30 minutos, com a margem de erro. O traço cinza mostra a mesma conta nos minutos comuns da mesma hora.
- `faixa_<ativo>.png`: onde o preço está 15 minutos depois do pico (faixa de 10% a 90% e mediana), ao
  lado da mesma faixa nos minutos comuns.

Tabela completa (17 horários × 3 horizontes, com as colunas `normal_*`): `pt2/reports/depois_<ativo>.csv`.

### A "expectativa de preço depois do pico"
A tabela funciona como consulta: dado o ativo, o horário do pico e o horizonte, ela devolve a chance de o
preço subir, a chance de continuar na direção do minuto do pico, a mediana e a faixa onde caem 80% dos dias.
Exemplo, **WIN, pico das 10:30, 15 minutos depois:** sobe em 49% dos pregões e cai em 51%, mediana de
−3 pontos, e 80% dos pregões terminam entre −378 e +425 pontos.

### Leitura
1. **Depois do pico, o preço não tem direção esperada.** Em 15 minutos, sobe em 48% a 55% dos pregões no
   WDO e em 46% a 52% no WIN. A mediana fica perto de zero: de −0,2 a +0,8 ponto no WDO e de −17 a +11
   pontos no WIN, quando a faixa de 80% dos dias tem de ±5 a ±13 pontos (WDO) e de ±140 a ±400 pontos (WIN).
2. **Continuar na direção do pico é quase o mesmo que num minuto comum.** Depois do pico, o preço continua
   em 45% a 57% dos casos, e nos minutos comuns em 49% a 53%. Das 102 comparações (17 horários × 3
   horizontes × 2 ativos), 11 saem da margem de erro. Só pelo acaso seriam esperadas ~5. São um pouco mais,
   mas sem padrão:
   - WDO: 9:30 (15 min), 10:00 (5 min), 14:00 (15 min), 16:00 (5 e 30 min) e 17:30 (30 min, com só 600 pregões).
   - WIN: 10:30 (30 min), 12:00 (30 min), 15:30, 16:30 e 17:00 (5 min).
   - Nenhum horário se repete entre WDO e WIN, e em dois casos do WDO o desvio é de reversão, não de continuação.

   Isso não sustenta uma regra de operação. Se o grupo quiser testar algum desses horários, o teste tem
   que ser escrito antes e rodado no hold-out (o último ano), uma vez só.
3. **O pico muda o tamanho do movimento, não a direção.** Em alguns picos da manhã, a faixa de 15 minutos
   fica mais larga que a dos minutos comuns: WIN 10:30 (+17%) e 12:00 (+18%), WDO 10:00 (+15%) e 12:00
   (+23%). Nos demais horários, a largura fica entre 0,9 e 1,1 vez a normal.

### O que isto NÃO diz (passo 2)
- Não é estratégia e não inclui custo. Em 15 minutos, a mediana depois do pico é menor que 1 tick na maioria dos horários.
- Os números são da exploração (até 2025). O hold-out não foi usado.
- 9:00 fica de fora também aqui: sem minuto anterior não há direção do minuto do pico.
