import asyncio
import json
import subprocess
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime

class Client:
    """Cliente para interactuar con el  MCP Server"""
    
    def __init__(self):
        self.server_process = None
        self.is_connected = False
        self.request_id = 1
    
    async def start_server(self, server_name, *args: str):
        """Inicia el servidor """
        try:
            # Asegurarse de que el archivo existe
            if server_name not in ("git", "filesystem", "remote"):
                server_path = Path(args[-1])
                if not server_path.exists():
                    print(f"❌ Servidor no encontrado: {server_path}")
                    return False
            
            self.server_process = await asyncio.create_subprocess_exec(
                *args,
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
            if await self._initialize_mcp(server_name):
                self.is_connected = True
                print(f"✅ {server_name} Server conectado y listo")
                return True
            else:
                print("❌ Falló la inicialización del servidor MCP")
                return False
                
        except Exception as e:
            print(f"❌ Error iniciando  Server: {e}")
            return False
    
    async def _initialize_mcp(self, server_name) -> bool:
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
                        "name": f"{server_name}-client",
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
            msg_str = json.dumps(message) + "\n"
            
            self.server_process.stdin.write(msg_str.encode())
            await self.server_process.stdin.drain()

            # Leer múltiples líneas hasta encontrar la respuesta correcta
            max_attempts = 5
            for attempt in range(max_attempts):
                line = await asyncio.wait_for(self.server_process.stdout.readline(), timeout=10.0)
                if not line:
                    print("❌ No se recibió respuesta")
                    return None
                    
                response = json.loads(line.decode().strip())
                
                # Si es una solicitud del servidor (como roots/list), responder y continuar
                if "method" in response and "id" in response:
                    await self._handle_server_request(response)
                    continue
                    
                # Si es la respuesta a nuestro mensaje (tiene el mismo ID)
                if "id" in response and response["id"] == message.get("id"):
                    return response
                    
                # Si es una respuesta sin ID específico pero tiene "result"
                if "result" in response or "error" in response:
                    return response
            
            print(f"❌ No se encontró respuesta válida después de {max_attempts} intentos")
            return None
            
        except asyncio.TimeoutError:
            print("❌ Timeout esperando respuesta")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error decodificando JSON: {e}")
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
    
    async def _handle_server_request(self, request):
        """Maneja solicitudes del servidor (como roots/list)"""
        try:
            if request.get("method") == "roots/list":
                # Responder con la lista de roots permitidos
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "roots": [
                            {
                                "uri": str(Path(__file__).parent),
                                "name": "LLM_PROYECTO1"
                            }
                        ]
                    }
                }
                
                msg_str = json.dumps(response) + "\n"
                self.server_process.stdin.write(msg_str.encode())
                await self.server_process.stdin.drain()
                
        except Exception as e:
            print(f"❌ Error manejando solicitud del servidor: {e}")
        
    async def list_tools(self) -> List[Dict]:
        """Lista las herramientas disponibles en el servidor"""
        if not self.is_connected:
            print("❌  Server no está conectado")
            return []
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "tools/list"
            }
            
            response = await self._send_message(message)
            
            if response and "result" in response:
                tools = response["result"]["tools"]
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
            return "❌  Server no está conectado"
        
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
            return f"❌ Error comunicándose con : {str(e)}"

    async def stop_server(self):
        """Detiene el servidor"""
        if self.server_process and self.server_process.returncode is None:
            print("🛑 Deteniendo  Server...")
            self.server_process.terminate()
            
            try:
                await asyncio.wait_for(self.server_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                print("⚠️ Forzando cierre del servidor...")
                self.server_process.kill()
                await self.server_process.wait()
            
            self.is_connected = False
            print("✅  Server detenido")