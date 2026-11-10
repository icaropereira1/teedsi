# Roteiro de Apresentação — 12/11 (7 Slides)

> **Tempo estimado:** ~10 a 12 minutos (com folga para perguntas dentro dos 15 min).  
> **Gráficos na identidade visual dos slides:** pasta `bigplayer/docs/apresentacao-12-11/graficos/`.

| Slide | Título sugerido | Gráfico / Visual | Tempo | Quem fala (sugestão) |
|---|---|---|---|---|
| **1** | Capa + O que mudou nesta etapa | Visual de capa / tópicos do pedido | 1,0 min | Gabriel Camargo |
| **2** | Como medimos agora (T = pico de volume e Alta × Baixa) | `01_todos_vs_alta_baixa_dia.png` | 2,0 min | Gabriel Camargo |
| **3** | WDO e WIN ao longo do dia: manhã × tarde | `02_wdo_win_janelas_30min.png` | 2,0 min | Ícaro Alves |
| **4** | Índice Dolarizado (`1000 × WIN / WDO`): visão do estrangeiro | `03_indice_dolarizado_manha_tarde.png` | 2,0 min | Ícaro Alves |
| **5** | Resumo comparativo em T+15 (WDO, WIN e Dolarizado) | `05_resumo_comparativo_t15.png` | 1,5 min | João Gabriel |
| **6** | Fluxo de investidores na B3: Estrangeiro × Pessoa Física | `04_fluxo_estrangeiro_x_pf.png` | 1,5 min | João Gabriel |
| **7** | Limitações e Conclusão | Tópicos diretos de fechamento | 1,5 min | Gabriel / João |

---

## Slide 1 — Capa e O que mudou nesta etapa (1,0 min)

**O que colocar no slide:**
- **Título:** Big Player — Picos de Volume até T+15, Índice Dolarizado e Fluxo de Investidores
- **Autores:** Gabriel Camargo Silva · Ícaro Alves de Sá · João Gabriel Abreu Soares
- **4 novidades a pedido do professor:**
  1. **Horizontes ampliados:** além de `T−1` e `T`, olhamos `T+3`, `T+5`, `T+10` e `T+15` minutos.
  2. **Novo `T`:** em vez de horário fixo, `T` é o **minuto de maior volume** de cada janela de 30 min (09:00 às 17:30) e do pregão inteiro (`DIA`).
  3. **Dias de alta × dias de baixa:** separados pela direção do próprio ativo no dia (sempre usando **mediana** e **em pontos** contra `T−1`).
  4. **Visão do estrangeiro:** série dolarizada (`1000 × WIN ÷ WDO`) + fluxo diário Estrangeiro × Pessoa Física na B3.

**Fala sugerida:**
> "Boa tarde. Na última apresentação, olhamos apenas o minuto antes (`T−1`) e o minuto do pico (`T`) misturando todos os pregões, e vimos que a mediana ficava em zero. Seguindo a recomendação do professor, fizemos quatro avanços: ampliamos a janela para `T+3`, `T+5`, `T+10` e `T+15`; passamos a definir `T` como o minuto exato de pico de volume dentro de cada janela de 30 minutos e no dia; separamos os pregões em dias de alta e dias de baixa; e trouxemos a visão do investidor estrangeiro, tanto pelo índice dolarizado quanto pelo fluxo na B3."

---

## Slide 2 — Por que separar Alta e Baixa? O pico de volume do DIA (2,0 min)

**Gráfico no slide:** `graficos/01_todos_vs_alta_baixa_dia.png`

**O que colocar no slide (ao lado ou abaixo do gráfico):**
- **Base de comparação (`T−1` = 0):** cada pico é comparado com o fechamento de 1 minuto antes, dentro do **mesmo pregão**.
- **Misturando todos os dias (linha cinza):** a mediana fica perto de zero porque ~50% dos dias são de alta e ~50% de baixa.
- **Separando Alta (roxo) e Baixa (laranja) no maior pico do dia (`DIA`):**
  - **WDO:** salta **+2,50 pt** (alta) e **−5,00 pt** (baixa) em `T`, mantendo **+2,50 / −4,00 pt** até `T+15`.
  - **WIN:** salta **+112,5 pt** (alta) e **−110,0 pt** (baixa) em `T`, sustentando **+95,0 / −105,0 pt** em `T+15`.
  - **Dolarizado:** salta **+25,3 pt** / **−25,7 pt** em `T` e **continua avançando até +27,0 / −28,7 pt em `T+15`**.

**Fala sugerida:**
> "Este primeiro gráfico responde por que antes víamos tudo em zero. A linha cinza tracejada mostra todos os dias juntos: como metade dos pregões sobe e metade cai, uma coisa anula a outra.
>
> Quando separamos dias de alta em roxo e dias de baixa em laranja, olhando o maior pico de volume do pregão, o padrão fica claro nos três ativos: o grosso do movimento acontece já no próprio candle de pico (`T`), há um leve respiro em `T+3`, mas o preço **não reverte** nos 15 minutos seguintes. No índice dolarizado, à direita, o movimento inclusive continua ganhando força até `T+15`."

