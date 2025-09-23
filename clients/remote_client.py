import asyncio
import httpx
import json
from typing import Any, Dict, Optional

class RemoteSleepQuotesClient:
    def __init__(self):
        self.server_url = "https://mcpremoteserver-production.up.railway.app"
    
    async def call_method(self, method: str, params: dict = None):
        """Hace una llamada al endpoint MCP remoto"""
        if params is None:
            params = {}
        async with httpx.AsyncClient() as client:
            response = await client.post(self.server_url + "/mcp", json={
                "method": method,
                "params": params
            })
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")
            
    def _format_wisdom_output(self, wisdom_data: Dict[Any, Any]) -> str:
        """Formatea la sabiduría diaria"""
        output = [self._format_quote_output(wisdom_data, "SABIDURIA DIARIA")]
        
        if "tip" in wisdom_data:
            tip = wisdom_data["tip"]
            output.extend([
                "\nCONSEJO ADICIONAL:",
                "----------------",
                f'"{tip.get("quote", "")}"',
                f"   - {tip.get('author', 'Sleep Expert')}"
            ])
        
        return "\n".join(output)
            
    def _format_quote_output(self, quote_data: Dict[Any, Any], title: str = "CITA") -> str:
        """Formatea una cita de manera legible"""
        if "result" in quote_data:
            quote_info = quote_data["result"]
        elif "daily_quote" in quote_data:
            quote_info = quote_data["daily_quote"]
        else:
            quote_info = quote_data
        
        output = [
            f"\n{title}:",
            "-" * (len(title) + 1),
            f'"{quote_info.get("quote", "")}"',
            f"   - {quote_info.get('author', 'Autor desconocido')}",
        ]
        
        # Agregar información adicional si está disponible
        if quote_info.get("category"):
            output.append(f"   Categoria: {quote_info['category']}")
        
        if quote_info.get("mood"):
            output.append(f"   Estado de animo: {quote_info['mood']}")
        
        if quote_info.get("time_of_day"):
            output.append(f"   Momento del dia: {quote_info['time_of_day']}")
        
        return "\n".join(output)
            
    def _format_search_results(self, search_data: Dict[Any, Any]) -> str:
        """Formatea los resultados de búsqueda"""
        results = search_data.get("results", [])
        query = search_data.get("query", "")
        
        if not results:
            return f"\nNo se encontraron resultados para: '{query}'"
        
        output = [
            f"\nRESULTADOS DE BUSQUEDA PARA: '{query}'",
            "=" * (len(query) + 30),
            f"Encontradas {len(results)} cita(s):\n"
        ]
        
        for i, quote in enumerate(results, 1):
            output.extend([
                f"{i}. \"{quote.get('quote', '')}\"",
                f"    - {quote.get('author', 'Autor desconocido')}",
                f"    Categoria: {quote.get('category', 'N/A')} | "
                f"Estado: {quote.get('mood', 'N/A')}",
                ""
            ])
        
        return "\n".join(output)
    
    async def get_inspirational_quote(self, category=None, mood=None, time_based=False):
        params = {}
        if category:
            params["category"] = category
        if mood:
            params["mood"] = mood
        params["time_based"] = time_based
        return await self.call_method("get_inspirational_quote", params)
    
    async def get_sleep_hygiene_tip(self):
        return await self.call_method("get_sleep_hygiene_tip")
    
    async def health_check(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.server_url}/health")
            r.raise_for_status()
            return r.json()

    async def get_quote(self, category: Optional[str] = None, mood: Optional[str] = None, time_based: bool = False):
        params = {}
        if category:
            params["category"] = category
        if mood:
            params["mood"] = mood
        if time_based:
            params["time_based"] = "true"

        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.server_url}/api/quote", params=params)
            r.raise_for_status()
            return r.json()

    async def get_tip(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.server_url}/api/tip")
            r.raise_for_status()
            return r.json()

    async def search_quotes(self, query: str, limit: int = 5):
        params = {"limit": limit}
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.server_url}/api/search/{query}", params=params)
            r.raise_for_status()
            return r.json()

    async def get_wisdom(self, include_tip: bool = True):
        params = {"include_tip": str(include_tip).lower()}
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.server_url}/api/wisdom", params=params)
            r.raise_for_status()
            return r.json()

# Ejemplo de uso
async def main():
    client = RemoteSleepQuotesClient()

    print("CHECK")
    verify = await client.health_check()
    print(verify)
    
    print("🌙 Obteniendo cita inspiracional...")
    quote = await client.get_inspirational_quote(time_based=True)
    print(json.dumps(quote, indent=2, ensure_ascii=False))
    
    print("\n💡 Obteniendo consejo de higiene del sueño...")
    tip = await client.get_sleep_hygiene_tip()
    print(json.dumps(tip, indent=2, ensure_ascii=False))
    
    print("\n📖 Sabiduría diaria del sueño...")
    wisdom = await client.get_wisdom(False)
    print(json.dumps(wisdom, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
