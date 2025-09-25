import asyncio
import aiohttp
import httpx
import json
from typing import Dict, List, Optional

class RemoteSleepQuotesClient:
    """Cliente para conectarse a servidores MCP remotos via HTTP"""
    
    def __init__(self, base_url: str = "https://mcpremoteserver-production.up.railway.app"):
        self.base_url = base_url.rstrip('/')
        self.is_connected = False
        self.session = None
        
    async def start_server(self, server_name: str = "remote"):
        """Inicia la conexión al servidor remoto"""
        try:
            
            # Crear sesión HTTP
            self.session = aiohttp.ClientSession()
            
            # Verificar que el servidor está disponible
            if await self._check_server_health():
                self.is_connected = True
                print(f"✅ {server_name} Server remoto conectado y listo")
                return True
            else:
                print("❌ El servidor remoto no está disponible")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando al servidor remoto: {e}")
            return False
    
    async def _check_server_health(self) -> bool:
        """Verifica la salud del servidor remoto"""
        try:
            async with self.session.get(f"{self.base_url}/health", timeout=10) as response:
                if response.status == 200:
                    await response.json()
                    return True
        except Exception as e:
            print(f"❌ Error verificando salud del servidor: {e}")
        return False
    
    async def list_tools(self) -> List[Dict]:
        """Lista las herramientas disponibles basadas en los endpoints REST"""
        if not self.is_connected:
            print("❌ Servidor remoto no está conectado")
            return []
        
        try:
            # Definir herramientas basadas en los endpoints disponibles
            tools = [
                {
                    "name": "health_check",
                    "description": "Verifica el estado de salud del servidor remoto",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_inspirational_quote",
                    "description": "Obtiene una cita inspiracional para dormir",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Categoría de la cita",
                                "enum": ["sleep_hygiene", "mindfulness", "motivation", "science", "holistic", "wellness", "inspiration", "techniques"]
                            },
                            "mood": {
                                "type": "string",
                                "description": "Estado de ánimo deseado",
                                "enum": ["calm", "motivational", "peaceful", "reflective", "educational"]
                            },
                            "time_based": {
                                "type": "boolean",
                                "description": "Si usar cita basada en la hora actual",
                                "default": False
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "get_sleep_hygiene_tip",
                    "description": "Obtiene un consejo específico de higiene del sueño",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "search_sleep_quotes",
                    "description": "Busca citas por palabra clave",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Palabra clave para buscar en las citas"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de resultados",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_daily_sleep_wisdom",
                    "description": "Obtiene sabiduría diaria sobre el sueño con cita y consejo",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "include_tip": {
                                "type": "boolean",
                                "description": "Incluir consejo práctico además de la cita",
                                "default": True
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "mcp_call",
                    "description": "Llamada genérica al endpoint MCP para funcionalidades avanzadas",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "method": {
                                "type": "string",
                                "description": "Método MCP a llamar"
                            },
                            "params": {
                                "type": "object",
                                "description": "Parámetros para el método MCP"
                            }
                        },
                        "required": ["method"]
                    }
                }
            ]
            
            
            return tools
            
        except Exception as e:
            print(f"❌ Error listando herramientas remotas: {e}")
            return []
    
    async def call_endpoint(self, tool_name: str, arguments: dict) -> str:
        """Llama a un endpoint REST usando el nombre de la herramienta"""
        if not self.is_connected:
            return "❌ Servidor remoto no está conectado"
        
        try:
            # Mapear tool_name a endpoint y método HTTP
            endpoint_mapping = {
                "health_check": ("GET", "/health", {}),
                "get_inspirational_quote": ("GET", "/api/quote", ["category", "mood", "time_based"]),
                "get_sleep_hygiene_tip": ("GET", "/api/tip", {}),
                "search_sleep_quotes": ("GET", "/api/search/{query}", ["query", "limit"]),
                "get_daily_sleep_wisdom": ("GET", "/api/wisdom", ["include_tip"]),
                "mcp_call": ("POST", "/mcp", {})
            }
            
            if tool_name not in endpoint_mapping:
                return f"❌ Herramienta desconocida: {tool_name}"
            
            method, endpoint, valid_params = endpoint_mapping[tool_name]
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                # Para search, manejar el path parameter
                if "{query}" in endpoint and "query" in arguments:
                    url = url.replace("{query}", str(arguments["query"]))
                    # Crear params sin query (ya está en la URL)
                    params = {
                        k: str(v) if isinstance(v, bool) else v
                        for k, v in arguments.items() 
                        if k != "query" and (not valid_params or k in valid_params)
                    }
                else:
                    # Para otros GET, usar query parameters normales
                    params = {
                        k: str(v) if isinstance(v, bool) else v
                        for k, v in arguments.items()
                        if not valid_params or k in valid_params
                    }

                async with self.session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        return f"❌ Error del servidor: {response.status}"
            
            elif method == "POST":
                async with self.session.post(url, json=arguments, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        return f"❌ Error del servidor: {response.status}"
                        
        except Exception as e:
            return f"❌ Error comunicándose con el servidor remoto: {str(e)}"
        
    async def stop_server(self):
        """Cierra la conexión al servidor remoto"""
        if self.session:
            await self.session.close()
            self.is_connected = False
            print("✅ Conexión al servidor remoto cerrada")