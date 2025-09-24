# MCP Chatbot - Model Context Protocol Local Chatbot

A powerful and privacy-focused chatbot system that combines local language models (via Ollama) with the Model Context Protocol (MCP) for enhanced functionality. This project demonstrates how to build a comprehensive AI assistant that runs entirely on your local machine while providing advanced features through MCP servers.

## 🌟 Features

### Core Functionality
- **100% Local & Private**: Uses Ollama for local language model inference
- **MCP Integration**: Extensible architecture using Model Context Protocol
- **Session Management**: Maintains conversation context and history
- **Comprehensive Logging**: Tracks all interactions and MCP operations
- **Command System**: Special commands for enhanced functionality

### Specialized MCP Servers
- **Sleep Coach**: Personalized sleep routine recommendations
- **File System**: File creation and management
- **Git Integration**: Basic git operations
- **External Services**: Beauty palette generator, movie recommendations, quotes

### Other Features
- **Context Management**: Smart conversation context handling
- **Error Recovery**: Robust error handling and recovery mechanisms
- **Statistics Tracking**: Detailed usage statistics and analytics
- **Session Persistence**: Save and restore conversation sessions

## 🏗️ Architecture

```
mcp-chatbot/
├── main.py                    # Main chatbot application
├── clients/
│   |── ollama_client.py       # Ollama local model client
│   |── kitchen_client.py      # Client for Kitchen Coach server
│   |── movies_client.py       # Client for Movies Recomendation server
│   |── remote_client.py       # Client for remote server (Sleep Quotes)
│   └── sleep_coach_client.py  # Client for Sleep Coach server
├── tools/
│   ├── session_manager.py     # Conversation context management
│   ├── logger.py              # Interaction logging system
│   └── command_handler.py     # Special command processing
├── mcp_oficial/
│   └── git_file_client.py      # File system and Git operations
```

## 🚀 Installation

### Prerequisites

1. **Python 3.8+**
2. **Ollama** (for local language models)

### Step 1: Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Download a model (in another terminal)
ollama pull llama3.2:3b
```

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Fabiola-cc/mcp-chatbot.git
cd mcp-chatbot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file (optional)
cp .env.example .env
```

### Step 3: Verify Installation

```bash
# Test Ollama connection
python src/chatbot/clients/ollama_client.py

# Test MCP servers
python mcp_servers/sleep_coach.py
```

## 🎯 Usage

### Basic Chatbot

```bash
# Start the chatbot
python src/chatbot/main.py
```

### Available Commands

#### General Commands
- `/help` - Show all available commands
- `/quit` - Exit the chatbot
- `/clear` - Clear conversation context
- `/stats` - Show session statistics
- `/context` - Show conversation summary
- `/save` - Save current session
- `/log` - Show interaction logs
- `/mcp` - Show MCP server interactions

#### File System Operations
```bash
/fs create filename.txt "File content here"
```

#### Git Operations
```bash
/git init                    # Initialize git repository
/git add                     # Add files to staging
/git commit "Commit message" # Commit changes
```

#### Sleep Coach
```bash
/sleep help                  # Show Sleep Coach help
/sleep profile               # Create sleep profile
/sleep analyze               # Analyze sleep patterns
/sleep recommendations       # Get personalized recommendations
/sleep schedule              # Create weekly sleep schedule
```

### Example Conversation

```
👤 You: Hello, I need help improving my sleep quality

🤖 Chatbot: I'd be happy to help you improve your sleep quality! I have a specialized Sleep Coach that can provide personalized recommendations. 

You can use:
- `/sleep profile` to create a detailed sleep profile
- `/sleep help` to see all sleep-related commands
- Or just tell me about your current sleep patterns and I'll provide general advice

What specific sleep issues are you experiencing?

👤 You: /sleep profile

🤖 Chatbot: Creating your sleep profile! Please provide the following information:
- Name: 
- Age:
- Current bedtime:
- Current wake time:
- Sleep goals:
...
```

## 🔧 Configuration

### Ollama Configuration

The chatbot automatically detects available Ollama models. You can specify a different model in the `OllamaClient` initialization:

```python
# In src/chatbot/clients/ollama_client.py
client = OllamaClient(model_name="llama3.2:3b")  # or any installed model
```

### Logging Configuration

Customize logging in `src/chatbot/tools/logger.py`:

```python
logger = InteractionLogger(
    log_dir="logs",        # Log directory
    log_level="INFO"       # Log level
)
```

### Session Management

Configure context size in `src/chatbot/tools/session_manager.py`:

```python
session = SessionManager(
    max_context_messages=20  # Maximum messages in context
)
```

## 🏥 Sleep Coach MCP Server

The Sleep Coach is a specialized MCP server that provides personalized sleep recommendations based on chronotypes, sleep science, and individual patterns.

