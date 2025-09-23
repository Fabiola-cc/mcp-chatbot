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
            print("🎬 Iniciando Movies MCP Server...")
            
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
            print(f"❌ Error iniciando servidor: {str(e)}")
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
            print("Timeout leyendo respuesta del servidor")
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
        except Exception as e:
            print(f"❌ Error leyendo respuesta: {str(e)}")
            
        return None

    def _format_movie_response(self, raw_response: str) -> str:
        """Formatea la respuesta de películas de manera legible"""
        try:
            # Intentar parsear como JSON
            data = json.loads(raw_response)
            
            # Si es una lista de películas
            if isinstance(data, list):
                return self._format_movie_list(data)
            
            # Si es una película individual
            elif isinstance(data, dict) and "title" in data:
                return self._format_single_movie(data)
            
            # Si es un resultado de herramienta específica
            elif isinstance(data, dict):
                return self._format_tool_result(data)
            
            else:
                return f"📋 Respuesta: {raw_response}"
                
        except json.JSONDecodeError:
            # Si no es JSON válido, devolver tal como está
            return f"📋 Respuesta: {raw_response}"
    
    def _format_single_movie(self, movie: Dict) -> str:
        """Formatea una película individual"""
        title = movie.get("title", "Título desconocido")
        year = movie.get("release_year", "N/A")
        rating = movie.get("vote_average", "N/A")
        runtime = movie.get("runtime", "N/A")
        overview = movie.get("overview", "Sin descripción")
        genres = movie.get("genres", [])
        imdb_id = movie.get("imdb_id", "")
        
        # Truncar overview si es muy largo
        if len(overview) > 200:
            overview = overview[:197] + "..."
        
        # Formatear géneros
        genres_str = ", ".join(genres) if genres else "N/A"
        
        formatted = f"""
 **{title}** ({year})
 Calificación: {rating}/10
 Duración: {runtime} min
 Géneros: {genres_str}
 Sinopsis: {overview}"""
        
        if imdb_id:
            formatted += f"\n IMDb: https://www.imdb.com/title/{imdb_id}"
        
        return formatted
    
    def _format_movie_list(self, movies: List[Dict]) -> str:
        """Formatea una lista de películas"""
        if not movies:
            return " No se encontraron películas"
        
        formatted = f"**Encontradas {len(movies)} películas:**\n"
        formatted += "=" * 50 + "\n"
        
        for i, movie in enumerate(movies, 1):
            title = movie.get("title", "Título desconocido")
            year = movie.get("release_year", "N/A")
            rating = movie.get("vote_average", "N/A")
            genres = movie.get("genres", [])
            overview = movie.get("overview", "")
            
            # Truncar overview
            if overview and len(overview) > 100:
                overview = overview[:97] + "..."
            
            genres_str = ", ".join(genres[:3]) if genres else "N/A"  # Max 3 géneros
            
            formatted += f"""
{i}.  **{title}** ({year})
    {rating}/10 |  {genres_str}
    {overview}
"""
        
        return formatted
    
    def _format_tool_result(self, data: Dict) -> str:
        """Formatea resultados de herramientas específicas"""
        # Si contiene información de playlist
        if "total_runtime" in data and "movies" in data:
            return self._format_playlist(data)
        
        # Si es información detallada de actor
        elif "actor" in data and "movies" in data:
            return self._format_actor_filmography(data)
        
        # Si es resultado de recomendaciones
        elif "recommendations" in data:
            return self._format_movie_list(data["recommendations"])
        
        # Formato genérico para otros casos
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _format_playlist(self, playlist: Dict) -> str:
        """Formatea una playlist de películas"""
        total_runtime = playlist.get("total_runtime", 0)
        movies = playlist.get("movies", [])
        target = playlist.get("target_minutes", 0)
        
        hours = total_runtime // 60
        minutes = total_runtime % 60
        
        formatted = f"""
 **PLAYLIST DE PELÍCULAS**
 Objetivo: {target} min | ⏱ Total: {hours}h {minutes}m
 {len(movies)} películas seleccionadas

{"=" * 50}
"""
        
        for i, movie in enumerate(movies, 1):
            title = movie.get("title", "Título desconocido")
            runtime = movie.get("runtime", "N/A")
            rating = movie.get("vote_average", "N/A")
            year = movie.get("release_year", "N/A")
            
            formatted += f"{i}. 🎬 {title} ({year}) - {runtime}min ⭐{rating}/10\n"
        
        return formatted
    
    def _format_actor_filmography(self, data: Dict) -> str:
        """Formatea la filmografía de un actor"""
        actor = data.get("actor", "Actor desconocido")
        movies = data.get("movies", [])
        
        formatted = f"""
 **FILMOGRAFÍA DE {actor.upper()}**
 {len(movies)} películas encontradas

{"=" * 50}
"""
        
        for i, movie in enumerate(movies, 1):
            title = movie.get("title", "Título desconocido")
            year = movie.get("release_year", "N/A")
            rating = movie.get("vote_average", "N/A")
            role = movie.get("character", movie.get("role", "N/A"))
            
            formatted += f"{i}. 🎬 {title} ({year}) ⭐{rating}/10\n"
            if role != "N/A":
                formatted += f"   👤 Personaje: {role}\n"
        
        return formatted

    async def call_tool(self, tool_name: str, params: Dict = None) -> str:
        """Llama a una herramienta usando el servidor persistente"""
        if not self.is_active or not self._initialized:
            return "❌ Servidor no inicializado. Use 'await start_server()' primero."
            
        try:
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
                            # Aplicar formateo aquí
                            return self._format_movie_response(first_content['text'])
                        else:
                            return self._format_movie_response(str(first_content))
                    else:
                        return "No existe esta información en la base de datos"
                
                # Si es directamente el resultado
                if isinstance(result, (list, dict)):
                    return self._format_movie_response(json.dumps(result, ensure_ascii=False))
                else:
                    return self._format_movie_response(str(result))
                    
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

    # Métodos de conveniencia con mejor documentación
    async def test_ping(self) -> str:
        """Test de ping"""
        result = await self.call_tool("ping_tool")
        return f"🏓 Ping: {result}"

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
        print("🛑 Movies Server desconectado")

    def stop_client(self):
        """Método síncrono para cerrar"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stop_server())
            loop.close()
        except:
            pass


# Función de prueba con formato mejorado
async def test_persistent_client():
    """Prueba el cliente persistente con formato mejorado"""
    client = MoviesClient()
    
    try:
        print("🧪 TESTING MOVIES CLIENT CON FORMATO MEJORADO")
        print("=" * 60)
        
        if not await client.start_server():
            print("❌ No se pudo iniciar el servidor persistente")
            return
        
        # Test ping
        print("\n📌 Test 1: Ping")
        result = await client.test_ping()
        print(f"📋 Resultado: {result}")
        
        # Test búsqueda - ahora con formato mejorado
        print("\n📌 Test 2: Búsqueda Batman (Formato Mejorado)")
        result = await client.search_movies("batman", 3)
        print("📋 Resultado:")
        print(result)
        
        # Test otra búsqueda para verificar persistencia
        print("\n📌 Test 3: Búsqueda Matrix (Formato Mejorado)")
        result = await client.search_movies("matrix", 2)
        print("📋 Resultado:")
        print(result)
        
        # Test recomendaciones
        print("\n📌 Test 4: Recomendaciones de Acción (Formato Mejorado)")
        prefs = {"genres": ["Action"], "min_rating": 8.0}
        result = await client.get_recommendations(prefs)
        print("📋 Resultado:")
        print(result)
        
        # Test filmografía de actor
        print("\n📌 Test 5: Filmografía de Leonardo DiCaprio")
        result = await client.get_actor_filmography("Leonardo DiCaprio", 5)
        print("📋 Resultado:")
        print(result)
        
        # Test playlist
        print("\n📌 Test 6: Crear Playlist de 4 horas")
        result = await client.create_playlist(480, {"genres": ["Drama","Thriller"], "prefer_high_rating": True})
        print("📋 Resultado:")
        print(result)
        
        print("\n✅ Todos los tests completados exitosamente con formato mejorado!")
        
    except Exception as e:
        print(f"❌ Error en tests: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.stop_server()

if __name__ == "__main__":
    asyncio.run(test_persistent_client())