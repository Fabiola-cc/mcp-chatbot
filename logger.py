# src/chatbot/logger.py
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class InteractionLogger:
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Inicializa el sistema de logging para interacciones MCP
        
        Args:
            log_dir: Directorio donde guardar los logs
            log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Archivo principal de log
        self.log_file = self.log_dir / "interactions.log"
        
        # Archivo específico para MCP
        self.mcp_log_file = self.log_dir / "mcp_interactions.json"
        
        # Configurar logging principal
        self._setup_logging(log_level)
        
        # Lista para almacenar interacciones MCP en memoria
        self.mcp_interactions = []
        
        # Cargar interacciones MCP existentes
        self._load_mcp_interactions()
    
    def _setup_logging(self, log_level: str) -> None:
        """Configura el sistema de logging"""
        
        # Crear formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configurar logger principal
        self.logger = logging.getLogger('MCPChatbot')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Handler para archivo
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Handler para consola (solo WARNING y ERROR)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        
        # Limpiar handlers existentes y agregar nuevos
        self.logger.handlers = []
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_user_input(self, message: str, session_id: str = None) -> None:
        """Registra entrada del usuario"""
        self.logger.info(f"USER_INPUT | Session: {session_id} | Message: {message}")
    
    def log_anthropic_response(self, response: str, tokens_used: int = None, session_id: str = None) -> None:
        """Registra respuesta de Anthropic"""
        response_preview = response[:200] + "..." if len(response) > 200 else response
        token_info = f" | Tokens: {tokens_used}" if tokens_used else ""
        self.logger.info(f"ANTHROPIC_RESPONSE | Session: {session_id}{token_info} | Response: {response_preview}")
    
    def log_mcp_interaction(self, server_name: str, action: str, parameters: Dict = None, 
                           result: Any = None, success: bool = True, error: str = None) -> None:
        """
        Registra interacciones con servidores MCP
        
        Args:
            server_name: Nombre del servidor MCP
            action: Acción realizada
            parameters: Parámetros enviados
            result: Resultado obtenido
            success: Si la operación fue exitosa
            error: Mensaje de error si falló
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'server': server_name,
            'action': action,
            'parameters': parameters or {},
            'success': success,
            'result': self._sanitize_result(result) if success else None,
            'error': error if not success else None
        }
        
        # Agregar a la lista en memoria
        self.mcp_interactions.append(interaction)
        
        # Guardar en archivo JSON
        self._save_mcp_interactions()
        
        # Log en archivo principal
        status = "SUCCESS" if success else "ERROR"
        log_msg = f"MCP_INTERACTION | {status} | Server: {server_name} | Action: {action}"
        
        if success:
            self.logger.info(log_msg + f" | Result: {str(result)[:100]}...")
        else:
            self.logger.error(log_msg + f" | Error: {error}")
    
    def _sanitize_result(self, result: Any) -> Any:
        """Sanitiza el resultado para evitar logs muy largos"""
        if isinstance(result, str) and len(result) > 1000:
            return result[:1000] + f"... [truncado, {len(result)} caracteres totales]"
        elif isinstance(result, (list, dict)):
            result_str = json.dumps(result, indent=2)
            if len(result_str) > 1000:
                return f"[Objeto grande truncado: {type(result).__name__} con {len(result)} elementos]"
        return result
    
    def _load_mcp_interactions(self) -> None:
        """Carga interacciones MCP existentes desde archivo"""
        try:
            if self.mcp_log_file.exists():
                with open(self.mcp_log_file, 'r', encoding='utf-8') as f:
                    self.mcp_interactions = json.load(f)
        except Exception as e:
            self.logger.warning(f"No se pudieron cargar interacciones MCP previas: {e}")
            self.mcp_interactions = []
    
    def _save_mcp_interactions(self) -> None:
        """Guarda interacciones MCP en archivo JSON"""
        try:
            with open(self.mcp_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.mcp_interactions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando interacciones MCP: {e}")
    
    def show_interaction_log(self, lines: int = 50) -> None:
        """
        Muestra las últimas líneas del log de interacciones
        
        Args:
            lines: Número de líneas a mostrar
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
            print(f"\n{'='*60}")
            print(f"📄 LOG DE INTERACCIONES (últimas {lines} líneas)")
            print(f"{'='*60}")
            
            for line in all_lines[-lines:]:
                print(line.rstrip())
                
            print(f"{'='*60}\n")
            
        except FileNotFoundError:
            print("📭 No hay log de interacciones disponible aún.")
    
    def show_mcp_interactions(self, server_filter: str = None, limit: int = 20) -> None:
        """
        Muestra interacciones MCP recientes
        
        Args:
            server_filter: Filtrar por servidor específico
            limit: Número máximo de interacciones a mostrar
        """
        interactions = self.mcp_interactions
        
        # Filtrar por servidor si se especifica
        if server_filter:
            interactions = [i for i in interactions if i['server'] == server_filter]
        
        # Tomar las más recientes
        recent_interactions = interactions[-limit:]
        
        print(f"\n{'='*60}")
        print(f"🔧 INTERACCIONES MCP (últimas {len(recent_interactions)})")
        if server_filter:
            print(f"📡 Servidor: {server_filter}")
        print(f"{'='*60}")
        
        for interaction in recent_interactions:
            timestamp = datetime.fromisoformat(interaction['timestamp'])
            status_icon = "✅" if interaction['success'] else "❌"
            
            print(f"\n{status_icon} {timestamp.strftime('%H:%M:%S')} | {interaction['server']} | {interaction['action']}")
            
            if interaction['parameters']:
                print(f"   📥 Parámetros: {json.dumps(interaction['parameters'], indent=6)}")
            
            if interaction['success'] and interaction['result']:
                result_str = str(interaction['result'])[:200]
                print(f"   📤 Resultado: {result_str}...")
            elif not interaction['success']:
                print(f"   ❌ Error: {interaction['error']}")
        
        print(f"{'='*60}\n")
    
    def get_mcp_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso de servidores MCP"""
        if not self.mcp_interactions:
            return {"total_interactions": 0, "servers_used": [], "success_rate": 0}
        
        total = len(self.mcp_interactions)
        successful = len([i for i in self.mcp_interactions if i['success']])
        servers = list(set(i['server'] for i in self.mcp_interactions))
        
        # Conteo por servidor
        server_counts = {}
        for interaction in self.mcp_interactions:
            server = interaction['server']
            server_counts[server] = server_counts.get(server, 0) + 1
        
        return {
            "total_interactions": total,
            "successful_interactions": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "servers_used": servers,
            "interactions_per_server": server_counts,
            "most_used_server": max(server_counts.items(), key=lambda x: x[1])[0] if server_counts else None
        }


# Test del sistema de logging
if __name__ == "__main__":
    logger = InteractionLogger()
    
    print("🧪 Probando sistema de logging...")
    
    # Simular interacciones
    logger.log_user_input("Crea un archivo README.md", "session_123")
    logger.log_mcp_interaction(
        server_name="filesystem",
        action="write_file",
        parameters={"filepath": "README.md", "content": "# Mi Proyecto"},
        result="Archivo creado exitosamente"
    )
    logger.log_anthropic_response("He creado el archivo README.md con el contenido solicitado", 45, "session_123")
    
    # Simular error MCP
    logger.log_mcp_interaction(
        server_name="git",
        action="commit",
        parameters={"message": "Initial commit"},
        success=False,
        error="No hay cambios para hacer commit"
    )
    
    # Mostrar estadísticas
    print(f"\n📊 Estadísticas MCP: {logger.get_mcp_stats()}")
    
    # Mostrar logs
    logger.show_interaction_log(10)
    logger.show_mcp_interactions()