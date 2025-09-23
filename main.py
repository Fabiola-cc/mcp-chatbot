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

from mcp_servers.mcp_files import create_file
from mcp_servers.mcp_git import git_init, git_add, git_commit

class MCPChatbot:
    def __init__(self):
        """Inicializa el chatbot con todos sus componentes"""
        load_dotenv()
        
        try:
            self.ollama = OllamaClient()
            self.session = SessionManager()
            self.logger = InteractionLogger()
            self.command_handler = CommandHandler()

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
        print("  /git init | /git add | /git add | /git commit \"msg\"")
        print("  /sleep help  - Conoce el recomendador de rutinas de sueño")
        print("  /quotes help  - Consejero de sueño")
        print("  /movies help - Recomendador de películas")
        print("  /help        - Mostrar esta ayuda")
        print("  /log         - Mostrar log de interacciones")
        print("  /mcp         - Mostrar interacciones MCP")
        print("  /stats       - Mostrar estadísticas de la sesión")
        print("  /context     - Mostrar resumen del contexto actual")
        print("  /clear       - Limpiar contexto de conversación")
        print("  /save        - Guardar sesión actual")
        print("  /quit        - Salir del chatbot")
        print()
        print("🛌 Sleep Coach y 🎬 Movies Recomendator listos para recomendaciones personalizadas")
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
            # /fs create <filename> <contenido>
            parts = command.split(" ", 3)
            if len(parts) < 4 or parts[1] != "create":
                print("❌ Uso: /fs create <filename> <contenido>")
                return True
            filename, content = parts[2], parts[3]
            result = create_file(filename, content)
            print(result)
            return True

        elif command.startswith('/git '):
            os.makedirs("workspace", exist_ok=True)
            parts = command.split(" ", 2)
            action = parts[1] if len(parts) > 1 else ""

            if action == "init":
                print(git_init())
                return True
            elif action == "add":
                print(git_add())
                return True
            elif action == "commit":
                if len(parts) < 3:
                    print("❌ Uso: /git commit \"mensaje\"")
                    return True
                message = parts[2].strip('"')
                print(git_commit(message))
                return True
            else:
                print("❌ Comandos disponibles: /git init | /git add | /git commit \"mensaje\"")
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