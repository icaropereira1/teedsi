# Status do projeto `bigplayer`

> Leia este arquivo primeiro. Ele diz **em que pé o projeto está**, **o que cada commit trouxe** e **qual é o próximo passo**.
> O plano completo e o checklist estão em [`ARCHITECTURE.md`](ARCHITECTURE.md) (seção 8). Atualize este arquivo a cada etapa concluída.

> **Parte 2 (desde 2026-11-02):** a análise recomeçou em [`../pt2/`](../pt2/README.md), focada no preço em volta dos horários de pico de volume. Este arquivo registra a parte 1.

**Última atualização:** 2026-10-14 · **Fase atual:** 2 — Hipótese de sinal (Gate 1 em M1: no-go; aguardando decisão do grupo) · **Branch:** `feat/bigplayer-win-eda` (a partir da `main`; análise inicial do WIN)

## Em uma frase
Estamos construindo um sistema que detecta atuação de grandes operadores (muitos contratos) no **mini dólar (WDO)** e segue a direção deles. Já está pronto: arquitetura, carga dos dados, split com hold-out trancado e a análise de qualidade dos dados. **Falta tratar os problemas encontrados nos dados e então partir para a EDA de indicadores.**

## Decisões já tomadas
| Decisão | Valor |
|---|---|
| Ativo | WDO (mini dólar). WIN fica para replicação futura |
| "Big player" | Evento de fluxo anômalo **inferido** (candle M1 não identifica agentes) |
| Capital-alvo | Não definido por ora |
| Realismo | Máximo: custos, latência e execução no candle seguinte (sem look-ahead) |
| Hold-out | Últimos 12 meses, **a partir de 2025-04-02**; trancado até a Fase 6 |
| Arquitetura | Orientada a eventos, mesmo núcleo de decisão em backtest e produção |
| Fluxo de trabalho | Checklist de fases (sem divisão por pessoa); avançar pelo primeiro `[ ]` |

## Como rodar (do zero)
```bash
git clone git@github.com:icaropereira1/teedsi.git && cd teedsi
git checkout feat/bigplayer-arquitetura
python -m venv .venv && source .venv/bin/activate
pip install pandas numpy pyarrow matplotlib pytest   # mínimo; ou: pip install -r requirements.txt
# colocar WDO$N_M1.csv (e WIN$N_M1.csv) em data/raw/ (fora do git)
cd bigplayer
python notebooks/00_carga_e_split.py             # gera os parquets e reports/split_manifest.json
MPLBACKEND=Agg python notebooks/01_qualidade_dados.py   # gera reports/figures/01_*.png
# mini índice: prefixar com BIGPLAYER_ASSET=WIN (gera wdo_* e win_* separados)
python -m pytest                                  # 3 testes (split e trava do hold-out)
```
Os notebooks são scripts `.py` com células `# %%`: abrem como notebook no VS Code ou via jupytext.

> **Regra de ouro:** notebooks e modelos usam **sempre** `load_exploration()`. O hold-out só abre com `load_holdout(i_understand_this_burns_the_holdout=True)`, uma vez, na avaliação final.

## O que foi commitado
Commit 1 — **Arquitetura e documentação**: `bigplayer/docs/ARCHITECTURE.md` (problema, tese, arquitetura, regras de realismo, plano em fases, decisões, riscos).

Commit 2 — **Notebooks 00 e 01 e infraestrutura de dados** (Fase 0 completa; Fase 1 parcial):
- `bigplayer/configs/split.toml`: ativo, arquivo bruto, data de corte do hold-out.
- `bigplayer/src/ingestion/loader.py`: leitura do CSV do MT5 e acesso controlado (`load_exploration`, `load_holdout` com trava).
- `bigplayer/src/ingestion/split.py`: split temporal sem embaralhar.
- `bigplayer/tests/test_split.py`: 3 testes (sem sobreposição, exige ordenação, hold-out trancado).
- `bigplayer/notebooks/00_carga_e_split.py`: carga, tipagem, split e gravação.
- `bigplayer/notebooks/01_qualidade_dados.py`: análise de qualidade (somente exploração).
- `bigplayer/reports/split_manifest.json` e `bigplayer/reports/figures/01_*.png`: resultados versionados.
- `bigplayer/pyproject.toml`, `bigplayer/.gitignore` (parquets ficam só locais) e `pyarrow` no `requirements.txt` da raiz.

