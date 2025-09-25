# MCP Chatbot - Asistente de IA Multi-Servidor

Un sistema de chatbot que integra múltiples servidores del Protocolo de Contexto de Modelo (MCP) con modelos de lenguaje tanto locales (Ollama) como en la nube (Anthropic Claude). Este proyecto proporciona una interfaz unificada para interactuar con varios servicios especializados incluyendo coaching de sueño, recomendaciones de belleza, información de videojuegos, gestión de archivos y más.

## ✨ Características

- **Soporte Dual de LLM**: Elige entre privacidad local con Ollama o capacidades avanzadas con Anthropic Claude
- **Múltiples Servidores MCP**: Soporte integrado para 6+ servidores especializados
- **Gestión de Sesiones**: Historial de conversaciones persistente con gestión de contexto
- **Logging Integral**: Seguimiento detallado de interacciones y monitoreo de rendimiento
- **Soporte de Servidor Remoto**: Conecta a servidores MCP tanto locales como remotos
- **Interfaz de Comandos**: Comandos especiales para gestión del sistema y depuración

## 🏗️ Arquitectura

```
src/chatbot/
├── clients/
│   ├── ollama_client.py          # Cliente LLM local (enfocado en privacidad)
│   ├── anthropic_client.py       # Cliente API Claude (basado en nube)
│   ├── connection.py             # Conexión genérica servidor MCP
│   └── remote_client.py          # Cliente servidor MCP remoto
├── tools/
│   ├── session_manager.py        # Gestión historial conversaciones
│   └── logger.py                 # Logging interacciones y analíticas
├── main.py                       # Punto entrada chatbot basado en Ollama
└── main_anthropic.py             # Punto entrada chatbot basado en Claude
```

## 🎯 Servidores MCP Soportados

