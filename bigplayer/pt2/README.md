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
| **Horários de pico** | Todo :00 e :30 de 9:00 a 17:30 (horários fixos). Nem todos têm pico de volume: no WDO, 16:30, 17:00 e 17:30 ficam abaixo do volume da tarde, e no WIN, 17:30 (coluna `volume_x_tarde`). |
| **T−2, T−1 e T** | Para o pico das 10:00: T−2 é a variação do minuto 9:58, T−1 a do 9:59 e T a do 10:00. No passo 1 só entram os pregões que têm as três. |
| **Mínima, mediana e máxima** | Calculadas sobre todos os pregões daquele horário, **com sinal** (negativo = caiu). |
| **Mediana do \|variação\|** | Mediana do tamanho da variação, **sem o sinal**. Responde "quanto o preço costuma andar", sem que subidas e quedas se cancelem. |
| **% mexeu mais** (`pico_maior_pct`, `antes_maior_pct`) | Comparação dia a dia. `pico_maior_pct`: em que % dos pregões o \|variação\| do minuto T foi maior que o do T−1. `antes_maior_pct`: o mesmo para T−1 contra T−2. Os empates ficam de fora. **50% = os dois minutos mexem igual.** Nos minutos comuns essa conta dá 49% a 51%, então 50% é a referência certa. |
| **Volume × tarde** | Volume mediano daquele minuto ao longo dos pregões, dividido pelo volume típico da tarde (mediana dos volumes medianos dos minutos de 14:00 a 16:59). É o gráfico de volume dos slides: 1 = normal da tarde. |
| **Variação depois do pico** (passo 2) | Preço médio em T+h **menos** o preço médio em T, em pontos, com h = 5, 15 e 30 minutos. Só existe se houve negócio exatamente h minutos depois. |
| **% sobe / % cai** | % dos pregões em que a variação depois do pico foi positiva ou negativa. O que falta para 100% é variação zero. |
| **Faixa de 10% a 90%** (`p10`, `p90`) | 10% dos pregões ficaram abaixo de `p10` e 10% acima de `p90`, ou seja, 80% dos pregões caem entre os dois. |
| **% continua / % volta** | Usa o **fechamento** (veja abaixo por quê). Só entram os pregões em que o fechamento de T foi diferente do de T−1 (`casos_direcao`). Continua = o fechamento em T+h está do mesmo lado desse movimento (subiu em T e está acima em T+h, ou caiu e está abaixo). Volta = do lado oposto. |
| **Normal da hora** (colunas `normal_*`) | A mesma conta do passo 2 feita em **todos os minutos comuns** da mesma hora, ou seja, os que não são :00 nem :30. É a referência: o pico só tem algo de especial se ficar longe dela. |
| **Margem de erro** (`*_margem_pct`, `margem_pct`) | `1,96 × √(0,25 / casos)`, em pontos percentuais. É a margem de 95% de uma porcentagem. Com ~1.000 pregões, dá ±3 pontos percentuais: um 53% não se distingue de 50%. |

**Por que mediana e não média:** alguns dias de notícia têm variações enormes (veja os extremos abaixo).
A média ficaria puxada por esses poucos dias, e a mediana mostra o dia comum.

**Por que o "continua" usa o fechamento, e não o preço médio:** o preço médio de um minuto mistura a
máxima e a mínima, que acontecem antes do fechamento. Então parte do movimento de um minuto aparece também
na média do minuto seguinte, e o movimento parece "continuar" sozinho. Isso pesa mais nos minutos que mexem
muito, como os picos. Na primeira versão desta análise, com o preço médio, os picos pareciam continuar
cerca de 1 ponto percentual mais que os minutos comuns. Com o fechamento, a diferença some (veja o passo 2).
O fechamento tem um efeito no sentido contrário: ele alterna entre o preço de quem compra e o de quem vende,
e por isso tende a "devolver" um pouco do movimento. O "continua" dos minutos comuns fica em 41% a 50%, e
não em 50%. Por isso a comparação certa é **pico contra minuto comum da mesma hora**, nunca pico contra 50%.

**Unidades:** no WDO o tick é 0,5 ponto (1 ponto = R$ 10 por contrato). No WIN o tick é 5 pontos
(1 ponto = R$ 0,20 por contrato). Como o preço médio é uma média de 3 preços, a variação anda em
"degraus" de 1/3 de tick (0,17 ponto no WDO e 1,67 ponto no WIN). Por isso a linha do gráfico do WDO
tem forma de escada, e por isso **a mediana do WDO esconde diferenças pequenas**: duas medianas iguais
podem vir de distribuições diferentes. A comparação dia a dia (% mexeu mais) não tem esse problema.
**Não compare pontos do WDO com pontos do WIN**: cada um tem a sua escala.