Não vão para o git: `data/raw/` (CSVs) e `bigplayer/data/{interim,holdout,processed}/` (parquets; regenerar com o notebook 00).

## Achados da qualidade dos dados (notebook 01, WDO, exploração)
Exploração: 575.144 barras · 17/09/2020 → 01/04/2025 · 1.038 dias. Hold-out: 142.088 barras · 250 dias.

**Está bem:** sem nulos, sem timestamps duplicados, série ordenada, OHLC 100% consistente, preços sempre múltiplos de 0,5 (tick do WDO), nenhum minuto com volume zero.

**Problemas e conclusões:**
1. **Fuso horário: é horário de Brasília (B3).** Primeira barra 09:00; picos de volume às 09:00, 09:30, 10:00, 10:30, 11:00, 12:00 e 15:00. Não precisa converter.
2. **Fechamento muda:** 17:59 de ~mar a out e 18:29 de ~nov a fev (2020 a 2023); **a partir de 2024 é sempre 18:29**. O calendário de sessão precisa tratar isso.
3. **⚠️ Buracos grandes nos dados** (dias úteis sem nenhuma barra, que não são feriado):
   - 24/11/2021 → 01/12/2021 (6 dias)
   - 15/07/2022 → 28/07/2022 (10 dias)
   - **05/06/2023 → 19/09/2023 (77 dias úteis, ~3,5 meses)**
   Mais 53 faltas isoladas, compatíveis com feriados. **Esta é a inconsistência mais séria**: precisa de decisão (usar só dados após set/2023, descartar o trecho, ou buscar outra fonte para o intervalo).
4. **`SPREAD` não é confiável:** 500 em 2020 a 2022, depois ~1 e até 2500. **Descartado**; custos serão modelados por fora.
5. **`VOL/TICKVOL`** (lote médio por negócio): mediana 3,4, p99 7,6; correlação log–log 0,96 entre os volumes. É compatível com `VOL` = contratos e `TICKVOL` = negócios. Em 6 barras `VOL < TICKVOL` (anomalia menor, investigar). Lote médio é um bom candidato a proxy de "lote grande".
6. **Forte sazonalidade intradiária:** volume nas primeiras horas é ~3 vezes o da tarde. Qualquer indicador de volume **precisa ser normalizado por horário** (RVOL), senão detectamos o relógio e não o big player.
7. **Gaps intradia** são raros (21, todos até 2022). **Outliers**: 105 barras com |z| > 10 no retorno de 1 min. As 8 maiores caem em horários de abertura/notícia (09:30, 10:30, 11:00...) com volume alto, o que sugere evento real e não erro de dado (as demais 97 não foram inspecionadas uma a uma).
8. **Rolagem:** não há salto sistemático óbvio; o |gap overnight| médio no 1º dia útil do mês é 0,45% vs ~0,3% nos demais (efeito leve). O maior gap (−4,2% em 29/07/2022) é explicado pelo buraco de 10 dias (item 3), não por rolagem.

## Achados da análise de insights (notebook 02, WDO, exploração)
Gerados por `notebooks/02_insights.py` (figuras em `reports/figures/02_*.png`).

1. **Dividir o volume pela mediana do horário corrige demais.** O volume da tarde varia mais (desvio do log do volume de 0,73 às 17h contra 0,55 às 9h), então a razão `vol / mediana do mesmo minuto nos 20 pregões anteriores` joga os alertas para o fim do dia: 22% do top 1% cai às 17h (no volume bruto, 77% cai entre 9h e 12h). O **z-score do log do volume** (média e desvio do mesmo minuto nos 20 pregões anteriores, só passado) distribui os alertas quase por igual: de 8% a 13% por hora, contra 11% esperados ao acaso. Nesses minutos, o |retorno| mediano de 1 min é 7,1 bps contra 1,9 bps no geral (movimento no mesmo minuto, não previsão).
2. **Lote médio alto, sozinho, marca minuto calmo, não big player.** No decil mais alto de `VOL/TICKVOL`, a mediana de negócios por minuto é 608 (contra 1.163 no geral) e o |retorno| mediano é 1,0 bp (contra 1,9). Lote alto aparece sobretudo quando há poucos negócios, e aí um único negócio grande pesa muito na média. O lote também varia com o horário (mediana de 2,95 às 9h e ~3,5 à tarde). Isso relativiza o item 5 acima: usar o lote como filtro junto com o volume normalizado, e normalizá-lo por horário também.

