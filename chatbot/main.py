# src/chatbot/main.py
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from ollama_client import OllamaClient
from session_manager import SessionManager
from logger import InteractionLogger

class MCPChatbot:
    def __init__(self):
        """Inicializa el chatbot con todos sus componentes"""
        load_dotenv()
        
        try:
            self.ollama = OllamaClient()
            self.session = SessionManager()
            self.logger = InteractionLogger()
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
        print("🤖 CHATBOT MCP LOCAL - ¡Bienvenido!")
        print("🏠 Usando modelo local con Ollama (100% privado)")
        print("="*60)
        print("💬 Puedes hacer preguntas normales o usar comandos especiales:")
        print()
        print("📋 COMANDOS ESPECIALES:")
        print("  /help     - Mostrar esta ayuda")
        print("  /log      - Mostrar log de interacciones")
        print("  /mcp      - Mostrar interacciones MCP")
        print("  /stats    - Mostrar estadísticas de la sesión")
        print("  /context  - Mostrar resumen del contexto actual")
        print("  /clear    - Limpiar contexto de conversación")
        print("  /save     - Guardar sesión actual")
        print("  /quit     - Salir del chatbot")
        print()
        print("🔧 FUNCIONALIDADES MCP (próximamente):")
        print("  - Filesystem operations (crear/leer archivos)")
        print("  - Git operations (init, add, commit)")
        print("  - Servidor personalizado")
        print(f"\n🧠 Modelo actual: {self.ollama.model_name}")
        available_models = self.ollama.list_available_models()
        if len(available_models) > 1:
            print(f"📦 Modelos disponibles: {', '.join(available_models)}")
        print("="*60)
    
    def process_special_command(self, command: str) -> bool:
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
            print(f"  💬 Total mensajes: {stats['total_messages']}")
            print(f"  👤 Mensajes usuario: {stats['user_messages']}")
            print(f"  🤖 Mensajes chatbot: {stats['assistant_messages']}")
            print(f"  ⏱️  Duración: {stats['session_duration']}")
            print(f"  🧠 Mensajes en contexto: {stats['messages_in_context']}")
            print(f"\n🔧 ESTADÍSTICAS MCP:")
            print(f"  📡 Interacciones totales: {mcp_stats['total_interactions']}")
            print(f"  ✅ Tasa de éxito: {mcp_stats['success_rate']:.1f}%")
            print(f"  🖥️  Servidores usados: {', '.join(mcp_stats['servers_used']) if mcp_stats['servers_used'] else 'Ninguno'}")
            
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
    
    def process_user_message(self, message: str) -> str:
        """
        Procesa mensaje del usuario y genera respuesta
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Respuesta del chatbot
        """
        # Por ahora, solo usar Ollama
        # TODO: Detectar si necesita MCP y enrutar apropiadamente
        
        context = self.session.get_context()
        response = self.ollama.send_message(message, context)
        
        return response
    
    
    def run(self):
        """Ejecuta el loop principal del chatbot"""
        self.show_welcome_message()
        
        try:
            while True:
                # Obtener entrada del usuario
                user_input = input(f"\n👤 Tú: ").strip()
                
                # Verificar si es comando especial
                if user_input.startswith('/'):
                    if self.process_special_command(user_input):
                        if user_input.lower() == '/quit':
                            break
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
                
        except KeyboardInterrupt:
            print("\n\n🛑 Chatbot interrumpido por el usuario")
        except Exception as e:
            print(f"\n❌ Error inesperado: {str(e)}")
            self.logger.logger.error(f"Error en loop principal: {str(e)}")
        finally:
            # Guardar sesión al salir
            self.session.save_session(f"/sessions{self.session_id}.json")
            print("💾 Sesión guardada automáticamente")
            print("👋 ¡Hasta luego!")


def main():
    """Función principal"""
    chatbot = MCPChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()