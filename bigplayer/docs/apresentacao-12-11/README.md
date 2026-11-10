# Apresentação 12/11 — o que foi feito nas últimas alterações (Big Player)

> Guia para quem vai montar os slides. Leia na ordem. Os números abaixo foram conferidos nos arquivos da pasta `dados/`.
> Pasta `apresentacao-12-11` (a data é 12/11; o `/` não vale em nome de pasta).

## 0. Resumo em 8 linhas
1. Na última apresentação, olhamos o preço só em **T-1 e T** (horários fixos de 30 em 30 min). O professor pediu para **ampliar**.
2. Passamos a olhar também **T+3, T+5, T+10 e T+15**.
3. Separamos tudo em **dias de alta** e **dias de baixa**.
4. Mudamos o T: em vez de um horário fixo, **T é o minuto de pico de volume** (a cada janela de 30 minutos e no pregão inteiro).
5. Passamos a trabalhar **sempre com a mediana** e **em pontos** (não em bps). Bonferroni foi abandonado a pedido do grupo.
6. Fizemos a mesma análise no **índice dolarizado** (WIN ÷ WDO), que é como o **investidor estrangeiro** enxerga o mercado brasileiro.
7. Buscamos o **fluxo de investidores** (estrangeiro × pessoa física) no Dados de Mercado e fizemos o gráfico de divergência.
8. **Achado principal:** o preço continua na direção do dia depois do pico de volume, mais forte de manhã. **Limitação importante:** "dia de alta/baixa" só se conhece no fim do pregão, então isso é descritivo, não é um sinal operável.

## 1. Conteúdo da pasta

| Caminho | O que é |
|---|---|
| `README.md` | Este guia |
| `ROTEIRO_APRESENTACAO.md` | Roteiro completo de fala para 7 slides (~10–12 min) |
| `TABELAS.md` | **Todas** as tabelas (WDO, WIN, dolarizado × alta/baixa × 19 janelas), prontas para virar slide |
| `graficos/01_todos_vs_alta_baixa_dia.png` | Pico do `DIA` (`T−1` a `T+15`): por que separar alta e baixa revela o movimento |
| `graficos/02_wdo_win_janelas_30min.png` | WDO e WIN nas 18 janelas de 30 min (`T` vs `T+15`): manhã × tarde |
| `graficos/03_indice_dolarizado_manha_tarde.png` | Índice dolarizado (`1000 × WIN / WDO`): evolução `T−1` a `T+15` e janelas de 30 min |
| `graficos/04_fluxo_estrangeiro_x_pf.png` | Gráfico de divergência estrangeiro × pessoa física (no padrão visual dos slides; também em `f1_estrangeiro_x_pf.png`) |
| `graficos/05_resumo_comparativo_t15.png` | Painel resumo comparando manhã, tarde e pico do `DIA` em `T+15` nos 3 ativos |
| `dados/medianas_pico30/` | 9 CSVs com as medianas (`pico30_<wdo|win|dolarizado>_<alta|baixa|todos>.csv`) |
| `dados/eventos/` | 3 arquivos `.parquet` com cada pico e cada offset (base para novos gráficos) |
| `dados/fluxo_investidores/fluxo_investidores.csv` | Fluxo diário por tipo de investidor (R$ milhões) |
| `dados/etapas_intermediarias/` | Versões anteriores (em bps e por hora cheia) e a tabela antiga T-1/T. Só para consulta |
| `codigo/` | Cópia dos scripts e do módulo usados. Os originais ficam em `bigplayer/notebooks/` e `bigplayer/src/evaluation/` |

Colunas dos CSVs de `medianas_pico30`: `grupo` (início da janela de 30 min, ou `DIA`), `offset` (-1, 0, 3, 5, 10, 15 minutos em relação a T),
`n` (nº de picos/pregões), `mediana_preco` (mediana do fechamento do candle, em pontos) e `mediana_pts` (mediana da variação em pontos contra T-1).

## 2. O pedido do professor (o ponto de partida)
Tínhamos a tabela `tabela-mediana-t1-t.csv`: para cada horário (09:30, 10:00, ... 17:30), a mediana do fechamento em T-1 e em T.
Pedidos:
1. Olhar também T+3, T+5, T+10 e T+15.
2. Repetir a análise separando **dias de alta** e **dias de baixa** do mercado.
3. Olhar o **índice dolarizado** (WIN ÷ WDO), porque o investidor estrangeiro vê o índice em dólares.

Decisões do grupo ao longo da conversa: usar **sempre a mediana**, trabalhar **em pontos**, esquecer o Bonferroni, e usar **T = pico de volume**.

## 3. Definições (precisam estar claras nos slides)

