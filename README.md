# MCP Chatbot - Multi-Server AI Assistant

A chatbot system that integrates multiple Model Context Protocol (MCP) servers with both local (Ollama) and cloud-based (Anthropic Claude) language models. This project provides a unified interface for interacting with various specialized services including sleep coaching, beauty recommendations, video game information, file management, and more.

## ✨ Features

- **Dual LLM Support**: Choose between local privacy with Ollama or advanced capabilities with Anthropic Claude
- **Multiple MCP Servers**: Integrated support for 6+ specialized servers
- **Session Management**: Persistent conversation history with context management
- **Comprehensive Logging**: Detailed interaction tracking and performance monitoring
- **Remote Server Support**: Connect to both local and remote MCP servers
- **Command Interface**: Special commands for system management and debugging

## 🏗️ Architecture

```
src/chatbot/
├── clients/
│   ├── ollama_client.py          # Local LLM client (privacy-focused)
│   ├── anthropic_client.py       # Claude API client (cloud-based)
│   ├── connection.py             # Generic MCP server connection
│   └── remote_client.py          # Remote MCP server client
├── tools/
│   ├── session_manager.py        # Conversation history management
│   └── logger.py                 # Interaction logging and analytics
├── main.py                       # Ollama-based chatbot entry point
└── main_anthropic.py             # Claude-based chatbot entry point
```

## 🎯 Supported MCP Servers

| Server | Description | Type | Features |
|--------|-------------|------|----------|
| **Sleep Coach** | Sleep hygiene and wellness advice | Local | Personalized sleep recommendations |
| **Beauty Palette** | Beauty and cosmetic recommendations | Local | Color matching, product suggestions |
| **Video Games** | Game information and recommendations | Local | Game search, reviews, recommendations |
| **Movies** | Movie database and recommendations | Local | Film search, ratings, suggestions |
| **Git** | Version control operations | Local | Repository management, commits |
| **Filesystem** | File and directory operations | Local | File read/write, directory navigation |
| **Sleep Quotes** | Inspirational sleep-related content | Remote | Daily wisdom, bedtime reminders |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for filesystem server)
- Git
- **For Ollama**: [Ollama installation](https://ollama.com/)
- **For Claude**: Anthropic API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Fabiola-cc/mcp-chatbot.git
cd mcp-chatbot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configurations
# For Claude API (optional):
ANTHROPIC_API_KEY=your_api_key_here
```

### Option 1: Local Setup with Ollama (Recommended for Privacy)

4. **Install and configure Ollama**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Download a model (in another terminal)
ollama pull llama3.2:3b
```

5. **Run the chatbot**
```bash
cd src/chatbot
python main.py
```

### Option 2: Cloud Setup with Anthropic Claude

4. **Configure API key**
- Get your API key from [Anthropic Console](https://console.anthropic.com/)
- Add it to your `.env` file

5. **Run the chatbot**
```bash
cd src/chatbot
python main_anthropic.py
```

## 💬 Usage

### Basic Commands

Once the chatbot is running, you can:

- **Chat normally**: Ask questions, request recommendations, or seek advice
- **Use special commands**: Type commands starting with `/`

### Special Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/stats` | Display session statistics |
| `/log` | View interaction logs |
| `/context` | Display conversation context |
| `/clear` | Clear conversation history |
| `/save` | Save current session |
| `/quit` | Exit the chatbot |

### Example Interactions

```
💤 You: I need help with my sleep schedule

🤖 Chatbot: I can help you with sleep recommendations! Let me get some 
personalized advice for you.

💤 You: Show me a motivational quote about sleep

🤖 Chatbot: [Calls Sleep Quotes server]
🌙 INSPIRATIONAL SLEEP QUOTE 🌙

"Sleep is the best meditation that exists. Surrender to it with gratitude."
— Dalai Lama

💤 You: What games are trending right now?

🤖 Chatbot: [Calls Video Games server for latest trends]
```

## 🔧 Configuration

### Model Selection

**Ollama Models** (Local):
- `llama3.2:3b` - Lightweight, good performance
- `qwen2.5:3b` - Excellent for Spanish
- `codellama:7b` - Code-specialized

**Claude Models** (Cloud):
- `claude-3-5-haiku-20241022` - Fast, efficient
- `claude-3-5-sonnet-20241022` - Balanced performance
- `claude-3-opus-20240229` - Maximum capability

### Session Configuration

```python
# In session_manager.py
session = SessionManager(
    max_context_messages=20  # Adjust context window
)
```

### Logging Configuration

```python
# In logger.py
logger = InteractionLogger(
    log_dir="logs",
    log_level="INFO"  # DEBUG, INFO, WARNING, ERROR
)
```

## 🔌 Adding New MCP Servers

1. **Create server implementation** in `servidores locales mcp/`
2. **Add client connection** in `clients/`
3. **Register in main.py**:

```python
self.clients["your_server"] = Client()

await self.clients["your_server"].start_server(
    "your_server", 
    sys.executable,
    "path/to/your/server.py"
)
```

4. **Update LLM context** with server tools

## 📊 Monitoring and Analytics

The system provides comprehensive monitoring:

- **Session Statistics**: Message counts, duration, context usage
- **MCP Interactions**: Success rates, server usage, error tracking
- **Performance Metrics**: Response times, token usage
- **Detailed Logging**: Full interaction history with timestamps

## 🐛 Troubleshooting

### Common Issues

**Ollama Connection Failed**
```bash
# Ensure Ollama is running
ollama serve

# Check if model is available
ollama list
```

**Anthropic API Error**
```bash
# Verify API key in .env
echo $ANTHROPIC_API_KEY

# Check API key validity at console.anthropic.com
```

**MCP Server Startup Failed**
```bash
# Check server logs
tail -f logs/interactions.log

# Verify server dependencies
python servidores_locales_mcp/YourServer/server.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code structure and naming conventions
- Add comprehensive error handling
- Include logging for new features
- Test with both Ollama and Claude configurations
- Update documentation for new MCP servers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) for the standardization
- [Anthropic](https://www.anthropic.com/) for Claude API
- [Ollama](https://ollama.com/) for local LLM infrastructure
- All contributors to the MCP server ecosystem