# src/chatbot/session_manager.py
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class SessionManager:
    def __init__(self, max_context_messages: int = 20):
        """
        Inicializa el gestor de sesiones
        
        Args:
            max_context_messages: Número máximo de mensajes a mantener en contexto
        """
        self.conversation_history = []
        self.max_context_messages = max_context_messages
        self.session_start = datetime.now()
        self.message_count = 0
        
    def add_message(self, role: str, content: str, metadata: Dict = None) -> None:
        """
        Agrega un mensaje al historial de conversación
        
        Args:
            role: 'user' o 'assistant'
            content: Contenido del mensaje
            metadata: Información adicional opcional (timestamp, tokens, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "message_id": self.message_count
        }
        
        if metadata:
            message.update(metadata)
        
        self.conversation_history.append(message)
        self.message_count += 1
        
        # Mantener solo los últimos N mensajes para evitar exceder límites de tokens
        self._trim_context()
    
    def get_context(self) -> List[Dict]:
        """
        Retorna el contexto actual de la conversación en formato para Anthropic API
        
        Returns:
            Lista de mensajes en formato {role: str, content: str}
        """
        return [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in self.conversation_history
        ]
    
    def get_full_history(self) -> List[Dict]:
        """
        Retorna el historial completo con metadata
        
        Returns:
            Lista completa de mensajes con timestamps y metadata
        """
        return self.conversation_history.copy()
    
    def clear_context(self) -> None:
        """Limpia completamente el contexto de la conversación"""
        self.conversation_history = []
        self.message_count = 0
        print(f"🧹 Contexto limpiado. Sesión reiniciada.")
    
    def _trim_context(self) -> None:
        """Mantiene solo los últimos N mensajes para evitar exceder límites"""
        if len(self.conversation_history) > self.max_context_messages:
            removed_count = len(self.conversation_history) - self.max_context_messages
            self.conversation_history = self.conversation_history[-self.max_context_messages:]
            print(f"ℹ️  Se removieron {removed_count} mensajes antiguos del contexto")
    
    def get_session_stats(self) -> Dict:
        """
        Retorna estadísticas de la sesión actual
        
        Returns:
            Diccionario con estadísticas de la sesión
        """
        if not self.conversation_history:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "session_duration": "0 minutos",
                "messages_in_context": 0
            }
        
        user_msgs = len([msg for msg in self.conversation_history if msg["role"] == "user"])
        assistant_msgs = len([msg for msg in self.conversation_history if msg["role"] == "assistant"])
        
        duration = datetime.now() - self.session_start
        duration_minutes = duration.total_seconds() / 60
        
        return {
            "total_messages": self.message_count,
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
            "session_duration": f"{duration_minutes:.1f} minutos",
            "messages_in_context": len(self.conversation_history)
        }
    
    def save_session(self, filename: str = None) -> None:
        """
        Guarda la sesión actual en un archivo JSON
        
        Args:
            filename: Nombre del archivo. Si no se proporciona, se genera automáticamente
        """
        # Carpeta destino
        save_dir = "sessionsInfo"
        os.makedirs(save_dir, exist_ok=True)  # Crea la carpeta si no existe

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"
        
        filepath = os.path.join(save_dir, filename) # guardar en la carpeta

        session_data = {
            "session_info": {
                "start_time": self.session_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_messages": self.message_count,
                "stats": self.get_session_stats()
            },
            "conversation_history": self.conversation_history
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Sesión guardada en: {filepath}")
        except Exception as e:
            print(f"❌ Error guardando sesión: {str(e)}")
    
    def load_session(self, filename: str) -> bool:
        """
        Carga una sesión desde un archivo JSON
        
        Args:
            filename: Nombre del archivo a cargar
            
        Returns:
            True si se cargó exitosamente, False en caso contrario
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.conversation_history = session_data.get("conversation_history", [])
            self.message_count = session_data.get("session_info", {}).get("total_messages", 0)
            
            print(f"📂 Sesión cargada desde: {filename}")
            print(f"ℹ️  {len(self.conversation_history)} mensajes restaurados")
            return True
            
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {filename}")
            return False
        except json.JSONDecodeError:
            print(f"❌ Error leyendo archivo JSON: {filename}")
            return False
        except Exception as e:
            print(f"❌ Error cargando sesión: {str(e)}")
            return False

    def show_context_summary(self) -> None:
        """Muestra un resumen del contexto actual"""
        if not self.conversation_history:
            print("📭 No hay mensajes en el contexto actual")
            return
        
        print("\n📋 RESUMEN DEL CONTEXTO ACTUAL:")
        print("-" * 40)
        
        for i, msg in enumerate(self.conversation_history[-5:], 1):  # Últimos 5 mensajes
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            content_preview = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            print(f"{i}. {role_icon} {content_preview}")
        
        stats = self.get_session_stats()
        print(f"\n📊 Total: {stats['total_messages']} mensajes | En contexto: {stats['messages_in_context']}")


# Ejemplo de uso y testing
if __name__ == "__main__":
    # Test del gestor de sesiones
    session = SessionManager()
    
    print("🧪 Probando SessionManager...")
    
    # Simular conversación
    session.add_message("user", "Hola, soy Juan")
    session.add_message("assistant", "Hola Juan, ¿en qué puedo ayudarte?")
    session.add_message("user", "¿Recuerdas mi nombre?")
    session.add_message("assistant", "Sí, tu nombre es Juan")
    
    # Mostrar contexto
    print("\n📋 Contexto para API:")
    for msg in session.get_context():
        print(f"  {msg['role']}: {msg['content']}")
    
    # Mostrar estadísticas
    print(f"\n📊 Estadísticas: {session.get_session_stats()}")
    
    # Mostrar resumen
    session.show_context_summary()
    
    # Guardar sesión de prueba
    session.save_session("test_session.json")