- **Candle:** barra de 1 minuto. Todos os preços usados são o **fechamento** do candle.
- **T-1, T, T+3, T+5, T+10, T+15:** o candle um minuto antes do pico, o candle do pico, e os candles 3, 5, 10 e 15 minutos depois.
- **T (pico de volume):** o minuto de maior volume (`vol`) dentro de cada janela de **30 minutos** (09:00, 09:30, ..., 17:30) e também o minuto de maior volume do **pregão inteiro** (linha `DIA`).
- **Dia de alta / baixa:** o dia é de alta quando o último fechamento do pregão fica acima da primeira abertura do pregão, e de baixa no contrário. **Cada série é classificada pelo próprio movimento.** Dias neutros (igual) ficam de fora: 3 no WDO e 3 no WIN.
- **Mediana do preço:** mediana, entre pregões, do preço em cada ponto. **Cuidado:** o nível do preço muda muito de um dia para outro (o WDO vai de cerca de 5.237 a 5.312). Por isso, para comparar o comportamento em torno de T, use a **mediana da variação contra T-1** (Tabela B), não a do preço (Tabela A).
- **Índice dolarizado:** `1000 × WIN ÷ WDO`. O WIN está em pontos do índice e o WDO é R$ por US$ 1.000, então a série equivale ao **Ibovespa em dólares** (cerca de 22.000 pontos).
  - O T vem do pico de volume do **WIN**.
  - A classificação alta/baixa é do **próprio índice dolarizado**.
  - Só entram pregões em que WIN e WDO existem: **993 pregões** (524 de alta, 469 de baixa), de 15/10/2020 a 01/04/2025.
- **Amostra:** WDO 1.034 pregões (512 de alta, 519 de baixa); WIN 1.118 pregões (584 de alta, 531 de baixa). Só dados de **exploração** (o hold-out de 12 meses continua trancado).

## 4. O que cada etapa fez (histórico, em ordem)

### Etapa 1 — T-1, T, T+3 ... T+15 com horários fixos, todos os dias (bps)
Validamos primeiro: reproduzimos a tabela antiga com diferença **0** nos dois ativos. Depois acrescentamos os horizontes.
Resultado: **a mediana é praticamente 0** em todos os horizontes (no WDO a mediana vira 0 porque o preço anda em passos de 1 tick). Misturando alta e baixa, uma coisa anula a outra.
Arquivos: `dados/etapas_intermediarias/horizontes_*_todos.csv`.

### Etapa 2 — separar dias de alta e dias de baixa (horários fixos, bps)
Aqui o sinal aparece: depois de T o preço **continua na direção do dia**, e cresce com o horizonte.
Exemplo, WIN às 10:30, mediana em T+15: **+5,81 bps** nos dias de alta e **−7,86 bps** nos de baixa.
Arquivos: `horizontes_*_alta.csv` e `horizontes_*_baixa.csv`.

### Etapa 3 — T = pico de volume, em pontos, janelas de 1 hora
Primeira versão do pedido "em pontos" e "T = pico de volume". O grupo notou que só olhávamos de hora em hora, e então passamos para 30 minutos.
Arquivos: `pico_volume_*.csv` (substituídos pela etapa 4, só para consulta).

### Etapa 4 — janelas de 30 minutos (versão final para a apresentação)
Mesmo método, agora com 18 janelas de 30 min (09:00 a 17:30) mais a linha `DIA`, para WDO e WIN.
Arquivos: `dados/medianas_pico30/pico30_wdo_*.csv` e `pico30_win_*.csv`.

### Etapa 5 — índice dolarizado (WIN ÷ WDO)
Mesma análise da etapa 4, na série dolarizada. Arquivos: `pico30_dolarizado_*.csv`.

### Etapa 6 — fluxo de investidores (estrangeiro × pessoa física)
Ver seção 6.

## 5. Resultados principais (pico de volume do pregão inteiro, linha `DIA`)
Mediana da variação em pontos contra T-1:

| Série | Dia | n | T | T+3 | T+5 | T+10 | T+15 |
|---|---|---|---|---|---|---|---|
| WDO | alta | 504 | +2,50 | +2,00 | +2,00 | +2,25 | +2,50 |
| WDO | baixa | 511 | −5,00 | −4,50 | −4,50 | −3,50 | −4,00 |
| WIN | alta | 578 | +112,5 | +100,0 | +105,0 | +102,5 | +95,0 |
| WIN | baixa | 530 | −110,0 | −97,5 | −75,0 | −100,0 | −105,0 |
| **Dolarizado** | alta | 518 | +25,33 | +23,79 | +23,95 | +26,75 | +26,98 |
| **Dolarizado** | baixa | 468 | −25,73 | −25,03 | −24,70 | −22,97 | −28,67 |

O que isso mostra:
- **O candle de pico já vem com movimento forte na direção do dia.** Há uma devolução pequena em T+3, mas o preço **não reverte**; no dolarizado ele ainda avança até T+15.
- **De manhã o efeito é maior.** No dolarizado, às 10:00: +9,69 em T e +14,04 em T+15 nos dias de alta; −10,32 e −20,12 nos de baixa. Depois das 13:00 os valores caem para algo entre 0 e 5 pontos.
- **No WDO a mediana é discreta** (valores perto de 0, ±0,5, ±1,0...), porque o preço anda de 0,5 em 0,5 ponto.
- Todas as tabelas, janela por janela, estão em `TABELAS.md`.

