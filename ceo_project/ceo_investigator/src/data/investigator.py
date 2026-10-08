"""Agente investigador de CEOs — orquestração.

Fluxo: busca point-in-time -> monta contexto com IDs de fonte -> consulta o
LLM (com cache em disco) -> valida o schema -> confere que toda citação
existe no contexto entregue.

Rode de dentro de ceo_investigator/:  py -m src.data.investigator
"""

import json
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any, List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError

from .cache import PROMPT_VERSION, ResponseCache, request_fingerprint
from .grounding import UngroundedProfileError, validate_grounding
from .schemas import CEOSummaryProfile
from .tools_search import SearchTools

load_dotenv()

_SYSTEM_INSTRUCTION = (
    "Você é um analista sênior de inteligência corporativa para hedge funds. "
    "Sua tarefa é analisar o histórico do executivo estritamente com base nos "
    "fatos fornecidos. Seja cético, destaque tanto conquistas quanto falhas "
    "de execução.\n"
    "\n"
    "REGRAS DE ANCORAGEM (não negociáveis):\n"
    "1. Toda afirmação deve citar, no campo 'fontes', os IDs das fontes do "
    "contexto que a sustentam. Ex: ['N-1', 'R-2'].\n"
    "2. Use apenas os IDs listados como disponíveis. Citar um ID inexistente "
    "faz o perfil inteiro ser rejeitado pelo validador.\n"
    "3. Você provavelmente conhece esta empresa e este executivo pelo seu "
    "treinamento. Ignore esse conhecimento por completo: qualquer fato "
    "posterior à data de corte contamina o backtest e invalida o estudo.\n"
    "4. Se as fontes não sustentam uma afirmação, omita-a. Lista vazia é uma "
    "resposta válida e preferível a especulação."
)


class InsufficientEvidenceError(Exception):
    """Nenhuma fonte sobreviveu ao filtro point-in-time."""


@dataclass
class Evidence:
    """Contexto entregue ao LLM e o conjunto exato de IDs que ele pode citar."""

    context_text: str
    source_ids: List[str] = field(default_factory=list)


