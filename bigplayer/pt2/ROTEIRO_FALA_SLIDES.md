# Roteiro de fala — apresentação "Big Player" (7 slides, do jeito que estão)

Deck: `Cópia de Big Player.pdf` (slides 1 a 7, sem alterações). Tempo total: ~13 minutos, com folga para
perguntas dentro dos 15. A divisão de quem fala é **sugestão**; ajustem entre vocês.

| # | Slide | Tempo | Quem (sugestão) |
|---|---|---|---|
| 1 | Capa | 0,5 min | Camargo |
| 2 | O que é um Big Player? | 1,5 min | Camargo |
| 3 | Como ele age e como pegamos o vácuo? | 2 min | Camargo |
| 4 | Volume negociado em cada minuto | 3 min | Ícaro |
| 5 | Preço de fechamento nos picos | 3 min | Ícaro |
| 6 | Máxima do minuto nos picos | 1,5 min | João |
| 7 | Mínima do minuto nos picos + conclusão | 1,5 min | João |

Explicação completa dos slides 4 a 7 (números e perguntas prováveis): `pt2/EXPLICACAO_SLIDES_4_A_7.md`.

---

## Slide 1 — Capa (0,5 min)

> "Boa tarde. Nosso projeto é o Big Player: entender como operam os grandes participantes do mercado
> e se dá para identificar a atuação deles nos dados de mini dólar e mini índice da B3."

---

## Slide 2 — O que é um Big Player? (1,5 min)

> "Big player é quem opera tanto que move o preço com as próprias ordens. No mini dólar, normalmente são
> bancos e tesourarias, fundos e gestoras, e investidores estrangeiros.
>
> Um ponto importante: muito volume não significa big player. Robôs de alta frequência negociam muito,
> compram e vendem o tempo todo, mas sem uma direção. Então volume alto, sozinho, não prova que tem um
> grande operador por trás."

**Transição:** "Então como um big player age, e como a gente tentaria aproveitar isso?"

---

## Slide 3 — Como ele age e como pegamos o vácuo? (2 min)

> "Primeiro: uma ordem grande não sai de uma vez. US$ 100 milhões são 10 mil contratos de mini dólar. Pelos
> nossos dados, isso é cerca de 1 minuto de todo o volume do mercado de manhã e uns 3 minutos à tarde. Se
> ele mandasse tudo de uma vez, empurraria o preço contra ele mesmo.
>
> Por isso, ele fatia a ordem, e isso deixa rastro: volume acima do normal, fluxo na mesma direção, ou
> preço parado mesmo com muito volume, que é quando alguém está absorvendo as ordens.
>
> A ideia de pegar o vácuo é: como nosso capital é pequeno, a gente entra e sai sem mexer no preço. Se
> conseguirmos ver o rastro, vamos atrás dele, como o carro que pega o vácuo do carro da frente.
>
> A pergunta dos próximos slides é: nos dados, quando o volume dispara, o preço segue alguma direção?"

---

## Slide 4 — Volume negociado em cada minuto do pregão (3 min)

**Antes de falar, apontar no gráfico:** eixo do horário, eixo de contratos, linha cheia e tracejada.

> "Este gráfico mostra quantos contratos são negociados em cada minuto do pregão. Usamos candles de 1
> minuto, de 2020 a 2025: cerca de 1.000 pregões do mini dólar e 1.100 do mini índice. O último ano de
> cada ativo ficou guardado e não entrou na análise.
>
> Para cada minuto do dia, juntamos o volume daquele minuto em todos os pregões. A linha cheia é a
> mediana, o dia típico. A tracejada é a média. A média fica sempre acima porque alguns poucos dias de
> notícia têm volume enorme e puxam a média para cima. A mediana não sofre com isso.
>
> O que aparece:
> - O volume é muito maior de manhã e vai caindo ao longo do dia. No mini dólar, são de 8 a 12 mil
>   contratos por minuto de manhã e uns 3 mil à tarde.
> - Os picos caem em horários redondos: 9:00, 9:30, 10:00, 10:30, 11:00, 12:00. No mini índice, o maior é
>   às 10:30, com quase 80 mil contratos no minuto.
> - O salto acontece no próprio minuto: o minuto antes tem volume normal.
>
> Conferimos os maiores movimentos de preço nesses picos e todos coincidem com divulgações de dados dos
> Estados Unidos, como inflação e emprego. Esses dados saem às 8:30 de Nova York, que é 9:30 em Brasília no
> horário de verão americano, ou 10:30 fora dele."

