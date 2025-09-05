# Sleep Coach MCP Server 💤

Un servidor MCP (Model Context Protocol) especializado en análisis y recomendaciones de sueño, construido en Python. Este servidor puede ser integrado con cualquier chatbot o aplicación que soporte el protocolo MCP.

## 🌟 Características

- **Análisis de rutinas de sueño**: Analiza patrones de sueño y detecta problemas
- **Recomendaciones personalizadas**: Proporciona consejos basados en datos específicos
- **Protocolo MCP estándar**: Compatible con cualquier cliente MCP
- **Multiplataforma**: Funciona en Windows, macOS y Linux
- **Fácil integración**: Se puede conectar desde cualquier lenguaje de programación

## 🔧 Herramientas Disponibles

### `get_sleep_recommendations`
Obtiene recomendaciones personalizadas de sueño basadas en datos del usuario.

**Parámetros:**
- `sleep_data` (string): Descripción de la rutina de sueño actual

**Ejemplo de uso:**
```json
{
  "sleep_data": "Duermo 5 horas por noche, me despierto cansado a las 6am"
}
```

### `analyze_sleep_pattern`
Analiza patrones de sueño a lo largo del tiempo.

**Parámetros:**
- `sleep_log` (string): Log de horarios de sueño

**Ejemplo de uso:**
```json
{
  "sleep_log": "Lunes: 11pm-5am, Martes: 12am-6am, Miércoles: 1am-6am"
}
```

## 📋 Requisitos

- Python 3.8+
- Dependencias: `asyncio`, `json`, `sys` (incluidas en Python estándar)

## 🚀 Instalación

### Opción 1: Descarga Directa
```bash
# Descargar el servidor
curl -O https://github.com/Fabiola-cc/mcp-chatbot/chatbot/mcp_servers/sleep_coach.py
```

### Opción 2: Clonar Repositorio
```bash
git clone https://github.com/Fabiola-cc/mcp-chatbot
cd chatbot/mcp_servers
```

## 🔌 Uso

### Ejecutar el Servidor

```bash
python sleep_coach.py
```

### Protocolo de Comunicación

El servidor implementa el protocolo MCP 2024-11-05. Aquí está la secuencia básica:

#### 1. Inicialización
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {"listChanged": true},
      "sampling": {}
    },
    "clientInfo": {
      "name": "tu-cliente",
      "version": "1.0.0"
    }
  }
}
```

#### 2. Notificación de Inicializado
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized",
  "params": {}
}
```

#### 3. Listar Herramientas
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

#### 4. Llamar Herramienta
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_sleep_recommendations",
    "arguments": {
      "sleep_data": "Duermo 5 horas, me despierto cansado"
    }
  }
}
```

## 💻 Ejemplos de Integración

### Python (Asyncio)
Puedes ver mi implementación en este repositorio.
- Utilicé un cliente para conectarme 'chatbot/sleep_coach_client.py'

### Node.js
```javascript
const { spawn } = require('child_process');
const readline = require('readline');

class SleepCoachClient {
    constructor() {
        this.server = null;
        this.rl = null;
        this.requestId = 1;
    }
    
    async start() {
        this.server = spawn('python', ['sleep_coach.py']);
        this.rl = readline.createInterface({
            input: this.server.stdout,
            output: process.stdout,
            terminal: false
        });
        
        // Inicializar
        const initMsg = {
            jsonrpc: "2.0",
            id: this.requestId++,
            method: "initialize",
            params: {
                protocolVersion: "2024-11-05",
                capabilities: { roots: { listChanged: true } },
                clientInfo: { name: "node-client", version: "1.0.0" }
            }
        };
        
        this.server.stdin.write(JSON.stringify(initMsg) + '\n');
        
        return new Promise((resolve) => {
            this.rl.once('line', (line) => {
                console.log('Inicializado:', JSON.parse(line));
                resolve();
            });
        });
    }
    
    async getSleepRecommendations(sleepData) {
        const msg = {
            jsonrpc: "2.0",
            id: this.requestId++,
            method: "tools/call",
            params: {
                name: "get_sleep_recommendations",
                arguments: { sleep_data: sleepData }
            }
        };
        
        this.server.stdin.write(JSON.stringify(msg) + '\n');
        
        return new Promise((resolve) => {
            this.rl.once('line', (line) => {
                const response = JSON.parse(line);
                resolve(response.result.content[0].text);
            });
        });
    }
    
    stop() {
        if (this.server) {
            this.server.kill();
        }
    }
}

// Uso
(async () => {
    const client = new SleepCoachClient();
    await client.start();
    
    const recommendations = await client.getSleepRecommendations(
        "Duermo 4 horas por noche y bebo mucho café"
    );
    
    console.log('Recomendaciones:', recommendations);
    client.stop();
})();
```

### Bash/cURL (Para Testing)
```bash
#!/bin/bash

# Iniciar servidor en background
python sleep_coach.py &
SERVER_PID=$!

# Esperar que inicie
sleep 2

# Función para enviar mensajes MCP
send_mcp_message() {
    echo "$1" | nc localhost 8000  # Si tu servidor usa socket
}

# Inicializar
INIT_MSG='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"roots":{"listChanged":true}},"clientInfo":{"name":"bash-client","version":"1.0.0"}}}'

# Llamar herramienta
TOOL_MSG='{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_sleep_recommendations","arguments":{"sleep_data":"Duermo muy poco"}}}'

# Limpiar al salir
trap "kill $SERVER_PID" EXIT
```

## 🛠️ Personalización

### Modificar Recomendaciones
Para personalizar las recomendaciones, edita el archivo `sleep_coach.py`:

```python
# Busca esta función y modifica las recomendaciones
async def get_sleep_recommendations(self, arguments: Dict) -> List[Dict]:
    # Agregar tus propias reglas aquí
    custom_recommendations = [
        "Tu recomendación personalizada aquí",
        # ...
    ]
```

### Agregar Nuevas Herramientas
```python
# En la clase SleepCoachServer, agregar nueva herramienta
@tool_handler("nueva_herramienta")
async def nueva_herramienta(self, arguments: Dict) -> List[Dict]:
    # Tu lógica aquí
    return [{"type": "text", "text": "Resultado de la nueva herramienta"}]

# Registrar en list_tools
def get_available_tools(self) -> List[Dict]:
    return [
        # ... herramientas existentes ...
        {
            "name": "nueva_herramienta",
            "description": "Descripción de la nueva herramienta",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "parametro": {"type": "string", "description": "Descripción del parámetro"}
                },
                "required": ["parametro"]
            }
        }
    ]
```

## 🐛 Solución de Problemas

### Problema: "Conexión rechazada"
**Solución:** 
1. Verificar que Python 3.8+ esté instalado
2. Ejecutar el servidor en una terminal separada
3. Verificar que no hay otros procesos usando el mismo puerto

### Problema: "Timeout en respuestas"
**Solución:** El servidor puede tardar en procesar análisis complejos. Aumentar el timeout en tu cliente.

### Problema: "Herramientas no encontradas"
**Solución:** Asegurarse de enviar el mensaje `initialize` antes de usar `tools/list` o `tools/call`.

## 📝 Logs y Debugging

### Activar Logs Detallados
Agregar al inicio de `sleep_coach.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verificar Comunicación
```python
# En tu cliente, agregar logging
import json

def log_message(direction, message):
    print(f"{direction}: {json.dumps(message, indent=2)}")

# Antes de enviar
log_message("ENVIANDO", message)

# Después de recibir  
log_message("RECIBIDO", response)
```

## 🤝 Contribuir
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request