class CEOInvestigatorAgent:

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        cache: Optional[ResponseCache] = None,
        use_cache: bool = True,
        client: Optional[Any] = None,
    ):
        # 'client' permite injetar um dublê nos testes, sem precisar de API key.
        self.client = client or genai.Client(
            api_key=api_key or os.getenv("GEMINI_API_KEY")
        )
        self.model_name = model_name

        # Instancia a classe de ferramentas de busca
        self.search_tools = SearchTools()

        self.cache = cache if cache is not None else ResponseCache()
        self.use_cache = use_cache

    def _fetch_documents_point_in_time(
        self, ceo_name: str, company: str, cutoff_date: date
    ) -> Evidence:
        """
        Executa a busca de notícias e relatórios (RAG/Search) e etiqueta cada
        fonte com um ID citável. Garante o filtro point-in-time para evitar
        data leakage no backtest.
        """
        valid_news = self.search_tools.search_historical_news(
            ceo_name=ceo_name, company=company, cutoff_date=cutoff_date
        )
        valid_filings = self.search_tools.fetch_sec_filings(
            ticker=company, cutoff_date=cutoff_date
        )

        source_ids: List[str] = []
        linhas = [f"--- DADOS COLETADOS ATÉ {cutoff_date.isoformat()} ---", ""]

        linhas.append("NOTÍCIAS:")
        if not valid_news:
            linhas.append("(nenhuma notícia sobreviveu ao filtro point-in-time)")
        for i, news in enumerate(valid_news, 1):
            sid = f"N-{i}"
            source_ids.append(sid)
            linhas.append(
                f"[FONTE {sid} | Data: {news['date']}] Título: {news['title']}"
            )
            linhas.append(f"Conteúdo: {news['content']}")
            linhas.append("")

        linhas.append("RELATÓRIOS OFICIAIS (SEC/CVM):")
        if not valid_filings:
            linhas.append("(nenhum relatório protocolado até a data de corte)")
        for i, filing in enumerate(valid_filings, 1):
            sid = f"R-{i}"
            source_ids.append(sid)
            linhas.append(
                f"[FONTE {sid} | Data: {filing['filingDate']}] "
                f"Formulário: {filing['form']}"
            )
            linhas.append(f"URL: {filing.get('url', 'N/A')}")
            linhas.append("")

        return Evidence(context_text="\n".join(linhas), source_ids=source_ids)

    def _build_prompt(
        self,
        ceo_name: str,
        target_company: str,
        as_of_date: date,
        evidence: Evidence,
    ) -> str:
        ids = ", ".join(evidence.source_ids) or "(nenhuma fonte disponível)"
        return f"""
        Analise o histórico profissional de {ceo_name}, que assumiu a empresa {target_company}.

        Data de corte: {as_of_date.isoformat()}. Nada posterior a esta data existe.

        IDs de fonte disponíveis para citação: {ids}

        Textos e fontes levantadas:
        {evidence.context_text}

        Extraia e estruture os dados do histórico de gestão conforme o esquema
        solicitado, citando em cada campo 'fontes' os IDs acima que sustentam
        a afirmação.
        """

    def analyze_ceo(
        self,
        ceo_name: str,
        target_company: str,
        as_of_date: date,
        allow_empty_evidence: bool = False,
    ) -> CEOSummaryProfile:
        """Coleta documentos até 'as_of_date' e sintetiza o perfil qualitativo.

        allow_empty_evidence existe apenas para o teste de controle: rodar com
        contexto vazio e confirmar que o modelo não preenche o perfil de
        memória. Em produção deve permanecer False.
        """
        evidence = self._fetch_documents_point_in_time(
            ceo_name=ceo_name, company=target_company, cutoff_date=as_of_date
        )

        if not evidence.source_ids and not allow_empty_evidence:
            raise InsufficientEvidenceError(
                f"Nenhuma fonte válida até {as_of_date.isoformat()} para "
                f"{ceo_name} / {target_company}. Um perfil montado sem fonte "
                "viria da memória do modelo, não dos dados."
            )

        prompt = self._build_prompt(ceo_name, target_company, as_of_date, evidence)
        schema_json = json.dumps(
            CEOSummaryProfile.model_json_schema(), sort_keys=True, ensure_ascii=False
        )
        fingerprint = request_fingerprint(
            model=self.model_name,
            system_instruction=_SYSTEM_INSTRUCTION,
            prompt=prompt,
            response_schema_json=schema_json,
        )

        raw = (
            self.cache.get(ceo_name, as_of_date, fingerprint)
            if self.use_cache
            else None
        )
        from_cache = raw is not None

        if raw is None:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=CEOSummaryProfile,
                    # Temperatura baixa reduz variação, mas não é determinismo:
                    # a reprodutibilidade real vem do cache em disco.
                    temperature=0.1,
                ),
            )
            raw = response.text
            if not raw:
                raise RuntimeError(
                    "Gemini devolveu resposta vazia (bloqueio de safety ou "
                    "corte por limite de tokens)."
                )

        meta = {
            "ceo_name": ceo_name,
            "target_company": target_company,
            "as_of_date": as_of_date.isoformat(),
            "model": self.model_name,
            "prompt_version": PROMPT_VERSION,
            "source_ids": evidence.source_ids,
        }

        try:
            profile = CEOSummaryProfile.model_validate_json(raw)
            validate_grounding(profile, evidence.source_ids)
        except (ValidationError, UngroundedProfileError) as exc:
            # O bruto vai para o disco mesmo inválido: sem ele não há como
            # depurar por que o modelo falhou. Nunca é servido como cache-hit.
            if self.use_cache and not from_cache:
                self.cache.put(
                    ceo_name,
                    as_of_date,
                    fingerprint,
                    raw,
                    meta,
                    invalid_reason=f"{type(exc).__name__}: {exc}",
                )
            raise

        if self.use_cache and not from_cache:
            self.cache.put(ceo_name, as_of_date, fingerprint, raw, meta)

        return profile


if __name__ == "__main__":
    # Teste de execução garantindo a reprodutibilidade temporal
    agent = CEOInvestigatorAgent()

    # A data de corte é obrigatória para simular o backtest corretamente
    data_corte = date(2021, 12, 31)

    perfil = agent.analyze_ceo(
        ceo_name="Executivo Exemplo",
        target_company="NovaTech S.A.",
        as_of_date=data_corte,
    )

    print(perfil.model_dump_json(indent=2))
