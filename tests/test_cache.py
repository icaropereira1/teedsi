"""O cache é o que torna o backtest reproduzível: mesma chave, mesma resposta,
sem gastar chamada de novo. Mas qualquer mudança no pedido tem que invalidá-lo,
senão você compara resultados de prompts diferentes achando que são iguais.
"""

import datetime
import json

from src.data.cache import ResponseCache, request_fingerprint
from src.data.investigator import CEOInvestigatorAgent
from tests.fakes import PERFIL_VALIDO, FakeClient

CORTE = datetime.date(2021, 12, 31)
CEO = "Executivo Exemplo"
EMPRESA = "NovaTech S.A."


def _agent(tmp_path, model_name="gemini-2.5-flash", use_cache=True, cache=None):
    return CEOInvestigatorAgent(
        client=FakeClient(PERFIL_VALIDO),
        cache=cache if cache is not None else ResponseCache(tmp_path),
        use_cache=use_cache,
        model_name=model_name,
    )


def test_segunda_chamada_vem_do_disco(tmp_path):
    agent = _agent(tmp_path)

    primeiro = agent.analyze_ceo(CEO, EMPRESA, CORTE)
    assert agent.client.calls == 1

    segundo = agent.analyze_ceo(CEO, EMPRESA, CORTE)
    assert agent.client.calls == 1, "cache-hit não deveria chamar o modelo"
    assert primeiro == segundo


def test_resposta_bruta_e_metadados_ficam_no_disco(tmp_path):
    agent = _agent(tmp_path)
    agent.analyze_ceo(CEO, EMPRESA, CORTE)

    arquivos = list(tmp_path.rglob("*.json"))
    assert len(arquivos) == 1

    payload = json.loads(arquivos[0].read_text(encoding="utf-8"))
    assert payload["raw_response"] == PERFIL_VALIDO
    assert payload["meta"]["as_of_date"] == "2021-12-31"
    assert payload["meta"]["model"] == "gemini-2.5-flash"
    assert payload["meta"]["source_ids"] == ["N-1", "R-1"]
    assert "invalid_reason" not in payload


def test_caminho_no_disco_e_legivel(tmp_path):
    agent = _agent(tmp_path)
    agent.analyze_ceo(CEO, EMPRESA, CORTE)
    arquivo = next(tmp_path.rglob("*.json"))
    assert arquivo.parent.name == "2021-12-31"
    assert arquivo.parent.parent.name == "executivo-exemplo"


def test_troca_de_modelo_invalida_a_entrada(tmp_path):
    cache = ResponseCache(tmp_path)

    _agent(tmp_path, cache=cache).analyze_ceo(CEO, EMPRESA, CORTE)

    outro = _agent(tmp_path, cache=cache, model_name="gemini-2.5-pro")
    outro.analyze_ceo(CEO, EMPRESA, CORTE)
    assert outro.client.calls == 1, "modelo diferente é pedido diferente"
    assert len(list(tmp_path.rglob("*.json"))) == 2


def test_data_de_corte_diferente_e_entrada_diferente(tmp_path):
    agent = _agent(tmp_path)
    agent.analyze_ceo(CEO, EMPRESA, CORTE)
    agent.analyze_ceo(CEO, EMPRESA, datetime.date(2021, 6, 30))
    assert agent.client.calls == 2
    assert len(list(tmp_path.rglob("*.json"))) == 2


def test_use_cache_false_nao_escreve_nem_le(tmp_path):
    agent = _agent(tmp_path, use_cache=False)
    agent.analyze_ceo(CEO, EMPRESA, CORTE)
    agent.analyze_ceo(CEO, EMPRESA, CORTE)
    assert agent.client.calls == 2
    assert list(tmp_path.rglob("*.json")) == []


def test_fingerprint_reage_a_cada_parte_do_pedido():
    base = dict(
        model="gemini-2.5-flash",
        system_instruction="sys",
        prompt="prompt",
        response_schema_json="{}",
    )
    ref = request_fingerprint(**base)

    assert request_fingerprint(**base) == ref
    assert request_fingerprint(**{**base, "prompt": "prompt "}) != ref
    assert request_fingerprint(**{**base, "system_instruction": "sys2"}) != ref
    assert request_fingerprint(**{**base, "response_schema_json": "{ }"}) != ref
    assert request_fingerprint(**base, prompt_version="2") != ref


def test_cache_corrompido_e_tratado_como_miss(tmp_path):
    cache = ResponseCache(tmp_path)
    agent = _agent(tmp_path, cache=cache)
    agent.analyze_ceo(CEO, EMPRESA, CORTE)

    arquivo = next(tmp_path.rglob("*.json"))
    arquivo.write_text("{ isto não é json", encoding="utf-8")

    agent.analyze_ceo(CEO, EMPRESA, CORTE)
    assert agent.client.calls == 2
