# AI-Powered IPC System Setup Guide

## 🚀 Quick Start

### 1. Install Ollama (Recommended for Local AI)

```bash
# Windows
winget install Ollama.Ollama

# Or download from
https://ollama.com/download/windows

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Start Ollama Service

```bash
# Start Ollama server
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### 3. Download AI Models

```bash
# Small & Fast (3GB)
ollama pull llama3.2

# Better quality (7GB)
ollama pull llama3.2:7b

# Code specialized
ollama pull codellama

# Multilingual (supports Korean)
ollama pull mistral
```

### 4. Start AI-Powered IPC System

```bash
# Run the batch file
D:\claude-ipc-mcp\start_ai_ipc_system.bat

# Or manually
python ai_powered_responder.py gemini llama3.2
```

## 🎯 Configuration Options

### Using Ollama (Local - No API Key Required)

```python
# Default configuration in ai_powered_responder.py
OLLAMA_API_URL = "http://localhost:11434"

# Start with specific model
python ai_powered_responder.py gemini llama3.2
python ai_powered_responder.py claude mistral
```

### Using Google Gemini API

```bash
# Set API key
set GEMINI_API_KEY=your-api-key-here

# Install SDK
pip install google-generativeai

# Run
python ai_powered_responder.py gemini
```

### Using OpenAI API

```bash
# Set API key
set OPENAI_API_KEY=your-api-key-here

# Install SDK
pip install openai

# Run
python ai_powered_responder.py claude
```

## 🤖 Instance Personas

Each instance has a specific AI persona:

- **Claude**: Intelligent assistant focused on coordination and analysis
- **Gemini**: Multi-modal AI specializing in creative thinking
- **Codex**: Code specialist for programming tasks
- **LM**: Language model expert in documentation

## 📊 Model Recommendations

### For General Chat
- `llama3.2` - Fast, good general responses
- `mistral` - Excellent multilingual support

### For Code Tasks
- `codellama` - Specialized for code
- `deepseek-coder` - Advanced code understanding

### For Korean Support
- `mistral` - Good Korean understanding
- `solar` - Korean-optimized model

## 🧪 Testing AI Responses

### Send Test Message

```python
# Send a message to test AI response
python tools/ipc_send.py claude gemini "안녕하세요! 프로젝트 파일 리스트를 알려주세요."

# Check response
python tools/ipc_check.py claude
```

### Monitor Real-time

```bash
# Start monitoring
python tools/monitor_instance.py claude
```

## 🔧 Troubleshooting

### Ollama Not Working

```bash
# Check if Ollama is installed
ollama --version

# Check if service is running
curl http://localhost:11434

# Restart Ollama
ollama serve

# Check logs
ollama logs
```

### Slow Responses

1. Use smaller models (3B instead of 7B)
2. Reduce max_tokens in configuration
3. Check system resources (RAM usage)

### No AI Response

1. Check if Ollama is running
2. Verify model is downloaded
3. Check API keys if using cloud services
4. Look for error messages in console

## 📈 Performance Tips

### Optimal Setup

```bash
# 1. Use local Ollama for privacy & speed
ollama pull llama3.2:3b

# 2. Pre-load models
ollama run llama3.2 "test"

# 3. Keep Ollama running
ollama serve &
```

### Resource Management

- **Minimum RAM**: 8GB for 3B models
- **Recommended RAM**: 16GB for 7B models
- **GPU**: Optional but 10x faster with NVIDIA GPU

## 🎨 Advanced Configuration

### Custom Personas

Edit `ai_powered_responder.py`:

```python
self.personas = {
    'gemini': "You are Gemini, an expert in analyzing code and providing detailed project information...",
    'custom': "Your custom persona here..."
}
```

### Model Selection by Instance

```python
# Different models for different instances
model_map = {
    'claude': 'llama3.2:7b',    # Larger model for coordinator
    'gemini': 'mistral',         # Multilingual for Gemini
    'codex': 'codellama',        # Code-specific for Codex
    'lm': 'llama3.2:3b'          # Smaller model for documentation
}
```

## 🌐 Multi-Instance Communication

### Example Conversation Flow

1. Claude sends complex question to Gemini
2. Gemini uses AI to understand and analyze
3. Gemini sends intelligent response back
4. All instances maintain conversation context

### Test Multi-Instance AI Chat

```python
# Start all AI responders
start_ai_ipc_system.bat

# Send messages between instances
python tools/ipc_send.py claude gemini "What files are in the project?"
python tools/ipc_send.py gemini codex "Can you help optimize this code?"
python tools/ipc_send.py codex lm "Please document this function"
```

## 📚 Additional Resources

- [Ollama Models](https://ollama.com/library)
- [Gemini API Docs](https://ai.google.dev/)
- [OpenAI API Docs](https://platform.openai.com/docs)