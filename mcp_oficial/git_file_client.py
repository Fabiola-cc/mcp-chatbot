import asyncio
import json
from pathlib import Path
import sys
import os
import subprocess

class MCPClient:
    """Cliente unificado para MCP Filesystem y Git Servers"""

    def __init__(self):
        self.fs_process = None
        self.git_process = None
        self.request_id = 1
        self.allowed_dir = "demo_workspace"

    def _get_request_id(self):
        rid = self.request_id
        self.request_id += 1
        return rid

    async def _send_message(self, process, message):
        """Envía un mensaje y espera respuesta"""
        try:
            msg_str = json.dumps(message) + "\n"
            
            process.stdin.write(msg_str.encode())
            await process.stdin.drain()

            # Leer múltiples líneas hasta encontrar la respuesta correcta
            max_attempts = 5
            for attempt in range(max_attempts):
                line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
                if not line:
                    print("❌ No se recibió respuesta")
                    return None
                    
                response = json.loads(line.decode().strip())
                
                # Si es una solicitud del servidor (como roots/list), responder y continuar
                if "method" in response and "id" in response:
                    await self._handle_server_request(process, response)
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

    async def _handle_server_request(self, process, request):
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
                                "uri": f"file://{Path(self.allowed_dir).resolve()}",
                                "name": self.allowed_dir
                            }
                        ]
                    }
                }
                
                msg_str = json.dumps(response) + "\n"
                process.stdin.write(msg_str.encode())
                await process.stdin.drain()
                
        except Exception as e:
            print(f"❌ Error manejando solicitud del servidor: {e}")

    async def _send_notification(self, process, notification):
        """Envía una notificación sin esperar respuesta"""
        try:
            msg_str = json.dumps(notification) + "\n"
            process.stdin.write(msg_str.encode())
            await process.stdin.drain()
        except Exception as e:
            print(f"❌ Error enviando notificación: {e}")

    async def _initialize_server(self, process, server_name):
        """Inicializa un servidor MCP con el handshake correcto"""
        
        init_message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "demo-client",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = await self._send_message(process, init_message)
        if not init_response or "error" in init_response:
            print(f"❌ Error inicializando {server_name}: {init_response}")
            return False
            
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        await self._send_notification(process, initialized_notification)
        print(f"✅ {server_name} inicializado correctamente")
        return True

    # -------------------- Método para crear repo con Git nativo --------------------
    def create_git_repo_native(self, repo_path):
        """Crea un repositorio Git usando comandos nativos"""
        try:
            repo_full_path = Path(repo_path).resolve()
            repo_full_path.mkdir(exist_ok=True)
            
            # Ejecutar git init
            result = subprocess.run(
                ["git", "init"],
                cwd=repo_full_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Repositorio Git creado exitosamente")
                return True
            else:
                print(f"❌ Error creando repositorio: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creando repositorio Git: {e}")
            return False

    def git_add_commit_native(self, repo_path, files, commit_message):
        """Hace add y commit usando comandos Git nativos"""
        try:
            repo_full_path = Path(repo_path).resolve()
            
            # Git add
            for file in files:
                result = subprocess.run(
                    ["git", "add", file],
                    cwd=repo_full_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"❌ Error en git add {file}: {result.stderr}")
                    return False
            
            # Git commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_full_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Commit realizado: {commit_message}")
                return True
            else:
                print(f"❌ Error en commit: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error en git add/commit: {e}")
            return False

    # -------------------- Servidores --------------------
    async def start_fs_server(self):
        """Inicia el servidor de filesystem"""
        print("🚀 Iniciando Filesystem MCP Server...")
        
        Path(self.allowed_dir).mkdir(exist_ok=True)
        npx_path = r"C:\Program Files\nodejs\npx.cmd"
        
        try:
            self.fs_process = await asyncio.create_subprocess_exec(
                npx_path, "-y", "@modelcontextprotocol/server-filesystem", self.allowed_dir,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            await asyncio.sleep(2)
            
            if self.fs_process.returncode is not None:
                stderr = await self.fs_process.stderr.read()
                print(f"❌ Filesystem server falló: {stderr.decode()}")
                return False
                
            success = await self._initialize_server(self.fs_process, "Filesystem")
            return success
            
        except Exception as e:
            print(f"❌ Error iniciando filesystem server: {e}")
            return False

    async def start_git_server_after_repo(self, repo_path):
        """Inicia el servidor Git DESPUÉS de que el repo ya existe"""
        print("🚀 Iniciando Git MCP Server...")
        
        try:
            self.git_process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "mcp_server_git", "--repository", repo_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            await asyncio.sleep(2)
            
            if self.git_process.returncode is not None:
                stderr = await self.git_process.stderr.read()
                print(f"❌ Git server falló: {stderr.decode()}")
                return False
                
            success = await self._initialize_server(self.git_process, "Git")
            return success
            
        except Exception as e:
            print(f"❌ Error iniciando git server: {e}")
            return False

    # -------------------- Operaciones Filesystem --------------------
    async def create_file(self, path: str, content: str):
        """Crea un archivo usando el servidor filesystem"""
        if not self.fs_process:
            print("❌ Filesystem server no está iniciado")
            return None
        
        # Usar path relativo al directorio permitido
        relative_path = self.allowed_dir + "/" + path if self.allowed_dir not in path else path
            
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": relative_path,
                    "content": content
                }
            }
        }
        
        response = await self._send_message(self.fs_process, message)
        
        if response and "result" in response:
            print(f"📄 Archivo creado exitosamente: {relative_path}")
        else:
            print(f"❌ Error creando archivo: {response}")
            
        return response

    async def list_tools(self, server_type="fs"):
        """Lista las herramientas disponibles"""
        process = self.fs_process if server_type == "fs" else self.git_process
        if not process:
            return None
            
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/list"
        }
        
        response = await self._send_message(process, message)
        print(f"🔧 Herramientas disponibles ({server_type}): {response}")
        return response

    # -------------------- Operaciones Git MCP --------------------
    async def git_status(self, repo_path: str):
        """Obtiene el status del repositorio"""
        if not self.git_process:
            print("❌ Git server no está iniciado")
            return None
            
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/call",
            "params": {
                "name": "git_status",
                "arguments": {
                    "repo_path": repo_path
                }
            }
        }
        
        response = await self._send_message(self.git_process, message)
        print(f"📊 Git status: {response}")
        return response

    async def git_log(self, repo_path: str):
        """Obtiene el log del repositorio"""
        if not self.git_process:
            print("❌ Git server no está iniciado")
            return None
            
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/call",
            "params": {
                "name": "git_log",
                "arguments": {
                    "repo_path": repo_path,
                    "max_count": 5
                }
            }
        }
        
        response = await self._send_message(self.git_process, message)
        print(f"📜 Git log: {response}")
        return response

    # -------------------- Cleanup --------------------
    async def stop_servers(self):
        """Detiene todos los servidores de manera segura"""
        for process, name in [(self.fs_process, "Filesystem"), (self.git_process, "Git")]:
            if process and process.returncode is None:
                try:
                    print(f"🛑 Deteniendo {name} Server...")
                    process.terminate()
                    
                    try:
                        await asyncio.wait_for(process.wait(), timeout=3)
                        print(f"✅ {name} Server detenido")
                    except asyncio.TimeoutError:
                        print(f"🔨 Forzando cierre de {name} Server...")
                        process.kill()
                        await process.wait()
                        
                except Exception as e:
                    print(f"❌ Error deteniendo {name}: {e}")

