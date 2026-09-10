"""Contratos de saída do agente investigador.

Toda afirmação qualitativa carrega os IDs das fontes que a sustentam. Sem
isso não há como distinguir análise ancorada em fonte de ficção plausível
gerada pela memória do modelo — ver src/data/grounding.py.
"""

from typing import List

from pydantic import BaseModel, Field


class Claim(BaseModel):
    """Afirmação qualitativa obrigatoriamente ancorada em fontes."""

    afirmacao: str = Field(description="A afirmação, em uma frase factual")
    fontes: List[str] = Field(
        min_length=1,
        description=(
            "IDs das fontes do contexto que sustentam esta afirmação. "
            "Ex: ['N-1', 'R-2']. Nunca inventar um ID."
        ),
    )


class ManagementEvent(BaseModel):
    empresa: str = Field(description="Nome da empresa onde atuou")
    periodo: str = Field(description="Ex: 2017 - 2021")
    tipo_evento: str = Field(
        description="M&A, Reestruturação, Crise, Turnaround ou Expansão"
    )
    descricao: str = Field(description="Resumo factual do ocorrido")
    impacto_reportado: str = Field(
        description="Resultado financeiro ou operacional divulgado na época"
    )
    fontes: List[str] = Field(
        min_length=1,
        description="IDs das fontes que documentam este evento. Ex: ['N-1']",
    )


class CEOSummaryProfile(BaseModel):
    nome_ceo: str
    estilo_gestao: Claim = Field(
        description="Ex: Foco em corte de custos, Foco em M&A, Inovação agressiva"
    )
    principais_entregas: List[Claim] = Field(
        description="Marcos de sucesso durante suas gestões"
    )
    principais_controversias: List[Claim] = Field(
        description="Polêmicas, metas não atingidas, atritos com conselho"
    )
    historico_eventos: List[ManagementEvent]
    nivel_confianca_fonte: float = Field(
        ge=0.0,
        le=1.0,
        description="Confiabilidade das fontes encontradas (0.0 a 1.0)",
    )