## Análise inicial do Mini Índice (WIN) — 2026-10-14
Rodar com `BIGPLAYER_ASSET=WIN` (config em `configs/split_win.toml`; mesmas regras do WDO). Notebooks 00 e 01 rodados; figuras em `reports/figures/win/01_*.png`, manifesto em `reports/split_manifest_win.json`. O hold-out do WIN segue a mesma regra do WDO (últimos 12 meses): **a partir de 2025-09-26, trancado**. *Corte a confirmar pelo grupo.*

Exploração: 617.846 barras · 15/10/2020 → 25/09/2025 · 1.119 dias. Hold-out: 139.870 barras · 249 dias.

**Está bem:** sem nulos, sem duplicatas, ordenado, OHLC 100% consistente, preços sempre múltiplos de 5 (tick do WIN), nenhum minuto com volume zero. Mesmo fuso do WDO (horário de Brasília, 1ª barra 09:00).

**Diferenças e pontos de atenção em relação ao WDO:**
1. **Buracos nos dados, os mesmos do WDO, só que maiores:** 15/11/2021 → 01/12/2021 (13 dias úteis), 15/07/2022 → 27/07/2022 (9) e **05/06/2023 → 16/10/2023 (96 dias úteis)**. Mais 54 faltas isoladas (feriados). A decisão do grupo (ignorar) vale; features com janela móvel atravessam os buracos.
2. **Fechamento:** 17:54 (~mar a out, 2021 a 2023) e 18:24 (~nov a fev); desde 2024 sempre 18:24. É o mesmo calendário do WDO, 5 min antes (17:59/18:29 no WDO).
3. **Dia parcial:** 17/10/2023 tem só 57 barras (primeiro dia depois do buraco de 96 dias).
4. **`SPREAD` não é informativo:** vale 5 (ou 0 em poucos dias). Descartado, como no WDO.
5. **`VOL/TICKVOL`:** mediana 3,5 e p99 5,3 (WDO: 3,4 e 7,6); correlação log–log 0,97. Só 2 barras com `VOL < TICKVOL`. Há **outliers de lote** em barras pós-fechamento (ex.: 02/12/2021 18:31, 2 negócios e 12.679 contratos, lote 6.339): filtrar barras fora de 09:00–17:59 antes de usar o lote.
6. **Rolagem:** o contínuo roda nos meses pares (vencimento perto do dia 15). Não há salto sistemático: o |gap overnight| médio nos dias 13 a 18 dos meses pares é 0,5 a 0,8% contra ~0,3% nos demais dias, efeito leve e pouco regular. Os maiores gaps (3 a 5%) coincidem com os buracos nos dados e com dias de notícia. Maior gap: −5% em 02/12/2021, logo após o buraco de nov/2021.
7. **Outliers:** 110 barras com |z| > 10 no retorno de 1 min (WDO: 105), com volume muito alto em horários de notícia (07/04/2025 11:11, 09/04/2025 14:20–14:29, 10/11/2022 10:32...). Compatíveis com evento real.
8. **Escala:** o WIN negocia 5,8 vezes o volume do WDO (23.861 contratos/min contra 4.126, mediana; ~15,8 milhões de contratos por pregão) e 5,7 vezes os negócios (6.654 contra 1.163 por min). Um lote grande é mais diluído: a mesma ordem pesa menos no minuto.

**Insights de volume e lote (equivalente ao notebook 02, números calculados, sem figuras de slide):**
1. **O horário domina o volume bruto, e mais ainda que no WDO.** 81% do 1% de minutos mais cheios cai entre 9h e 11h59 (WDO: 77%), e **50% só na hora das 10h**, por causa do pico às **10:30** (mediana de 78.703 contratos no minuto; no WDO o pico era às 09:01). Isso é abertura de dados dos EUA, não big player. O mínimo das 09:00 é baixo (28.361) e 09:01 é 64.605.
2. **Z-score por horário continua sendo a normalização certa.** Alertas do 1% mais extremo ficam de 8% a 13% por hora (11% ao acaso). A razão simples `vol / mediana do mesmo minuto` repete o defeito do WDO: manda 23% dos alertas para as 17h e só 2% para as 10h. O desvio do log do volume sobe de 0,42 (10h) para 0,56 (17h). Nesses minutos, o |retorno| mediano é 8,3 bps contra 2,2 no geral (4x; WDO: 3,7x).
3. **Lote médio alto, sozinho, também marca minuto fraco.** No decil mais alto de lote, a mediana é de 4.806 negócios por minuto (contra 6.654 no geral) e o |retorno| mediano é 1,7 bp (contra 2,2). O efeito é mais suave que no WDO (608 contra 1.163 negócios, 1,0 contra 1,9 bp). O lote mediano sobe com a hora (3,05 às 9h; ~3,6 à tarde): normalizar por horário também.
4. **Volume diário estável:** mediana de 13,4 a 18,5 milhões de contratos por pregão ao longo dos anos (pico em 2021, queda em 2025).

