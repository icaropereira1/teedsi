from typing import List, Optional
from pydantic import BaseModel, Field


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


class CEOSummaryProfile(BaseModel):
    nome_ceo: str
    estilo_gestao: str = Field(
        description="Ex: Foco em corte de custos, Foco em M&A, Inovação agressiva"
    )
    principais_entregas: List[str] = Field(
        description="Marcos de sucesso durante suas gestões"
    )
    principais_controversias: List[str] = Field(
        description="Polêmicas, metas não atingidas, atritos com conselho"
    )
    historico_eventos: List[ManagementEvent]
    nivel_confianca_fonte: float = Field(
        ge=0.0,
        le=1.0,
        description="Confiabilidade das fontes encontradas (0.0 a 1.0)",
    )