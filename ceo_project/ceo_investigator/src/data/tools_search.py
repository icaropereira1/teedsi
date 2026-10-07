import datetime
import requests
from typing import List, Dict

class SearchTools:
    """
    Ferramentas de busca projetadas para evitar data leakage, 
    garantindo que apenas informações point-in-time sejam retornadas.
    """

    def _is_valid_date(self, item_date_str: str, cutoff_date: datetime.date) -> bool:
        """Validador rigoroso de data para evitar vazamento futuro."""
        try:
            # Assumindo formato ISO retornado pelas APIs (YYYY-MM-DD)
            item_date = datetime.datetime.fromisoformat(item_date_str[:10]).date()
            return item_date <= cutoff_date
        except (ValueError, TypeError):
            # Se não conseguimos provar quando a notícia saiu, descartamos (Ceticismo)
            return False

    def search_historical_news(self, ceo_name: str, company: str, cutoff_date: datetime.date) -> List[Dict]:
        """
        Busca notícias limitadas a uma data específica.
        Exemplo genérico conectando a uma API hipotética (como NewsAPI, Tavily ou GNews).
        """
        query = f'"{ceo_name}" "{company}"'
        
        # 1. Envia a restrição de data para a API (se suportado)
        # Exemplo de payload para uma API padrão:
        params = {
            "q": query,
            "to": cutoff_date.isoformat(),
            "language": "pt",
            "sort_by": "relevance"
        }
        
        # Simulação de resposta da API
        # response = requests.get("https://api.exemplo.com/news", params=params)
        # raw_results = response.json().get("articles", [])
        
        raw_results = [
            {"title": f"{ceo_name} assume empresa", "date": "2020-01-15", "content": "..."},
            {"title": "Resultados anuais decepcionam", "date": "2022-03-10", "content": "..."} # Dado futuro!
        ]

        # 2. Filtragem local obrigatória (Point-in-Time real)
        valid_news = []
        for news in raw_results:
            if self._is_valid_date(news["date"], cutoff_date):
                valid_news.append(news)
                
        return valid_news

    def fetch_sec_filings(self, ticker: str, cutoff_date: datetime.date) -> List[Dict]:
        """
        Busca formulários oficiais (ex: 8-K para mudanças de CEO) na SEC EDGAR.
        Garante que só relatórios protocolados até a data de corte sejam usados.
        """
        # A SEC exige um User-Agent descritivo
        headers = {'User-Agent': 'ProjetoAcademico_TEEDSI meu_email@exemplo.com'}
        
        # Na prática, você usaria a biblioteca 'sec-api' ou acessaria a API pública da SEC:
        # url = f"https://data.sec.gov/submissions/CIK{obter_cik(ticker)}.json"
        
        # Simulação do filtro:
        simulated_filings = [
            {"form": "8-K", "filingDate": "2019-12-01", "url": "..."}
        ]
        
        valid_filings = [
            f for f in simulated_filings 
            if self._is_valid_date(f["filingDate"], cutoff_date)
        ]
        
        return valid_filings