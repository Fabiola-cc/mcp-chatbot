# mcp_servers/sleep_coach.py
"""
Servidor MCP Sleep Coach - Recomendador de rutinas de sueño personalizado

Funcionalidades:
- Análisis personalizado de patrones de sueño
- Recomendaciones basadas en cronotipos
- Rutinas de higiene del sueño
- Planificación de horarios optimizados
- Seguimiento de hábitos
"""

import asyncio
import json
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import mcp.types as types
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

# Modelos de datos
class Chronotype(Enum):
    MORNING_LARK = "morning_lark"  # Alondra matutina
    NIGHT_OWL = "night_owl"       # Búho nocturno
    INTERMEDIATE = "intermediate"  # Intermedio

class SleepGoal(Enum):
    BETTER_QUALITY = "better_quality"
    MORE_ENERGY = "more_energy"
    WEIGHT_LOSS = "weight_loss"
    STRESS_REDUCTION = "stress_reduction"
    ATHLETIC_PERFORMANCE = "athletic_performance"
    COGNITIVE_PERFORMANCE = "cognitive_performance"

@dataclass
class UserProfile:
    name: str
    age: int
    chronotype: Chronotype
    current_bedtime: str  # "22:30"
    current_wake_time: str  # "07:00"
    sleep_duration_hours: float
    goals: List[SleepGoal]
    work_schedule: str  # "9-17" o "shift" o "flexible"
    exercise_time: Optional[str] = None
    caffeine_cutoff: Optional[str] = None
    screen_time_before_bed: int = 60  # minutos
    stress_level: int = 5  # 1-10
    sleep_quality_rating: int = 6  # 1-10

@dataclass
class SleepRecommendation:
    category: str
    recommendation: str
    priority: int  # 1 = alta, 2 = media, 3 = baja
    timeframe: str
    expected_benefit: str