- you can access this server in this repository: [https://github.com/Fabiola-cc/SleepCoachServer](https://github.com/Fabiola-cc/SleepCoachServer)

### Features

- **Chronotype Analysis**: Morning lark, night owl, or intermediate
- **Personalized Recommendations**: Based on age, goals, and current patterns
- **Weekly Schedule Creation**: Optimized sleep/wake times
- **Sleep Hygiene Guidelines**: Evidence-based recommendations
- **Progress Tracking**: Monitor improvements over time

### Sleep Coach Tools

1. **create_user_profile**: Create detailed user profile with sleep habits
2. **analyze_sleep_pattern**: Analyze current sleep patterns and identify issues
3. **get_personalized_recommendations**: Generate personalized recommendations
4. **create_weekly_schedule**: Create optimized weekly sleep schedule
5. **quick_sleep_advice**: Get quick advice for specific sleep issues

### Example Usage

```python
# Create user profile
profile_data = {
    "user_id": "user123",
    "name": "John Doe",
    "age": 30,
    "chronotype": "night_owl",
    "current_bedtime": "23:30",
    "current_wake_time": "07:00",
    "sleep_duration_hours": 7.5,
    "goals": ["better_quality", "more_energy"]
}

# Get analysis and recommendations
analysis = sleep_coach.analyze_sleep_pattern("user123")
recommendations = sleep_coach.get_personalized_recommendations("user123")
```

## 🔌 MCP Server Development

### Creating New MCP Servers

1. **Define Tools**: Specify available functions and their schemas
2. **Implement Handlers**: Create async handlers for each tool
3. **Add to Main**: Register the server in the main application

Example MCP server structure:

```python
import asyncio
import mcp.types as types
from mcp.server import Server

app = Server("my-server")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="my_tool",
            description="My custom tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "my_tool":
        return [types.TextContent(
            type="text", 
            text=f"Processing: {arguments['input']}"
        )]
```

## 🔍 Monitoring and Debugging

### Logs Location

- **Main Log**: `logs/interactions.log`
- **MCP Interactions**: `logs/mcp_interactions.json`
- **Session Files**: `session_YYYYMMDD_HHMMSS.json`

### Debug Mode

Enable debug mode by setting the log level:

```python
logger = InteractionLogger(log_level="DEBUG")
```

### Performance Monitoring

- Response times are automatically tracked
- Token usage estimation for local models
- MCP server success rates and error tracking

## 🛠️ Development

### Project Structure

```
├── src/chatbot/           # Main chatbot application
├── clients/              # MCP client implementations
├── logs/                # Log files (auto-created)
├── workspace/           # Git operations workspace
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Adding New Features

1. **New Commands**: Add to `CommandHandler` class
2. **New MCP Servers**: Create in `mcp_servers/` directory
3. **New Clients**: Add to `clients/` directory
4. **New Tools**: Extend existing MCP servers

### Testing

```bash
# Test individual components
python src/chatbot/clients/ollama_client.py
python mcp_servers/sleep_coach.py
python clients/sleep_coach_client.py

# Test full integration
python src/chatbot/main.py
```

## 📊 Performance

### Local Model Performance

- **Llama 3.2 3B**: Fast responses, good for general chat
- **CodeLlama 7B**: Better for code-related tasks
- **Qwen2.5 3B**: Excellent multilingual support

### Optimization Tips

1. **Use smaller models** for faster responses
2. **Limit context size** to reduce processing time
3. **Enable GPU acceleration** if available with Ollama
4. **Monitor memory usage** with larger models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Test thoroughly
5. Submit a pull request

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add comprehensive error handling
- Include type hints where possible
- Document new MCP servers and tools
- Test with multiple Ollama models

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🔗 Related Projects

- [Ollama](https://ollama.com/) - Local language model runtime
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [Anthropic MCP](https://github.com/anthropics/mcp) - MCP implementations

## 🆘 Support

### Common Issues

**Ollama Connection Failed**
```bash
# Make sure Ollama is running
ollama serve

# Check if models are available
ollama list

# Download a model if needed
ollama pull llama3.2:3b
```

**MCP Server Not Starting**
- Check Python dependencies are installed
- Verify server file permissions
- Check logs for detailed error messages

**Memory Issues**
- Use smaller models (3B instead of 7B+)
- Reduce context window size
- Monitor system resources

### Getting Help

- Check the logs: `/log` and `/mcp` commands
- Review error messages in console output
- Test individual components separately
- Open an issue on GitHub with detailed information

## 🎯 Roadmap

- [ ] Web interface for the chatbot
- [ ] Additional MCP servers (calendar, email, etc.)
- [ ] Multi-model support
- [ ] Voice interface integration
- [ ] Docker containerization
- [ ] Advanced sleep tracking integration
- [ ] Plugin system for easy extensions

---

**Built with ❤️ using Local AI and MCP**