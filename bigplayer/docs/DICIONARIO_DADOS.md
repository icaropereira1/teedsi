# Dicionário de dados — WDO e WIN (candles de 1 minuto)

Fonte: export do MetaTrader 5, contínuo `$N` (`WDO$N_M1.csv`, `WIN$N_M1.csv`), em `data/raw/`.
Fuso: horário de Brasília (B3); `ts` é a abertura do candle, sem fuso explícito.

## Colunas do dado bruto (após `read_raw_csv`)
| Coluna | Tipo | Significado | Observações |
|---|---|---|---|
| `ts` | datetime | início do minuto (`DATE` + `TIME`) | ordenado, sem duplicatas |
| `open`, `high`, `low`, `close` | número | preços do minuto | WDO: tick 0,5 (float); WIN: tick 5 (int). OHLC 100% consistente |
| `tickvol` | int | **nº de negócios** no minuto | nunca zero nos dois ativos |
| `vol` | int | **nº de contratos** negociados no minuto | correlação log–log com `tickvol` de 0,96 a 0,97 |
| `spread` | int | **descartada** | WDO: 500 (2020–22), depois ~1 a 2500; WIN: constante 5. Não confiável; custos serão modelados à parte |

Minutos sem negócio **não existem** como barra (não há linha com volume zero).

Derivados úteis: `vol / tickvol` = lote médio por negócio (WDO: mediana 3,4; WIN: 3,5). Isolado, não
identifica big player (ver `STATUS.md`); normalizar por horário.

## Colunas de marcação (`mark_bars`, arquivo `data/interim/<ativo>_m1_limpo.parquet`)
| Coluna | Tipo | Significado |
|---|---|---|
| `session_date` | datetime | data do pregão |
| `in_session` | bool | a barra está dentro da sessão do calendário (`calendar.session_for`) |
| `partial_day` | bool | pregão com menos de 60% das barras esperadas (dia incompleto) |
| `roll_day` | bool | pregão em que o contínuo troca de contrato; o gap overnight inclui o carry |
| `usable` | bool | `in_session & ~partial_day`. **Filtro padrão das features** |
| `segment` | int | trecho contínuo; muda a cada buraco de dias úteis |
| `day_in_segment` | int | 1 no 1º pregão do trecho, 2 no seguinte... |
| `after_intraday_gap` | bool | a barra vem após uma pausa de 5+ minutos no mesmo dia |

Nenhuma linha é removida do dataset limpo; as marcações dizem o que usar.

## Regras de uso (invariantes)
1. **Filtrar por `usable`.** Descartadas hoje: WDO 593 barras (0,10%), WIN 65 (0,01%).
2. **Janelas de N pregões** (RVOL, z-score): só valem onde `day_in_segment > N` (`lookback_ok`). Não misturar os dois lados de um buraco.
3. **Rolagem:** nunca calcular retorno que atravesse a abertura de um `roll_day` (salto de ~0,4% no WDO e ~1,5% no WIN, de carry, não de mercado). Retornos intradiários não são afetados.
4. **Calendário:** sessão 09:00 → última barra WDO 17:59/18:29, WIN 17:54/18:24 (curta no horário de verão dos EUA até 2023; longa desde 2024). Quarta-feira de Cinzas abre 13:00.
5. **Hold-out:** só via `load_holdout(...)`. O mesmo `mark_bars` vale para ele na avaliação final.

## Buracos conhecidos (dias úteis sem nenhum dado; `reports/buracos_<ativo>.csv`)
| Ativo | Início | Fim | Pregões |
|---|---|---|---|
| WDO | 2021-11-24 | 2021-12-01 | 6 |
| WDO | 2022-07-15 | 2022-07-28 | 10 |
| WDO | 2023-06-05 | 2023-09-19 | 75 |
| WIN | 2021-11-16 | 2021-12-01 | 12 |
| WIN | 2022-07-15 | 2022-07-27 | 9 |
| WIN | 2023-06-05 | 2023-10-16 | 93 |