---

## Slide 3 — WDO e WIN ao longo do dia: a manhã concentra o efeito (2,0 min)

**Gráfico no slide:** `graficos/02_wdo_win_janelas_30min.png`

**O que colocar no slide:**
- **18 janelas de 30 min (09:00 às 17:30):** barra clara = variação no minuto do pico (`T`); barra escura = variação acumulada em `T+15`.
- **No WDO (mini dólar):** de manhã (09:00 e 09:30), a variação em `T+15` chega a **+2,5 a +3,0 pt** na alta e **−2,0 pt** na baixa. À tarde (após 13h), trava em **0,0 a 0,5 pt (1 tick)**.
- **No WIN (mini índice):** janelas das **10:00 e 10:30** lideram (abertura do mercado à vista e notícias dos EUA), chegando a **+40 a +50 pt** na alta e **−75 pt** na baixa em `T+15`. À tarde, cai para **5 a 15 pt**.

**Fala sugerida:**
> "Aqui abrimos o comportamento janela por janela, de 30 em 30 minutos, das 9h às 17h30. A barra mais clara é o que acontece no próprio minuto do pico (`T`), e a barra mais escura é onde o preço está 15 minutos depois (`T+15`).
>
> O recado principal é a diferença entre manhã e tarde: entre 9h e 12h, onde o volume é muito maior, o preço anda e amplia o movimento até `T+15` — com destaque para 10h00 e 10h30 no WIN, que chegam a +50 pontos na alta e −75 pontos na baixa. Já depois das 13h, mesmo no pico de volume da meia hora, a mediana no dólar fica entre zero e meio ponto, que é apenas um tick."

---

## Slide 4 — Índice Dolarizado (`1000 × WIN / WDO`): a visão do estrangeiro (2,0 min)

**Gráfico no slide:** `graficos/03_indice_dolarizado_manha_tarde.png`

**O que colocar no slide:**
- **O que é:** `1000 × WIN ÷ WDO` ≈ Ibovespa em dólares (~22.200 pontos), nos 993 pregões com ambos os ativos (524 de alta, 469 de baixa), usando o pico de volume do WIN.
- **Por que importa:** o investidor estrangeiro mede retorno em dólar (bolsa + câmbio juntos).
- **Continuação pós-pico na manhã:** diferente dos ativos isolados, na série dolarizada o preço **continua abrindo distância de `T` até `T+15`**:
  - **09:00:** de **+5,9 pt (`T`)** para **+15,9 pt (`T+15`)** na alta; de **−8,1 pt** para **−21,7 pt** na baixa.
  - **10:00:** de **+9,7 pt (`T`)** para **+14,0 pt (`T+15`)** na alta; de **−10,3 pt** para **−20,1 pt** na baixa.

**Fala sugerida:**
> "Para enxergar o mercado como o investidor estrangeiro, construímos o índice dolarizado: mil vezes o WIN dividido pelo WDO, que representa o Ibovespa em dólares.
>
> À esquerda vemos a trajetória de `T−1` até `T+15` nas janelas da manhã contra uma janela típica da tarde (14h). Enquanto no WIN isolado boa parte do movimento se esgota já no minuto `T`, quando combinamos índice e dólar o movimento depois do pico da manhã continua crescendo até `T+15`: às 10h, por exemplo, sai de +9,7 pontos em `T` para +14,0 em `T+15` nos dias de alta, e dobra de −10,3 para −20,1 pontos nos dias de baixa."

---

## Slide 5 — Síntese em T+15: Manhã × Tarde × Pico do Dia (1,5 min)

**Gráfico no slide:** `graficos/05_resumo_comparativo_t15.png`

**O que colocar no slide:**
- **Comparação direta em `T+15`** das janelas chave da manhã (`09:00`, `10:00`, `10:30`), da tarde (`14:00`, `16:00`) e do maior pico do pregão (`DIA`).
- **Três padrões consistentes nos 3 ativos:**
  1. Os pontos claros (todos os dias misturados) ficam sempre colados em zero.
  2. As janelas da manhã carregam de **3× a 10× mais movimento** até `T+15` do que as janelas da tarde.
  3. O maior pico do pregão (`DIA`) concentra o maior deslocamento do dia (**+2,5 / −4,0 pt** no WDO; **+95 / −105 pt** no WIN; **+27,0 / −28,7 pt** no Dolarizado).

**Fala sugerida:**
> "Este painel resume lado a lado os três ativos em `T+15`. Ele deixa visualmente claro o contraste entre as três janelas principais da manhã — abertura às 9h, abertura das ações às 10h e noticiário americano às 10h30 — contra o marasmo das janelas da tarde às 14h e 16h, além da força do maior pico do dia na última coluna."

---

## Slide 6 — Fluxo de Investidores na B3: Estrangeiro × Pessoa Física (1,5 min)

**Gráfico no slide:** `graficos/04_fluxo_estrangeiro_x_pf.png`