## Passo 1 — o minuto antes do pico e o minuto do pico

Figuras:
- `perfil_<ativo>.png`: em cima, o volume por minuto (o mesmo gráfico dos slides). Embaixo, quanto o
  preço médio anda em cada minuto do dia.
- `picos_<ativo>.png`: em cima, a mediana do \|variação\| no minuto antes (T−1) e no minuto do pico (T).
  Embaixo, a comparação dia a dia, com margem de erro.

### Mediana do |variação| em pontos e comparação dia a dia

| Horário | WDO T−1 | WDO T | WDO: T mexeu mais | WDO vol. × tarde | WIN T−1 | WIN T | WIN: T mexeu mais | WIN vol. × tarde |
|---|---|---|---|---|---|---|---|---|
| 09:30 | 1,17 | 1,50 | 59% | 3,7 | 21,7 | 28,3 | 58% | 1,9 |
| 10:00 | 1,50 | 1,67 | 52% | 4,2 | 23,3 | 38,3 | 65% | 3,0 |
| 10:30 | 1,00 | 1,17 | 54% | 3,4 | 31,7 | 41,7 | 58% | 3,9 |
| 11:00 | 1,00 | 1,33 | 56% | 3,5 | 30,0 | 40,0 | 59% | 2,9 |
| 11:30 | 1,00 | 1,00 | 53% | 2,6 | 28,3 | 31,7 | 55% | 2,6 |
| 12:00 | 1,00 | 1,00 | 53% | 3,1 | 25,0 | 28,3 | 55% | 2,0 |
| 13:00 | 0,83 | 0,83 | 49% | 2,1 | 18,3 | 21,7 | 57% | 1,3 |
| 15:00 | 0,67 | 0,83 | 51% | 1,4 | 18,3 | 23,3 | 56% | 1,4 |
| 17:00 | 0,50 | 0,50 | 51% | 0,9 | 18,3 | 25,0 | 60% | 1,3 |

"T mexeu mais" = % dos pregões em que o minuto do pico andou mais que o minuto antes (margem ±3 pontos
percentuais). Tabela completa (todos os horários, com mínima, mediana e máxima com sinal) nos CSVs.

### Leitura
1. **No minuto antes do pico, o preço não tem direção.** A mediana com sinal é praticamente 0 em
   todos os horários (WDO: −0,17 a +0,17 ponto; WIN: −1,67 a +1,67 ponto, ou seja, ±1/3 de tick).
   Somando todos os horários, o minuto antes sobe em 47% dos casos e cai em 47% no WDO (49% e 49% no WIN).
2. **Em tamanho, o minuto antes quase sempre é um minuto comum, com uma exceção: 10:00.** Comparando
   T−1 com T−2 dia a dia, o resultado fica perto de 50% na maioria dos horários. Fora da margem:
   - **10:00, nos dois ativos:** o minuto 9:59 mexe mais que o 9:58 em 53% dos pregões no WDO e em
     54% no WIN. O volume também já sobe às 9:59 (WDO: de 2,59 para 2,85 vezes a tarde; WIN: de 1,16 para 1,31). É a única exceção que aparece nos dois ativos.
   - WDO 17:00 (53%): o 16:59 mexe mais que o 16:58.
   - 13:30 e 17:30, nos dois ativos (46% a 47%): o minuto antes mexe *menos* que o anterior a ele.

   São 34 comparações (17 horários × 2 ativos), e cerca de 2 sairiam da margem só por acaso. Por isso só o
   10:00, que se repete nos dois ativos, merece atenção.
3. **O preço anda mais no minuto do pico do que no minuto antes.**
   - **WIN:** em 15 de 17 horários o minuto do pico mexe mais em mais da metade dos pregões, acima da
     margem (de 53% a 65%; o maior é às 10:00). As exceções, 12:30 e 13:30, ficam dentro da margem.
   - **WDO:** acima da margem em 7 de 17 horários (9:30, 10:30, 11:00, 11:30, 14:00, 14:30 e 17:30),
     com 53% a 61%.
   - O WDO às 10:00 fica em 52%, dentro da margem. Uma explicação provável é que o 9:59 já está agitado
     (item 2), então o pico das 10:00 mexe mais que um minuto que também já mexia.
   - Nos outros horários do WDO, a mediana mostra T−1 e T iguais, mas isso é em parte efeito dos degraus
     de 1/3 de tick. A comparação dia a dia fica entre 49% e 53%.