**Conclusão:** o WIN tem a mesma qualidade e as mesmas armadilhas do WDO (buracos, sazonalidade intradiária, lote não-confiável isolado). Nada impede replicar o pipeline. Duas particularidades: os picos de volume do WIN são ainda mais ligados a horários de notícia (10:30), e há barras pós-fechamento com lote absurdo que devem ser filtradas.

## Calendário e marcação de buracos — 2026-10-14
Código: `src/cleaning/calendar.py` (sessão, feriados), `src/cleaning/holes.py` (auditoria e marcação), `tests/test_calendar_holes.py` (6 testes; 9 no total), `notebooks/03_calendario_buracos.py` (roda com `BIGPLAYER_ASSET=WDO|WIN`; grava `reports/buracos_<ativo>.csv`).

**Calendário (conferido contra os dados dos dois ativos):**
- Sessão abre 09:00. Última barra: WDO 17:59 / 18:29, WIN 17:54 / 18:24. A sessão curta vale do 1º pregão após o início do horário de verão dos EUA até o fim dele; **desde 2024 é sempre a longa**. Exceção: WDO fechava 17:55 na curta de set–out/2020.
- Quarta-feira de Cinzas abre às **13:00** (325 barras no WIN, confere em 5 anos).
- Feriados: Carnaval (seg e ter), sexta-feira santa, Corpus Christi, 1/1, 21/4, 1/5, 7/9, 12/10, 2/11, 15/11, 24/12, 25/12, **31/12 (ou último dia útil do ano)** e **20/11 só a partir de 2024** (a B3 operou em 2023).
- Duas ausências sem regra conhecida, inferidas por estarem ausentes nos dois ativos: 25/01/2021 e 09/07/2021 (`OBSERVED_CLOSURES`; confirmar com a B3 se importar).
- Resultado: com essas regras, **todo dia útil ausente é um buraco real**. Nenhuma ausência isolada sobra sem explicação.

**Buracos (dias úteis esperados e ausentes):**
| Ativo | Buraco | Pregões ausentes |
|---|---|---|
| WDO | 24/11/2021 → 01/12/2021 | 6 |
| WDO | 15/07/2022 → 28/07/2022 | 10 |
| WDO | 05/06/2023 → 19/09/2023 | 75 |
| WIN | 16/11/2021 → 01/12/2021 | 12 |
| WIN | 15/07/2022 → 27/07/2022 | 9 |
| WIN | 05/06/2023 → 16/10/2023 | 93 |

(Os números do notebook 01 contavam feriados dentro do buraco, por isso eram um pouco maiores.)

**Marcação (por barra, sem remover nada):** `session_date`, `in_session`, `segment` (id do trecho contínuo), `day_in_segment`, `partial_day`, `after_intraday_gap`. Feature com janela de N pregões só vale com `lookback_ok(marked, N)`, ou seja, `day_in_segment > N`. Com isso, 93% das barras servem para janela de 20 pregões e 77% (WDO) a 79% (WIN) para 60.

**Observações:**
- **Pregões parciais ao lado dos buracos:** WDO 23/11/2021 (54 barras), 29/07/2022 (29) e 20/09/2023 (279); WIN 17/10/2023 (57). Marcados como `partial_day`; decisão do grupo: **não entram** (coluna `usable = False`).
- **Barras fora da sessão:** 3 no WDO (18:00, quase sem negócio) e 8 no WIN. Seis delas são só um minuto a mais no fim do dia, com volume normal (17:55, 18:25: 700 a 1.200 negócios), e **não** são lixo. As duas com lote absurdo são `2021-10-28 18:01` e `2021-12-02 18:31` (2 negócios, 6.557 e 12.679 contratos), mais `2022-02-07 18:31` (1 negócio). **Decisão do grupo: todas as barras fora da sessão são descartadas** (`usable = False`), sem exceção manual.
- **Início do WIN** (15/10/2020) é às 11:49, não 09:00; a 1ª sessão é incompleta mas não cai na regra de parcial (> 60%).
- Pausas intradiárias de 5+ min: 13 no WDO e 6 no WIN (marcadas, sem tratamento).

