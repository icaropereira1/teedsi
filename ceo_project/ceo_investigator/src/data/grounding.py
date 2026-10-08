"""Verificação de ancoragem (grounding).

O filtro point-in-time de tools_search.py protege as *fontes*, mas não
protege contra o conhecimento paramétrico do LLM: o modelo foi treinado com
dados posteriores à data de corte e pode "saber" o que aconteceu depois.
Filtrar o RAG não resolve isso.

A defesa é exigir citação no schema e conferir, em código, que todo ID
citado existe de fato no contexto que foi entregue. Um perfil que cita
FONTE N-9 quando só existiam N-1 e R-1 está vindo da memória do modelo.
"""

import re
from typing import Dict, Iterable, List, Optional

from .schemas import CEOSummaryProfile

# Aceita "N-1", "n-1", "FONTE N-1" — o modelo varia a forma de citar.
_CITATION_RE = re.compile(r"^(?:FONTE\s+)?([NR]-\d+)$", re.IGNORECASE)


class UngroundedProfileError(Exception):
    """O perfil cita fontes que não estavam no contexto."""

    def __init__(self, invalid: Dict[str, List[str]]) -> None:
        self.invalid = invalid
        detalhe = "; ".join(
            f"{campo}: {ids}" for campo, ids in sorted(invalid.items())
        )
        super().__init__(f"Perfil cita fontes inexistentes no contexto -> {detalhe}")


def normalize_citation(raw: str) -> Optional[str]:
    """Devolve o ID canônico ('N-1') ou None se não for uma citação válida."""
    if not isinstance(raw, str):
        return None
    match = _CITATION_RE.match(raw.strip())
    return match.group(1).upper() if match else None


def collect_citations(profile: CEOSummaryProfile) -> Dict[str, List[str]]:
    """Mapeia campo -> citações brutas, para o erro apontar onde foi o furo."""
    cites: Dict[str, List[str]] = {"estilo_gestao": list(profile.estilo_gestao.fontes)}

    for i, claim in enumerate(profile.principais_entregas, 1):
        cites[f"principais_entregas[{i}]"] = list(claim.fontes)

    for i, claim in enumerate(profile.principais_controversias, 1):
        cites[f"principais_controversias[{i}]"] = list(claim.fontes)

    for i, evento in enumerate(profile.historico_eventos, 1):
        cites[f"historico_eventos[{i}]"] = list(evento.fontes)

    return cites


def validate_grounding(
    profile: CEOSummaryProfile, valid_ids: Iterable[str]
) -> None:
    """Levanta UngroundedProfileError se algum ID citado não existir no contexto."""
    disponiveis = {str(i).upper() for i in valid_ids}
    invalid: Dict[str, List[str]] = {}

    for campo, citacoes in collect_citations(profile).items():
        ruins = [
            bruto
            for bruto in citacoes
            if (normalize_citation(bruto) or "") not in disponiveis
        ]
        if ruins:
            invalid[campo] = ruins

    if invalid:
        raise UngroundedProfileError(invalid)