**Transição:** "Sabendo onde estão os picos, olhamos o que o preço faz neles."

---

## Slide 5 — Preço de fechamento nos picos (3 min)

**Apontar:** bolinha colorida = minuto do pico (t); bolinha cinza = minuto antes (t−1); três números.

> "Aqui usamos os mesmos picos: todos os :00 e :30, das 9:30 às 17:30. As 9:00 ficam de fora porque não
> existe minuto antes da abertura.
>
> Acima de cada pico tem três números, todos em pontos. O colorido é a mediana do preço de fechamento no
> minuto do pico. O cinza é a mediana no minuto antes. E o delta é a diferença entre os dois.
>
> Duas coisas para ler certo:
> - Os números ficam todos perto de 5.270 no dólar e 120.600 no índice porque são a mediana de cinco anos
>   de preço. Eles mostram o nível do período, não o que acontece no pico.
> - O delta compara duas medianas que vêm de dias diferentes. Por isso aparecem valores como −105 no
>   índice às 15h.
>
> Para saber o que o preço faz de verdade, refizemos a conta comparando cada dia com ele mesmo: fechamento
> do pico menos fechamento do minuto antes, no mesmo pregão. O resultado: no mini dólar, a variação típica
> é zero em todos os picos. No mini índice, fica entre −5 e +5 pontos, que é um tick. E o preço sobe em
> 40 a 50% dos dias e cai numa proporção parecida."

**Se perguntarem do −105:** "É efeito da conta: a mediana do minuto antes e a do pico caem em dias
diferentes, com quase um ano de distância. Dia a dia, às 15h, a variação típica é −5 pontos."

---

## Slide 6 — Máxima do minuto nos picos (1,5 min)

> "Mesmo gráfico, agora com a máxima do minuto: o maior preço negociado ali.
>
> Os números seguem a mesma lógica do slide anterior, e o delta tem a mesma limitação. Mas aparece um
> padrão: de manhã, no mini índice, o delta da máxima é positivo e grande, de +22,5 a +55 pontos entre
> 9:30 e 11:30. Ou seja, a máxima do minuto do pico tende a ir mais alto que a do minuto antes."

**Transição:** "Isso quer dizer que o preço sobe no pico? Para responder, precisamos olhar a mínima."

---

## Slide 7 — Mínima do minuto nos picos + conclusão (1,5 min)

> "Aqui é a mínima: o menor preço do minuto. No mini dólar, de manhã, o delta da mínima é negativo: −2,0 às
> 9:30, −3,5 às 10:00, −2,0 às 11:00. A mínima do pico tende a ir mais baixo.
>
> Juntando os dois slides: no minuto de pico, a máxima sobe e a mínima desce. O preço não vai para um lado;
> ele oscila mais para os dois lados. E, pelo fechamento, termina o minuto praticamente onde começou.
>
> A nossa conclusão: **o pico de volume aumenta o tamanho do movimento do preço, mas não define a
> direção.** Para a ideia de pegar o vácuo do big player com candle de 1 minuto, o pico diz *quanto* o preço
> vai mexer, não *para onde*. Como o candle não mostra quem comprou ou vendeu, separar o big player do resto
> do mercado exigiria dados negócio a negócio."

> "Obrigado. Ficamos à disposição para perguntas."

---

## Perguntas que o professor provavelmente faz

| Pergunta | Resposta curta |
|---|---|
| "Mediana ou média?" | Mediana, porque poucos dias de notícia têm valores enormes que puxam a média. Mostramos a média tracejada para deixar isso visível. |
| "Por que os preços são todos ~5.270?" | São a mediana de cinco anos de preço; refletem o nível do período, não o pico. |
| "O que significa um ponto?" | WDO: 1 ponto = R$ 10 por contrato; 5.270 = dólar a R$ 5,27. WIN: 1 ponto = R$ 0,20 por contrato. |
| "Por que o mini índice varia tanto mais?" | O preço dele é ~23 vezes maior em pontos. Em porcentagem, varia só 10 a 20% mais que o dólar. |
| "Por que valores quebrados como 5.270,8?" | Com número par de dias, a mediana é a média dos dois valores do meio. |
| "Por que comparar dia a dia?" | Para comparar cada pregão com ele mesmo; subtrair medianas mistura dias de anos diferentes. |
| "Dá para ganhar dinheiro?" | Não com estes dados: a direção é ~50/50 e o movimento típico é até 1 tick, antes dos custos. |
| "Quantos anos de dados?" | ~4,5 anos no WDO e ~5 no WIN (2020 a 2025), com o último ano guardado para validação. |