## Rolagem, dicionário e dataset limpo — 2026-10-14
**Correção:** a nota anterior de que a rolagem tinha "efeito leve" valia para o WDO e **estava errada para o WIN**. Medindo o gap overnight na abertura do dia certo, a troca de contrato é clara nos dois:

| Ativo | Dia da troca (abertura traz o contrato novo) | Gap overnight na troca (mediana, com sinal) | Nos demais dias |
|---|---|---|---|
| WIN | quarta-feira mais próxima do dia 15 dos meses pares | **+1,49%** (91% positivos; n=27) | +0,02% |
| WDO | último pregão do mês | **+0,36%** (81% positivos; n=51) | −0,04% |

É carry entre contratos, que acompanha a Selic (WIN: ~0,3% em 2020, ~2% em 2022 e 2025). Não é movimento de mercado.

**Decisão aplicada:** não ajustar o preço, só **marcar** (`roll_day`). Regra: **nunca usar retorno que atravesse a abertura de um `roll_day`** (retorno overnight, rótulo de vários dias). Retornos intradiários não são afetados. Código: `calendar.roll_days`, `holes.mark_bars`.

**Dicionário de dados:** `docs/DICIONARIO_DADOS.md` (colunas, marcações, invariantes e buracos).

**Dataset limpo:** `notebooks/04_dataset_limpo.py` grava `data/interim/<ativo>_m1_limpo.parquet` (só exploração, 15 colunas, nenhuma barra removida; `spread` fora). Leitura: `load_clean()` e filtro `usable`. WDO: 575.144 barras, 99,90% usáveis. WIN: 617.846 barras, 99,99% usáveis. O hold-out não foi tocado; o mesmo `mark_bars` será aplicado a ele na Fase 6.

## Fase 2 — Estudo de evento (Gate 1) — 2026-10-14
Código: `src/features/flow.py`, `src/evaluation/event_study.py`, `notebooks/05_estudo_evento.py` (WDO; WIN com `BIGPLAYER_ASSET=WIN`), `reports/estudo_evento_<ativo>.csv`. 14 testes passam.

**Desenho (pré-registrado no cabeçalho do notebook, antes de ver resultado):**
- 3 definições de evento: **E1** `z_vol ≥ 3`; **E2** `z_vol ≥ 3` e `z_lot ≥ 1`; **E3** média de `z_vol` nas 5 últimas barras `≥ 2`. Direção = sinal do movimento do preço (barra, ou 5 barras no E3).
- Entrada na abertura da barra seguinte, saída no fechamento de `t+h` (h = 1, 5, 15, 30, 60 min), sempre no mesmo pregão.
- Episódios com cooldown de 30 min. Controle: barras comuns (`z < 1`) da mesma hora e do mesmo quintil de |retorno|. Bootstrap por dia; 15 testes, **limite de Bonferroni p < 0,0033**.
- Só exploração; hold-out intocado.

**Resultado: nenhum dos 15 testes passa, nos dois ativos.**
| | WDO | WIN |
|---|---|---|
| Episódios (E1 / E2 / E3) | 1.619 / 655 / 849 | 2.140 / 795 / 925 |
| Menor p | 0,068 (E1, 1 min) | 0,064 (E3, 15 min) |
| Efeito (bps), faixa | −1,2 a +0,3 | −2,3 a +1,5 |
| Taxa de acerto | 38% a 48% | 43% a 49% |
| Efeito positivo em quantos anos (de 6) | 1 a 4, sem padrão | 2 a 5, sem padrão |

- **Sem sinal de continuação.** Em quase todas as células o efeito é negativo ou nulo: depois do pico de volume, o preço tende a *não* seguir (leve reversão em 1 a 5 min no WDO), mas nada passa a correção de múltiplos testes.
- **Pouco poder estatístico para efeitos pequenos.** Os intervalos de 95% têm largura de 1 a 5 bps. Não dá para excluir um efeito de ~1 bp. Mesmo assim, 1 tick vale ~0,95 bp (WDO) e ~0,41 bp (WIN), e o custo de ida e volta fica em 2 a 3 ticks no mínimo, então um efeito dessa ordem não sobreviveria ao Gate 2.
- **Instabilidade por ano:** o sinal do efeito troca de ano para ano (ex.: WDO E1 em 60 min: +5,96 em 2020, −2,76 em 2021). Típico de ruído.

