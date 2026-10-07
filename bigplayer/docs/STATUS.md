# Status do projeto `bigplayer`

> Leia este arquivo primeiro. Ele diz **em que pé o projeto está**, **o que cada commit trouxe** e **qual é o próximo passo**.
> O plano completo e o checklist estão em [`ARCHITECTURE.md`](ARCHITECTURE.md) (seção 8). Atualize este arquivo a cada etapa concluída.

**Última atualização:** 2026-10-07 · **Fase atual:** 1 — Dados (em andamento) · **Branch:** `feat/bigplayer-arquitetura` (local, ainda sem push/PR)

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
git checkout feat/bigplayer-arquitetura          # quando a branch for publicada
python -m venv .venv && source .venv/bin/activate
pip install pandas numpy pyarrow matplotlib pytest   # mínimo; ou: pip install -r requirements.txt
# colocar WDO$N_M1.csv em data/raw/ (fora do git)
cd bigplayer
python notebooks/00_carga_e_split.py             # gera os parquets e reports/split_manifest.json
MPLBACKEND=Agg python notebooks/01_qualidade_dados.py   # gera reports/figures/01_*.png
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

## Próximo passo (primeiro `[ ]` do checklist)
Ainda na **Fase 1 — Dados** (ver `ARCHITECTURE.md`, seção 8):
1. **Decisão do grupo sobre os buracos** (principalmente jun–set/2023). Opções: (a) usar só dados contínuos, descartando o trecho ou tudo antes dele; (b) buscar fonte alternativa para o intervalo. O hold-out (abr/2025 em diante) não é afetado.
2. Construir o **calendário de pregão B3** (sessões 17:59/18:29, feriados) em `src/cleaning/`.
3. Decidir o **tratamento da rolagem** do contínuo (efeito leve; talvez bastem marcar e excluir o 1º dia útil).
4. Escrever o **dicionário de dados** em `docs/`.
5. Salvar o dataset limpo em `data/interim/` e atualizar este STATUS.

Só depois disso começa a **Fase 2** (features de fluxo e estudo de evento, com o **Gate 1**: o sinal existe?).

## Perguntas em aberto
- Como tratar o buraco de jun–set/2023 (item 3)?
- Os arquivos se chamam `WDO$N_M1.csv` / `WIN$N_M1.csv` aqui, mas o README da raiz cita `WDON_M1` / `WINN_M1`. Qual nome vale?
- Publicar a branch e abrir PR quando? (por ora, tudo local)
