# Big Player · parte 2 — o preço nos horários de pico de volume

A parte 1 (pastas `notebooks/`, `src/`, `docs/` do `bigplayer`) montou os dados limpos e testou
estratégias com estudo de evento. A parte 2 recomeça a análise pelo que o professor pediu: olhar o
**preço** nos horários em que o volume tem pico, em **pontos**, com contas simples.

**Status (2026-11-02):** pronto o passo 1 (minuto antes do pico e minuto do pico). Falta o passo 2
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

Saídas: `pt2/reports/picos_wdo.csv`, `pt2/reports/picos_win.csv` e as figuras em `pt2/reports/figures/`.
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

Por que **mediana** e não média: alguns dias de notícia têm variações enormes (veja os extremos abaixo).
A média ficaria puxada por esses poucos dias, e a mediana mostra o dia comum.

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

### O que isto NÃO diz
- Não diz quem negociou: o candle não mostra o agressor.
- Não é estratégia. É uma descrição do que acontece em volta do pico. O que acontece **depois** do pico
  é o passo 2.
- Não olha a abertura (9:00), que é o maior pico do WDO.

## Próximo passo (para o artigo)
**Passo 2: o que o preço faz depois do pico.** Para cada horário, a distribuição da variação de T até
T+5, T+15 e T+30 minutos: % de vezes que sobe, mediana e faixas (de 10% a 90%). É a "expectativa de
preço depois do pico" que o professor pediu. O passo 2 é descritivo. Se virar regra de operação, tem que
ser conferido no hold-out.
