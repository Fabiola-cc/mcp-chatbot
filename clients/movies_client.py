# src/chatbot/clients/movies_client_persistent.py
import asyncio
import subprocess
import json
import sys
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class MoviesClient:
    def __init__(self):
        """Cliente para el servidor MCP de películas"""
        self.server_process = None
        self.is_active = False
        self._message_id = 0
        self._initialized = False
        
        # Ruta al servidor
        self.server_path = Path(__file__).parent.parent.parent / "servidores locales mcp" / "Movies_ChatBot" / "movie_server.py"
        
    def _get_next_id(self) -> int:
        """Obtiene el siguiente ID para mensajes"""
        self._message_id += 1
        return self._message_id
        
    async def start_server(self) -> bool:
        """Inicia el servidor MCP de forma persistente"""
        if self.is_active and self.server_process and self.server_process.returncode is None:
            return True
            
        try:
            print("🎬 Iniciando Movies MCP Server persistente...")
            
            # Verificar que el archivo del servidor existe
            if not self.server_path.exists():
                print(f"❌ No se encontró el servidor en: {self.server_path}")
                return False
            
            # Crear proceso persistente
            cmd = [sys.executable, str(self.server_path)]
            
            self.server_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ}
            )
            
            # Inicializar el servidor
            if await self._initialize_server():
                self.is_active = True
                print("✅ Movies MCP Server iniciado y inicializado")
                return True
            else:
                await self._cleanup()
                return False
                
        except Exception as e:
            print(f"❌ Error iniciando servidor persistente: {str(e)}")
            await self._cleanup()
            return False

    async def _initialize_server(self) -> bool:
        """Inicializa el servidor con la secuencia MCP correcta"""
        try:
            # Mensaje de inicialización
            init_message = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": "movies-persistent-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Enviar inicialización
            await self._send_message(init_message)
            
            # Leer respuesta de inicialización
            init_response = await self._read_response()
            if not init_response or 'error' in init_response:
                print(f"❌ Error en inicialización: {init_response}")
                return False
            
            # Enviar notificación de inicializado
            initialized_message = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await self._send_message(initialized_message)
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando servidor: {str(e)}")
            return False

    async def _send_message(self, message: Dict) -> None:
        """Envía un mensaje al servidor"""
        if not self.server_process or not self.server_process.stdin:
            raise Exception("Servidor no disponible")
            
        message_json = json.dumps(message) + "\n"
        self.server_process.stdin.write(message_json.encode())
        await self.server_process.stdin.drain()

    async def _read_response(self, timeout: float = 10.0) -> Optional[Dict]:
        """Lee una respuesta del servidor"""
        if not self.server_process or not self.server_process.stdout:
            return None
            
        try:
            # Leer línea con timeout
            line = await asyncio.wait_for(
                self.server_process.stdout.readline(),
                timeout=timeout
            )
            
            if not line:
                return None
                
            line_str = line.decode().strip()
            if line_str:
                return json.loads(line_str)
                
        except asyncio.TimeoutError:
            print("⏰ Timeout leyendo respuesta del servidor")
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
        except Exception as e:
            print(f"❌ Error leyendo respuesta: {str(e)}")
            
        return None

    async def call_tool(self, tool_name: str, params: Dict = None) -> str:
        """Llama a una herramienta usando el servidor persistente"""
        if not self.is_active or not self._initialized:
            return "❌ Servidor no inicializado. Use 'await start_server()' primero."
            
        try:
            print(f"🔧 Llamando {tool_name} con parámetros: {params}")
            
            # Preparar argumentos según el tipo de herramienta
            if tool_name == "ping_tool":
                arguments = {}
            else:
                arguments = {"params": params if params is not None else {}}
            
            # Crear mensaje de llamada a herramienta
            tool_message = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Enviar mensaje
            await self._send_message(tool_message)
            
            # Leer respuesta
            response = await self._read_response(30.0)  # Timeout más largo para herramientas
            
            if not response:
                return f"❌ No se recibió respuesta para {tool_name}"
            
            # Procesar respuesta
            if 'result' in response:
                result = response['result']
                
                # Manejar formato de respuesta MCP
                if isinstance(result, dict) and 'content' in result:
                    content = result['content']
                    if isinstance(content, list) and len(content) > 0:
                        first_content = content[0]
                        if isinstance(first_content, dict) and 'text' in first_content:
                            return first_content['text']
                        else:
                            return str(first_content)
                
                # Si es directamente el resultado
                if isinstance(result, (list, dict)):
                    return json.dumps(result, indent=2, ensure_ascii=False)
                else:
                    return str(result)
                    
            elif 'error' in response:
                error = response['error']
                return f"❌ Error del servidor: {error.get('message', str(error))}"
            else:
                return f"❌ Respuesta inesperada: {response}"
                
        except Exception as e:
            print(f"❌ Excepción en call_tool: {str(e)}")
            # Si hay error de comunicación, reiniciar servidor
            if "Broken pipe" in str(e) or "connection" in str(e).lower():
                print("🔄 Reiniciando servidor por error de conexión...")
                await self._cleanup()
                await self.start_server()
            return f"❌ Error ejecutando {tool_name}: {str(e)}"

    async def _cleanup(self):
        """Limpia recursos del servidor"""
        self.is_active = False
        self._initialized = False
        
        if self.server_process:
            try:
                if self.server_process.returncode is None:
                    self.server_process.terminate()
                    await asyncio.wait_for(self.server_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                print("⚠️ Forzando cierre del servidor")
                self.server_process.kill()
            except Exception as e:
                print(f"⚠️ Error cerrando servidor: {e}")
            finally:
                self.server_process = None

    # Métodos de conveniencia
    async def test_ping(self) -> str:
        """Test de ping"""
        return await self.call_tool("ping_tool")

    async def search_movies(self, query: str, limit: int = 10) -> str:
        """Busca películas por título"""
        params = {"query": query, "limit": limit}
        return await self.call_tool("search_movie", params)

    async def get_movie_details(self, title: str) -> str:
        """Obtiene detalles de una película"""
        params = {"title": title}
        return await self.call_tool("movie_details", params)

    async def get_recommendations(self, preferences: Dict) -> str:
        """Obtiene recomendaciones basadas en preferencias"""
        params = {}
        
        if preferences.get("genres"):
            params["genres"] = preferences["genres"]
        if preferences.get("min_rating"):
            params["min_vote"] = float(preferences["min_rating"])
        if preferences.get("from_year"):
            params["from_year"] = preferences["from_year"]
        if preferences.get("to_year"):
            params["to_year"] = preferences["to_year"]
        if preferences.get("actors"):
            params["include_cast"] = preferences["actors"]
        
        params["limit"] = 15
        return await self.call_tool("recommend_movies_tool", params)

    async def get_popular_movies(self, limit: int = 10) -> str:
        """Obtiene películas populares"""
        params = {
            "genres": ["Action", "Drama", "Thriller"],
            "min_vote": 7.0,
            "from_year": 2015,
            "to_year": 2023,
            "limit": limit
        }
        return await self.call_tool("recommend_movies_tool", params)

    async def search_by_genre(self, genre: str, limit: int = 15) -> str:
        """Busca películas por género"""
        params = {
            "genres": [genre],
            "min_vote": 6.0,
            "limit": limit
        }
        return await self.call_tool("recommend_movies_tool", params)

    async def get_actor_filmography(self, actor: str, limit: int = 15) -> str:
        """Obtiene filmografía de un actor"""
        params = {"actor": actor, "limit": limit}
        return await self.call_tool("top_movies_by_actor_tool", params)

    async def find_similar_movies(self, title: str, limit: int = 10) -> str:
        """Encuentra películas similares"""
        params = {"title": title, "limit": limit}
        return await self.call_tool("similar_movies_tool", params)

    async def create_playlist(self, target_minutes: int = 480, preferences: Dict = None) -> str:
        """Crea una playlist de películas"""
        params = {
            "target_minutes": target_minutes,
            "prefer_high_rating": preferences.get("prefer_high_rating", True) if preferences else True,
        }
        
        if preferences:
            if preferences.get("genres"):
                params["genres"] = preferences["genres"]
            if preferences.get("language"):
                params["language"] = preferences["language"]
        
        return await self.call_tool("build_playlist_tool", params)

    async def stop_server(self):
        """Para el servidor"""
        await self._cleanup()
        print("🛑 Movies Server persistente desconectado")

    def stop_client(self):
        """Método síncrono para cerrar"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stop_server())
            loop.close()
        except:
            pass


# Función de prueba
async def test_persistent_client():
    """Prueba el cliente persistente"""
    client = MoviesClient()
    
    try:
        print("🧪 TESTING MOVIES CLIENT PERSISTENTE")
        print("=" * 50)
        
        if not await client.start_server():
            print("❌ No se pudo iniciar el servidor persistente")
            return
        
        # Test ping
        print("\n📌 Test 1: Ping")
        result = await client.test_ping()
        print(f"📋 Resultado: {result}")
        
        # Test búsqueda
        print("\n📌 Test 2: Búsqueda Batman")
        result = await client.search_movies("batman", 3)
        print(f"📋 Resultado: {result[:400]}...")
        
        # Test otra búsqueda para verificar persistencia
        print("\n📌 Test 3: Búsqueda Matrix")
        result = await client.search_movies("matrix", 2)
        print(f"📋 Resultado: {result[:400]}...")
        
        # Test recomendaciones
        print("\n📌 Test 4: Recomendaciones")
        prefs = {"genres": ["Action"], "min_rating": 8.0}
        result = await client.get_recommendations(prefs)
        print(f"📋 Resultado: {result[:400]}...")
        
        print("\n✅ Todos los tests completados exitosamente")
        
    except Exception as e:
        print(f"❌ Error en tests: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.stop_server()

if __name__ == "__main__":
    asyncio.run(test_persistent_client())