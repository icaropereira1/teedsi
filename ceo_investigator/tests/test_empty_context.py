"""Teste de controle: com contexto vazio o perfil não pode nascer.

Se o pipeline devolvesse um perfil aqui, ele estaria vindo da memória do
modelo — treinado com dados posteriores à data de corte — e não das fontes.
É exatamente o leakage que o filtro point-in-time não pega.
"""

import datetime
import json
import os

import pytest
from pydantic import ValidationError

from src.data.cache import ResponseCache
from src.data.grounding import UngroundedProfileError
from src.data.investigator import (
    CEOInvestigatorAgent,
    Evidence,
    InsufficientEvidenceError,
)
from tests.fakes import PERFIL_ALUCINADO, FakeClient

CORTE = datetime.date(2021, 12, 31)


def _agent(tmp_path, raw, sem_fontes=False):
    agent = CEOInvestigatorAgent(
        client=FakeClient(raw), cache=ResponseCache(tmp_path)
    )
    if sem_fontes:
        agent._fetch_documents_point_in_time = lambda **kwargs: Evidence(
            context_text="(nenhuma fonte)", source_ids=[]
        )
    return agent


def test_contexto_vazio_nao_chega_ao_llm(tmp_path):
    # Sem fonte não se gasta chamada: o perfil seria necessariamente inventado.
    agent = _agent(tmp_path, PERFIL_ALUCINADO, sem_fontes=True)
    with pytest.raises(InsufficientEvidenceError):
        agent.analyze_ceo("Executivo Exemplo", "NovaTech S.A.", CORTE)
    assert agent.client.calls == 0


def test_perfil_de_memoria_e_rejeitado(tmp_path):
    # Forçando a chamada com contexto vazio (allow_empty_evidence), qualquer
    # perfil que o modelo devolva é ancorado em nada e deve ser barrado.
    agent = _agent(tmp_path, PERFIL_ALUCINADO, sem_fontes=True)
    with pytest.raises(UngroundedProfileError):
        agent.analyze_ceo(
            "Executivo Exemplo", "NovaTech S.A.", CORTE, allow_empty_evidence=True
        )
    assert agent.client.calls == 1


def test_citacao_fora_do_contexto_e_rejeitada(tmp_path):
    # Aqui existem fontes (N-1 e R-1 do stub), mas o modelo citou N-9.
    agent = _agent(tmp_path, PERFIL_ALUCINADO)
    with pytest.raises(UngroundedProfileError):
        agent.analyze_ceo("Executivo Exemplo", "NovaTech S.A.", CORTE)


def test_resposta_invalida_fica_no_disco_para_depuracao(tmp_path):
    agent = _agent(tmp_path, PERFIL_ALUCINADO)
    with pytest.raises(UngroundedProfileError):
        agent.analyze_ceo("Executivo Exemplo", "NovaTech S.A.", CORTE)

    invalidos = list(tmp_path.rglob("*.invalid.json"))
    assert len(invalidos) == 1
    payload = json.loads(invalidos[0].read_text(encoding="utf-8"))
    assert payload["raw_response"] == PERFIL_ALUCINADO
    assert "UngroundedProfileError" in payload["invalid_reason"]

    # E não vira cache-hit: a próxima tentativa chama o modelo de novo.
    assert list(tmp_path.rglob("*.json")) == invalidos


def test_afirmacao_sem_fonte_quebra_no_schema(tmp_path):
    raw = json.dumps(
        {
            "nome_ceo": "Executivo Exemplo",
            "estilo_gestao": {"afirmacao": "Agressivo em M&A", "fontes": []},
            "principais_entregas": [],
            "principais_controversias": [],
            "historico_eventos": [],
            "nivel_confianca_fonte": 0.8,
        }
    )
    agent = _agent(tmp_path, raw)
    with pytest.raises(ValidationError):
        agent.analyze_ceo("Executivo Exemplo", "NovaTech S.A.", CORTE)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), reason="requer GEMINI_API_KEY"
)
def test_controle_com_api_real_nao_inventa_perfil(tmp_path):
    """Prova de fogo contra o leakage paramétrico, com o Gemini de verdade.

    Rode com:  py -m pytest -m integration
    Se este teste falhar (isto é, se um perfil válido nascer de contexto
    vazio), o modelo está respondendo de memória e o backtest está
    contaminado — nenhum filtro de fonte conserta isso.
    """
    agent = CEOInvestigatorAgent(cache=ResponseCache(tmp_path))
    agent._fetch_documents_point_in_time = lambda **kwargs: Evidence(
        context_text="(nenhuma fonte)", source_ids=[]
    )
    with pytest.raises((ValidationError, UngroundedProfileError)):
        agent.analyze_ceo(
            "Steve Jobs", "Apple Inc.", CORTE, allow_empty_evidence=True
        )
