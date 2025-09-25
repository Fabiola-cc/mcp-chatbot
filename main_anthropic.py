# src/chatbot/main.py
import json
from pathlib import Path
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from clients.anthropic_client import AnthropicClient
from clients.connection import Client
from clients.remote_client import RemoteSleepQuotesClient

from tools.session_manager import SessionManager
from tools.logger import InteractionLogger


class MCPChatbot:
    def __init__(self):
        """Inicializa el chatbot con todos sus componentes"""
        load_dotenv()
        
        try:
            self.claude = AnthropicClient()
            self.session = SessionManager()
            self.logger = InteractionLogger()

            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.clients = {
                "git": Client(),
                "files": Client(),
                "sleep_coach": Client(),
                "remote": RemoteSleepQuotesClient(),
                "beauty": Client(),
                "videogames": Client(),
                "movies": Client()
            }
                
        except Exception as e:
            print(f"❌ Error inicializando chatbot: {str(e)}")
            sys.exit(1)
    
    async def initialize_servers(self):
        await self.clients["git"].start_server(
            "git", sys.executable, "-m", "mcp_server_git", "--repository", str(Path(__file__).parent)
        )
        
        await self.clients["files"].start_server(
            "filesystem", r"C:\Program Files\nodejs\npx.cmd",
            "-y", "@modelcontextprotocol/server-filesystem", str(Path(__file__).parent)
        )

        await self.clients["sleep_coach"].start_server(
            "sleep_coach", sys.executable,
            str(Path(__file__).parent.parent / "servidores locales mcp/SleepCoachServer/sleep_coach.py")
        )

        await self.clients["beauty"].start_server(
            "beauty", sys.executable,
            str(Path(__file__).parent.parent / "servidores locales mcp/beauty-palette-server-local/beauty_mcp_server_local.py")
        )

        await self.clients["videogames"].start_server(
            "videogames", sys.executable,
            str(Path(__file__).parent.parent / "servidores locales mcp/MCP_VIDEOGAMES_REC_INFO/server/mcp_server.py")
        )

        await self.clients["movies"].start_server(
            "movies", sys.executable,
            str(Path(__file__).parent.parent / "servidores locales mcp/Movies_ChatBot/movie_server.py")
        )

        await self.clients["remote"].start_server()
        
        return
    
    async def servers_with_llm(self):
        # Obtener herramientas de cada servidor MCP
        sleep_tools = await self.clients["sleep_coach"].list_tools()
        git_tools = await self.clients["git"].list_tools()
        files_tools = await self.clients["files"].list_tools()
        beauty_tools = await self.clients["beauty"].list_tools()
        videogames_tools = await self.clients["videogames"].list_tools()
        movies_tools = await self.clients["movies"].list_tools()
        remote_tools = await self.clients["remote"].list_tools()

        # Construir contexto para el LLM
        llm_context = f"""
        Este es el contexto para esta conversación
        Eres un asistente conectado a varios servidores MCP. 
        Tienes acceso a las siguientes herramientas, agrupadas por servidor:

        - Sleep Coach (sleep_coach):
        {sleep_tools}

        - Beauty Recomendation (beauty):
        {beauty_tools}

        - Videogame Search (videogames):
        {videogames_tools}

        - Movies Search (movies):
        {movies_tools}

        - Sleep Quotes (remote)
        {remote_tools}

        - Git (git):
        {git_tools}

        - Filesystem (files):
        {files_tools}

        Instrucciones importantes:
        1. Analiza siempre el mensaje del usuario.
        2. Si el mensaje requiere usar una herramienta de un servidor MCP, responde ÚNICAMENTE en JSON con este formato:
        {{
        "action": "call_tool",
        "server": "<nombre_servidor>",   // uno de: "sleep_coach", "beauty", "videogames", "git", "files"
        "tool": "<nombre_tool>",         // el nombre de la herramienta exacta
        "arguments": {{ ... }}           // diccionario de argumentos
        }}
        3. Si el mensaje no requiere usar ninguna herramienta, responde con texto normal, de manera natural.
        4. No combines respuesta en texto con el JSON. Es uno u otro.
        5. Si no estás seguro de qué herramienta usar, responde en texto normal y pide más aclaración.

        Ejemplo 1 (el usuario pide un consejo para dormir mejor):
        {{
        "action": "call_tool",
        "server": "sleep_coach",
        "tool": "get_quote",
        "arguments": {{"category": "motivación"}}
        }}

        Ejemplo 2 (el usuario pide ver el contenido de un archivo README.md):
        {{
        "action": "call_tool",
        "server": "files",
        "tool": "fs/readFile",
        "arguments": {{"path": "README.md"}}
        }}

        Ejemplo 3 (el usuario pregunta algo general sin usar tools):
        "Claro, ¿quieres que te dé un resumen de los pasos a seguir?"
        """
        try:
            # Enviar el contexto al LLM y registrar en la sesión
            self.claude.send_message(llm_context)
            self.session.add_message("user", llm_context)
        except Exception as e:
            print(f"❌ Error enviando contexto: {e}")

        return


    def show_welcome_message(self):
        """Muestra mensaje de bienvenida y comandos disponibles"""
        print("\n" + "="*60)
        print("CHATBOT MCP CON ANTHROPIC CLAUDE - ¡Bienvenido!")
        print("Usando Claude API (inteligencia avanzada en la nube)")
        print("="*60)
        print("💬 Puedes hacer preguntas normales o usar comandos especiales:")
        print()
        print("COMANDOS ESPECIALES:")
        print("  /help         - Mostrar esta ayuda")
        print("  /log          - Mostrar log de interacciones")
        print("  /mcp          - Mostrar interacciones MCP")
        print("  /stats        - Mostrar estadísticas de la sesión")
        print("  /context      - Mostrar resumen del contexto actual")
        print("  /clear        - Limpiar contexto de conversación")
        print("  /save         - Guardar sesión actual")
        print("  /quit         - Salir del chatbot")
        print()
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
        
        if command == '/help':
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
        
        return False

    async def process_user_message(self, message: str) -> str:
        """
        Procesa mensaje del usuario y genera respuesta
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Respuesta del chatbot
        """
        context = self.session.get_context()
        # Preguntar al LLM qué hacer
        llm_response = self.claude.send_message(message, context)

        # Intentar interpretar como JSON
        try:
            parsed = json.loads(llm_response)

            if parsed["server"] == "remote":
                tool = parsed["tool"]
                result = await self.clients["remote"].call_tool(tool)

            if parsed.get("action") == "call_tool":
                server_name = parsed["server"]
                tool = parsed["tool"]
                args = parsed.get("arguments", {})

                if server_name in self.clients:
                    result = await self.clients[server_name].call_tool(tool, args)
                    final_answer = f"Respuesta de {server_name}/{tool}:\n {result}"
                else:
                    final_answer = f"❌ Servidor desconocido: {server_name}"
            else:
                final_answer = llm_response

        except json.JSONDecodeError:
            # No era JSON → respuesta normal del LLM
            final_answer = llm_response

        # Guardar respuesta en historial
        self.session.add_message("assistant", final_answer)
        
        return final_answer
    
    async def _async_run(self):
        print("Inicializando servidores disponibles")
        await self.initialize_servers()
        await self.servers_with_llm()

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
            response = await self.process_user_message(user_input)
            
            # Agregar al contexto
            self.session.add_message("user", user_input)
            self.session.add_message("assistant", response)
            
            # Registrar respuesta
            estimated_tokens = self.claude.estimate_tokens(response)
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
            # Guardar sesión al salir
            self.session.save_session(f"{self.session_id}.json")
            print("Sesión guardada automáticamente")
            print("¡Hasta luego!")


if __name__ == "__main__":
    asyncio.run(MCPChatbot().run())