import sys
from typing import Dict

from clients.kitchen_client import KitchenCoachClient
from clients.sleep_coach_client import SleepCoachClient
from clients.remote_client import RemoteSleepQuotesClient
from clients.movies_client import MoviesClient

class CommandHandler:

    def __init__(self):
        """Inicializa el chatbot con todos sus componentes"""
        try:
            # Cliente Sleep Coach
            self.sleep_coach = SleepCoachClient()
            self.sleep_coach_active = False

            # Clientes para servicios externos
            self.movies_client = MoviesClient()
            self.movies_active = False

            self.kitchen_client = KitchenCoachClient()
            self.kitchen_active = False

            # Cliente remoto de consejos
            self.remote_quotes = RemoteSleepQuotesClient()
            self.remote_quotes_active = False
                
        except Exception as e:
            print(f"❌ Error inicializando clientes: {str(e)}")
            sys.exit(1)

    async def handle_quotes_command(self, command: str) -> bool:
        """Maneja comandos del servidor remoto de citas inspiracionales"""
        parts = command.split(" ", 2)

        if len(parts) < 2 or parts[1] == "help":
            self.show_quotes_help()
            return True

        action = parts[1]

        # Iniciar conexión si no está activa
        if not self.remote_quotes_active:
            client = RemoteSleepQuotesClient()
            response = await client.health_check()

            if response["status"] == "healthy":
                self.remote_quotes_active = True
            else:
                print("❌ No se pudo conectar al servidor de citas")
                return True

        try:
            if action == "get":
                result = await self.remote_quotes.get_inspirational_quote()
                print(self.remote_quotes._format_quote_output(result, "CITA INSPIRACIONAL"))

            elif action == "tip":
                result = await self.remote_quotes.get_sleep_hygiene_tip()
                print(self.remote_quotes._format_quote_output(result, "CONSEJO DE HIGIENE DEL SUEÑO"))

            elif action == "search":
                if len(parts) < 3:
                    print("❌ Uso: /quotes search <palabra>")
                    return True
                query = parts[2]
                result = await self.remote_quotes.search_quotes(query)
                print(self.remote_quotes._format_search_results(result))

            elif action == "wisdom":
                result = await self.remote_quotes.get_wisdom(False)
                print(self.remote_quotes._format_wisdom_output(result))

            else:
                print(f"❌ Acción desconocida: {action}")
                self.show_quotes_help()

        except Exception as e:
            print(f"❌ Error procesando comando quotes: {str(e)}")

        return True

    def show_quotes_help(self):
        print("\n📖 COMANDOS QUOTES (servidor remoto)")
        print("=" * 40)
        print("  /quotes help             - Mostrar esta ayuda")
        print("  /quotes get              - Obtener cita inspiracional")
        print("  /quotes tip              - Obtener consejo de higiene")
        print("  /quotes search <query>   - Buscar citas")
        print("  /quotes wisdom           - Obtener sabiduría diaria")
        print("=" * 40)

    async def handle_sleep_command(self, command: str) -> bool:
        """Maneja comandos del Sleep Coach"""
        parts = command.split(" ", 2)
        
        if len(parts) < 2:
            self.show_sleep_help()
            return True
        
        action = parts[1]
        
        # Iniciar servidor si no está activo
        if not self.sleep_coach_active:
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
        print("=" * 40)

    async def handle_movies_command(self, command: str) -> bool:
        """Maneja comandos del Movies MCP Server"""
        parts = command.split(" ", 3)
        
        if len(parts) < 2:
            self.show_movies_help()
            return True
        
        action = parts[1]
        
        # Iniciar servidor si no está activo
        if not self.movies_active:
            if await self.movies_client.start_server():
                self.movies_active = True
            else:
                return True
        
        try:
            if action == "help":
                self.show_movies_help()

            elif action == "test":
                # Test de conexión con ping
                result = await self.movies_client.test_ping()
                print(f"\n🏓 Test de conexión: {result}")
                return True
            
            elif action == "tools":
                # Esta funcionalidad no está disponible en el cliente alternativo
                print("\n🔧 HERRAMIENTAS DISPONIBLES:")
                print("  - ping_tool: Test de conexión")
                print("  - search_movie: Buscar películas por título")
                print("  - movie_details: Detalles de película específica")
                print("  - recommend_movies_tool: Recomendaciones por filtros")
                print("  - top_movies_by_actor_tool: Top películas por actor")
                print("  - similar_movies_tool: Películas similares")
                print("  - build_playlist_tool: Crear playlist de películas")
            
            elif action == "search":
                # /movies search <query>
                if len(parts) < 3:
                    print("❌ Uso: /movies search <término de búsqueda>")
                    return True
                
                query = " ".join(parts[2:])
                print(f"🔍 Buscando películas con: '{query}'...")
                result = await self.movies_client.search_movies(query, 5)  # Limitar a 5 resultados
                print(f"\n🎬 RESULTADOS DE BÚSQUEDA PARA: '{query}'")
                print("-" * 50)
                print(result)
            
            elif action == "details":
                # /movies details <title>
                if len(parts) < 3:
                    print("❌ Uso: /movies details <título de película>")
                    return True
                
                title = " ".join(parts[2:])
                print(f"📋 Obteniendo detalles de: '{title}'...")
                result = await self.movies_client.get_movie_details(title)
                print(f"\n🎬 DETALLES DE PELÍCULA: '{title}'")
                print("-" * 50)
                print(result)
            
            elif action == "popular":
                # /movies popular [limit]
                limit = 10
                if len(parts) > 2 and parts[2].isdigit():
                    limit = int(parts[2])
                
                print(f"⭐ Obteniendo películas populares (top {limit})...")
                result = await self.movies_client.get_popular_movies(limit)
                print(f"\n🎬 PELÍCULAS POPULARES (Top {limit}):")
                print("-" * 50)
                print(result)
            
            elif action == "genre":
                # /movies genre <genre_name>
                if len(parts) < 3:
                    print("❌ Uso: /movies genre <nombre_del_género>")
                    print("📋 Géneros sugeridos: Action, Drama, Comedy, Thriller, Sci-Fi, Romance, Horror")
                    return True
                
                genre = parts[2]
                print(f"🎭 Buscando películas del género: '{genre}'...")
                result = await self.movies_client.search_by_genre(genre, 10)
                print(f"\n🎬 PELÍCULAS DEL GÉNERO: {genre.upper()}")
                print("-" * 50)
                print(result)
            
            elif action == "actor":
                # /movies actor <actor_name>
                if len(parts) < 3:
                    print("❌ Uso: /movies actor <nombre del actor>")
                    return True
                
                actor = " ".join(parts[2:])
                print(f"🎭 Buscando películas de: '{actor}'...")
                result = await self.movies_client.get_actor_filmography(actor, 10)
                print(f"\n🎬 PELÍCULAS DE: {actor.upper()}")
                print("-" * 50)
                print(result)
            
            elif action == "similar":
                # /movies similar <title>
                if len(parts) < 3:
                    print("❌ Uso: /movies similar <título de película>")
                    return True
                
                title = " ".join(parts[2:])
                print(f"🔄 Buscando películas similares a: '{title}'...")
                result = await self.movies_client.find_similar_movies(title, 8)
                print(f"\n🎬 PELÍCULAS SIMILARES A: '{title}'")
                print("-" * 50)
                print(result)
            
            elif action == "playlist":
                # /movies playlist [minutes]
                target_minutes = 480  # Default 8 horas
                if len(parts) > 2 and parts[2].isdigit():
                    target_minutes = int(parts[2])
                
                print(f"📋 Creando playlist de {target_minutes} minutos...")
                result = await self.movies_client.create_playlist(target_minutes)
                print(f"\n🎬 PLAYLIST GENERADA ({target_minutes} minutos):")
                print("-" * 50)
                print(result)
            
            elif action == "recommend":
                # /movies recommend - con preferencias interactivas
                print("🎬 Generando recomendaciones personalizadas...")
                preferences = await self.collect_movie_preferences()
                
                print("🔍 Procesando preferencias...")
                result = await self.movies_client.get_recommendations(preferences)
                print(f"\n✨ RECOMENDACIONES PERSONALIZADAS:")
                print("-" * 50)
                print(result)
            
            else:
                print(f"❌ Acción desconocida: {action}")
                self.show_movies_help()
        
        except Exception as e:
            print(f"❌ Error procesando comando movies: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return True

    def show_movies_help(self):
        """Muestra ayuda de comandos Movies MCP"""
        print("\n🎬 COMANDOS MOVIES MCP SERVER")
        print("=" * 50)
        print("📋 Comandos disponibles:")
        print("  /movies help                    - Mostrar esta ayuda")
        print("  /movies test                    - Test de conexión")
        print("  /movies tools                   - Ver herramientas disponibles")
        print("  /movies search <query>          - Buscar películas")
        print("  /movies details <título>        - Detalles de película")
        print("  /movies popular [limit]         - Películas populares")
        print("  /movies genre <género>          - Buscar por género")
        print("  /movies actor <actor>           - Películas de un actor")
        print("  /movies similar <título>        - Películas similares")
        print("  /movies playlist [minutos]      - Crear playlist")
        print("  /movies recommend               - Recomendaciones personalizadas")
        print("\n💡 Ejemplos:")
        print("  /movies search batman")
        print("  /movies details The Dark Knight")
        print("  /movies genre Action")
        print("  /movies actor Tom Hanks")
        print("  /movies similar Inception")
        print("=" * 50)

    async def collect_movie_preferences(self) -> Dict:
        """Recopila preferencias para movies"""
        print("\n🎬 PREFERENCIAS DE PELÍCULAS")
        print("-" * 30)
        
        genres = input("🎭 Géneros favoritos (separados por coma): ").strip()
        actors = input("⭐ Actores favoritos: ").strip()
        year_range = input("📅 Rango de años (ej: 2010-2023): ").strip()
        rating = input("⭐ Rating mínimo (1-10): ").strip()
        
        return {
            "genres": [g.strip() for g in genres.split(",") if g.strip()],
            "actors": [a.strip() for a in actors.split(",") if a.strip()],
            "year_range": year_range or "2010-2023",
            "min_rating": float(rating) if rating.isdigit() else 7.0
        }
    
    async def handle_kitchen_command(self, command: str) -> bool:
        """Maneja comandos relacionados con Kitchen Coach"""
        parts = command.split(" ", 2)
        
        if len(parts) < 2:
            self._show_kitchen_help()
            return True
        
        action = parts[1].lower()
    
        if not self.kitchen_active:
            print("🍳 Iniciando Kitchen Coach...")
            self.kitchen_coach_client = KitchenCoachClient()
            if await self.kitchen_coach_client.start_server():
                self.kitchen_active = True
                print("✅ Kitchen Coach listo para recomendaciones culinarias")
            else:
                print("❌ No se pudo iniciar Kitchen Coach")
        
        if action == "help":
            self._show_kitchen_help()
            return True

        elif action == "stop":
            if self.kitchen_active and self.kitchen_coach_client:
                await self.kitchen_coach_client.stop_server()
                self.kitchen_active = False
                self.kitchen_coach_client = None
                print("🛑 Kitchen Coach detenido")
            else:
                print("ℹ️ Kitchen Coach no está activo")
            return True
        
        elif action == "tools":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            tools = await self.kitchen_coach_client.list_tools()
            print(f"\n🔧 HERRAMIENTAS KITCHEN COACH ({len(tools)} disponibles):")
            for tool in tools:
                print(f"  • {tool['name']}: {tool['description']}")
            return True
        
        elif action == "mood":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            if len(parts) < 3:
                print("❌ Uso: /kitchen mood <estado_animo> [temporada]")
                print("Estados de ánimo: happy, excited, tender, scared, angry, sad")
                print("Temporadas: spring, summer, autumn, winter")
                return True
            
            mood_parts = parts[2].split()
            mood = mood_parts[0]
            season = mood_parts[1] if len(mood_parts) > 1 else None
            
            result = await self.kitchen_coach_client.recommend_by_mood_and_season(mood, season)
            print(f"🍽️ RECOMENDACIÓN POR ESTADO DE ÁNIMO:\n{result}")
            return True
        
        elif action == "diet":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            if len(parts) < 3:
                print("❌ Uso: /kitchen diet <tipo_dieta> [max_calorias]")
                print("Tipos de dieta: vegan, keto, mediterranean, paleo, dash")
                return True
            
            diet_parts = parts[2].split()
            diet = diet_parts[0]
            max_calories = int(diet_parts[1]) if len(diet_parts) > 1 and diet_parts[1].isdigit() else None
            
            result = await self.kitchen_coach_client.suggest_recipe_by_diet(diet, max_calories)
            print(f"🥗 RECETAS PARA DIETA {diet.upper()}:\n{result}")
            return True
        
        elif action == "substitute":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            if len(parts) < 3:
                print("❌ Uso: /kitchen substitute <ingrediente>")
                return True
            
            ingredient = parts[2]
            result = await self.kitchen_coach_client.suggest_ingredient_substitution(ingredient)
            print(f"🔄 SUSTITUTOS PARA '{ingredient}':\n{result}")
            return True
        
        elif action == "utensils":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            if len(parts) < 3:
                print("❌ Uso: /kitchen utensils <nombre_receta>")
                return True
            
            recipe_name = parts[2]
            result = await self.kitchen_coach_client.suggest_utensils_for_recipe(recipe_name)
            print(f"🔪 UTENSILIOS PARA '{recipe_name}':\n{result}")
            return True
        
        elif action == "ingredients":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            if len(parts) < 3:
                print("❌ Uso: /kitchen ingredients <ingrediente1,ingrediente2,...>")
                return True
            
            ingredients_str = parts[2]
            ingredients = [ing.strip() for ing in ingredients_str.split(",")]
            
            result = await self.kitchen_coach_client.get_recipes_by_ingredients(ingredients)
            print(f"🍲 RECETAS CON {', '.join(ingredients)}:\n{result}")
            return True
        
        elif action == "search":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            # Ejemplo de búsqueda nutricional
            result = await self.kitchen_coach_client.search_foods(min_protein=10, max_calories=200)
            print(f"🔍 BÚSQUEDA DE ALIMENTOS (min 10g proteína, max 200 cal):\n{result}")
            return True
        
        elif action == "food":
            if not self.kitchen_active:
                print("❌ Kitchen Coach no está activo. Usa '/kitchen start' primero")
                return True
            
            if len(parts) < 3:
                print("❌ Uso: /kitchen food <nombre_alimento>")
                return True
            
            food_name = parts[2]
            result = await self.kitchen_coach_client.get_food_by_name(food_name)
            print(f"🍎 INFORMACIÓN DE '{food_name}':\n{result}")
            return True
        
        else:
            print(f"❌ Acción desconocida: {action}")
            self._show_kitchen_help()
            return True

    def _show_kitchen_help(self):
        """Muestra ayuda para comandos Kitchen Coach"""
        print("""
🍳 KITCHEN COACH - Recomendador culinario inteligente
====================================================

COMANDOS DISPONIBLES:
  /kitchen stop                     - Detener Kitchen Coach Server
  /kitchen tools                    - Listar herramientas disponibles
  /kitchen mood <estado> [temporada]- Recomendar por estado de ánimo
  /kitchen diet <dieta> [max_cal]   - Recetas por tipo de dieta
  /kitchen substitute <ingrediente> - Sustitutos para ingrediente
  /kitchen utensils <receta>        - Utensilios necesarios
  /kitchen ingredients <ing1,ing2>  - Recetas con ingredientes específicos
  /kitchen search                   - Buscar alimentos (ejemplo nutricional)
  /kitchen food <nombre>            - Información nutricional de alimento
  /kitchen help                     - Mostrar esta ayuda

ESTADOS DE ÁNIMO: happy, excited, tender, scared, angry, sad
TEMPORADAS: spring, summer, autumn, winter
DIETAS: vegan, keto, mediterranean, paleo, dash

EJEMPLOS:
  /kitchen mood happy summer
  /kitchen diet vegan 500
  /kitchen substitute "milk"
  /kitchen ingredients "chicken,rice,vegetables"

        """)