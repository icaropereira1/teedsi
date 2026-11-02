# Roteiro — apresentação de 03/11/2026 (15 min)

Todas as figuras estão em `pt2/reports/figures/`. Os números vêm de `pt2/README.md`, que explica cada conta.
**Usem só os números deste roteiro e do README.** A primeira versão da parte 2 tinha leituras que foram
corrigidas, então não vale reaproveitar nada dela.

A divisão de quem fala é só uma **sugestão**; ajustem entre vocês. O importante é que os três leiam a seção
"Perguntas prováveis".

| # | Slide | Figura | Tempo | Quem (sugestão) |
|---|---|---|---|---|
| 1 | O que mudou desde a última apresentação | — | 1 min | Ícaro |
| 2 | Os dados | slide "Os dados" da apresentação anterior | 1,5 min | Camargo |
| 3 | O preço ao lado do volume | `perfil_win.png` (e `perfil_wdo.png`) | 2,5 min | Ícaro |
| 4 | O minuto antes e o minuto do pico | `picos_win.png` (e `picos_wdo.png`) | 3,5 min | Ícaro |
| 5 | Os extremos são dados dos EUA | `extremos_win.png` + tabela do README | 2 min | João |
| 6 | Depois do pico: a expectativa de preço | `faixa_win.png` e `continua_win.png` | 3 min | João |
| 7 | Conclusão e próximo passo | — | 1,5 min | Camargo |

Mostrem o WIN nos slides: o efeito aparece mais nele. Deixem o WDO de reserva, para o caso de perguntas.

---

## 1. O que mudou desde a última apresentação (1 min)
- Na última vez, apresentamos um teste estatístico complexo (estudo de evento). O professor pediu algo mais
  direto: **olhar o preço em volta dos horários de pico de volume, em pontos.**
- Fizemos isso em três perguntas: o que o preço faz **antes** do pico, **no** minuto do pico e **depois** dele.
- Tudo em **pontos**, não em bps. 1 ponto do WDO = R$ 10 por contrato; 1 ponto do WIN = R$ 0,20 por contrato.

## 2. Os dados (1,5 min)
- Candles de 1 minuto do WDO (mini dólar) e do WIN (mini índice), de 2020 a 2025: 1.034 pregões no WDO e
  1.118 no WIN.
- O último ano de cada ativo ficou guardado e não foi usado.
- **Preço médio do minuto = (máxima + mínima + fechamento) / 3.** Com candle de 1 minuto não existe o preço
  de cada negócio, então essa é a média possível.
- **Horários de pico = todo :00 e :30, das 9:00 às 17:30.** São os horários onde o volume salta no gráfico
  que já mostramos.

## 3. O preço ao lado do volume (2,5 min) — `perfil_win.png`
- Três gráficos com o mesmo eixo de horário. Em cima, o volume (o gráfico de antes). No meio, o preço médio.
  Embaixo, quanto o preço anda por minuto.
- **Gráfico do meio:** é o preço de cada minuto **menos o preço da abertura do mesmo dia**. Não dá para fazer
  a média do preço em si, porque o dólar foi de ~5.000 a ~6.000 pontos no período e a média misturaria anos.
- O que mostrar:
  - A **linha** (mediana dos dias) fica colada no zero o dia todo. O preço não tem um caminho típico.
  - A **faixa** (80% dos dias) abre como um funil. Às 12:00 já tem 73% da largura do fim do dia. É a hora em
    que o volume é maior.
- **Gráfico de baixo:** o preço anda mais nos mesmos horários em que o volume tem pico (as "agulhas"
  coincidem).

## 4. O minuto antes e o minuto do pico (3,5 min) — `picos_win.png`
- **Gráfico de cima:** quanto o preço anda (mediana, sem o sinal) no minuto antes (cinza) e no minuto do pico
  (laranja). Exemplo: no WIN às 10:00, de 23 pontos para 38.
- **Gráfico de baixo:** a comparação dia a dia, ou seja, em que % dos dias o minuto andou mais que o anterior.
  50% = andaram igual. A barrinha é a margem de erro (±3 pontos percentuais).
- O que dizer:
  1. **Antes do pico, o preço não tem direção.** No minuto antes, ele sobe em 49% dos dias e cai em 49% (WIN).
  2. **Antes do pico, o minuto é comum**, com uma exceção: **às 10:00, o 9:59 já mexe mais** que o 9:58, nos
     dois ativos, e o volume também já sobe nesse minuto.
  3. **No minuto do pico, o preço anda mais:** no WIN, em 15 dos 17 horários, de 53% a 65% dos dias (o maior
     é às 10:00). No WDO, em 7 dos 17.
- Se perguntarem pela máxima e pela mínima: estão no slide seguinte e nos CSVs.

## 5. Os extremos são dados dos EUA (2 min) — `extremos_win.png`
- A mediana fica em ~0, e as pontas vêm de poucos dias.
- **Conferimos os 10 maiores de cada ativo: todos caem no minuto exato de uma divulgação americana.**
  São inflação (CPI), emprego (payroll), a decisão do Fed de 18/09/2024 e o discurso de Powell em 22/08/2025.
  - O maior do WIN: **+1.047 pontos em 22/08/2025 às 11:00**, o discurso de Powell em Jackson Hole.
  - O maior do WDO: **−36 pontos em 03/05/2024 às 9:30**, o payroll de abril.
