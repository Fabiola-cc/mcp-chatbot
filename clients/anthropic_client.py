# src/chatbot/anthropic_client.py
import os
import time
from typing import List, Dict
import anthropic
from dotenv import load_dotenv

class AnthropicClient:
    def __init__(self, model_name: str = "claude-3-5-haiku-20241022", api_key: str = None):
        """
        Cliente para interactuar con Anthropic Claude API
        
        Args:
            model_name: Nombre del modelo Claude a usar
            api_key: Clave API de Anthropic (si no se proporciona, se lee del .env)
        """
        load_dotenv()
        
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "No se encontró la clave API de Anthropic. "
                "Agrega ANTHROPIC_API_KEY a tu archivo .env o pásala como parámetro"
            )
        
        # Inicializar cliente de Anthropic
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            print(f"✅ Cliente Anthropic inicializado con modelo: {model_name}")
            
            # Verificar conexión con una consulta simple
            self._test_connection()
            
        except Exception as e:
            raise ConnectionError(f"Error inicializando cliente Anthropic: {str(e)}")
    
    def _test_connection(self):
        """Prueba la conexión con la API"""
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            if response.content:
                print("🔗 Conexión con Anthropic API verificada")
        except Exception as e:
            raise ConnectionError(f"No se pudo conectar con Anthropic API: {str(e)}")
    
    def send_message(self, message: str, conversation_history: List[Dict] = None) -> str:
        """
        Envía mensaje a Claude via Anthropic API
        
        Args:
            message: Mensaje del usuario
            conversation_history: Historial de conversación
            
        Returns:
            Respuesta del modelo
        """
        try:
            start_time = time.time()
            
            # Construir mensajes en formato de Anthropic
            messages = self._build_messages(message, conversation_history)
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4000,
                temperature=0.7,
                messages=messages
            )
            
            response_time = time.time() - start_time
            
            # Extraer texto de la respuesta
            if response.content and len(response.content) > 0:
                answer = response.content[0].text.strip()
                
                return answer if answer else "🤔 Claude no generó una respuesta clara."
            else:
                return "❌ No se recibió respuesta válida de Claude."
                
        except anthropic.APIError as e:
            if "rate_limit" in str(e).lower():
                return "❌ Límite de tasa alcanzado. Espera un momento antes de intentar de nuevo."
            elif "authentication" in str(e).lower():
                return "❌ Error de autenticación. Verifica tu clave API de Anthropic."
            else:
                return f"❌ Error de API de Anthropic: {str(e)}"
                
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"
    
    def _build_messages(self, message: str, history: List[Dict] = None) -> List[Dict]:
        """
        Construye mensajes en formato de Anthropic API
        
        Args:
            message: Mensaje actual del usuario
            history: Historial de conversación
            
        Returns:
            Lista de mensajes formateados para Anthropic
        """
        messages = []
        
        if history:
            # Incluir solo los últimos mensajes para no exceder límites
            recent_history = history[-20:]  # Últimos 20 mensajes
            
            for msg in recent_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Agregar mensaje actual
        messages.append({
            "role": "user", 
            "content": message
        })
        
        return messages
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima el número de tokens en un texto
        Aproximación para modelos Claude: 1 token ≈ 3-4 caracteres
        """
        return len(text) // 3
    
    def get_model_info(self) -> Dict:
        """Obtiene información del modelo actual"""
        return {
            "model_name": self.model_name,
            "provider": "Anthropic",
            "max_tokens": 4000,
            "temperature": 0.7
        }
    
    def list_available_models(self) -> List[str]:
        """Lista modelos disponibles de Anthropic"""
        # Modelos Claude disponibles (actualizado a diciembre 2024)
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", 
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]


# Función helper para configuración
def setup_anthropic():
    """Script helper para configurar Anthropic API"""
    print("🔧 CONFIGURACIÓN DE ANTHROPIC API")
    print("=" * 40)
    
    # Verificar si existe archivo .env
    env_file = ".env"
    if not os.path.exists(env_file):
        print("📝 Creando archivo .env...")
        with open(env_file, "w") as f:
            f.write("# Clave API de Anthropic\n")
            f.write("ANTHROPIC_API_KEY=your_api_key_here\n")
        
        print(f"✅ Archivo {env_file} creado")
        print("\n🔑 PASOS PARA OBTENER TU API KEY:")
        print("1. Ve a https://console.anthropic.com/")
        print("2. Inicia sesión o crea una cuenta")
        print("3. Ve a la sección 'API Keys'")
        print("4. Crea una nueva API key")
        print("5. Copia la clave y pégala en el archivo .env")
        print(f"6. Reemplaza 'your_api_key_here' con tu clave real")
        return False
    
    # Verificar si la clave API está configurada
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key or api_key == "your_api_key_here":
        print("❌ Clave API no configurada en .env")
        print("\n🔑 Para configurar tu API key:")
        print("1. Abre el archivo .env")
        print("2. Reemplaza 'your_api_key_here' con tu clave real de Anthropic")
        print("3. Guarda el archivo")
        return False
    
    # Probar conexión
    try:
        client = AnthropicClient()
        print("✅ Anthropic API configurado correctamente")
        
        # Mostrar modelos disponibles
        models = client.list_available_models()
        print(f"\n📦 Modelos disponibles:")
        for i, model in enumerate(models, 1):
            current = " (ACTUAL)" if model == client.model_name else ""
            print(f"   {i}. {model}{current}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando Anthropic: {str(e)}")
        return False


if __name__ == "__main__":
    # Test del cliente
    try:
        print("🧪 TESTING CLIENTE ANTHROPIC")
        print("=" * 40)
        
        # Configurar si es necesario
        if not setup_anthropic():
            print("\n💡 Configura tu API key antes de continuar")
            exit(1)
        
        # Crear cliente
        client = AnthropicClient()
        
        # Test básico
        print("\n📝 Test 1: Mensaje simple")
        response = client.send_message("Hola, preséntate brevemente en español")
        print(f"🤖 Claude: {response}")
        
        # Test con contexto
        print("\n📝 Test 2: Mantenimiento de contexto")
        history = [
            {"role": "user", "content": "Mi nombre es Juan"},
            {"role": "assistant", "content": "Hola Juan, es un placer conocerte"}
        ]
        
        response = client.send_message("¿Recuerdas mi nombre?", history)
        print(f"🤖 Claude: {response}")
        
        # Información del modelo
        info = client.get_model_info()
        print(f"\n📊 Información del modelo: {info}")
        print(f"📊 Tokens estimados última respuesta: {client.estimate_tokens(response)}")
        print("✅ Cliente Anthropic funcionando correctamente")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Asegúrate de que tu API key esté configurada correctamente")