# -------------------- Demo Híbrido --------------------
async def demo():
    client = MCPClient()
    
    try:
        print("=== PASO 1: Iniciar Filesystem Server ===")
        fs_success = await client.start_fs_server()
        if not fs_success:
            print("❌ No se pudo iniciar filesystem server")
            return
        
        print("\n=== PASO 2: Crear Repositorio Git (nativo) ===")
        repo_path = client.allowed_dir
        git_created = client.create_git_repo_native(repo_path)
        if not git_created:
            print("❌ No se pudo crear el repositorio Git")
            return
        
        print("\n=== PASO 3: Crear archivo con MCP ===")
        readme_content = """# Demo Repo MCP

Este proyecto demuestra cómo usar MCP servers de forma híbrida:

## Tecnologías
- **MCP Filesystem Server**: Para operaciones de archivos
- **Git nativo**: Para inicialización del repo  
- **MCP Git Server**: Para operaciones avanzadas de Git

## Estado
✅ Funcionando correctamente!
"""
        
        file_result = await client.create_file("README.md", readme_content)
        if not file_result or "error" in file_result:
            print("❌ Error creando archivo")
            return
            
        print("\n=== PASO 4: Commit con Git nativo ===")
        commit_success = client.git_add_commit_native(
            repo_path, 
            [f"./{repo_path}/README.md"], 
            "Initial commit: Add README via MCP"
        )
        
        if not commit_success:
            print("❌ Error en commit")
            return
            
        print("\n=== PASO 5: Iniciar Git MCP Server ===")
        git_success = await client.start_git_server_after_repo(repo_path)
        if git_success:
            print("\n=== PASO 6: Operaciones con Git MCP ===")
            await client.git_status(repo_path)
            await client.git_log(repo_path)
        else:
            print("⚠️ Git MCP server no disponible, pero el repo funciona")
        
        print("\n🎉 ¡Demo completado exitosamente!")
        print(f"📁 Repositorio creado en: {Path(repo_path).resolve()}")
        
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
        
    finally:
        print(f"\n🧹 Limpiando recursos...")
        await client.stop_servers()

if __name__ == "__main__":
    print("🚀 Demo MCP Client - Enfoque Híbrido\n")
    asyncio.run(demo())