class SleepCoachEngine:
    """Motor principal de recomendaciones de sueño"""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserProfile] = {}
        self.sleep_data = self._load_sleep_knowledge()
    
    def _load_sleep_knowledge(self) -> Dict:
        """Base de conocimientos sobre sueño"""
        return {
            "optimal_sleep_duration": {
                "18-25": (7, 9),
                "26-64": (7, 9),
                "65+": (7, 8)
            },
            "chronotype_patterns": {
                Chronotype.MORNING_LARK: {
                    "optimal_bedtime": "21:30-22:30",
                    "optimal_wake": "06:00-07:00",
                    "energy_peak": "10:00-12:00",
                    "afternoon_dip": "13:00-15:00"
                },
                Chronotype.NIGHT_OWL: {
                    "optimal_bedtime": "23:30-00:30",
                    "optimal_wake": "07:30-08:30",
                    "energy_peak": "18:00-22:00",
                    "afternoon_dip": "14:00-16:00"
                },
                Chronotype.INTERMEDIATE: {
                    "optimal_bedtime": "22:30-23:30",
                    "optimal_wake": "06:30-07:30",
                    "energy_peak": "10:00-14:00",
                    "afternoon_dip": "13:00-15:00"
                }
            },
            "sleep_hygiene_rules": [
                "Mantener horarios consistentes todos los días",
                "Evitar cafeína 6-8 horas antes de dormir",
                "No usar pantallas 1-2 horas antes de dormir",
                "Mantener el dormitorio fresco (18-20°C)",
                "Ejercitarse regularmente, pero no 3 horas antes de dormir",
                "Evitar comidas pesadas 3 horas antes de dormir",
                "Crear un ritual de relajación pre-sueño",
                "Usar la cama solo para dormir y actividad íntima"
            ]
        }
    
    def analyze_sleep_pattern(self, user_id: str) -> Dict[str, Any]:
        """Analiza el patrón de sueño del usuario"""
        if user_id not in self.user_profiles:
            return {"error": "Usuario no encontrado"}
        
        profile = self.user_profiles[user_id]
        analysis = {}
        
        # Análisis de duración
        optimal_min, optimal_max = self._get_optimal_duration(profile.age)
        if profile.sleep_duration_hours < optimal_min:
            analysis["duration"] = "insufficient"
            analysis["duration_gap"] = optimal_min - profile.sleep_duration_hours
        elif profile.sleep_duration_hours > optimal_max:
            analysis["duration"] = "excessive"
            analysis["duration_gap"] = profile.sleep_duration_hours - optimal_max
        else:
            analysis["duration"] = "optimal"
            analysis["duration_gap"] = 0
        
        # Análisis de cronotipos
        chronotype_data = self.sleep_data["chronotype_patterns"][profile.chronotype]
        analysis["chronotype_alignment"] = self._check_chronotype_alignment(profile, chronotype_data)
        
        # Análisis de calidad
        analysis["quality_issues"] = []
        if profile.screen_time_before_bed > 60:
            analysis["quality_issues"].append("Exceso de tiempo de pantalla antes de dormir")
        if profile.stress_level > 7:
            analysis["quality_issues"].append("Nivel de estrés alto")
        if profile.sleep_quality_rating < 6:
            analysis["quality_issues"].append("Calidad de sueño autoreportada baja")
        
        return analysis
    
    def generate_personalized_recommendations(self, user_id: str) -> List[SleepRecommendation]:
        """Genera recomendaciones personalizadas"""
        if user_id not in self.user_profiles:
            return []
        
        profile = self.user_profiles[user_id]
        analysis = self.analyze_sleep_pattern(user_id)
        recommendations = []
        
        # Recomendaciones de horario
        recommendations.extend(self._get_schedule_recommendations(profile, analysis))
        
        # Recomendaciones de higiene del sueño
        recommendations.extend(self._get_hygiene_recommendations(profile))
        
        # Recomendaciones específicas por objetivos
        recommendations.extend(self._get_goal_specific_recommendations(profile))
        
        # Recomendaciones por problemas detectados
        recommendations.extend(self._get_problem_specific_recommendations(profile, analysis))
        
        # Ordenar por prioridad
        recommendations.sort(key=lambda x: x.priority)
        
        return recommendations
    
    def create_weekly_schedule(self, user_id: str) -> Dict[str, Any]:
        """Crea un horario semanal optimizado"""
        if user_id not in self.user_profiles:
            return {"error": "Usuario no encontrado"}
        
        profile = self.user_profiles[user_id]
        chronotype_data = self.sleep_data["chronotype_patterns"][profile.chronotype]
        
        # Horario base optimizado
        optimal_bedtime = self._parse_time_range(chronotype_data["optimal_bedtime"])[0]
        optimal_wake = self._parse_time_range(chronotype_data["optimal_wake"])[0]
        
        schedule = {
            "bedtime_routine": self._create_bedtime_routine(profile),
            "weekly_schedule": {},
            "wake_routine": self._create_wake_routine(profile),
            "tips": []
        }
        
        # Crear horario para cada día
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        for day in days:
            is_weekend = day in ["sábado", "domingo"]
            
            # Permitir 30-60 min más tarde en fines de semana
            bedtime_adj = 30 if is_weekend else 0
            wake_adj = 60 if is_weekend else 0
            
            bedtime = self._add_minutes_to_time(optimal_bedtime.strftime("%H:%M"), bedtime_adj)
            wake_time = self._add_minutes_to_time(optimal_wake.strftime("%H:%M"), wake_adj)
            
            schedule["weekly_schedule"][day] = {
                "bedtime": bedtime,
                "wake_time": wake_time,
                "sleep_duration": self._calculate_duration(bedtime, wake_time)
            }
        
        return schedule
    
    def _get_schedule_recommendations(self, profile: UserProfile, analysis: Dict) -> List[SleepRecommendation]:
        """Recomendaciones específicas de horarios"""
        recommendations = []
        
        if analysis.get("duration") == "insufficient":
            gap = analysis.get("duration_gap", 0)
            rec = SleepRecommendation(
                category="Horario",
                recommendation=f"Aumenta tu tiempo de sueño en {gap:.1f} horas. Considera acostarte {int(gap*60)} minutos más temprano.",
                priority=1,
                timeframe="1-2 semanas",
                expected_benefit="Mejor recuperación, más energía y mejor concentración"
            )
            recommendations.append(rec)
        
        if not analysis.get("chronotype_alignment", {}).get("aligned", True):
            chronotype_name = "madrugador" if profile.chronotype == Chronotype.MORNING_LARK else "nocturno" if profile.chronotype == Chronotype.NIGHT_OWL else "intermedio"
            rec = SleepRecommendation(
                category="Cronotipos",
                recommendation=f"Tu horario actual no está alineado con tu cronotipo {chronotype_name}. Ajusta gradualmente tus horarios de sueño.",
                priority=1,
                timeframe="2-4 semanas",
                expected_benefit="Mejor calidad de sueño y mayor energía durante el día"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _get_hygiene_recommendations(self, profile: UserProfile) -> List[SleepRecommendation]:
        """Recomendaciones de higiene del sueño"""
        recommendations = []
        
        if profile.screen_time_before_bed > 60:
            rec = SleepRecommendation(
                category="Higiene del sueño",
                recommendation=f"Reduce el tiempo de pantalla antes de dormir de {profile.screen_time_before_bed} a máximo 30 minutos, idealmente cero.",
                priority=2,
                timeframe="1 semana",
                expected_benefit="Mejor producción de melatonina y conciliación más rápida"
            )
            recommendations.append(rec)
        
        if not profile.caffeine_cutoff:
            rec = SleepRecommendation(
                category="Higiene del sueño",
                recommendation="Establece un horario límite para el consumo de cafeína, idealmente 6-8 horas antes de dormir.",
                priority=2,
                timeframe="3-5 días",
                expected_benefit="Mejor conciliación del sueño y sueño más profundo"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _get_goal_specific_recommendations(self, profile: UserProfile) -> List[SleepRecommendation]:
        """Recomendaciones específicas por objetivos"""
        recommendations = []
        
        for goal in profile.goals:
            if goal == SleepGoal.BETTER_QUALITY:
                rec = SleepRecommendation(
                    category="Calidad del sueño",
                    recommendation="Implementa una rutina de relajación 1 hora antes de dormir: lectura, meditación o estiramientos suaves.",
                    priority=2,
                    timeframe="2-3 semanas",
                    expected_benefit="Sueño más profundo y reparador"
                )
                recommendations.append(rec)
            
            elif goal == SleepGoal.MORE_ENERGY:
                rec = SleepRecommendation(
                    category="Energía",
                    recommendation="Exponte a luz natural en los primeros 30 minutos después de despertar para regular tu ritmo circadiano.",
                    priority=1,
                    timeframe="1-2 semanas",
                    expected_benefit="Mayor alerta matutina y mejor energía durante el día"
                )
                recommendations.append(rec)
            
            elif goal == SleepGoal.STRESS_REDUCTION:
                rec = SleepRecommendation(
                    category="Manejo del estrés",
                    recommendation="Practica técnicas de respiración profunda o meditación mindfulness antes de dormir.",
                    priority=2,
                    timeframe="2-4 semanas",
                    expected_benefit="Reducción del cortisol nocturno y mejor relajación"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _get_problem_specific_recommendations(self, profile: UserProfile, analysis: Dict) -> List[SleepRecommendation]:
        """Recomendaciones para problemas específicos detectados"""
        recommendations = []
        
        if profile.stress_level > 7:
            rec = SleepRecommendation(
                category="Manejo del estrés",
                recommendation="Dado tu alto nivel de estrés, considera técnicas de relajación progresiva muscular antes de dormir.",
                priority=1,
                timeframe="1-3 semanas",
                expected_benefit="Reducción de la tensión corporal y mejor conciliación"
            )
            recommendations.append(rec)
        
        if profile.sleep_quality_rating < 5:
            rec = SleepRecommendation(
                category="Calidad del sueño",
                recommendation="Evalúa tu ambiente de sueño: temperatura (18-20°C), oscuridad completa y silencio o ruido blanco.",
                priority=1,
                timeframe="Inmediato",
                expected_benefit="Mejor mantenimiento del sueño y menos despertares"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _create_bedtime_routine(self, profile: UserProfile) -> List[Dict]:
        """Crea una rutina personalizada para antes de dormir"""
        routine = []
        
        # Rutina base adaptada al cronotipos
        if profile.chronotype == Chronotype.NIGHT_OWL:
            routine.extend([
                {"time": "-90 min", "activity": "Última comida ligera permitida"},
                {"time": "-60 min", "activity": "Apagar dispositivos electrónicos"},
                {"time": "-45 min", "activity": "Ducha tibia o baño relajante"},
                {"time": "-30 min", "activity": "Lectura o música suave"},
                {"time": "-15 min", "activity": "Técnicas de respiración o meditación"},
                {"time": "0 min", "activity": "Acostarse con luces apagadas"}
            ])
        else:
            routine.extend([
                {"time": "-75 min", "activity": "Última comida ligera permitida"},
                {"time": "-60 min", "activity": "Apagar pantallas y actividades estimulantes"},
                {"time": "-30 min", "activity": "Actividad relajante (lectura, estiramiento)"},
                {"time": "-10 min", "activity": "Preparar el ambiente (temperatura, oscuridad)"},
                {"time": "0 min", "activity": "Acostarse"}
            ])
        
        return routine
    
    def _create_wake_routine(self, profile: UserProfile) -> List[Dict]:
        """Crea una rutina matutina optimizada"""
        routine = [
            {"time": "0 min", "activity": "Despertar (evitar snooze)"},
            {"time": "+5 min", "activity": "Hidratarse con un vaso de agua"},
            {"time": "+10 min", "activity": "Exposición a luz natural (ventana o exterior)"},
            {"time": "+15 min", "activity": "Movimiento suave (estiramientos)"}
        ]
        
        if profile.chronotype == Chronotype.MORNING_LARK:
            routine.append({"time": "+30 min", "activity": "Ejercicio moderado (opcional)"})
        
        return routine
    
    # Métodos auxiliares
    def _get_optimal_duration(self, age: int) -> tuple:
        """Obtiene duración óptima de sueño por edad"""
        if age <= 25:
            return self.sleep_data["optimal_sleep_duration"]["18-25"]
        elif age <= 64:
            return self.sleep_data["optimal_sleep_duration"]["26-64"]
        else:
            return self.sleep_data["optimal_sleep_duration"]["65+"]
    
    def _check_chronotype_alignment(self, profile: UserProfile, chronotype_data: Dict) -> Dict:
        """Verifica alineación con cronotipos"""
        current_bed = datetime.strptime(profile.current_bedtime, "%H:%M").time()
        current_wake = datetime.strptime(profile.current_wake_time, "%H:%M").time()
        
        optimal_bed_range = self._parse_time_range(chronotype_data["optimal_bedtime"])
        optimal_wake_range = self._parse_time_range(chronotype_data["optimal_wake"])
        
        bed_aligned = optimal_bed_range[0] <= current_bed <= optimal_bed_range[1]
        wake_aligned = optimal_wake_range[0] <= current_wake <= optimal_wake_range[1]
        
        return {
            "aligned": bed_aligned and wake_aligned,
            "bedtime_aligned": bed_aligned,
            "wake_aligned": wake_aligned
        }
    
    def _parse_time_range(self, time_range: str) -> tuple:
        """Parsea rango de tiempo como '21:30-22:30'"""
        start, end = time_range.split("-")
        return (
            datetime.strptime(start, "%H:%M").time(),
            datetime.strptime(end, "%H:%M").time()
        )
    
    def _add_minutes_to_time(self, time_str: str, minutes: int) -> str:
        """Agrega minutos a un tiempo"""
        dt = datetime.strptime(time_str, "%H:%M")
        dt += timedelta(minutes=minutes)
        return dt.strftime("%H:%M")
    
    def _calculate_duration(self, bedtime: str, wake_time: str) -> str:
        """Calcula duración entre dos tiempos"""
        bed_dt = datetime.strptime(bedtime, "%H:%M")
        wake_dt = datetime.strptime(wake_time, "%H:%M")
        
        # Si wake_time es menor, es del día siguiente
        if wake_dt < bed_dt:
            wake_dt += timedelta(days=1)
        
        duration = wake_dt - bed_dt
        hours = duration.total_seconds() / 3600
        return f"{hours:.1f} horas"

# Servidor MCP
app = Server("sleep-coach")
engine = SleepCoachEngine()

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Lista todas las herramientas disponibles"""
    return [
        types.Tool(
            name="create_user_profile",
            description="Crea un perfil personalizado de usuario con sus hábitos de sueño actuales",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID único del usuario"},
                    "name": {"type": "string", "description": "Nombre del usuario"},
                    "age": {"type": "integer", "description": "Edad del usuario"},
                    "chronotype": {"type": "string", "enum": ["morning_lark", "night_owl", "intermediate"]},
                    "current_bedtime": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
                    "current_wake_time": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
                    "sleep_duration_hours": {"type": "number", "minimum": 4, "maximum": 12},
                    "goals": {"type": "array", "items": {"type": "string"}},
                    "work_schedule": {"type": "string"},
                    "exercise_time": {"type": "string", "description": "Horario de ejercicio opcional"},
                    "screen_time_before_bed": {"type": "integer", "minimum": 0},
                    "stress_level": {"type": "integer", "minimum": 1, "maximum": 10},
                    "sleep_quality_rating": {"type": "integer", "minimum": 1, "maximum": 10}
                },
                "required": ["user_id", "name", "age", "chronotype", "current_bedtime", "current_wake_time", "sleep_duration_hours", "goals", "work_schedule"]
            }
        ),
        types.Tool(
            name="analyze_sleep_pattern",
            description="Analiza el patrón de sueño actual del usuario y detecta problemas",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="get_personalized_recommendations",
            description="Genera recomendaciones personalizadas basadas en el perfil del usuario",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="create_weekly_schedule",
            description="Crea un horario semanal optimizado con rutinas personalizadas",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="quick_sleep_advice",
            description="Proporciona consejos rápidos basados en una consulta específica",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta específica sobre sueño"},
                    "user_context": {"type": "string", "description": "Contexto adicional del usuario (opcional)"}
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Maneja las llamadas a herramientas"""
    print(f"Recibido tool call: {name}, args={arguments}")

    if name == "ping":
        return [types.TextContent(type="text", text=f"pong! recibí: {arguments['msg']}")]
    
    if name == "create_user_profile":
        try:
            # Convertir goals de strings a enums
            goals = [SleepGoal(goal) for goal in arguments["goals"]]
            chronotype = Chronotype(arguments["chronotype"])
            
            profile = UserProfile(
                name=arguments["name"],
                age=arguments["age"],
                chronotype=chronotype,
                current_bedtime=arguments["current_bedtime"],
                current_wake_time=arguments["current_wake_time"],
                sleep_duration_hours=arguments["sleep_duration_hours"],
                goals=goals,
                work_schedule=arguments["work_schedule"],
                exercise_time=arguments.get("exercise_time"),
                screen_time_before_bed=arguments.get("screen_time_before_bed", 60),
                stress_level=arguments.get("stress_level", 5),
                sleep_quality_rating=arguments.get("sleep_quality_rating", 6)
            )
            
            engine.user_profiles[arguments["user_id"]] = profile
            
            return [types.TextContent(
                type="text",
                text=f"Perfil creado para {arguments['name']} ({arguments['user_id']})"
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error creando perfil: {str(e)}"
            )]
    
    elif name == "analyze_sleep_pattern":
        try:
            analysis = engine.analyze_sleep_pattern(arguments["user_id"])
            
            if "error" in analysis:
                return [types.TextContent(type="text", text=f"{analysis['error']}")]
            
            result = "**ANÁLISIS DE PATRÓN DE SUEÑO**\n\n"
            
            # Análisis de duración
            duration_status = analysis["duration"]
            if duration_status == "insufficient":
                result += f"**Duración:** Insuficiente (faltan {analysis['duration_gap']:.1f} horas)\n"
            elif duration_status == "excessive":
                result += f"**Duración:** Excesiva (sobran {analysis['duration_gap']:.1f} horas)\n"
            else:
                result += "**Duración:** Óptima\n"
            
            # Alineación con cronotipos
            alignment = analysis["chronotype_alignment"]
            if alignment["aligned"]:
                result += "**Cronotipos:** Bien alineado\n"
            else:
                result += "**Cronotipos:** Desalineado\n"
                if not alignment["bedtime_aligned"]:
                    result += "  - Hora de dormir no óptima\n"
                if not alignment["wake_aligned"]:
                    result += "  - Hora de despertar no óptima\n"
            
            # Problemas de calidad
            if analysis["quality_issues"]:
                result += "\n**Problemas detectados:**\n"
                for issue in analysis["quality_issues"]:
                    result += f"  - {issue}\n"
            else:
                result += "\n**Calidad:** No se detectaron problemas mayores\n"
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error en análisis: {str(e)}")]
    
    elif name == "get_personalized_recommendations":
        try:
            recommendations = engine.generate_personalized_recommendations(arguments["user_id"])
            
            if not recommendations:
                return [types.TextContent(type="text", text="Usuario no encontrado")]
            
            result = "**RECOMENDACIONES PERSONALIZADAS**\n\n"
            
            # Agrupar por prioridad
            high_priority = [r for r in recommendations if r.priority == 1]
            medium_priority = [r for r in recommendations if r.priority == 2]
            low_priority = [r for r in recommendations if r.priority == 3]
            
            if high_priority:
                result += "**PRIORIDAD ALTA**\n"
                for rec in high_priority:
                    result += f"**{rec.category}:** {rec.recommendation}\n"
                    result += f"   ⏱️ Tiempo: {rec.timeframe} | 🎁 Beneficio: {rec.expected_benefit}\n\n"
            
            if medium_priority:
                result += "**PRIORIDAD MEDIA**\n"
                for rec in medium_priority:
                    result += f"**{rec.category}:** {rec.recommendation}\n"
                    result += f"   ⏱️ Tiempo: {rec.timeframe} | 🎁 Beneficio: {rec.expected_benefit}\n\n"
            
            if low_priority:
                result += "**RECOMENDACIONES ADICIONALES**\n"
                for rec in low_priority:
                    result += f"**{rec.category}:** {rec.recommendation}\n"
                    result += f"   ⏱️ Tiempo: {rec.timeframe} | 🎁 Beneficio: {rec.expected_benefit}\n\n"
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error generando recomendaciones: {str(e)}")]
    
    elif name == "create_weekly_schedule":
        try:
            schedule = engine.create_weekly_schedule(arguments["user_id"])
            
            if "error" in schedule:
                return [types.TextContent(type="text", text=f"{schedule['error']}")]
            
            result = "**HORARIO SEMANAL OPTIMIZADO**\n\n"
            
            # Horario por día
            for day, times in schedule["weekly_schedule"].items():
                result += f"**{day.upper()}**\n"
                result += f"   Dormir: {times['bedtime']}\n"
                result += f"   Despertar: {times['wake_time']}\n"
                result += f"   ⏱️ Duración: {times['sleep_duration']}\n\n"
            
            # Rutina de la noche
            result += "**RUTINA NOCTURNA**\n"
            for step in schedule["bedtime_routine"]:
                result += f"   {step['time']}: {step['activity']}\n"
            
            result += "\n**RUTINA MATUTINA**\n"
            for step in schedule["wake_routine"]:
                result += f"   {step['time']}: {step['activity']}\n"
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error creando horario: {str(e)}")]
    
    elif name == "quick_sleep_advice":
        try:
            query = arguments["query"].lower()
            user_context = arguments.get("user_context", "")
            
            # Base de consejos rápidos
            quick_advice = {
                "insomnio": [
                    "Levántate de la cama si no puedes dormir en 20 minutos",
                    "Prueba la técnica de respiración 4-7-8: inhala 4, mantén 7, exhala 8",
                    "Lee algo aburrido con luz tenue hasta sentir sueño",
                    "Evita mirar el reloj, aumenta la ansiedad"
                ],
                "despertar": [
                    "Usa un despertador de luz gradual",
                    "Bebe agua inmediatamente al despertar",
                    "Evita el botón snooze, fragmenta el sueño REM",
                    "Haz 5 minutos de ejercicio ligero"
                ],
                "sueño": [
                    "Mantén la habitación entre 18-20°C",
                    "Usa modo nocturno o filtros de luz azul",
                    "Prueba té de manzanilla o valeriana",
                    "Toma una ducha tibia 1-2 horas antes de dormir"
                ],
                "energia": [
                    "Consume cafeína solo en las primeras 6 horas del día",
                    "Exposición a luz natural en la mañana",
                    "Siesta de máximo 20 minutos antes de las 3 PM",
                    "Ejercicio regular mejora la calidad del sueño"
                ],
                "estres": [
                    "Escribe tus preocupaciones antes de dormir",
                    "Meditación mindfulness de 10 minutos",
                    "Música relajante o sonidos de la naturaleza",
                    "Relajación muscular progresiva"
                ]
            }
            
            advice_list = []
            
            # Buscar consejos relevantes
            for keyword, tips in quick_advice.items():
                if keyword in query:
                    advice_list.extend(tips)
            
            # Consejos generales si no hay match específico
            if not advice_list:
                advice_list = [
                    "Mantén horarios consistentes todos los días",
                    "Apaga pantallas 1 hora antes de dormir",
                    "Evita comidas pesadas 3 horas antes de acostarte",
                    "Limita la cafeína después de las 2 PM"
                ]
            
            result = "💡 **CONSEJOS RÁPIDOS PARA TU CONSULTA**\n\n"
            for tip in advice_list[:4]:  # Máximo 4 consejos
                result += f"{tip}\n"
            
            result += f"\n📋 **Tu consulta:** {arguments['query']}\n"
            if user_context:
                result += f"**Contexto:** {user_context}\n"
            
            result += "\n💬 Para recomendaciones más personalizadas, crea un perfil de usuario completo."
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error proporcionando consejo: {str(e)}")]
    
    else:
        return [types.TextContent(type="text", text=f"Herramienta desconocida: {name}")]

async def main():
    print("Sleep Coach MCP Server corriendo y esperando mensajes...")

    """Función principal del servidor"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream, 
            write_stream, 
            InitializationOptions(
                server_name="sleep-coach",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())