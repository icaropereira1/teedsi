# Resultado — confirmação do A1 no WIN

**Data:** 2026-10-14 · **Pré-registro:** `PRE_REGISTRO_CONFIRMACAO_A1_WIN.md` (congelado antes de rodar)
**Código:** `notebooks/07_confirmacao_a1_win.py` · **Números:** `reports/confirmacao_a1_win.csv`
**Veredito: NÃO confirma.** Um único teste, horizonte de 15 min, WIN, exploração.

## Resultado
| | WIN, A1 em 15 min | (WDO, para comparar) |
|---|---|---|
| Episódios | 617 em 419 dias | 730 |
| A favor da direção (bps) | +1,04 | +1,21 |
| Controle (bps) | +0,09 | −0,13 |
| **Efeito (bps)** | **+0,95** | +1,34 |
| IC 95% (bps) | [−0,46; +2,36] | [+0,30; +2,36] |
| p (bilateral, bootstrap por dia) | **0,176** | 0,0145 |
| Acerto | 49,1% | 48,8% |
| Anos com efeito positivo | 4 de 6 | 6 de 6 |

| Ano | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| Efeito WIN (bps) | +10,10 (n=23) | −0,69 (n=138) | +0,27 (n=134) | +3,58 (n=78) | −0,43 (n=156) | +2,28 (n=88) |

## Critérios pré-registrados
| Critério | Resultado |
|---|---|
| 1. Efeito > 0 com p < 0,05 | **Não** (p = 0,176) |
| 2. N ≥ 300 | Sim (617) |
| 3. Efeito ≥ 1 tick (~0,41 bps) | Sim (+0,95) |
| 4. ≥ 4 de 6 anos positivos (descritivo) | Sim (4 de 6) |

Falhou o critério 1, que é obrigatório. **A1 não é confirmado.**

## Leitura
- **A direção e a ordem de grandeza batem** com o WDO (+0,95 contra +1,34 bps), mas o intervalo de 95% inclui o zero.
  Com 617 episódios, o erro-padrão é de ~0,7 bps: o teste só detectaria com confiança efeitos acima de ~1,5 bps.
  O resultado é, ao mesmo tempo, **compatível com zero** e **compatível com o efeito do WDO**. Não dá para escolher entre os dois.
- **Os dois ativos juntos não formam evidência suficiente.** No WDO o p corrigido não passou, e o WIN não chegou a 0,05.
  Combinar os dois p-valores não resolve, porque o WDO já foi usado para escolher o A1 entre 15 candidatos (viés de seleção).
- **O efeito não é estável por ano** no WIN (de −0,69 a +10,10 bps, com n entre 23 e 156). O +10,10 de 2020 vem de 23 episódios.
- **Taxa de acerto em 49%** nos dois ativos: o ganho médio vem de poucos movimentos grandes, não de acertar mais.

## Conclusão do Gate 1 para dado M1
Nas duas rodadas, 6 definições de evento de fluxo (E1, E2, E3, A1, P1, X1), 2 ativos e 5 horizontes, **nenhuma passou**.
O único candidato (A1, 15 min) não se confirmou em um segundo ativo. Pelas regras do projeto, o Gate 1 fica como
**no-go para candles de 1 minuto**. Isso é um resultado: com este dado, seguir o fluxo "anômalo" não tem base estatística.

## O que fica em aberto (decisão do grupo)
1. **Dado tick a tick** (negócio a negócio, com agressor comprador/vendedor): é o dado natural para esta ideia e o
   que o plano já previa. É a continuação mais coerente.
2. **Mais uma rodada em M1:** só se houver uma hipótese nova de fundo. Cada teste extra piora o limite de Bonferroni
   e, depois de 6 definições sem sinal, o ganho esperado é baixo.
3. **Encerrar** e entregar o resultado negativo documentado.