## 6. Fluxo de investidores: estrangeiro × pessoa física

**Fonte:** Dados de Mercado, https://www.dadosdemercado.com.br/fluxo (tabela pública, gratuita). Saldo diário (compras − vendas) em **R$ milhões**.

**O que tentamos:** a API do site (`GET /v1/investors`) exige token (sem ele responde `401 Missing token`). O "dump" de 5 anos aparece listado, mas o link responde 404. **Decisão do grupo: usar só os dados gratuitos da página.**

**Cobertura:** 245 pregões, de **11/11/2025 a 06/11/2026**. Isso **não coincide** com os dados de WIN e WDO (que terminam em abr/2025 e set/2025), portanto **não cruzamos o fluxo com o preço**. O gráfico mostra só a divergência entre os dois investidores.

**Gráfico:** `graficos/f1_estrangeiro_x_pf.png`
- Em cima, o saldo **acumulado** de cada um (R$ bilhões). Embaixo, a correlação entre os dois em janela de 20 pregões.
- **Correlação diária: −0,57. Em 68% dos dias os dois têm sinais opostos** (um compra enquanto o outro vende).
- O estrangeiro acumulou cerca de R$ 70 bi até abril de 2026 e caiu para cerca de R$ 14 bi em agosto. Nesse trecho a pessoa física foi no sentido contrário (de cerca de −7 bi para +9 bi).
- A correlação de 20 pregões ficou quase sempre negativa e chegou perto de −1 em outubro de 2026.

Estatísticas diárias (R$ milhões): estrangeiro média 130, desvio-padrão 1.499; pessoa física média 80, desvio-padrão 722.

## 7. Limitações (devem aparecer na apresentação, são o que dá credibilidade)
1. **Alta/baixa usa o dia inteiro.** Só sabemos se o dia foi de alta ou de baixa no fechamento. Os números são **descritivos**, não uma estratégia que se possa operar. Parte do efeito é a própria tendência do dia.
2. **Sem teste estatístico.** A pedido do grupo, tudo é mediana, sem p-valor nem Bonferroni. Não dá para afirmar significância.
3. **Janelas das pontas têm menos amostra.**
   - 17:30: o pico cai perto do fim do pregão e falta T+15, então o pico é descartado (dolarizado: 427 de alta, 389 de baixa, contra cerca de 520 nas outras janelas).
   - 09:00: o pico que cai exatamente em 09:00 não tem T-1.
4. **Série dolarizada usa dois contratos diferentes** (WIN e WDO têm rolagens em datas diferentes). Os dias de rolagem **continuam na amostra**. Como cada medida olha só dentro do mesmo pregão (de T-1 a T+15), a troca de contrato não entra na variação, mas o **nível** do preço (Tabela A) pode misturar contratos diferentes entre dias. Por isso a Tabela B é a mais confiável.
5. **Fluxo não cruza com preço** (períodos diferentes, ver seção 6). É só uma visão da divergência.
6. **Hold-out intacto.** Nada disso usou os últimos 12 meses reservados.
7. **Resultado anterior continua valendo:** o Gate 1 deu no-go com candles de 1 minuto. Estas análises são descritivas e complementares, não revertem esse resultado.

## 8. Sugestões de slides
1. **Contexto:** o que o professor pediu (seção 2).
2. **Método:** T = pico de volume, janelas de 30 min, mediana em pontos, dia de alta × baixa (seção 3).
3. **WIN e WDO:** mostrar a Tabela B da linha `DIA` e de 2 ou 3 janelas da manhã.
4. **Dolarizado:** a mesma comparação (a tabela da seção 5), com a explicação de que é o Ibovespa em dólares.
5. **Fluxo de investidores:** o gráfico `f1_estrangeiro_x_pf.png` e os números de divergência.
6. **Limitações** (seção 7).

Os gráficos no padrão visual dos slides já estão gerados em `graficos/01_*.png` a `05_*.png`, e o roteiro de fala de 7 slides está em `ROTEIRO_APRESENTACAO.md`.

## 9. Como reproduzir
A partir de `teedsi/bigplayer/` (com o ambiente `../.venv`):

```bash
../.venv/bin/python notebooks/09_horizontes_t.py            # etapas 1 e 2 (horários fixos, bps)
../.venv/bin/python notebooks/10_pico_volume_pontos.py      # etapas 4 e 5 (pico de volume, pontos, WDO, WIN, dolarizado)
../.venv/bin/python notebooks/11_fluxo_investidores.py      # fluxo de investidores (página pública, sem token)
../.venv/bin/python notebooks/12_graficos_apresentacao.py   # gráficos da apresentação de 12/11 no padrão visual dos slides
```

O módulo com as funções está em `src/evaluation/horizons.py` (cópia em `codigo/horizons.py`).
Saídas: `reports/pico30_*.csv`, `data/processed/pico30_*_eventos.parquet`, `data/processed/fluxo_investidores.csv`, `reports/figures/fluxo/`.

Observação sobre `codigo/`: os scripts de lá são cópias para leitura e não rodam sozinhos fora de `teedsi/bigplayer/`.
