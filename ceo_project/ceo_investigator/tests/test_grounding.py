"""O filtro point-in-time protege as fontes; o grounding protege contra a
memória do modelo. Estes testes cobrem a segunda metade."""

import pytest
from pydantic import ValidationError

from src.data.grounding import (
    UngroundedProfileError,
    collect_citations,
    normalize_citation,
    validate_grounding,
)
from src.data.schemas import CEOSummaryProfile, Claim, ManagementEvent


def _profile(fontes_estilo=("N-1",), fontes_evento=("R-1",)):
    return CEOSummaryProfile(
        nome_ceo="Executivo Exemplo",
        estilo_gestao=Claim(
            afirmacao="Foco em corte de custos", fontes=list(fontes_estilo)
        ),
        principais_entregas=[],
        principais_controversias=[],
        historico_eventos=[
            ManagementEvent(
                empresa="NovaTech S.A.",
                periodo="2019 - 2021",
                tipo_evento="Turnaround",
                descricao="Reestruturação operacional",
                impacto_reportado="Margem reportada em alta",
                fontes=list(fontes_evento),
            )
        ],
        nivel_confianca_fonte=0.5,
    )


@pytest.mark.parametrize(
    "bruto,esperado",
    [
        ("N-1", "N-1"),
        ("n-1", "N-1"),
        ("  R-12  ", "R-12"),
        ("FONTE N-3", "N-3"),
        ("fonte r-2", "R-2"),
    ],
)
def test_normalize_citation_aceita_variacoes(bruto, esperado):
    assert normalize_citation(bruto) == esperado


@pytest.mark.parametrize(
    "bruto", ["X-1", "1", "", "N1", "N-", "notícia da Folha", None]
)
def test_normalize_citation_rejeita_lixo(bruto):
    assert normalize_citation(bruto) is None


def test_perfil_ancorado_passa():
    validate_grounding(_profile(), ["N-1", "R-1"])


def test_id_inventado_e_rejeitado():
    with pytest.raises(UngroundedProfileError) as exc:
        validate_grounding(_profile(fontes_estilo=("N-9",)), ["N-1", "R-1"])
    assert "estilo_gestao" in str(exc.value)
    assert "N-9" in str(exc.value)


def test_erro_nomeia_o_evento_especifico():
    with pytest.raises(UngroundedProfileError) as exc:
        validate_grounding(_profile(fontes_evento=("R-7",)), ["N-1", "R-1"])
    assert "historico_eventos[1]" in str(exc.value)


def test_sem_fontes_disponiveis_qualquer_citacao_e_invalida():
    with pytest.raises(UngroundedProfileError):
        validate_grounding(_profile(), [])


def test_schema_exige_pelo_menos_uma_fonte():
    # É a metade do grounding que roda antes do validador: o próprio contrato
    # não aceita uma afirmação órfã.
    with pytest.raises(ValidationError):
        Claim(afirmacao="Cortou custos", fontes=[])


def test_collect_citations_cobre_todos_os_campos_preenchidos():
    campos = collect_citations(_profile())
    assert set(campos) == {"estilo_gestao", "historico_eventos[1]"}
