"""
Cliente MCP Remoto para Citas Inspiracionales de Sueño
Conecta con el servidor MCP desplegado en la nube
"""

import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RemoteQuote:
    """Estructura para citas remotas"""
    id: int
    quote: str
    author: str
    category: str
    time_of_day: str
    mood: str

class RemoteSleepQuotesClient:
    """Cliente para conectar con el servidor MCP remoto de citas inspiracionales"""
    
    def __init__(self, server_url: str = None):
        """
        Inicializa el cliente remoto
        
        Args:
            server_url: URL del servidor MCP remoto
        """
        # URLs de servidores desplegados (se actualizarán después del despliegue)
        self.fallback_urls = [
            "http://localhost:8000"                   # Desarrollo local
        ]
        
        self.server_url = server_url or self.fallback_urls[0]
        self.session = None
        self.is_connected = False
        
        # Cache para mejorar rendimiento
        self.cache = {}
        self.cache_ttl = 300  # 5 minutos
        
    async def __aenter__(self):
        """Inicializa sesión HTTP async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'MCP-Sleep-Quotes-Client/1.0'}
        )
        await self.test_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra sesión HTTP"""
        if self.session:
            await self.session.close()
    
    async def test_connection(self) -> bool:
        """Prueba conexión con el servidor remoto"""
        for url in [self.server_url] + self.fallback_urls:
            try:
                async with self.session.get(f"{url}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "healthy":
                            self.server_url = url
                            self.is_connected = True
                            logger.info(f"✅ Conectado a servidor remoto: {url}")
                            return True
            except Exception as e:
                logger.warning(f"⚠️ No se pudo conectar a {url}: {str(e)}")
                continue
        
        self.is_connected = False
        logger.error("❌ No se pudo conectar a ningún servidor MCP remoto")
        return False
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica si el cache es válido"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (datetime.now().timestamp() - cached_time) < self.cache_ttl
    
    def _set_cache(self, cache_key: str, data: Any):
        """Guarda datos en cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def _get_cache(self, cache_key: str) -> Any:
        """Obtiene datos del cache"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    async def get_inspirational_quote(
        self, 
        category: Optional[str] = None, 
        mood: Optional[str] = None,
        time_based: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene una cita inspiracional del servidor remoto
        
        Args:
            category: Categoría de la cita
            mood: Estado de ánimo deseado
            time_based: Si usar cita basada en la hora actual
            
        Returns:
            Diccionario con la cita y metadatos
        """
        if not self.is_connected:
            return self._get_offline_response("quote")
        
        # Verificar cache
        cache_key = f"quote_{category}_{mood}_{time_based}"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            params = {}
            if category:
                params['category'] = category
            if mood:
                params['mood'] = mood
            if time_based:
                params['time_based'] = 'true'
            
            async with self.session.get(
                f"{self.server_url}/api/quote",
                params=params
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Formatear respuesta
                    quote_data = data['quote']
                    formatted_response = {
                        'success': True,
                        'message': f"""🌙 CITA INSPIRACIONAL PARA DORMIR 🌙

"{quote_data['quote']}"

— {quote_data['author']}

📅 Hora: {datetime.now().strftime('%H:%M')}
🏷️  Categoría: {quote_data['category'].replace('_', ' ').title()}
💭 Estado: {quote_data['mood'].title()}
⏰ Momento: {quote_data['time_of_day'].replace('_', ' ').title()}

✨ Que tengas dulces sueños ✨""",
                        'quote_data': quote_data,
                        'source': 'remote_server',
                        'timestamp': data['timestamp']
                    }
                    
                    # Guardar en cache
                    self._set_cache(cache_key, formatted_response)
                    
                    return formatted_response
                else:
                    logger.error(f"Error HTTP {response.status}")
                    return self._get_offline_response("quote")
                    
        except Exception as e:
            logger.error(f"Error obteniendo cita: {str(e)}")
            return self._get_offline_response("quote")
    
    async def get_sleep_hygiene_tip(self) -> Dict[str, Any]:
        """Obtiene un consejo de higiene del sueño"""
        if not self.is_connected:
            return self._get_offline_response("tip")
        
        # Verificar cache
        cache_key = "sleep_tip"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            async with self.session.get(f"{self.server_url}/api/tip") as response:
                if response.status == 200:
                    data = await response.json()
                    tip_data = data['tip']
                    
                    formatted_response = {
                        'success': True,
                        'message': f"""💡 CONSEJO DE HIGIENE DEL SUEÑO 💡

{tip_data['quote']}

— {tip_data['author']}

🎯 Esta es tu recomendación personalizada para mejorar tu calidad de sueño.

💤 Recuerda: Pequeños cambios en tus hábitos pueden generar grandes mejoras en tu descanso.""",
                        'tip_data': tip_data,
                        'source': 'remote_server',
                        'timestamp': data['timestamp']
                    }
                    
                    # Guardar en cache
                    self._set_cache(cache_key, formatted_response)
                    
                    return formatted_response
                else:
                    return self._get_offline_response("tip")
                    
        except Exception as e:
            logger.error(f"Error obteniendo consejo: {str(e)}")
            return self._get_offline_response("tip")
    
    async def search_quotes(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Busca citas por palabra clave"""
        if not self.is_connected:
            return self._get_offline_response("search")
        
        try:
            async with self.session.get(
                f"{self.server_url}/api/search/{query}",
                params={'limit': limit}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data['results']:
                        message = f"""🔍 BÚSQUEDA: "{query}"

❌ No se encontraron citas que coincidan con tu búsqueda.

💡 Intenta con términos como: sueño, descanso, noche, relajación, paz"""
                    else:
                        message = f"""🔍 RESULTADOS DE BÚSQUEDA: "{query}"

📚 Encontré {len(data['results'])} cita(s) para ti:

"""
                        for i, quote in enumerate(data['results'], 1):
                            message += f"""
{i}. "{quote['quote']}"
   — {quote['author']} | {quote['category'].replace('_', ' ').title()}

"""
                    
                    return {
                        'success': True,
                        'message': message,
                        'results': data['results'],
                        'total_found': data['total_found'],
                        'source': 'remote_server',
                        'timestamp': data['timestamp']
                    }
                else:
                    return self._get_offline_response("search")
                    
        except Exception as e:
            logger.error(f"Error en búsqueda: {str(e)}")
            return self._get_offline_response("search")
    
    async def get_daily_wisdom(self, include_tip: bool = True) -> Dict[str, Any]:
        """Obtiene sabiduría diaria sobre el sueño"""
        if not self.is_connected:
            return self._get_offline_response("wisdom")
        
        # Verificar cache (cache por día)
        cache_key = f"daily_wisdom_{datetime.now().strftime('%Y-%m-%d')}_{include_tip}"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            params = {'include_tip': 'true' if include_tip else 'false'}
            
            async with self.session.get(
                f"{self.server_url}/api/wisdom",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    quote_data = data['daily_quote']
                    current_date = datetime.now().strftime("%A, %d de %B")
                    current_time = datetime.now().strftime("%H:%M")
                    
                    message = f"""📖 SABIDURÍA DIARIA DEL SUEÑO 📖

📅 {current_date} • {current_time}

🌟 CITA DEL DÍA:
"{quote_data['quote']}"
— {quote_data['author']}

"""
                    
                    if include_tip and 'daily_tip' in data:
                        tip_data = data['daily_tip']
                        message += f"""💡 CONSEJO PRÁCTICO:
{tip_data['quote']}

🎯 Aplica este consejo hoy y observa cómo mejora tu descanso nocturno.

"""
                    
                    message += """🌙 Que tengas un día productivo y una noche de sueño reparador. 🌙"""
                    
                    formatted_response = {
                        'success': True,
                        'message': message,
                        'daily_quote': quote_data,
                        'daily_tip': data.get('daily_tip'),
                        'source': 'remote_server',
                        'timestamp': data['timestamp']
                    }
                    
                    # Guardar en cache (válido por un día)
                    self.cache_ttl = 3600  # 1 hora para sabiduría diaria
                    self._set_cache(cache_key, formatted_response)
                    self.cache_ttl = 300  # Restaurar TTL normal
                    
                    return formatted_response
                else:
                    return self._get_offline_response("wisdom")
                    
        except Exception as e:
            logger.error(f"Error obteniendo sabiduría diaria: {str(e)}")
            return self._get_offline_response("wisdom")
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Obtiene el estado del servidor remoto"""
        try:
            async with self.session.get(f"{self.server_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'connected': True,
                        'server_info': data,
                        'url': self.server_url
                    }
                else:
                    return {'success': False, 'connected': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'success': False, 'connected': False, 'error': str(e)}
    
    def _get_offline_response(self, response_type: str) -> Dict[str, Any]:
        """Respuestas offline cuando el servidor no está disponible"""
        offline_responses = {
            "quote": {
                'success': False,
                'message': """❌ SERVIDOR REMOTO NO DISPONIBLE

🔌 No se pudo conectar al servidor de citas inspiracionales.

💡 Cita offline:
"El sueño es la mejor inversión que puedes hacer en tu bienestar. Descansa bien esta noche."
— Sleep Coach Local

🌙 El servidor estará disponible pronto. ¡Dulces sueños!""",
                'source': 'offline_fallback'
            },
            
            "tip": {
                'success': False,
                'message': """❌ SERVIDOR REMOTO NO DISPONIBLE

🔌 No se pudo conectar al servidor de consejos de sueño.

💡 Consejo offline:
"Mantén tu habitación fresca (18-20°C), oscura y silenciosa para un sueño óptimo."

🌙 El servidor estará disponible pronto.""",
                'source': 'offline_fallback'
            },
            
            "search": {
                'success': False,
                'message': """❌ SERVIDOR REMOTO NO DISPONIBLE

🔌 No se puede realizar la búsqueda en este momento.

⏳ Intenta nuevamente cuando el servidor esté disponible.""",
                'source': 'offline_fallback'
            },
            
            "wisdom": {
                'success': False,
                'message': """❌ SERVIDOR REMOTO NO DISPONIBLE

🔌 No se pudo obtener la sabiduría diaria.

💭 Reflexión offline:
"Cada noche es una oportunidad de descanso y renovación. Aprovecha este momento para cuidar tu bienestar."

🌙 El servidor estará disponible pronto.""",
                'source': 'offline_fallback'
            }
        }
        
        return offline_responses.get(response_type, {
            'success': False,
            'message': '❌ Servidor remoto no disponible',
            'source': 'offline_fallback'
        })

# Cliente sincronizado para uso fácil
class SleepQuotesRemoteClient:
    """Cliente sincronizado para citas inspiracionales remotas"""
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url
        self._async_client = None
    
    async def _get_client(self):
        """Obtiene o crea cliente async"""
        if self._async_client is None:
            self._async_client = RemoteSleepQuotesClient(self.server_url)
            await self._async_client.__aenter__()
        return self._async_client
    
    async def close(self):
        """Cierra el cliente"""
        if self._async_client:
            await self._async_client.__aexit__(None, None, None)
    
    async def get_quote(self, category: str = None, mood: str = None, time_based: bool = False):
        """Obtiene cita inspiracional"""
        client = await self._get_client()
        return await client.get_inspirational_quote(category, mood, time_based)
    
    async def get_tip(self):
        """Obtiene consejo de higiene del sueño"""
        client = await self._get_client()
        return await client.get_sleep_hygiene_tip()
    
    async def search(self, query: str):
        """Busca citas"""
        client = await self._get_client()
        return await client.search_quotes(query)
    
    async def get_daily_wisdom(self, include_tip: bool = True):
        """Obtiene sabiduría diaria"""
        client = await self._get_client()
        return await client.get_daily_wisdom(include_tip)
    
    async def status(self):
        """Obtiene estado del servidor"""
        client = await self._get_client()
        return await client.get_server_status()
    
    async def __aenter__(self):
        self.__init__
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()