| Servidor | Descripción | Tipo | Características |
|----------|-------------|------|-----------------|
| **Sleep Coach** | Consejos higiene sueño y bienestar | Local | Recomendaciones personalizadas de sueño |
| **Beauty Palette** | Recomendaciones belleza y cosméticos | Local | Combinación colores, sugerencias productos |
| **Video Games** | Información y recomendaciones juegos | Local | Búsqueda juegos, reseñas, recomendaciones |
| **Movies** | Base datos películas y recomendaciones | Local | Búsqueda films, calificaciones, sugerencias |
| **Git** | Operaciones control de versiones | Local | Gestión repositorios, commits |
| **Filesystem** | Operaciones archivos y directorios | Local | Lectura/escritura archivos, navegación |
| **Sleep Quotes** | Contenido inspiracional relacionado sueño | Remoto | Sabiduría diaria, recordatorios dormir |

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.8+
- Node.js (para servidor filesystem)
- Git
- **Para Ollama**: [Instalación Ollama](https://ollama.com/)
- **Para Claude**: Clave API Anthropic

### Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/Fabiola-cc/mcp-chatbot.git
cd mcp-chatbot
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
# Copiar plantilla entorno
cp .env.example .env

# Editar archivo .env con tus configuraciones
# Para API Claude (opcional):
ANTHROPIC_API_KEY=tu_clave_api_aquí
```

### Opción 1: Configuración Local con Ollama (Recomendado para Privacidad)

4. **Instalar y configurar Ollama**
```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Iniciar servicio Ollama
ollama serve

# Descargar un modelo (en otra terminal)
ollama pull llama3.2:3b
```

5. **Ejecutar el chatbot**
```bash
cd src/chatbot
python main.py
```

### Opción 2: Configuración Nube con Anthropic Claude

4. **Configurar clave API**
- Obtén tu clave API desde [Consola Anthropic](https://console.anthropic.com/)
- Agrégala a tu archivo `.env`

5. **Ejecutar el chatbot**
```bash
cd src/chatbot
python main_anthropic.py
```

## 💬 Uso

### Comandos Básicos

Una vez que el chatbot esté ejecutándose, puedes:

- **Chatear normalmente**: Hacer preguntas, solicitar recomendaciones, o buscar consejos
- **Usar comandos especiales**: Escribir comandos que inicien con `/`

### Comandos Especiales

| Comando | Descripción |
|---------|-------------|
| `/help` | Mostrar comandos disponibles |
| `/stats` | Mostrar estadísticas de sesión |
| `/log` | Ver logs de interacciones |
| `/context` | Mostrar contexto conversación |
| `/clear` | Limpiar historial conversación |
| `/save` | Guardar sesión actual |
| `/quit` | Salir del chatbot |

### Ejemplos de Interacciones

```
💤 Tú: Necesito ayuda con mi horario de sueño

🤖 Chatbot: ¡Puedo ayudarte con recomendaciones de sueño! Permíteme obtener
algunos consejos personalizados para ti.

💤 Tú: Muéstrame una cita motivacional sobre el sueño

🤖 Chatbot: [Llama al servidor Sleep Quotes]
🌙 CITA INSPIRACIONAL PARA DORMIR 🌙

"El sueño es la mejor meditación que existe. Entrégate a él con gratitud."
— Dalai Lama

💤 Tú: ¿Qué juegos están en tendencia ahora?

🤖 Chatbot: [Llama al servidor Video Games para tendencias actuales]
```

## 🔧 Configuración

### Selección de Modelo

**Modelos Ollama** (Local):
- `llama3.2:3b` - Ligero, buen rendimiento
- `qwen2.5:3b` - Excelente para español
- `codellama:7b` - Especializado en código

**Modelos Claude** (Nube):
- `claude-3-5-haiku-20241022` - Rápido, eficiente
- `claude-3-5-sonnet-20241022` - Rendimiento equilibrado
- `claude-3-opus-20240229` - Máxima capacidad

### Configuración Sesión

```python
# En session_manager.py
session = SessionManager(
    max_context_messages=20  # Ajustar ventana contexto
)
```

### Configuración Logging

```python
# En logger.py
logger = InteractionLogger(
    log_dir="logs",
    log_level="INFO"  # DEBUG, INFO, WARNING, ERROR
)
```

## 🔌 Agregar Nuevos Servidores MCP

1. **Crear implementación servidor** en `servidores locales mcp/`
2. **Agregar conexión cliente** en `clients/`
3. **Registrar en main.py**:

```python
self.clients["tu_servidor"] = Client()

await self.clients["tu_servidor"].start_server(
    "tu_servidor", 
    sys.executable,
    "ruta/a/tu/servidor.py"
)
```

4. **Actualizar contexto LLM** con herramientas servidor

## 📊 Monitoreo y Analíticas

El sistema proporciona monitoreo integral:

- **Estadísticas Sesión**: Conteos mensajes, duración, uso contexto
- **Interacciones MCP**: Tasas éxito, uso servidores, seguimiento errores
- **Métricas Rendimiento**: Tiempos respuesta, uso tokens
- **Logging Detallado**: Historial completo interacciones con timestamps

## 🐛 Solución de Problemas

### Problemas Comunes

**Falló Conexión Ollama**
```bash
# Asegurar que Ollama esté ejecutándose
ollama serve

# Verificar si modelo está disponible
ollama list
```

**Error API Anthropic**
```bash
# Verificar clave API en .env
echo $ANTHROPIC_API_KEY

# Verificar validez clave API en console.anthropic.com
```

**Falló Inicio Servidor MCP**
```bash
# Verificar logs servidor
tail -f logs/interactions.log

# Verificar dependencias servidor
python servidores_locales_mcp/TuServidor/server.py
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama característica (`git checkout -b feature/característica-increíble`)
3. Commit tus cambios (`git commit -m 'Agregar característica increíble'`)
4. Push a la rama (`git push origin feature/característica-increíble`)
5. Abrir Pull Request

### Guías Desarrollo

- Seguir estructura código existente y convenciones nomenclatura
- Agregar manejo errores integral
- Incluir logging para nuevas características
- Probar con configuraciones Ollama y Claude
- Actualizar documentación para nuevos servidores MCP

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 🙏 Reconocimientos

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) por la estandarización
- [Anthropic](https://www.anthropic.com/) por API Claude
- [Ollama](https://ollama.com/) por infraestructura LLM local
- Todos los contribuidores al ecosistema servidor MCP