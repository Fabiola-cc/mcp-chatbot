# src/chatbot/main.py
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv
from mcp import ClientSession

from clients.ollama_client import OllamaClient

from tools.session_manager import SessionManager
from tools.logger import InteractionLogger
from tools.command_handler import CommandHandler

from mcp_oficial.git_file_client import MCPClient

class MCPChatbot:
    def __init__(self):
        """Inicializa el chatbot con todos sus componentes"""
        load_dotenv()
        
        try:
            self.ollama = OllamaClient()
            self.session = SessionManager()
            self.logger = InteractionLogger()
            self.command_handler = CommandHandler()

            self.git_file_client = MCPClient()
            self.gf_active = False

            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print("🤖 Inicializando chatbot MCP con Ollama...")
            print("✅ Conexión con Ollama establecida")
                
        except Exception as e:
            print(f"❌ Error inicializando chatbot: {str(e)}")
            print("\n💡 Soluciones:")
            print("1. Verificar que Ollama esté instalado: curl -fsSL https://ollama.com/install.sh | sh")
            print("2. Iniciar Ollama: ollama serve")
            print("3. Descargar un modelo: ollama pull llama3.2:3b")
            sys.exit(1)
    
    def show_welcome_message(self):
        """Muestra mensaje de bienvenida y comandos disponibles"""
        print("\n" + "="*60)
        print("CHATBOT MCP LOCAL - ¡Bienvenido!")
        print("Usando modelo local con Ollama (100% privado)")
        print("="*60)
        print("💬 Puedes hacer preguntas normales o usar comandos especiales:")
        print()
        print("COMANDOS ESPECIALES:")
        print("  /fs create <file> <contenido>")
        print("  /git init | /git add | /git commit \"msg\"")
        print("  /sleep help   - Conoce el recomendador de rutinas de sueño")
        print("  /quotes help  - Consejero de sueño")
        print("  /movies help  - Recomendador de películas")
        print("  /kitchen help - Recomendador de películas")
        print("  /help         - Mostrar esta ayuda")
        print("  /log          - Mostrar log de interacciones")
        print("  /mcp          - Mostrar interacciones MCP")
        print("  /stats        - Mostrar estadísticas de la sesión")
        print("  /context      - Mostrar resumen del contexto actual")
        print("  /clear        - Limpiar contexto de conversación")
        print("  /save         - Guardar sesión actual")
        print("  /quit         - Salir del chatbot")
        print()
        print("🛌 Sleep Coach, 👨‍🍳 Kitchen Coach y 🎬 Movies Recomendator listos para recomendaciones personalizadas")
        print("="*60)
    
    async def process_special_command(self, command: str) -> bool:
        """
        Procesa comandos especiales del usuario
        
        Args:
            command: Comando ingresado por el usuario
            
        Returns:
            True si era un comando especial, False si no
        """
        command = command.lower().strip()
        
        if command.startswith("/sleep"): # Servidor local propio
            return await self.command_handler.handle_sleep_command(command)
        
        elif command.startswith("/quotes"): # Servidor remoto
            return await self.command_handler.handle_quotes_command(command)

        elif command.startswith("/movies"): # Servidor externo
            return await self.command_handler.handle_movies_command(command)
        
        elif command.startswith("/kitchen"): # Servidor externo
            return await self.command_handler.handle_kitchen_command(command)

        elif command == '/help':
            self.show_welcome_message()
            return True
            
        elif command == '/log':
            self.logger.show_interaction_log()
            return True
            
        elif command == '/mcp':
            self.logger.show_mcp_interactions()
            return True
            
        elif command == '/stats':
            stats = self.session.get_session_stats()
            mcp_stats = self.logger.get_mcp_stats()
            
            print(f"\n📊 ESTADÍSTICAS DE SESIÓN:")
            print(f"  Total mensajes: {stats['total_messages']}")
            print(f"  Mensajes usuario: {stats['user_messages']}")
            print(f"  Mensajes chatbot: {stats['assistant_messages']}")
            print(f"   Duración: {stats['session_duration']}")
            print(f"  Mensajes en contexto: {stats['messages_in_context']}")
            print(f"\nESTADÍSTICAS MCP:")
            print(f"  Interacciones totales: {mcp_stats['total_interactions']}")
            print(f"  Tasa de éxito: {mcp_stats['success_rate']:.1f}%")
            print(f"  Servidores usados: {', '.join(mcp_stats['servers_used']) if mcp_stats['servers_used'] else 'Ninguno'}")
            
            return True
            
        elif command == '/context':
            self.session.show_context_summary()
            return True
            
        elif command == '/clear':
            self.session.clear_context()
            return True
            
        elif command == '/save':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"
            self.session.save_session(filename)
            return True
            
        elif command == '/quit':
            return True
        
        elif command.startswith('/fs '):
            if self.gf_active == False:
                fs_success = await self.git_file_client.start_fs_server()
                if not fs_success:
                    print("❌ Error iniciando Filesystem server")
                    return True
                self.gf_active = True
            
            # /fs create <filename> <contenido>
            parts = command.split(" ", 3)
            if len(parts) < 4 or parts[1] != "create":
                print("❌ Uso: /fs create <filename> <contenido>")
                return True
            
            filename, content = parts[2], parts[3]
            result = await self.git_file_client.create_file(filename, content)
            
            if result and "isError" not in result:
                print(f"✅ Archivo '{filename}' creado exitosamente")
            else:
                print(f"❌ Error creando archivo: {result}")
            
            return True

        elif command.startswith('/git '):
            if self.gf_active == False:
                fs_success = await self.git_file_client.start_fs_server()
                if not fs_success:
                    print("❌ Error iniciando Filesystem server")
                    return True
                self.gf_active = True
            
            parts = command.split(" ", 4)  # Aumenté para manejar mensaje con espacios
            action = parts[1] if len(parts) > 1 else ""
            
            if action == "init":
                if len(parts) < 3:
                    print("❌ Uso: /git init <nombre_repositorio>")
                    return True
                
                repo_name = parts[2]
                
                # Crear repositorio con Git nativo
                success = self.git_file_client.create_git_repo_native(repo_name)
                if success:
                    print(f"✅ Repositorio '{repo_name}' creado exitosamente")
                    
                    # Opcionalmente, iniciar Git MCP server si existe el repo
                    try:
                        await self.git_file_client.start_git_server_after_repo(repo_name)
                        print(f"✅ Git MCP server iniciado para '{repo_name}'")
                    except:
                        print("⚠️ Git MCP server no disponible, usando solo Git nativo")
                else:
                    print(f"❌ Error creando repositorio '{repo_name}'")
                
                return True
            
            elif action == "commit":
                if len(parts) < 5:
                    print("❌ Uso: /git commit <repositorio> <archivo> \"mensaje\"")
                    return True
                
                repo_name = parts[2]
                file_path = parts[3]
                commit_message = parts[4].strip('"')
                
                # Hacer commit con Git nativo
                success = self.git_file_client.git_add_commit_native(
                    repo_name, 
                    [file_path], 
                    commit_message
                )
                
                if success:
                    print(f"✅ Commit realizado en '{repo_name}': {commit_message}")
                else:
                    print(f"❌ Error en commit para '{repo_name}'")
                
                return True
            
            elif action == "status":
                if len(parts) < 3:
                    print("❌ Uso: /git status <repositorio>")
                    return True
                
                repo_name = parts[2]
                
                # Intentar usar Git MCP si está disponible
                if hasattr(self.git_file_client, 'git_process') and self.git_file_client.git_process:
                    result = await self.git_file_client.git_status(repo_name)
                    if result and "result" in result:
                        content = result["result"]["content"][0]["text"]
                        print(f"📊 Status de '{repo_name}':\n{content}")
                    else:
                        print(f"❌ Error obteniendo status de '{repo_name}'")
                else:
                    print("⚠️ Git MCP no disponible. Use: git status (comando nativo)")
                
                return True
            
            elif action == "log":
                if len(parts) < 3:
                    print("❌ Uso: /git log <repositorio>")
                    return True
                
                repo_name = parts[2]
                
                # Intentar usar Git MCP si está disponible
                if hasattr(self.git_file_client, 'git_process') and self.git_file_client.git_process:
                    result = await self.git_file_client.git_log(repo_name)
                    if result and "result" in result:
                        content = result["result"]["content"][0]["text"]
                        print(f"📜 Log de '{repo_name}':\n{content}")
                    else:
                        print(f"❌ Error obteniendo log de '{repo_name}'")
                else:
                    print("⚠️ Git MCP no disponible. Use: git log (comando nativo)")
                
                return True
            
            else:
                print("❌ Comandos disponibles:")
                print("   /git init <repositorio>")
                print("   /git commit <repositorio> <archivo> \"mensaje\"")
                print("   /git status <repositorio>")
                print("   /git log <repositorio>")
                return True

        return False

    def process_user_message(self, message: str) -> str:
        """
        Procesa mensaje del usuario y genera respuesta
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Respuesta del chatbot
        """
        # Por ahora, solo usar Ollama
        
        context = self.session.get_context()
        response = self.ollama.send_message(message, context)
        
        return response
    
    async def call_sleep_coach(self, message: str):
        """Conecta con el servidor Sleep Coach MCP"""
        try:
            async with ClientSession("ws://localhost:8000") as session:
                response = await session.call("sleep-coach", "recommend_sleep", {"message": message})
                return response["recommendations"]
        except Exception as e:
            return [f"❌ Error conectando con Sleep Coach: {str(e)}"]
    
    async def _async_run(self):
        """Versión async del loop principal"""
        while True:
            # Obtener entrada del usuario
            user_input = input(f"\n👤 Tú: ").strip()
            
            # Verificar si es comando especial
            if user_input.startswith('/'):
                should_quit = await self.process_special_command(user_input)
                if user_input.lower() == '/quit':
                    break
                if should_quit:
                    continue
                
            # Verificar entrada vacía
            if not user_input:
                print("💭 Por favor ingresa un mensaje o usa /help para ver comandos")
                continue
            
            # Registrar entrada del usuario
            self.logger.log_user_input(user_input, self.session_id)
            
            # Procesar mensaje
            print("🤔 Pensando...")
            response = self.process_user_message(user_input)
            
            # Agregar al contexto
            self.session.add_message("user", user_input)
            self.session.add_message("assistant", response)
            
            # Registrar respuesta
            estimated_tokens = self.ollama.estimate_tokens(response)
            self.logger.log_anthropic_response(response, estimated_tokens, self.session_id)
            
            # Mostrar respuesta
            print(f"\n🤖 Chatbot: {response}")

    def run(self):
        """Ejecuta el loop principal del chatbot"""
        self.show_welcome_message()
        
        try:
            # Iniciar loop asyncio si no está corriendo
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No hay loop corriendo, crear uno nuevo
                asyncio.run(self._async_run())
                return
            
            # Si ya hay un loop, usar run_until_complete
            loop.run_until_complete(self._async_run())
                
        except KeyboardInterrupt:
            print("\n\n🛑 Chatbot interrumpido por el usuario")
        except Exception as e:
            print(f"\nError inesperado: {str(e)}")
            self.logger.logger.error(f"Error en loop principal: {str(e)}")
        finally:
            # Limpiar recursos
            if self.command_handler.sleep_coach_active:
                print("🧹 Cerrando Sleep Coach Server...")
                try:
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(self.sleep_coach.stop_server())
                except:
                    pass
            
            # Limpiar recursos de servicios externos
            if self.command_handler.movies_active:
                self.command_handler.movies_client.stop_server()

            # Guardar sesión al salir
            self.session.save_session(f"{self.session_id}.json")
            print("Sesión guardada automáticamente")
            print("¡Hasta luego!")


if __name__ == "__main__":
    asyncio.run(MCPChatbot().run())