# src/chatbot/clients/kitchen_coach_client.py
import asyncio
import json
import subprocess
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime

class KitchenCoachClient:
    """Cliente para interactuar con el Kitchen Coach MCP Server"""
    
    def __init__(self):
        self.server_process = None
        self.is_connected = False
        self.request_id = 1
    
    async def start_server(self):
        """Inicia el servidor Kitchen Coach"""
        try:
            # Buscar el servidor Kitchen en la ruta esperada
            server_path = Path(__file__).parent.parent.parent / "servidores locales mcp" / "kitchen-mcp" / "src" / "mcp-server.js"
            
            # Asegurarse de que el archivo existe
            if not server_path.exists():
                print(f"❌ Servidor no encontrado: {server_path}")
                return False
            
            print("🚀 Iniciando Kitchen Coach Server...")
            
            # Ejecutar con Node.js
            self.server_process = await asyncio.create_subprocess_exec(
                "node", str(server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Esperar un momento para que el servidor se inicie
            await asyncio.sleep(2)
            
            # Verificar si el proceso sigue ejecutándose
            if self.server_process.returncode is not None:
                stderr_output = await self.server_process.stderr.read()
                print(f"❌ El servidor se cerró inmediatamente: {stderr_output.decode()}")
                return False
            
            # Inicializar el servidor MCP
            if await self._initialize_mcp():
                self.is_connected = True
                print("✅ Kitchen Coach Server conectado y listo")
                return True
            else:
                print("❌ Falló la inicialización del servidor MCP")
                return False
                
        except FileNotFoundError:
            print("❌ Node.js no encontrado. Instala Node.js para usar Kitchen Coach")
            return False
        except Exception as e:
            print(f"❌ Error iniciando Kitchen Coach Server: {e}")
            return False
    
    async def _initialize_mcp(self) -> bool:
        """Inicializa la conexión MCP con el servidor"""
        try:
            # 1. Enviar mensaje de inicialización
            init_message = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "kitchen-coach-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_message(init_message)
            if not response or "error" in response:
                print(f"❌ Error en inicialización: {response.get('error') if response else 'Sin respuesta'}")
                return False
            
            # 2. Enviar notificación de inicializado
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            # Las notificaciones no esperan respuesta
            await self._send_notification(initialized_notification)
            
            return True
            
        except Exception as e:
            print(f"❌ Error en inicialización MCP: {e}")
            return False
    
    async def _send_message(self, message: dict) -> dict:
        """Envía un mensaje y espera respuesta"""
        try:
            message_str = json.dumps(message) + "\n"
            
            self.server_process.stdin.write(message_str.encode())
            await self.server_process.stdin.drain()
            
            # Leer respuesta
            response_line = await asyncio.wait_for(
                self.server_process.stdout.readline(), 
                timeout=10.0
            )
            
            if not response_line:
                print("❌ No se recibió respuesta del servidor")
                return None
            
            response_str = response_line.decode().strip()
            
            return json.loads(response_str)
            
        except asyncio.TimeoutError:
            print("❌ Timeout esperando respuesta del servidor")
            return None
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return None
    
    async def _send_notification(self, notification: dict):
        """Envía una notificación (no espera respuesta)"""
        try:
            message_str = json.dumps(notification) + "\n"
            
            self.server_process.stdin.write(message_str.encode())
            await self.server_process.stdin.drain()
            
        except Exception as e:
            print(f"❌ Error enviando notificación: {e}")
    
    def _get_request_id(self) -> int:
        """Genera un ID único para cada request"""
        request_id = self.request_id
        self.request_id += 1
        return request_id
    
    async def list_tools(self) -> List[Dict]:
        """Lista las herramientas disponibles en el servidor"""
        if not self.is_connected:
            print("❌ Kitchen Coach Server no está conectado")
            return []
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "tools/list",
                "params": {}
            }
            
            response = await self._send_message(message)
            
            if response and "result" in response:
                tools = response["result"]["tools"]
                print(f"🔧 Herramientas disponibles: {[tool['name'] for tool in tools]}")
                return tools
            else:
                print(f"❌ Error listando herramientas: {response}")
                return []
                
        except Exception as e:
            print(f"❌ Error listando herramientas: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Llama a una herramienta del servidor MCP"""
        if not self.is_connected:
            return "❌ Kitchen Coach Server no está conectado"
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self._send_message(message)
            
            if response and "result" in response:
                # Extraer el contenido de la respuesta
                content = response["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    return content[0]["text"]
                else:
                    return str(content)
            elif response and "error" in response:
                return f"❌ Error: {response['error']['message']}"
            else:
                return "❌ Respuesta inesperada del servidor"
                
        except Exception as e:
            return f"❌ Error comunicándose con Kitchen Coach: {str(e)}"

    # Métodos específicos para Kitchen Coach
    
    async def recommend_by_mood_and_season(self, mood: str, season: str = None, type: str = "recipe") -> str:
        """Recomienda comidas o recetas basadas en estado de ánimo y temporada"""
        args = {"mood": mood, "type": type}
        if season:
            args["season"] = season
        return await self.call_tool("recommend_by_mood_and_season", args)
    
    async def suggest_utensils_for_recipe(self, recipe_name: str) -> str:
        """Sugiere utensilios necesarios para una receta"""
        return await self.call_tool("suggest_utensils_for_recipe", {"recipe_name": recipe_name})
    
    async def suggest_recipe_by_diet(self, diet: str, max_calories: int = None) -> str:
        """Sugiere recetas por tipo de dieta"""
        args = {"diet": diet}
        if max_calories:
            args["maxCalories"] = max_calories
        return await self.call_tool("suggest_recipe_by_diet", args)
    
    async def suggest_ingredient_substitution(self, ingredient: str) -> str:
        """Sugiere sustitutos para un ingrediente"""
        return await self.call_tool("suggest_ingredient_substitution", {"ingredient": ingredient})
    
    async def get_food_by_name(self, name: str) -> str:
        """Busca un alimento específico por nombre"""
        return await self.call_tool("get_food_by_name", {"name": name})
    
    async def search_foods(self, min_protein: float = None, max_fat: float = None, max_calories: int = None) -> str:
        """Busca alimentos por criterios nutricionales"""
        args = {}
        if min_protein is not None:
            args["minProtein"] = min_protein
        if max_fat is not None:
            args["maxFat"] = max_fat
        if max_calories is not None:
            args["maxCalories"] = max_calories
        return await self.call_tool("search_foods", args)
    
    async def get_recipes_by_ingredients(self, ingredients: List[str]) -> str:
        """Encuentra recetas que contengan ingredientes específicos"""
        return await self.call_tool("get_recipes_by_ingredients", {"ingredients": ingredients})
    
    async def get_all_foods(self) -> str:
        """Obtiene todos los alimentos disponibles"""
        return await self.call_tool("get_foods", {})
    
    async def get_all_recipes(self) -> str:
        """Obtiene todas las recetas disponibles"""
        return await self.call_tool("get_recipes", {})
    
    async def get_ingredients(self) -> str:
        """Obtiene lista de ingredientes disponibles"""
        return await self.call_tool("get_ingredients", {})
    
    async def get_recipe_suggestions(self) -> str:
        """Obtiene sugerencias de recetas basadas en contenido nutricional"""
        return await self.call_tool("get_recipe_suggestions", {})

    async def stop_server(self):
        """Detiene el servidor"""
        if self.server_process and self.server_process.returncode is None:
            print("🛑 Deteniendo Kitchen Coach Server...")
            self.server_process.terminate()
            
            try:
                await asyncio.wait_for(self.server_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                print("⚠️ Forzando cierre del servidor...")
                self.server_process.kill()
                await self.server_process.wait()
            
            self.is_connected = False
            print("✅ Kitchen Coach Server detenido")

# Función de prueba
async def test_kitchen_coach():
    """Función para probar el cliente Kitchen Coach"""
    client = KitchenCoachClient()
    
    try:
        # Iniciar servidor
        if await client.start_server():
            print("✅ Servidor iniciado correctamente")
            
            # Listar herramientas
            tools = await client.list_tools()
            print(f"🔧 Herramientas disponibles: {len(tools)}")
            
            # Probar recomendación por estado de ánimo
            mood_recommendation = await client.recommend_by_mood_and_season("happy", "summer")
            print(f"😊 Recomendación por estado de ánimo: {mood_recommendation[:200]}...")
            
            # Probar búsqueda de alimentos
            food_search = await client.search_foods(min_protein=10, max_calories=200)
            print(f"🥗 Búsqueda de alimentos: {food_search[:200]}...")
            
            # Probar sustitución de ingredientes
            substitution = await client.suggest_ingredient_substitution("orange juice")
            print(f"🔄 Sustitución de ingrediente: {substitution[:200]}...")
            
            # Probar recetas por dieta
            diet_recipes = await client.suggest_recipe_by_diet("vegan")
            print(f"🌱 Recetas veganas: {diet_recipes[:200]}...")
            
        else:
            print("❌ No se pudo iniciar el servidor")
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    finally:
        await client.stop_server()

# Ejecutar prueba si se ejecuta directamente
if __name__ == "__main__":
    asyncio.run(test_kitchen_coach())