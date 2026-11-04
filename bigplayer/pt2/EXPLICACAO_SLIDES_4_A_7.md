# Explicação dos slides 4 a 7 (apresentação "Big Player")

Material de apoio para quem for apresentar. Para cada slide: o que está desenhado, como cada número foi
calculado, o que dá para concluir, o que **não** dá para concluir e as perguntas prováveis.

**Dados de todos os slides:** candles de 1 minuto do mini dólar (WDO) e do mini índice (WIN), da B3.
WDO: 1.034 pregões, de 18/09/2020 a 01/04/2025. WIN: 1.118 pregões, de 15/10/2020 a 25/09/2025.
O último ano de cada ativo ficou guardado e não foi usado. Só entram minutos dentro do horário de pregão
e dias completos.

**Unidade dos preços: pontos.**

| | WDO | WIN |
|---|---|---|
| O que o preço é | reais por US$ 1.000 (5.270 = dólar a R$ 5,27) | o Ibovespa futuro |
| 1 ponto vale | R$ 10 por contrato | R$ 0,20 por contrato |
| Menor variação (tick) | 0,5 ponto = R$ 5 | 5 pontos = R$ 1 |

Não compare pontos do WDO com pontos do WIN: um ponto do WDO vale 50 vezes um do WIN.

---

## Slide 4 — Volume negociado em cada minuto do pregão

### O que está desenhado
- **Eixo horizontal:** o horário do pregão, das 9h ao fechamento (~18h30 no WDO e ~18h25 no WIN).
- **Eixo vertical:** quantos contratos foram negociados naquele minuto.
- **Linha cheia (mediana):** para cada minuto do dia (9:00, 9:01, 9:02...), junta-se o volume daquele
  minuto em todos os pregões e pega-se o valor do meio. É o volume de um **dia típico**.
- **Linha tracejada (média):** a média dos mesmos valores.
- O volume é o número bruto de contratos, **sem normalizar** (não é dividido por nada).

### Por que mostrar mediana e média
A média fica **sempre acima** da mediana. Isso acontece porque alguns poucos dias têm volume muito maior
que o normal (dias de notícia), e esses dias puxam a média para cima. A mediana não é afetada por eles e
mostra o dia comum. A distância entre as duas linhas é maior justamente nos picos: é ali que os dias de
notícia pesam mais.

### O que dá para ver
1. **O volume é muito maior de manhã e cai ao longo do dia.**
   - WDO: ~8 a 12 mil contratos por minuto de manhã; ~3 mil à tarde; ~1 mil no fim do pregão.
   - WIN: ~25 a 50 mil de manhã; ~20 mil à tarde; ~5 a 10 mil no fim.
2. **Os picos acontecem em horários redondos (:00 e :30).** Os mais fortes:
   - WDO: 9:00 (abertura, ~17 mil), 9:30, 10:00, 10:30, 11:00, 12:00 e 13:00.
   - WIN: 9:00, 9:30, 10:00, **10:30 (o maior, ~79 mil na mediana)**, 11:00 e 11:30.
3. **O salto acontece no próprio minuto.** O minuto antes do pico tem volume de minuto comum; o volume
   dispara no minuto redondo e volta a cair em poucos minutos.
4. **No WIN, depois das 10:00 o volume fica em outro patamar.** Antes das 10:00 ele gira em ~25 mil;
   depois, em ~40 a 50 mil.

### Por que esses horários (o que já conferimos e o que é hipótese)
- **Conferido:** os 10 maiores movimentos de preço no minuto de pico de cada ativo caíram, todos, no minuto
  exato de uma divulgação dos EUA (inflação/CPI, emprego/payroll, decisão do Fed, discurso do presidente do
  Fed). Esses dados saem às 8:30 de Nova York, que é **9:30 em Brasília** quando os EUA estão no horário de
  verão (março a novembro) e **10:30** fora dele. O Brasil não tem mais horário de verão, por isso o horário
  muda ao longo do ano. Tabela completa com fontes: `pt2/README.md`.
- **Hipótese (não conferida):** 10:00 coincide com a abertura do mercado de ações da B3, e 10:30 com a
  abertura da bolsa de Nova York no horário de verão americano. Isso explicaria o volume do WIN ficar mais
  alto depois das 10:00. Os picos da tarde (13:00, 15:00, 16:00 no WDO) não foram investigados.

