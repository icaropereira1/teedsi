# Pré-registro — confirmação do A1 no WIN (CONGELADO em 2026-10-14, antes da execução)

**Contexto:** na rodada 2, A1 (pausa com volume, 15 min) teve +1,34 bps, p = 0,0145 no WDO, 6 de 6 anos, mas não passou o limite
corrigido (p < 0,0017). O grupo aprovou uma **confirmação única** em outro ativo. Isto foge do pré-registro da rodada 2
(que só replicava o que passasse) e fica registrado como **confirmação exploratória aprovada pelo grupo**.

## Teste (um único)
- **Ativo:** WIN, exploração (`win_m1_limpo.parquet`). Hold-out intocado.
- **Evento:** A1 exatamente como em `PRE_REGISTRO_GATE1_RODADA2.md` (seção 2). Nenhum parâmetro muda.
- **Direção:** sinal de `r15` (continuação). **Horizonte:** 15 min. **Execução, controle, cooldown e bootstrap:** idênticos.
- **Notebook:** `notebooks/07_confirmacao_a1_win.py` (calcula só este teste).

## Critério (todos obrigatórios)
1. Efeito **> 0** com **p < 0,05** (1 teste, sem correção).
2. N ≥ 300 episódios.
3. Efeito ≥ **1 tick do WIN** (~0,41 bps) para seguir ao Gate 2.
4. Mesmo sinal em ≥ 4 de 6 anos (descritivo; não reprova sozinho).

## Interpretação antes de ver o resultado
- **Passa (1 a 3):** A1 ganha peso, mas ainda precisa de hold-out (Fase 6) e custos (Gate 2). Não vira "go" automático, porque
  o WDO sozinho não passou o limite corrigido.
- **Não passa:** rodada 2 fecha como no-go para M1. Decisão passa a ser dado tick a tick ou encerrar.
- Nenhum horizonte ou definição vizinha será testado depois deste resultado sem novo pré-registro.