**Registro completo, com tabelas e explicação do porquê: `docs/RESULTADO_GATE1_RODADA1.md`.**

**Leitura do Gate 1:** com candles de 1 min e estas definições, **não há evidência de que o evento de fluxo anômalo preveja o preço**. Pela regra pré-registrada, o resultado é *no-go* nestas definições. A decisão de go/no-go é do grupo (registrar na seção 9 do `ARCHITECTURE.md`).

**Opções (ainda não executadas):**
1. **Novas definições**, declaradas antes de rodar: absorção (muito volume com preço parado), esforço × resultado, fluxo assinado por barra, ou condicionar por regime (abertura, dias de notícia). Cada nova definição aumenta o nº de testes; mantém-se o pré-registro e a correção.
2. **Dado tick a tick** (previsto no plano): com M1 a direção do fluxo é inferida só do movimento do preço, o que perde muito sinal.
3. **Encerrar a hipótese** e registrar o resultado negativo, que também é um resultado do projeto.

## Fase 2 — Gate 1, rodada 2 — 2026-10-14
Pré-registro congelado em `docs/PRE_REGISTRO_GATE1_RODADA2.md`; resultado em `docs/RESULTADO_GATE1_RODADA2.md`. Código: `notebooks/06_estudo_evento_r2.py`; 15 testes passam.

**Resultado (WDO): nenhuma das 3 definições passa o Gate 1** (0 de 15 testes; limite p < 0,0017).
- **P1 (fluxo persistente) e X1 (pressão no extremo):** sem sinal, efeito negativo ou nulo.
- **A1 (pausa com volume):** único com efeito positivo, +1,34 bps em 15 min, p = 0,0145, 6 de 6 anos. **Não passa o limite corrigido.** Candidato a confirmação, não "go".
- WIN não foi rodado (pré-registro: só replica o que passar).

**Decisão pendente do grupo:** confirmar A1 (15 min) no WIN como teste único e pré-registrado, ou encerrar M1 e decidir sobre dado tick a tick.

## Confirmação do A1 no WIN — 2026-10-14
Pré-registro: `docs/PRE_REGISTRO_CONFIRMACAO_A1_WIN.md`; resultado: `docs/RESULTADO_CONFIRMACAO_A1_WIN.md`; código: `notebooks/07_confirmacao_a1_win.py`.

**Não confirma.** A1 em 15 min no WIN: +0,95 bps, IC 95% [−0,46; +2,36], **p = 0,176**, 617 episódios, 4 de 6 anos positivos. Direção e ordem de grandeza batem com o WDO (+1,34), mas o resultado é compatível com zero.

**Gate 1 para dado M1: no-go** (6 definições, 2 ativos, 5 horizontes, nenhuma passa).

**Decisão pendente do grupo:** (1) dado tick a tick, (2) uma nova rodada em M1 só com hipótese nova, ou (3) encerrar.

## Próximo passo (primeiro `[ ]` do checklist)
**Gate 1 (M1): no-go.** Aguardando decisão do grupo entre dado tick a tick, nova rodada com hipótese nova ou encerramento. As Fases 3 a 5 só começam com um passe no Gate 1.

## Decisões recentes (do grupo)
- **Buraco de jun–set/2023 (e os outros buracos): ignorar.** Seguimos com os dados como estão. Consequência a lembrar: features com janela móvel (ex.: RVOL de N dias) atravessam o buraco; no cálculo, não misturar barras de lados diferentes de um buraco sem avisar.
- **Nome dos arquivos:** `WDON_M1.rar` / `WINN_M1.rar` eram os originais compactados; os `.csv` extraídos (`WDO$N_M1.csv`, `WIN$N_M1.csv`) são os que usamos. Nada a renomear.
- **Git:** branch publicada com push; o PR para `main` ainda não foi aberto (decidir quando).

## Perguntas em aberto
- Nenhuma no momento. Próximo passo: calendário de pregão B3, rolagem e dicionário de dados (Fase 1).