### Ligação com o slide 3
O slide 3 diz que uma ordem de US$ 100 milhões são 10 mil contratos de WDO, cerca de 2 a 3 minutos de todo
o volume. Este gráfico permite conferir: de manhã, 10 mil contratos são ~1 minuto de volume típico; à tarde,
~3 minutos. Por isso um operador grande precisa fatiar a ordem.

### Conclusão do slide
**Existem picos de volume em horários fixos, e eles são previsíveis pelo relógio.** Isso é o ponto de
partida das análises seguintes: o que acontece com o preço nesses minutos.

### Perguntas prováveis
- **"Por que mediana e não média?"** Porque poucos dias de notícia têm volume enorme e puxam a média. A
  mediana mostra o dia comum. Mostramos as duas para deixar isso visível.
- **"O que é 'sem normalizar'?"** Que é o número bruto de contratos. Não dividimos pelo volume do dia nem
  pelo volume médio daquele horário.
- **"Esse volume é de big player?"** Não dá para saber. O candle de 1 minuto mostra quanto foi negociado,
  não quem negociou. Volume alto em horário de notícia é o mercado inteiro reagindo, não necessariamente um
  operador grande.

---

## Slides 5, 6 e 7 — o preço nos picos

Os três slides têm **o mesmo desenho**; muda só qual preço do minuto é usado:

| Slide | Preço usado | O que é |
|---|---|---|
| 5 | **fechamento** | o preço do último negócio do minuto |
| 6 | **máxima** | o maior preço negociado no minuto |
| 7 | **mínima** | o menor preço negociado no minuto |

### Como ler (vale para os três)
- **Linhas:** o mesmo volume do slide 4 (mediana cheia, média tracejada).
- **Horários de pico:** todo :00 e :30 das 9:30 às 17:30 (17 por ativo). As 9:00 ficam de fora porque não
  existe minuto antes da abertura.
- **Bolinha colorida:** o minuto do pico (t). **Bolinha cinza:** o minuto antes (t−1). Elas ficam sobre a
  curva de volume, para mostrar onde estão no gráfico.
- **Três números acima de cada pico:**
  1. **colorido:** a mediana do preço (fechamento, máxima ou mínima) no minuto do pico, em todos os pregões;
  2. **cinza:** a mesma mediana no minuto antes (t−1);
  3. **Δ:** o número colorido menos o cinza.

### Por que todos os números são parecidos (~5.270 e ~120.600)
Cada número é a mediana de **~1.000 pregões, de 2020 a 2025**. Nesse período o dólar foi de ~R$ 4,65 a
~R$ 6,27 e o índice de ~100 mil a ~130 mil. A mediana só aponta o **meio desse período**: ~5.270 no WDO e
~120.600 no WIN, qualquer que seja o horário. Por isso os números quase não mudam de um pico para outro.

**Por que aparecem valores "quebrados" (5.270,8; 120.727,5)?** Com um número par de pregões, a mediana é a
média dos dois valores do meio (por exemplo, 5.270,5 e 5.271,0 dão 5.270,75, que aparece como 5.270,8).
Nenhum negócio saiu a esse preço; é só o resultado da conta.

### O cuidado mais importante: o que o Δ mede
O Δ destes slides **subtrai duas medianas tiradas de dias diferentes**. A mediana do pico pode vir de um dia
de 2022 e a de t−1 de um dia de 2024. Como o preço muda centenas de pontos entre os dias e só poucos pontos
entre dois minutos, o Δ fica dominado pela diferença entre dias, não pelo que aconteceu no pico.

A prova: trocando só o preço usado (fechamento, máxima, mínima), o Δ muda de sinal no mesmo horário.

| WIN | Fechamento (slide 5) | Máxima (slide 6) | Mínima (slide 7) |
|---|---|---|---|
| 10:00 | −7,5 | +52,5 | −25,0 |
| 15:00 | −105,0 | −5,0 | −65,0 |

Se o Δ medisse o movimento do preço no pico, as três colunas contariam a mesma história.

**A conta certa é dia a dia:** para cada pregão, preço no pico menos preço em t−1, e só depois a mediana.
Assim cada dia é comparado consigo mesmo e o nível do preço daquele ano se cancela. Essa versão existe para
o fechamento (`pt2/reports/figures/picos_dia_fechamento_dia_a_dia.png`) e é a que recomendamos mostrar
junto ou no lugar do slide 5.

---

### Slide 5 — fechamento

