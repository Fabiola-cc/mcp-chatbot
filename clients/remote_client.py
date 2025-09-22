import asyncio
import httpx
import json
from typing import Optional

SERVER_URL = "https://mcpremoteserver-production.up.railway.app"

class MCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
    
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
        
    async def test_connection(self) -> bool:
        """Prueba conexión con el servidor remoto"""
        url = "https://mcpremoteserver-production.up.railway.app"
        try:
            async with httpx.AsyncClient() as client:
                response = client.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    data = await response.json()
                    if data.get("status") == "healthy":
                        self.server_url = url
                        self.is_connected = True
                        print(f"✅ Conectado a servidor remoto: {url}")
                        return True
        except Exception as e:
            print(f"⚠️ No se pudo conectar a {url}: {str(e)}")
        
        self.is_connected = False
        return False

    async def health_check(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{SERVER_URL}/health")
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
            r = await client.get(f"{SERVER_URL}/api/quote", params=params)
            r.raise_for_status()
            return r.json()

    async def get_tip(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{SERVER_URL}/api/tip")
            r.raise_for_status()
            return r.json()

    async def search_quotes(self, query: str, limit: int = 5):
        params = {"limit": limit}
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{SERVER_URL}/api/search/{query}", params=params)
            r.raise_for_status()
            return r.json()

    async def get_wisdom(self, include_tip: bool = True):
        params = {"include_tip": str(include_tip).lower()}
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{SERVER_URL}/api/wisdom", params=params)
            r.raise_for_status()
            return r.json()

# Ejemplo de uso
async def main():
    client = MCPClient(SERVER_URL)

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