- **Por que às vezes 9:30 e às vezes 10:30:** o dado sai às 8:30 de Nova York. Os EUA têm horário de verão e
  o Brasil não tem mais. Com o horário de verão americano, 8:30 lá é 9:30 aqui; sem ele, é 10:30.
- A tabela completa, com as fontes (BLS e Fed), está no README.

## 6. Depois do pico: a expectativa de preço (3 min) — `faixa_win.png` e `continua_win.png`
- A tabela de expectativa funciona como consulta: ativo + horário + prazo → chance de subir, mediana e faixa.
- **Exemplo para falar:** WIN, pico das 10:30, 15 minutos depois. O preço sobe em 49% dos dias e cai em 51%,
  a mediana é −3 pontos, e 80% dos dias terminam entre −378 e +425 pontos. Num minuto comum das 10h, a faixa
  vai de −337 a +348.
- **`faixa_win.png`:** a faixa depois do pico (laranja) costuma ser um pouco mais larga que a de um minuto
  comum (cinza). Às 9:00 ela é 58% mais larga no WIN.
- **`continua_win.png`:** "o preço continua na direção do minuto do pico?" Compare o ponto com o traço cinza,
  que é o mesmo cálculo num minuto comum.
  - Somando todos os horários, a diferença é de no máximo 0,4 ponto percentual, menor que a margem
    (de ±0,7 a ±0,8).
  - **Depois do pico, o preço se comporta igual a um minuto comum.**
- Frase para fechar o slide: **o pico muda o tamanho do movimento, não a direção.**

## 7. Conclusão e próximo passo (1,5 min)
- **Antes do pico:** sem direção. A única antecipação é o 9:59, que já mexe mais antes das 10:00.
- **No pico:** o preço anda mais, e os maiores movimentos são dados dos EUA.
- **Depois do pico:** sem direção previsível. A faixa fica um pouco mais larga, mas para cima ou para baixo
  é como um minuto comum.
- **Para quem quer "seguir o big player" com candle de 1 minuto:** o pico de volume diz *quanto* o preço vai
  mexer, não *para onde*.
- **Próximo passo:** o relatório em formato de artigo, para a última semana de novembro.

---

## Perguntas prováveis (os três precisam saber)

**"Como vocês calcularam o preço médio?"**
(máxima + mínima + fechamento) / 3 de cada minuto. Com candle de 1 minuto não temos o preço de cada negócio,
então não dá para fazer o preço médio ponderado por volume.

**"Esse gráfico é média ou mediana?"**
Onde o gráfico mostra um valor típico, é sempre a mediana. Os dias de notícia têm movimentos enormes: um único
dia de +1.047 pontos puxaria a média. A mediana mostra o dia comum. Os outros gráficos mostram porcentagem de
dias (por exemplo, "em 65% dos dias") ou a faixa de 10% a 90%.

**"Por que a variação está em pontos e não em porcentagem?"**
Foi o que o senhor pediu. Por isso também não comparamos WDO com WIN: os pontos têm escalas diferentes (no WDO
o tick é 0,5 ponto; no WIN, 5 pontos).

**"Por que as 9:00 não aparecem no antes e no pico?"**
É a abertura: não existe minuto antes dela. As 9:00 aparecem nos gráficos de preço ao longo do dia e no "depois
do pico". No WDO, em 111 dos 1.034 dias o primeiro negócio sai entre 9:01 e 9:04.

**"O que é essa barrinha (margem de erro)?"**
Com ~1.000 dias, uma porcentagem tem margem de ±3 pontos percentuais (95% de confiança). Então 53% não se
distingue de 50%. Fórmula: 1,96 × √(0,25 / número de dias).

**"O que é a faixa de 10% a 90%?"**
Ordenando os dias, 10% ficaram abaixo da faixa e 10% acima. Então 80% dos dias caem dentro dela.

**"Por que o 'continua' do minuto comum não é 50%?"**
Porque o fechamento de um minuto alterna entre o preço de quem compra e o de quem vende, e tende a devolver um
pouco do movimento. Por isso comparamos o pico com o minuto comum da mesma hora, e não com 50%.

**"Por que o 'continua' usa o fechamento e não o preço médio?"**
O preço médio mistura máxima e mínima, que acontecem antes do fechamento. Então parte do movimento de um minuto
aparece também no minuto seguinte, e o preço parece "continuar" sozinho. Testamos: com o preço médio aparecia
um falso padrão de cerca de 1 ponto percentual; com o fechamento, ele some.

**"Então dá para ganhar dinheiro com isso?"**
Não com estes dados. Depois do pico, a chance de subir ou cair é praticamente 50/50, e a mediana da variação
em 15 minutos fica abaixo de 1 tick em boa parte dos horários, antes de pagar custo. O preço anda bastante, mas
sem lado previsível. O que o pico diz é o *tamanho* do movimento.

**"Por que vocês não usaram o último ano?"**
Ele ficou guardado para testar alguma regra no fim, em dado que não foi usado para criá-la. Se usássemos agora,
qualquer regra pareceria melhor do que é.

**"E aquele estudo de evento da última vez?"**
Era a parte 1, com a mesma conclusão (seguir o fluxo em candle de 1 minuto não deu sinal), mas complexa demais.
A parte 2 responde à mesma pergunta de forma mais direta, como o senhor pediu.