4. **Os extremos parecem ser dias de notícia dos EUA.** As maiores variações no minuto do pico (WDO −36
   pontos e WIN +725 em 03/05/2024 às 9:30; WIN +1.047 pontos em 22/08/2025 às 11:00; WDO −32,5 e WIN
   +670 em 10/08/2022 às 9:30) caem em datas que parecem ser de payroll, inflação (CPI) e discurso do
   presidente do Fed. *A coincidência com o calendário dos EUA ainda não foi conferida dia a dia.*

### O que isto NÃO diz (passo 1)
- Não diz quem negociou: o candle não mostra o agressor.
- Não olha a abertura (9:00), que é o maior pico do WDO: não existe minuto antes dela.

## Passo 2 — o que o preço faz depois do pico

Figuras:
- `continua_<ativo>.png`: % de pregões em que o fechamento continua na direção do minuto do pico, em 5, 15
  e 30 minutos, com a margem de erro. O traço cinza mostra a mesma conta nos minutos comuns da mesma hora,
  e é com ele que se compara.
- `faixa_<ativo>.png`: onde o preço médio está 15 minutos depois do pico (faixa de 10% a 90% e mediana),
  ao lado da mesma faixa nos minutos comuns.

Tabela completa (18 horários × 3 horizontes, com as colunas `normal_*`): `pt2/reports/depois_<ativo>.csv`.
Às 9:00 a tabela tem % sobe, mediana e faixa, mas não tem "continua": sem minuto anterior não existe
direção do minuto do pico.

### A "expectativa de preço depois do pico"
A tabela funciona como consulta: dado o ativo, o horário do pico e o horizonte, ela devolve a chance de o
preço subir, a mediana, a faixa onde caem 80% dos dias e a chance de continuar na direção do minuto do pico,
sempre ao lado do que acontece num minuto comum.
Exemplo, **WIN, pico das 10:30, 15 minutos depois:** sobe em 49% dos pregões e cai em 51%, mediana de
−3 pontos, e 80% dos pregões terminam entre −378 e +425 pontos. Num minuto comum das 10h, a faixa vai de
−337 a +348.

### Leitura
1. **Depois do pico, o preço não tem direção esperada.** Em 15 minutos, sobe em 47% a 55% dos pregões no
   WDO e em 46% a 52% no WIN. A mediana fica perto de zero: de −0,5 a +0,8 ponto no WDO e de −17 a +11
   pontos no WIN. Enquanto isso, a faixa de 80% dos dias vai de ±5 a ±17 pontos (WDO) e de ±140 a ±425
   pontos (WIN).
2. **Continuar na direção do pico é igual a um minuto comum.**
   - Somando todos os horários, a diferença entre pico e minuto comum é de +0,2, +0,4 e +0,3 ponto
     percentual no WDO (5, 15 e 30 min) e de +0,2, +0,0 e +0,3 no WIN. A margem desse total é de ±0,7 a
     ±0,8, então nenhuma diferença se distingue de zero.
   - Horário a horário, 7 de 102 comparações saem da margem (3 no WDO e 4 no WIN). Só pelo acaso seriam
     esperadas cerca de 5.
3. **O pico muda o tamanho do movimento, não a direção.**
   - Na maioria dos horários a faixa de 15 minutos depois do pico é um pouco mais larga que a dos minutos
     comuns (13 de 18 horários no WDO, 12 de 18 no WIN).
   - As maiores diferenças: 9:00 (WDO +24%, WIN +58%), 12:00 (WDO +23%, WIN +18%), WDO 10:00 (+15%) e
     WIN 10:30 (+17%).
   - Não calculamos margem de erro para essa razão. Diferenças de até ~10% podem ser acaso.
   - O 9:30 sai mais estreito que o normal (WDO 0,95; WIN 0,89), mas a referência da hora 9 inclui os
     minutos 9:01 a 9:29, logo depois da abertura, que são mais agitados.

### O que isto NÃO diz (passo 2)
- Não é estratégia e não inclui custo. Em 15 minutos, a mediana depois do pico é menor que 1 tick em
  14 de 18 horários no WDO e em 9 de 18 no WIN.
- Os números são da exploração (até 2025). O hold-out não foi usado. Se alguém quiser testar um horário
  específico como regra, o teste tem que ser escrito antes e rodado no hold-out, uma vez só.
- **9:00 no WDO:** a barra das 9:00 só existe em 923 dos 1.034 pregões. Nos outros, o primeiro negócio sai
  entre 9:01 e 9:04.
- **17:30 com 30 minutos** só tem pregões de sessão longa (600 no WDO, 719 no WIN), porque na sessão curta
  não existe a barra das 18:00. É um recorte diferente dos outros horários.
