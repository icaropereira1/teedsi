"""Dublês e payloads compartilhados pelos testes que exercitam o agente."""

import json
from types import SimpleNamespace


class FakeModels:
    def __init__(self, raw: str) -> None:
        self.raw = raw
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(text=self.raw)


class FakeClient:
    """Substitui genai.Client: conta chamadas e devolve um JSON fixo."""

    def __init__(self, raw: str) -> None:
        self.models = FakeModels(raw)

    @property
    def calls(self) -> int:
        return self.models.calls


# O stub de tools_search.py, com corte em 2021-12-31, produz exatamente
# duas fontes citáveis: N-1 (notícia de 2020-01-15) e R-1 (8-K de 2019-12-01).
PERFIL_VALIDO = json.dumps(
    {
        "nome_ceo": "Executivo Exemplo",
        "estilo_gestao": {
            "afirmacao": "Assumiu com mandato de turnaround",
            "fontes": ["N-1"],
        },
        "principais_entregas": [
            {"afirmacao": "Troca de comando formalizada em 8-K", "fontes": ["R-1"]}
        ],
        "principais_controversias": [],
        "historico_eventos": [
            {
                "empresa": "NovaTech S.A.",
                "periodo": "2020 - 2021",
                "tipo_evento": "Turnaround",
                "descricao": "Assumiu a companhia em janeiro de 2020",
                "impacto_reportado": "Não divulgado nas fontes disponíveis",
                "fontes": ["N-1", "R-1"],
            }
        ],
        "nivel_confianca_fonte": 0.4,
    },
    ensure_ascii=False,
)

# Cita N-9, que nunca existiu no contexto: é o modelo respondendo de memória.
PERFIL_ALUCINADO = json.dumps(
    {
        "nome_ceo": "Executivo Exemplo",
        "estilo_gestao": {
            "afirmacao": "Foco em M&A agressivo e corte de custos",
            "fontes": ["N-9"],
        },
        "principais_entregas": [],
        "principais_controversias": [],
        "historico_eventos": [],
        "nivel_confianca_fonte": 0.9,
    },
    ensure_ascii=False,
)
