# src/chatbot/main.py
import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from mcp import ClientSession

from ollama_client import OllamaClient
from session_manager import SessionManager
from logger import InteractionLogger
from sleep_coach_client import SleepCoachClient

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
            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Cliente Sleep Coach
            self.sleep_coach = SleepCoachClient()
            self.sleep_coach_active = False
            
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
        print("  /fs create <file> <contenido>")
        print("  /git init | /git add | /git commit \"msg\"")
        print("  /sleep help  - Conoce el recomendador de rutinas de sueño")
        print("  /help        - Mostrar esta ayuda")
        print("  /log         - Mostrar log de interacciones")
        print("  /mcp         - Mostrar interacciones MCP")
        print("  /stats       - Mostrar estadísticas de la sesión")
        print("  /context     - Mostrar resumen del contexto actual")
        print("  /clear       - Limpiar contexto de conversación")
        print("  /save        - Guardar sesión actual")
        print("  /quit        - Salir del chatbot")
        print()
        print(f"\n🧠 Modelo actual: {self.ollama.model_name}")
        available_models = self.ollama.list_available_models()
        if len(available_models) > 1:
            print(f"📦 Modelos disponibles: {', '.join(available_models)}")
        print("🛌 Sleep Coach: Listo para recomendaciones personalizadas")
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
        
        if command.startswith("/sleep"):
            return await self.handle_sleep_command(command)

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
    
    async def handle_sleep_command(self, command: str) -> bool:
        """Maneja comandos del Sleep Coach"""
        parts = command.split(" ", 2)
        
        if len(parts) < 2:
            self.show_sleep_help()
            return True
        
        action = parts[1]
        
        # Iniciar servidor si no está activo
        if not self.sleep_coach_active:
            print("🚀 Iniciando Sleep Coach Server...")
            if await self.sleep_coach.start_server():
                self.sleep_coach_active = True
            else:
                print("❌ No se pudo iniciar Sleep Coach Server")
                return True
        
        try:
            if action == "help":
                self.show_sleep_help()
            
            elif action == "create_profile":
                # Procesar creación de perfil interactiva
                await self.create_user_profile_interactive()
            
            elif action == "analyze":
                # /sleep analyze user_id
                if len(parts) < 3:
                    print("❌ Uso: /sleep analyze <user_id>")
                    return True
                
                user_id = parts[2]
                result = await self.sleep_coach.call_tool("analyze_sleep_pattern", {"user_id": user_id})
                print(f"\n{result}")
            
            elif action == "recommendations" or action == "recs":
                # /sleep recommendations user_id
                if len(parts) < 3:
                    print("❌ Uso: /sleep recommendations <user_id>")
                    return True
                
                user_id = parts[2]
                result = await self.sleep_coach.call_tool("get_personalized_recommendations", {"user_id": user_id})
                print(f"\n{result}")
            
            elif action == "schedule":
                # /sleep schedule user_id
                if len(parts) < 3:
                    print("❌ Uso: /sleep schedule <user_id>")
                    return True
                
                user_id = parts[2]
                result = await self.sleep_coach.call_tool("create_weekly_schedule", {"user_id": user_id})
                print(f"\n{result}")
            
            elif action == "advice":
                # /sleep advice "consulta específica"
                if len(parts) < 3:
                    print("❌ Uso: /sleep advice \"<tu consulta>\"")
                    return True
                
                query = parts[2].strip('"')
                result = await self.sleep_coach.call_tool("quick_sleep_advice", {"query": query})
                print(f"\n{result}")
            
            else:
                print(f"❌ Acción desconocida: {action}")
                self.show_sleep_help()
        
        except Exception as e:
            print(f"❌ Error procesando comando sleep: {str(e)}")
        
        return True
    
    async def create_user_profile_interactive(self):
        """Crea un perfil de usuario de forma interactiva"""
        print("\n🏥 CREACIÓN DE PERFIL SLEEP COACH")
        print("=" * 40)
        
        try:
            # Recopilar datos del usuario
            user_id = input("🆔 Crea tu nombre de usuario (ej: juan_123): ").strip()
            name = input("👤 Nombre: ").strip()
            age = int(input("🎂 Edad: ").strip())
            
            # Cronotipos
            print("\n🦉 Selecciona tu cronotipo:")
            print("1. Madrugador - energía en la mañana")
            print("2. Nocturno - energía en la noche")
            print("3. Intermedio - flexible")
            
            chronotype_map = {"1": "morning_lark", "2": "night_owl", "3": "intermediate"}
            chronotype_choice = input("Selección (1-3): ").strip()
            chronotype = chronotype_map.get(chronotype_choice, "intermediate")
            
            # Horarios
            bedtime = input("🛏️ Hora actual de dormir (HH:MM, ej: 23:30): ").strip()
            wake_time = input("⏰ Hora actual de despertar (HH:MM, ej: 07:00): ").strip()
            duration = float(input("⏱️ Horas de sueño promedio (ej: 7.5): ").strip())
            
            # Objetivos
            print("\n🎯 Objetivos (selecciona números separados por comas):")
            print("1. Mejor calidad de sueño")
            print("2. Más energía en el día")
            print("3. Pérdida de peso")
            print("4. Reducción de estrés")
            print("5. Rendimiento atlético")
            print("6. Rendimiento cognitivo")
            
            goal_map = {
                "1": "better_quality",
                "2": "more_energy", 
                "3": "weight_loss",
                "4": "stress_reduction",
                "5": "athletic_performance",
                "6": "cognitive_performance"
            }
            
            goal_choices = input("Objetivos (ej: 1,2,4): ").strip().split(",")
            goals = [goal_map.get(choice.strip(), "better_quality") for choice in goal_choices if choice.strip() in goal_map]
            
            if not goals:
                goals = ["better_quality"]
            
            # Información adicional
            work_schedule = input("💼 Horario laboral (ej: 9-17, flexible, shift): ").strip()
            screen_time = int(input("📱 Tiempo de pantalla antes de dormir (minutos, ej: 60): ").strip() or "60")
            stress_level = int(input("😰 Nivel de estrés (1-10): ").strip() or "5")
            sleep_quality = int(input("💤 Calidad de sueño actual (1-10): ").strip() or "6")
            
            # Crear perfil
            profile_data = {
                "user_id": user_id,
                "name": name,
                "age": age,
                "chronotype": chronotype,
                "current_bedtime": bedtime,
                "current_wake_time": wake_time,
                "sleep_duration_hours": duration,
                "goals": goals,
                "work_schedule": work_schedule,
                "screen_time_before_bed": screen_time,
                "stress_level": stress_level,
                "sleep_quality_rating": sleep_quality
            }
            
            # Enviar al servidor
            result = await self.sleep_coach.call_tool("create_user_profile", profile_data)
            print(f"\n{result}")
            
            # Ofrecer análisis inmediato
            analyze = input("\n🔍 ¿Realizar análisis inmediato? (s/n): ").strip().lower()
            if analyze == 's':
                analysis_result = await self.sleep_coach.call_tool("analyze_sleep_pattern", {"user_id": user_id})
                print(f"\n{analysis_result}")
        
        except Exception as e:
            print(f"❌ Error creando perfil: {str(e)}")
    
    def show_sleep_help(self):
        """Muestra ayuda de comandos Sleep Coach"""
        print("\n🛌 COMANDOS SLEEP COACH")
        print("=" * 40)
        print("📋 Comandos disponibles:")
        print("  /sleep help                    - Mostrar esta ayuda")
        print("  /sleep create_profile          - Crear perfil interactivo")
        print("  /sleep analyze <user_id>       - Analizar patrón de sueño")
        print("  /sleep recommendations <id>    - Obtener recomendaciones")
        print("  /sleep schedule <user_id>      - Crear horario semanal")
        print("  /sleep advice \"<consulta>\"    - Consejo rápido")
        print("\n🔧 Ejemplos:")
        print("  /sleep create_profile")
        print("  /sleep analyze juan_123")
        print("  /sleep recommendations juan_123")
        print("  /sleep advice \"No puedo dormir\"")
        print("=" * 40)

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
            if self.sleep_coach_active:
                print("🧹 Cerrando Sleep Coach Server...")
                try:
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(self.sleep_coach.stop_server())
                except:
                    pass
            
            # Guardar sesión al salir
            self.session.save_session(f"{self.session_id}.json")
            print("💾 Sesión guardada automáticamente")
            print("👋 ¡Hasta luego!")


if __name__ == "__main__":
    asyncio.run(MCPChatbot().run())