**O que os números dizem:**
- Δ do slide (subtração das medianas): WDO de −1,5 a +3,0 pontos; WIN de −105 a +40 pontos, sem padrão.
- **Conta dia a dia (a que vale):**
  - WDO: Δ = **0,0 em todos os 17 picos**. Num dia típico, o fechamento do minuto do pico é igual ao do
    minuto antes.
  - WIN: Δ entre **−5 e +5 pontos** (no máximo 1 tick = R$ 1 por contrato).
  - Em todos os horários, o preço **sobe em 40% a 50% dos dias e cai em 39% a 52%**. O resto fica igual.
    Exemplo, WIN às 15:00: o slide mostra Δ −105, mas dia a dia o preço sobe em 45% dos dias, cai em 50% e a
    variação típica é −5 pontos.

**Conclusão:** o pico de volume **não tem direção**. Do minuto antes para o minuto do pico, o fechamento
sobe e cai em proporções parecidas, e a variação típica é de 0 a 1 tick.

### Slide 6 — máxima

**O que os números dizem:**
- Δ do slide: WDO de −2,5 a +3,2 pontos; WIN de −30 a +55 pontos.
- No WIN, os picos da manhã têm Δ positivo e grande: 9:30 (+25), 10:00 (+52,5), 10:30 (+55), 11:00 (+30),
  11:30 (+22,5).

**Leitura:** a máxima do minuto do pico tende a ser mais alta que a do minuto antes, sobretudo de manhã no
WIN. Mas como o Δ é subtração de medianas, este slide sozinho não prova isso.

### Slide 7 — mínima

**O que os números dizem:**
- Δ do slide: WDO de −3,5 a +1,0 ponto; WIN de −70 a +45 pontos.
- No WDO, os picos da manhã têm Δ negativo: 9:30 (−2,0), 10:00 (−3,5), 10:30 (−1,5), 11:00 (−2,0).

**Leitura:** a mínima do minuto do pico tende a ser mais baixa que a do minuto antes, de manhã no WDO.
Mesma ressalva do slide 6.

### Slides 6 e 7 juntos: o que eles indicam
No pico, **a máxima sobe e a mínima desce**: o preço oscila mais dentro do minuto, para os dois lados. Isso
é confirmado de forma direta pelo gráfico de **amplitude** (máxima − mínima, `picos_dia_amplitude.png`),
que não tem o problema das medianas de dias diferentes, porque mede a oscilação dentro do próprio minuto:

| | Amplitude típica em t−1 → no pico |
|---|---|
| WDO | de 1,5–4,0 para 2,0–4,5 pontos (aumenta ou fica igual nos 17 picos) |
| WIN | de 40–95 para 55–140 pontos (aumenta nos 17 picos; +45 às 10:00 e às 10:30) |

Sugestão: incluir o gráfico de amplitude como slide 8, porque é ele que fecha o raciocínio dos slides 6 e 7.

---

## Conclusão geral dos slides 4 a 7

1. **O volume tem picos em horários fixos**, ligados ao relógio e, nos maiores casos, a divulgações dos EUA.
2. **No minuto do pico, o preço oscila mais** (máxima mais alta, mínima mais baixa, amplitude maior).
3. **Mas não escolhe lado:** dia a dia, sobe e cai em proporções parecidas, e termina o minuto
   praticamente onde estava (0 a 1 tick).

Em uma frase: **o pico de volume aumenta o tamanho do movimento do preço, não a direção.** Para quem quer
"seguir o big player" com candle de 1 minuto, o pico diz *quanto* o preço vai mexer, não *para onde*.

## Perguntas prováveis sobre os slides 5 a 7
- **"Por que os números são todos ~5.270?"** São a mediana de 5 anos de preço; refletem o nível do dólar no
  período, não o pico.
- **"O Δ de −105 no WIN às 15:00 quer dizer que o preço cai 105 pontos?"** Não. É a diferença entre duas
  medianas de dias diferentes. Dia a dia, a variação típica é de −5 pontos e o preço sobe em 45% dos dias.
- **"Então por que mostrar esses slides?"** Porque mostram que, quando o volume salta, a máxima e a mínima se
  afastam (o preço oscila mais). A direção é respondida pela conta dia a dia.
- **"Por que mediana?"** Porque os dias de notícia têm movimentos enormes que puxariam a média.
- **"Dá para ganhar dinheiro com isso?"** Não com estes dados: a direção é praticamente 50/50 e o movimento
  típico é de até 1 tick, antes de pagar corretagem e custos.
