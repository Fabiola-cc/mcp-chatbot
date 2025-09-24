# src/chatbot/ollama_client.py
import requests
import json
import time
from typing import List, Dict, Optional

class OllamaClient:
    def __init__(self, model_name: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        """
        Cliente para interactuar con Ollama local
        
        Args:
            model_name: Nombre del modelo a usar
            base_url: URL base de Ollama
        """
        self.model_name = model_name
        self.base_url = base_url
        self.session = requests.Session()
        
        # Verificar conexión al inicializar
        if not self.check_connection():
            raise ConnectionError("No se puede conectar a Ollama. ¿Está ejecutándose?")
        
        # Verificar si el modelo está disponible
        if not self.is_model_available():
            print(f"⚠️  Modelo {model_name} no encontrado. Modelos disponibles:")
            available = self.list_available_models()
            if available:
                for model in available:
                    print(f"   - {model}")
                raise ValueError(f"Modelo {model_name} no disponible. Usa 'ollama pull {model_name}' para descargarlo")
            else:
                print("   (No hay modelos instalados)")
                raise ValueError("No hay modelos disponibles. Descarga uno con 'ollama pull llama3.2:3b'")
        
        print(f"✅ Cliente Ollama inicializado con modelo: {model_name}")
    
    def send_message(self, message: str, conversation_history: List[Dict] = None) -> str:
        """
        Envía mensaje al modelo local via Ollama
        
        Args:
            message: Mensaje del usuario
            conversation_history: Historial de conversación
            
        Returns:
            Respuesta del modelo
        """
        # Construir prompt con contexto
        prompt = self._build_prompt(message, conversation_history)
        
        try:
            start_time = time.time()
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 2000,  # máximo tokens de salida
                        "repeat_penalty": 1.1,
                        "top_k": 40
                    }
                },
                timeout=1200  # timeout más largo para modelos locales
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                # Log de rendimiento
                if response_time > 10:
                    print(f"⚠️  Respuesta lenta: {response_time:.1f}s")
                
                return answer if answer else "🤔 El modelo no generó una respuesta clara."
                
            else:
                return f"❌ Error del servidor Ollama: {response.status_code} - {response.text}"
                
        except requests.exceptions.ConnectionError:
            return "❌ No se puede conectar a Ollama. ¿Está ejecutándose? (ollama serve)"
        except requests.exceptions.Timeout:
            return "❌ Timeout: El modelo está tardando demasiado. Intenta con un mensaje más corto."
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"
    
    def _build_prompt(self, message: str, history: List[Dict] = None) -> str:
        """
        Construye prompt optimizado con contexto de conversación
        
        Args:
            message: Mensaje actual del usuario
            history: Historial de conversación
            
        Returns:
            Prompt formateado para el modelo
        """
        # Prompt base que define el comportamiento
        prompt = "\n"
        
        if history:
            # Incluir solo los últimos mensajes para no exceder el contexto
            recent_history = history[-8:]  # Últimos 8 mensajes
            
            for msg in recent_history:
                if msg["role"] == "user":
                    prompt += f"Usuario: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    prompt += f"Asistente: {msg['content']}\n"
        
        prompt += f"Usuario: {message}\nAsistente:"
        
        return prompt
    
    def check_connection(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_model_available(self) -> bool:
        """Verifica si el modelo específico está disponible"""
        available_models = self.list_available_models()
        return self.model_name in available_models
    
    def list_available_models(self) -> List[str]:
        """Lista modelos disponibles en Ollama"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except Exception as e:
            print(f"Error listando modelos: {e}")
        return []
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima el número de tokens en un texto
        Aproximación para modelos tipo Llama: 1 token ≈ 3-4 caracteres
        """
        return len(text) // 3
    
    def get_model_info(self) -> Dict:
        """Obtiene información del modelo actual"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": self.model_name},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}
    
    def check_model_and_download(self, model_name: str = None) -> bool:
        """
        Verifica si un modelo está disponible y ofrece descargarlo si no
        
        Args:
            model_name: Modelo a verificar (usa self.model_name si no se especifica)
            
        Returns:
            True si el modelo está disponible o se descargó exitosamente
        """
        model_to_check = model_name or self.model_name
        
        if model_to_check in self.list_available_models():
            return True
        
        print(f"📥 Modelo {model_to_check} no encontrado.")
        download = input(f"¿Descargar {model_to_check}? (s/n): ").lower().strip()
        
        if download == 's':
            return self.download_model(model_to_check)
        
        return False
    
    def download_model(self, model_name: str) -> bool:
        """
        Descarga un modelo desde Ollama
        
        Args:
            model_name: Nombre del modelo a descargar
            
        Returns:
            True si se descargó exitosamente
        """
        print(f"🔄 Descargando modelo {model_name}...")
        print("⚠️  Esto puede tomar varios minutos dependiendo del tamaño del modelo...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=1800  # 30 minutos timeout para descarga
            )
            
            if response.status_code == 200:
                # Procesar respuestas streaming de descarga
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                print(f"📥 {data['status']}")
                            if "error" in data:
                                print(f"❌ Error: {data['error']}")
                                return False
                        except json.JSONDecodeError:
                            continue
                
                print(f"✅ Modelo {model_name} descargado exitosamente")
                return True
            else:
                print(f"❌ Error descargando modelo: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error durante descarga: {str(e)}")
            return False


# Script de configuración y testing
def setup_ollama():
    """Script helper para configurar Ollama"""
    print("🔧 CONFIGURACIÓN DE OLLAMA")
    print("=" * 40)
    
    # Verificar si Ollama está instalado y ejecutándose
    client = OllamaClient.__new__(OllamaClient)  # Crear instancia sin init
    client.base_url = "http://localhost:11434"
    client.session = requests.Session()
    
    if not client.check_connection():
        print("❌ Ollama no está ejecutándose o instalado")
        print("\n📋 PASOS PARA INSTALAR:")
        print("1. Instalar Ollama:")
        print("   curl -fsSL https://ollama.com/install.sh | sh")
        print("\n2. Iniciar el servicio:")
        print("   ollama serve")
        print("\n3. En otra terminal, descargar un modelo:")
        print("   ollama pull llama3.2:3b")
        return False
    
    # Listar modelos disponibles
    available = client.list_available_models()
    print(f"✅ Ollama está ejecutándose")
    print(f"📦 Modelos disponibles: {len(available)}")
    
    if not available:
        print("\n⚠️  No hay modelos instalados")
        print("📥 Modelos recomendados para tu proyecto:")
        print("   - llama3.2:3b (ligero, ~2GB)")
        print("   - qwen2.5:3b (bueno para español, ~2GB)")
        print("   - codellama:7b (especializado en código, ~4GB)")
        
        model_choice = input("\n¿Qué modelo descargar? (llama3.2:3b): ").strip()
        if not model_choice:
            model_choice = "llama3.2:3b"
        
        return client.download_model(model_choice)
    else:
        print("\n📦 Modelos disponibles:")
        for i, model in enumerate(available, 1):
            print(f"   {i}. {model}")
        return True


if __name__ == "__main__":
    # Test del cliente
    try:
        print("🧪 TESTING CLIENTE OLLAMA")
        print("=" * 40)
        
        # Configurar si es necesario
        if not setup_ollama():
            exit(1)
        
        # Crear cliente
        client = OllamaClient("llama3.2:3b")
        
        # Test básico
        print("\n🔄 Test 1: Mensaje simple")
        response = client.send_message("Hola, preséntate brevemente")
        print(f"🤖 Respuesta: {response}")
        
        # Test con contexto
        print("\n🔄 Test 2: Mantenimiento de contexto")
        history = [
            {"role": "user", "content": "Mi nombre es Juan"},
            {"role": "assistant", "content": "Hola Juan, es un placer conocerte"}
        ]
        
        response = client.send_message("¿Recuerdas mi nombre?", history)
        print(f"🤖 Respuesta: {response}")
        
        # Información del modelo
        print(f"\n📊 Tokens estimados: {client.estimate_tokens(response)}")
        print("✅ Cliente Ollama funcionando correctamente")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Asegúrate de que Ollama esté instalado y ejecutándose")