**O que colocar no slide:**
- **Fonte:** Dados de Mercado (tabela pública gratuita), cobrindo **245 pregões** (11/11/2025 a 06/11/2026), saldo diário líquido em R$ bilhões.
- **Divergência estrutural:**
  - **Correlação diária de −0,57** (chegando a **−0,95** na janela móvel de 20 pregões em out/2026).
  - Em **68% dos pregões**, estrangeiro e pessoa física operam em **lados opostos** (um compra enquanto o outro vende).
  - **Ciclo claro:** até abril/2026 o estrangeiro acumulou **+R$ 69,7 bi** enquanto a PF vendeu **−R$ 6,5 bi**; na queda até agosto, o estrangeiro realizou para **+R$ 13,8 bi** enquanto a PF comprou até **+R$ 9,3 bi**.

**Fala sugerida:**
> "Também buscamos os dados públicos de fluxo de investidores da B3 nos últimos 245 pregões. O gráfico de cima mostra o saldo acumulado em bilhões de reais do investidor estrangeiro, em roxo, contra a pessoa física, em laranja.
>
> O resultado mostra uma oposição clássica de mercado: em 68% dos dias eles têm sinais opostos, com correlação diária de −0,57. Quando o estrangeiro puxou a compra acumulando quase R$ 70 bilhões até abril, a pessoa física vendeu; quando o estrangeiro realizou lucro entre maio e agosto, a pessoa física entrou comprando."

---

## Slide 7 — Limitações Metodológicas e Conclusão (1,5 min)

**O que colocar no slide:**
- **Limitações importantes (transparência metodológica):**
  1. **Classificação Alta/Baixa usa o pregão inteiro:** só sabemos se o dia foi de alta ou de baixa no fechamento. Logo, o resultado é **descritivo** (mostra que o pico acompanha a tendência do dia), **não um sinal operável em tempo real**.
  2. **Análise descritiva por medianas:** a pedido para esta etapa, avaliamos puramente medianas em pontos (sem p-valor/Bonferroni).
  3. **Janelas de ponta e períodos distintos:** `17:30` tem amostra menor (~20% dos picos caem nos últimos 15 min e não têm `T+15`), e o fluxo público (2025–2026) não se sobrepõe ao período da base M1 (2020–2025, com hold-out de 12 meses preservado).
- **Conclusão central:**
  - Nos picos de volume da manhã, o preço salta forte em `T` e **sustenta a direção do dia até `T+15`** (no índice dolarizado, continua avançando após o pico).
  - Contudo, sem conhecer a direção do dia de antemão (ou o agressor negócio a negócio), o candle de 1 minuto sozinho continua não oferecendo um sinal operável automático.

**Fala sugerida:**
> "Para fechar com transparência metodológica, destacamos três cuidados essenciais: primeiro, saber se o dia é de alta ou de baixa depende do fechamento do dia — portanto, essa análise descreve como o preço se comporta em dias direcionais, mas não é uma regra que dê para operar na hora do pico sem olhar o futuro. Segundo, os dados públicos de fluxo cobrem o último ano (2025 a 2026), então servem para caracterizar o comportamento dos participantes, sem cruzar diretamente com a janela de candles de 2020 a 2025. E o nosso período de validação (hold-out) segue 100% intocado.
>
> Em resumo: mostramos que nos picos de volume da manhã o preço não devolve o movimento até `T+15` — especialmente na visão dolarizada do estrangeiro —, mas confirmar quem está agredindo naquele minuto em tempo real exige dados tick a tick. Obrigado!"

---

## Cola Rápida para Perguntas do Professor

| Pergunta provável | Resposta direta |
|---|---|
| **"Por que vocês usaram a variação contra T−1 (Tabela B) no gráfico em vez da mediana do preço (Tabela A)?"** | Porque a mediana do nível de preço mistura pregões de 2020 a 2025 (quando o WDO variou de 4.650 a 6.270 pts). Comparando cada pico com o seu próprio `T−1` dentro do mesmo pregão, isolamos o movimento real daqueles 15 minutos e eliminamos o efeito de rolagem de contratos. (Mas todas as tabelas de nível também estão prontas em `TABELAS.md`). |
| **"Como foi calculado o índice dolarizado?"** | `1000 × WIN ÷ WDO`. Como o WIN está em pontos do Ibovespa e o WDO é cotado em reais por US$ 1.000, essa razão dá exatamente o Ibovespa em dólares (~22.200 pontos). O minuto `T` vem do pico de volume do WIN nos 993 pregões em que os dois ativos negociaram juntos. |
| **"Dá para operar comprando em T e saindo em T+15?"** | Não diretamente a partir deste gráfico, porque a separação entre "dia de alta" e "dia de baixa" usa o fechamento do final do dia. Sem essa separação (olhando todos os dias juntos), a mediana de `T` para `T+15` fica próxima de zero. |
| **"Por que não cruzaram o fluxo do estrangeiro com os candles?"** | Porque a página pública gratuita do Dados de Mercado fornece apenas os últimos 12 meses (nov/2025 a nov/2026), enquanto nossa base limpa de candles de exploração vai de 2020 a abr/set de 2025. |
