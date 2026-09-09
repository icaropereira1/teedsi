import os
from datetime import date
from typing import Optional
from google import genai
from google.genai import types

# 1. Importações dos arquivos locais que criamos
from schemas import CEOSummaryProfile
from tools_search import SearchTools


class CEOInvestigatorAgent:

    def __init__(self, api_key: Optional[str] = None):
        self.client = genai.Client(
            api_key=api_key or os.getenv("GEMINI_API_KEY")
        )
        self.model_name = "gemini-2.5-flash"
        
        # 2. Instancia a classe de ferramentas de busca
        self.search_tools = SearchTools()

    def _fetch_documents_point_in_time(
        self, ceo_name: str, company: str, cutoff_date: date
    ) -> str:
        """
        Executa a busca de notícias e relatórios (RAG/Search).
        Garante o filtro point-in-time para evitar data leakage no backtest.
        """
        # 3. Utiliza as ferramentas para buscar dados limpos e validados temporalmente
        valid_news = self.search_tools.search_historical_news(
            ceo_name=ceo_name, company=company, cutoff_date=cutoff_date
        )
        
        valid_filings = self.search_tools.fetch_sec_filings(
            ticker=company, cutoff_date=cutoff_date
        )

        # 4. Compila os resultados em um texto único para o LLM analisar
        context_text = f"--- DADOS COLETADOS ATÉ {cutoff_date.isoformat()} ---\n\n"
        
        context_text += "NOTÍCIAS:\n"
        for i, news in enumerate(valid_news, 1):
            context_text += f"[FONTE N-{i} | Data: {news['date']}] Título: {news['title']}\nConteúdo: {news['content']}\n\n"
            
        context_text += "RELATÓRIOS OFICIAIS (SEC/CVM):\n"
        for i, filing in enumerate(valid_filings, 1):
            context_text += f"[FONTE R-{i} | Data: {filing['filingDate']}] Formulário: {filing['form']}\nURL: {filing.get('url', 'N/A')}\n\n"

        return context_text

    def analyze_ceo(
        self,
        ceo_name: str,
        target_company: str,
        as_of_date: date,
    ) -> CEOSummaryProfile:
        """Coleta documentos até 'as_of_date' e sintetiza o perfil qualitativo."""
        
        # Agora passamos também a empresa para refinar a busca
        raw_text = self._fetch_documents_point_in_time(
            ceo_name=ceo_name, company=target_company, cutoff_date=as_of_date
        )

        system_instruction = (
            "Você é um analista sênior de inteligência corporativa para hedge funds. "
            "Sua tarefa é analisar o histórico do executivo estritamente com base nos fatos fornecidos. "
            "Seja cético, destaque tanto conquistas quanto falhas de execução. "
            "Não infira dados que não estejam corroborados pelas fontes."
        )

        prompt = f"""
        Analise o histórico profissional de {ceo_name}, que assumiu a empresa {target_company}.
        
        Textos e fontes levantadas:
        {raw_text}
        
        Extraia e estruture os dados do histórico de gestão conforme o esquema solicitado.
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CEOSummaryProfile,
                temperature=0.1, 
            ),
        )

        profile = CEOSummaryProfile.model_validate_json(response.text)
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