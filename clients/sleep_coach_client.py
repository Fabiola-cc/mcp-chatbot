import asyncio
import json
import subprocess
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime

class SleepCoachClient:
    """Cliente para interactuar con el Sleep Coach MCP Server"""
    
    def __init__(self):
        self.server_process = None
        self.is_connected = False
        self.request_id = 1
    
    async def start_server(self):
        """Inicia el servidor Sleep Coach"""
        try:
            server_path = Path(__file__).parent.parent.parent / "servidores locales mcp" / "SleepCoachServer" / "sleep_coach.py"
            
            # Asegurarse de que el archivo existe
            if not server_path.exists():
                print(f"❌ Servidor no encontrado: {server_path}")
                return False
            
            print("🚀 Iniciando Sleep Coach Server...")
            self.server_process = await asyncio.create_subprocess_exec(
                sys.executable, server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Esperar un momento para que el servidor se inicie
            await asyncio.sleep(1)
            
            # Verificar si el proceso sigue ejecutándose
            if self.server_process.returncode is not None:
                stderr_output = await self.server_process.stderr.read()
                print(f"❌ El servidor se cerró inmediatamente: {stderr_output.decode()}")
                return False
            
            # Inicializar el servidor MCP
            if await self._initialize_mcp():
                self.is_connected = True
                print("✅ Sleep Coach Server conectado y listo")
                return True
            else:
                print("❌ Falló la inicialización del servidor MCP")
                return False
                
        except Exception as e:
            print(f"❌ Error iniciando Sleep Coach Server: {e}")
            return False
    
    async def _initialize_mcp(self) -> bool:
        """Inicializa la conexión MCP con el servidor"""
        try:
            # 1. Enviar mensaje de inicialización
            init_message = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "sleep-coach-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_message(init_message)
            if not response or "error" in response:
                print(f"❌ Error en inicialización: {response.get('error') if response else 'Sin respuesta'}")
                return False
            
            # 2. Enviar notificación de inicializado
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            # Las notificaciones no esperan respuesta
            await self._send_notification(initialized_notification)
            
            return True
            
        except Exception as e:
            print(f"❌ Error en inicialización MCP: {e}")
            return False
    
    async def _send_message(self, message: dict) -> dict:
        """Envía un mensaje y espera respuesta"""
        try:
            message_str = json.dumps(message) + "\n"
        
            self.server_process.stdin.write(message_str.encode())
            await self.server_process.stdin.drain()
            
            # Leer respuesta
            response_line = await asyncio.wait_for(
                self.server_process.stdout.readline(), 
                timeout=5.0
            )
            
            if not response_line:
                print("❌ No se recibió respuesta del servidor")
                return None
            
            response_str = response_line.decode().strip()
            
            return json.loads(response_str)
            
        except asyncio.TimeoutError:
            print("❌ Timeout esperando respuesta del servidor")
            return None
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return None
    
    async def _send_notification(self, notification: dict):
        """Envía una notificación (no espera respuesta)"""
        try:
            message_str = json.dumps(notification) + "\n"
            
            self.server_process.stdin.write(message_str.encode())
            await self.server_process.stdin.drain()
            
        except Exception as e:
            print(f"❌ Error enviando notificación: {e}")
    
    def _get_request_id(self) -> int:
        """Genera un ID único para cada request"""
        request_id = self.request_id
        self.request_id += 1
        return request_id
    
    async def list_tools(self) -> List[Dict]:
        """Lista las herramientas disponibles en el servidor"""
        if not self.is_connected:
            print("❌ Sleep Coach Server no está conectado")
            return []
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "tools/list",
                "params": {}
            }
            
            response = await self._send_message(message)
            
            if response and "result" in response:
                tools = response["result"]["tools"]
                print(f"🔧 Herramientas disponibles: {[tool['name'] for tool in tools]}")
                return tools
            else:
                print(f"❌ Error listando herramientas: {response}")
                return []
                
        except Exception as e:
            print(f"❌ Error listando herramientas: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Llama a una herramienta del servidor MCP"""
        if not self.is_connected:
            return "❌ Sleep Coach Server no está conectado"
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self._send_message(message)
            
            if response and "result" in response:
                # Extraer el contenido de la respuesta
                content = response["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    return content[0]["text"]
                else:
                    return str(content)
            elif response and "error" in response:
                return f"❌ Error: {response['error']['message']}"
            else:
                return "❌ Respuesta inesperada del servidor"
                
        except Exception as e:
            return f"❌ Error comunicándose con Sleep Coach: {str(e)}"

    async def get_sleep_recommendations(self, sleep_data: str) -> str:
        """Obtiene recomendaciones de sueño"""
        return await self.call_tool("get_sleep_recommendations", {"sleep_data": sleep_data})
    
    async def analyze_sleep_pattern(self, sleep_log: str) -> str:
        """Analiza patrones de sueño"""
        return await self.call_tool("analyze_sleep_pattern", {"sleep_log": sleep_log})

    async def stop_server(self):
        """Detiene el servidor"""
        if self.server_process and self.server_process.returncode is None:
            print("🛑 Deteniendo Sleep Coach Server...")
            self.server_process.terminate()
            
            try:
                await asyncio.wait_for(self.server_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                print("⚠️ Forzando cierre del servidor...")
                self.server_process.kill()
                await self.server_process.wait()
            
            self.is_connected = False
            print("✅ Sleep Coach Server detenido")

# Función de prueba
async def test_sleep_coach():
    """Función para probar el cliente Sleep Coach"""
    client = SleepCoachClient()
    
    try:
        # Iniciar servidor
        if await client.start_server():
            print("✅ Servidor iniciado correctamente")
            
            # Listar herramientas
            tools = await client.list_tools()
            print(f"🔧 Herramientas disponibles: {len(tools)}")
            
            # Probar herramienta de recomendaciones
            sleep_data = "Duermo 5 horas por noche, me despierto cansado"
            recommendations = await client.get_sleep_recommendations(sleep_data)
            print(f"💤 Recomendaciones: {recommendations}")
            
            # Probar análisis de patrones
            sleep_log = "Lunes: 11pm-5am, Martes: 12am-6am, Miércoles: 1am-6am"
            analysis = await client.analyze_sleep_pattern(sleep_log)
            print(f"📊 Análisis: {analysis}")
            
        else:
            print("❌ No se pudo iniciar el servidor")
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    finally:
        await client.stop_server()

# Ejecutar prueba si se ejecuta directamente
if __name__ == "__main__":
    asyncio.run(test_sleep_coach())