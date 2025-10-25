# Codemni

<div align="center">

<img src="https://raw.githubusercontent.com/CodexJitin/Codemni/main/assets/codemni-logo.jpg" alt="Codemni Logo" width="400"/>

**🚀 The Complete AI Agent Framework for Python**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](https://github.com/CodexJitin/Codemni/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-CodexJitin%2FCodemni-181717?logo=github)](https://github.com/CodexJitin/Codemni)

*The most powerful framework for building autonomous AI agents - featuring intelligent tool execution, multi-LLM orchestration, and advanced conversational memory*

[Features](#-features) • [Installation](#-installation) • [Modules](#-modules) • [Quick Start](#-quick-start) • [Documentation](#-documentation)

</div>

---

## 📖 About

**Codemni** is a powerful Python framework for building production-ready AI agents and LLM applications. Unlike simple wrappers, Codemni provides a complete ecosystem with intelligent tool-calling agents, multi-provider LLM integrations, and sophisticated memory systems. Whether you're building chatbots, automation systems, or complex AI workflows, Codemni gives you the foundation to create robust, scalable solutions.

**Why Choose Codemni?**

- 🤖 **Complete Agent Framework**: Not just an LLM wrapper - build agents that can think, decide, and execute tools
- ✨ **Production-Ready**: Battle-tested with built-in error handling, retries, and intelligent fallbacks
- 🎯 **Multi-Provider Support**: Seamlessly switch between OpenAI, Google, Anthropic, Groq, and Ollama
- 🧠 **Advanced Memory**: 4 memory strategies to maintain context and conversation history
- 🔧 **Developer-Friendly**: Intuitive APIs, comprehensive documentation, and consistent interfaces
- 🚀 **Performance-Optimized**: Designed for speed, efficiency, and reliability at scale
- 🛡️ **Enterprise-Grade**: Robust error handling, logging, and production-ready code

---

## 🧩 Modules

### 🤖 [ToolCalling Agent](./TOOL_CALLING_AGENT/) - AI Agent Framework

Powerful and flexible AI agent framework that enables LLMs to intelligently select and execute tools.

**Key Features:**
- 🔧 Dynamic tool execution based on LLM decisions
- 💾 Optional conversation memory (4 different strategies)
- 🎨 Custom agent personality/role support
- 📊 Verbose mode for debugging
- 🔌 Multi-LLM support (OpenAI, Google Gemini, Anthropic, Groq, Ollama)
- ⚠️ Designed for standard models (reasoning models like o1, o3 not supported)

**[📚 Full Agent Documentation →](./TOOL_CALLING_AGENT/README.md)**

---

### 💾 [Memory Module](./memory/) - Conversation History Management

Flexible conversation memory system for maintaining context in multi-turn interactions.

**Available Memory Types:**
- 📝 **ConversationalBufferMemory** - Store all messages
- 🪟 **ConversationalWindowMemory** - Keep last N exchanges
- 🎫 **ConversationalTokenBufferMemory** - Limit by token count
- 📋 **ConversationalSummaryMemory** - Summarize old conversations

**Key Features:**
- Common API across all memory types
- Easy serialization (save/load)
- Lightweight and efficient
- Integrates seamlessly with ToolCalling Agent

**[📚 Full Memory Documentation →](./memory/README.md)**

---

### 📡 [LLM Module](./llm/) - Large Language Model Wrappers

Production-ready wrappers for popular LLM providers with unified interface.

**Supported Providers:**
- 🔷 Google Gemini (`gemini-pro`, `gemini-2.0-flash-exp`)
- 🟢 OpenAI (`gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`)
- 🟣 Anthropic Claude (`claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`)
- ⚡ Groq (`llama3-70b`, `mixtral-8x7b`)
- 🦙 Ollama (Local models: `llama2`, `mistral`, `codellama`)

**Key Features:**
- Automatic retries with exponential backoff
- Configurable timeouts
- Consistent API across all providers
- Both function and class-based interfaces
- Silent operation (no logging)
- Minimal dependencies

**[📚 Full LLM Documentation →](./llm/README.md)**

---

## 📦 Installation

### Install from PyPI (Recommended)

```bash
# Install the base package
pip install Codemni

# Install with specific LLM providers
pip install Codemni[openai]        # OpenAI support
pip install Codemni[anthropic]     # Anthropic Claude support
pip install Codemni[groq]          # Groq support
pip install Codemni[google]        # Google Gemini support
pip install Codemni[ollama]        # Ollama (local) support

# Install with all LLM providers
pip install Codemni[all]
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/CodexJitin/Codemni.git
cd Codemni

# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e .[all]
```

---

## 🚀 Quick Start

### Installation

```bash
pip install Codemni[all]  # Install with all LLM providers
```

### ToolCalling Agent - Basic Usage

```python
from Codemni.TOOL_CALLING_AGENT.agent import Create_ToolCalling_Agent
from Codemni.llm.Google_llm import GoogleLLM

# Initialize LLM
llm = GoogleLLM(
    model="gemini-2.0-flash-exp",
    api_key="YOUR_API_KEY"  # or set GOOGLE_API_KEY env var
)

# Create agent
agent = Create_ToolCalling_Agent(llm=llm, verbose=True)

# Define a tool
def calculator(expression):
    return str(eval(expression))

# Add tool to agent
agent.add_tool("calculator", "Evaluate mathematical expressions", calculator)

# Use the agent
response = agent.invoke("What is 125 * 48?")
print(response)  # Agent will use the calculator tool
```

### ToolCalling Agent with Memory

```python
from Codemni.TOOL_CALLING_AGENT.agent import Create_ToolCalling_Agent
from Codemni.llm.Google_llm import GoogleLLM
from Codemni.memory.conversational_buffer_memory import ConversationalBufferMemory

# Initialize LLM and memory
llm = GoogleLLM(model="gemini-2.0-flash-exp", api_key="YOUR_API_KEY")
memory = ConversationalBufferMemory()

# Create agent with memory
agent = Create_ToolCalling_Agent(llm=llm, memory=memory, verbose=True)
agent.add_tool("calculator", "Evaluate math", calculator)

# Multi-turn conversation with context
response1 = agent.invoke("Calculate 50 + 25")  # Returns: 75
response2 = agent.invoke("Now multiply that by 2")  # Returns: 150 (remembers 75!)
```

### LLM Module - Basic Usage

```python
from Codemni.llm import google_llm, openai_llm, anthropic_llm

# Google Gemini
response = google_llm(
    prompt="Explain quantum computing in simple terms",
    model="gemini-pro",
    api_key="your-api-key"  # or set GOOGLE_API_KEY env var
)
print(response)

# OpenAI GPT
response = openai_llm(
    prompt="Write a Python function to calculate fibonacci",
    model="gpt-4",
    temperature=0.7,
    max_tokens=500
)
print(response)

# Anthropic Claude
response = anthropic_llm(
    prompt="Explain the concept of recursion",
    model="claude-3-sonnet-20240229",
    max_tokens=300
)
print(response)
```

### Error Handling

```python
from Codemni.llm import google_llm, GoogleLLMError, GoogleLLMAPIError

try:
    response = google_llm(
        prompt="Hello, world!",
        model="gemini-pro"
    )
    print(response)
except GoogleLLMAPIError as e:
    print(f"API Error: {e}")
except GoogleLLMError as e:
    print(f"General Error: {e}")
```

---

## 🔐 Configuration

### Environment Variables

Set these to avoid hardcoding API keys:

```bash
# Linux/Mac
export GOOGLE_API_KEY="your-google-key"
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GROQ_API_KEY="your-groq-key"
export OLLAMA_BASE_URL="http://localhost:11434"  # Optional

# Windows PowerShell
$env:GOOGLE_API_KEY="your-google-key"
$env:OPENAI_API_KEY="your-openai-key"
```

### Using .env File

```bash
# Install python-dotenv
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

# Now your environment variables are loaded
from Codemni.llm import google_llm

response = google_llm(prompt="Hello", model="gemini-pro")
```

---

## 🏗️ Project Structure

```
Codemni/
├── 📄 README.md              # This file - Main documentation
├── 📄 LICENSE                # License information
├── 📄 requirements.txt       # Base dependencies
├── 📄 __init__.py            # Package initialization
│
├── � TOOL_CALLING_AGENT/    # AI Agent Module
│   ├── __init__.py
│   ├── README.md             # Agent documentation
│   ├── agent.py              # Main agent implementation
│   └── prompt.py             # Prompt templates
│
├── � memory/                # Memory Module
│   ├── __init__.py
│   ├── README.md             # Memory documentation
│   ├── conversational_buffer_memory.py
│   ├── conversational_window_memory.py
│   ├── conversational_token_buffer_memory.py
│   └── conversational_summary_memory.py
│
├── 📁 llm/                   # LLM Module
│   ├── __init__.py
│   ├── README.md             # LLM module documentation
│   ├── Google_llm.py         # Google Gemini wrapper
│   ├── OpenAI_llm.py         # OpenAI wrapper
│   ├── Anthropic_llm.py      # Anthropic wrapper
│   ├── Groq_llm.py           # Groq wrapper
│   └── Ollama_llm.py         # Ollama wrapper
│
├── 📁 core/                  # Core utilities
│   └── adapter.py            # Tool execution adapter
│
└── 📁 assets/                # Assets and media
    └── codemni-logo.jpg
```

---

## 📚 Documentation

### Module Documentation

- **[ToolCalling Agent](./TOOL_CALLING_AGENT/README.md)** - AI agent framework guide
  - Complete API reference for all methods
  - Memory integration guide
  - Tool definition best practices
  - Custom prompt guidelines
  - Troubleshooting and examples
  
- **[Memory Module](./memory/README.md)** - Conversation memory guide
  - Memory type comparison
  - Usage examples for each type
  - Serialization and persistence
  - Integration with agents

- **[LLM Module](./llm/README.md)** - Comprehensive guide to LLM wrappers
  - API reference for all providers
  - Advanced usage examples
  - Exception handling guide
  - Provider-specific notes

---

## ✨ Features by Module

### ToolCalling Agent

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-LLM Support** | Works with OpenAI, Google Gemini, Anthropic, Groq, Ollama |
| 🔧 **Dynamic Tools** | Automatically selects and executes appropriate tools |
| 💾 **Optional Memory** | 4 memory strategies for conversation context |
| 🎨 **Custom Prompts** | Customize agent personality and role |
| 📊 **Verbose Mode** | Detailed logging for debugging |
| ⚠️ **Standard Models** | Optimized for instruction-following models (not reasoning models) |

### Memory Module

| Feature | Description |
|---------|-------------|
| 📝 **Buffer Memory** | Store all conversation messages |
| 🪟 **Window Memory** | Keep only recent N exchanges |
| 🎫 **Token Buffer** | Limit memory by token count |
| 📋 **Summary Memory** | Summarize old conversations |
| 💾 **Serialization** | Save/load conversation history |
| 🔌 **Easy Integration** | Works seamlessly with agents |

### LLM Module

| Feature | Description |
|---------|-------------|
| 🔄 **Auto Retry** | Exponential backoff for transient failures |
| ⏱️ **Timeouts** | Configurable request timeouts (30-60s) |
| 🛡️ **Error Handling** | Clear exception hierarchy per provider |
| 🔇 **Silent Mode** | No logging - clean operation |
| 📦 **Minimal Deps** | Install only what you need |
| 🎯 **Unified API** | Same interface across all providers |
| ✅ **Validation** | Input validation and defensive coding |
| 🔧 **Dual Interface** | Both function and class-based APIs |

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push to the branch (`git push origin feature/AmazingFeature`)
5. 🔀 Open a Pull Request

### Development Guidelines

- Follow existing code style and patterns
- Add tests for new features
- Update documentation
- Keep dependencies minimal
- Maintain backward compatibility

---

## 📋 Requirements

- Python 3.8 or higher
- Optional dependencies (install as needed):
  - `openai>=1.0.0` - For OpenAI support
  - `anthropic>=0.18.0` - For Anthropic support
  - `groq>=0.4.0` - For Groq support
  - `google-generativeai>=0.3.0` - For Google Gemini support
  - `ollama>=0.1.0` - For Ollama support

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**CodexJitin**

- GitHub: [@CodexJitin](https://github.com/CodexJitin)
- Repository: [Codemni](https://github.com/CodexJitin/Codemni)

---

## 🔖 Version

**Current Version: 1.1.0**

### Changelog

#### v1.1.0 (2025-10-25)
- 🎉 Added ToolCalling Agent module
- 💾 Added Memory module with 4 memory strategies
- 🔧 LLM module now supports both function and class-based interfaces
- 📚 Comprehensive documentation for all modules
- ⚠️ Added warnings about reasoning model compatibility

#### v1.0.0 (2025-10-24)
- 🎉 Initial release
- ✅ LLM module with 5 provider support
- ✅ Production-ready error handling
- ✅ Comprehensive documentation

---

## 🌟 Show Your Support

If you find Codemni useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 🔀 Contributing code

---

## 📞 Support

- 📧 Issues: [GitHub Issues](https://github.com/CodexJitin/Codemni/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/CodexJitin/Codemni/discussions)

---

<div align="center">

**Made with ❤️ by CodexJitin**

*Empowering developers to build better AI applications*

</div>
