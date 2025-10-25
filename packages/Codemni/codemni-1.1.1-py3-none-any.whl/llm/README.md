# Codemni LLM Module

**Production-ready LLM wrappers with robust error handling, retries, and minimal dependencies.**

A unified Python module that provides simple, consistent interfaces to multiple Large Language Model (LLM) providers. Each wrapper is designed for production use with built-in retry logic, timeout handling, and clear exception hierarchies.

**NEW**: Now includes **class-based wrappers** alongside functions for stateful usage with agents!

## Installation

```bash
# Install from PyPI
pip install Codemni

# Install with specific providers
pip install Codemni[openai]
pip install Codemni[google]
pip install Codemni[anthropic]
pip install Codemni[groq]
pip install Codemni[ollama]

# Install with all providers
pip install Codemni[all]
```

## ✨ Features

- 🔄 **Automatic Retries**: Built-in exponential backoff for transient failures
- ⚡ **Timeout Support**: Configurable request timeouts to prevent hanging
- 🛡️ **Robust Error Handling**: Clear exception hierarchy for each provider
- 🔇 **No Logging**: Silent operation by design (per project requirements)
- 📦 **Minimal Dependencies**: Only install what you need
- 🎯 **Consistent API**: Same function signature across all providers
- 🧪 **Production-Ready**: Input validation and defensive coding practices
- ⭐ **Two Interfaces**: Functions for one-off calls, Classes for stateful usage

## 🚀 Supported Providers

| Provider | Function | Class | Models Supported |
|----------|----------|-------|-----------------|
| **Google Gemini** | `google_llm()` | `GoogleLLM` | gemini-pro, gemini-2.0-flash-exp, etc. |
| **OpenAI** | `openai_llm()` | `OpenAILLM` | gpt-4, gpt-3.5-turbo, etc. |
| **Anthropic Claude** | `anthropic_llm()` | `AnthropicLLM` | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| **Groq** | `groq_llm()` | `GroqLLM` | llama3-70b-8192, mixtral-8x7b-32768, etc. |
| **Ollama** | `ollama_llm()` | `OllamaLLM` | llama2, mistral, codellama (local) |

## 📚 Two Ways to Use

### Option 1: Function-Based (Original)
Perfect for one-off calls where you pass all parameters each time:

```python
from Codemni.llm import openai_llm

response = openai_llm(
    prompt="What is Python?",
    model="gpt-4",
    api_key="your-api-key"
)
```

### Option 2: Class-Based (NEW!)
Perfect for agents and repeated calls with the same configuration:

```python
from Codemni.llm import OpenAILLM

llm = OpenAILLM(model="gpt-4", api_key="your-api-key")

response1 = llm.generate_response("What is Python?")
response2 = llm.generate_response("What is JavaScript?")
```

## 📦 Installation

### Install from GitHub

```bash
# Clone the repository
git clone https://github.com/CodexJitin/Codemni.git
cd Codemni

# Install the Codemni package
pip install -e .
```

Or install directly from GitHub:
```bash
pip install git+https://github.com/CodexJitin/Codemni.git
```

### Install optional dependencies (based on your needs)

```bash
# For OpenAI
pip install openai>=1.0.0

# For Anthropic Claude
pip install anthropic>=0.18.0

# For Groq
pip install groq>=0.4.0

# For Google Gemini
pip install google-generativeai>=0.3.0

# For Ollama (local models)
pip install ollama>=0.1.0
```

Or install multiple at once:
```bash
pip install openai anthropic groq google-generativeai ollama
```

## 🎯 Quick Start

### Function-Based Examples

Import using: `from Codemni.llm import ...`

#### Google Gemini

```python
from Codemni.llm import google_llm, GoogleLLMError

try:
    response = google_llm(
        prompt="Explain Python in one sentence",
        model="gemini-pro",
        api_key="your-api-key-here"  # or set GOOGLE_API_KEY env var
    )
    print(response)
except GoogleLLMError as e:
    print(f"Error: {e}")
```

#### OpenAI

```python
from Codemni.llm import openai_llm, OpenAILLMError

try:
    response = openai_llm(
        prompt="Write a haiku about programming",
        model="gpt-3.5-turbo",
        api_key="your-api-key-here",  # or set OPENAI_API_KEY env var
        temperature=0.7,
        max_tokens=50
    )
    print(response)
except OpenAILLMError as e:
    print(f"Error: {e}")
```

### Class-Based Examples (NEW!)

#### OpenAI Class

```python
from Codemni.llm import OpenAILLM

llm = OpenAILLM(
    model="gpt-4",
    api_key="your-api-key",  # or set OPENAI_API_KEY env var
    temperature=0.7
)

response = llm.generate_response("What is artificial intelligence?")
print(response)
```

#### Google Gemini Class

```python
from Codemni.llm import GoogleLLM

llm = GoogleLLM(
    model="gemini-1.5-pro",
    api_key="your-api-key",  # or set GOOGLE_API_KEY env var
    temperature=0.9
)

response = llm.generate_response("Write a creative story")
print(response)
```

#### Anthropic Claude Class

```python
from Codemni.llm import AnthropicLLM

llm = AnthropicLLM(
    model="claude-3-sonnet-20240229",
    api_key="your-api-key",  # or set ANTHROPIC_API_KEY env var
    max_tokens=4096
)

response = llm.generate_response("Explain quantum computing")
print(response)
```

#### Use with Agents

Classes are perfect for use with agents that expect a `generate_response()` method:

```python
from Codemni.llm import OpenAILLM
from TOOL_CALLING_AGENT.agent import Create_ToolCalling_Agent

# Initialize LLM
llm = OpenAILLM(model="gpt-4", api_key="your-key")

# Pass to agent
agent = Create_ToolCalling_Agent(llm=llm, verbose=True)

# Add tools
agent.add_tool("calculator", "Calculate expressions", lambda x: eval(x))

# Use agent
result = agent.invoke("What is 100 + 200?")
```

### Anthropic Claude (Function)

```python
from codemni_LLM import anthropic_llm, AnthropicLLMError

try:
    response = anthropic_llm(
        prompt="Explain machine learning in simple terms",
        model="claude-3-sonnet-20240229",
        api_key="your-api-key-here",  # or set ANTHROPIC_API_KEY env var
        temperature=0.5,
        max_tokens=150
    )
    print(response)
except AnthropicLLMError as e:
    print(f"Error: {e}")
```

### Groq

```python
from codemni_LLM import groq_llm, GroqLLMError

try:
    response = groq_llm(
        prompt="What is artificial intelligence?",
        model="llama3-70b-8192",
        api_key="your-api-key-here",  # or set GROQ_API_KEY env var
        temperature=0.3
    )
    print(response)
except GroqLLMError as e:
    print(f"Error: {e}")
```

### Ollama (Local)

```python
from codemni_LLM import ollama_llm, OllamaLLMError

try:
    response = ollama_llm(
        prompt="Explain Docker in one sentence",
        model="llama2",
        base_url="http://localhost:11434",  # or set OLLAMA_BASE_URL env var
        temperature=0.8
    )
    print(response)
except OllamaLLMError as e:
    print(f"Error: {e}")
```

## 🔧 API Reference

All LLM functions share a similar signature:

### Common Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | `str` | ✅ Yes | - | The input text/prompt to send to the model |
| `model` | `str` | ✅ Yes | - | Model identifier (e.g., "gpt-4", "gemini-pro") |
| `api_key` | `str` | No | `None` | API key (falls back to environment variable) |
| `max_retries` | `int` | No | `3` | Number of retry attempts on failures |
| `timeout` | `float` | No | `30.0` | Request timeout in seconds (60s for Ollama) |
| `backoff_factor` | `float` | No | `0.5` | Exponential backoff multiplier for retries |
| `temperature` | `float` | No | `None` | Sampling temperature (0.0-1.0 or 0.0-2.0) |
| `max_tokens` | `int` | No | Provider-specific | Maximum tokens in response |

### Provider-Specific Notes

#### Google Gemini
- Environment variable: `GOOGLE_API_KEY`
- Robust response extraction handles different client versions
- Supports safety settings and generation config

#### OpenAI
- Environment variable: `OPENAI_API_KEY`
- Supports both chat models (gpt-4) and legacy completion models
- Temperature range: 0.0-2.0

#### Anthropic Claude
- Environment variable: `ANTHROPIC_API_KEY`
- `max_tokens` parameter is required (default: 4096)
- Temperature range: 0.0-1.0

#### Groq
- Environment variable: `GROQ_API_KEY`
- Fast inference with open-source models
- Temperature range: 0.0-2.0

#### Ollama
- Environment variable: `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- Requires Ollama server running locally
- No API key required
- Default timeout: 60 seconds

## 🚨 Exception Hierarchy

Each provider has its own exception hierarchy:

```python
# Base exception
{Provider}LLMError
    ├── {Provider}LLMImportError     # SDK not installed or import failed
    ├── {Provider}LLMAPIError         # API request failed after retries
    └── {Provider}LLMResponseError    # Response parsing/validation failed
```

Example for Google:
- `GoogleLLMError` (base)
- `GoogleLLMImportError`
- `GoogleLLMAPIError`
- `GoogleLLMResponseError`

## 🔐 Environment Variables

Set these environment variables to avoid passing API keys in code:

```bash
export GOOGLE_API_KEY="your-google-key"
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GROQ_API_KEY="your-groq-key"
export OLLAMA_BASE_URL="http://localhost:11434"  # Optional, has default
```

Or use a `.env` file with `python-dotenv`:

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

# Now environment variables are loaded
from codemni_LLM import google_llm
response = google_llm(prompt="Hello", model="gemini-pro")
```

## 📝 Examples

See `examples.py` for complete working examples of all providers.

Run examples:
```bash
cd Codemni
python -m llm.examples
```

## 🏗️ Project Structure

```
Codemni/llm/
├── __init__.py           # Package initialization and exports
├── Google_llm.py         # Google Gemini wrapper
├── OpenAI_llm.py         # OpenAI GPT wrapper
├── Anthropic_llm.py      # Anthropic Claude wrapper
├── Groq_llm.py           # Groq wrapper
├── Ollama_llm.py         # Ollama local wrapper
├── examples.py           # Usage examples for all providers
└── README.md             # This file
```

## 🧪 Testing

Each function includes comprehensive input validation:
- ✅ Non-empty string validation for prompts and models
- ✅ Numeric range validation for temperatures and tokens
- ✅ API key presence validation
- ✅ Retry count validation

## 🤝 Contributing

This package follows these design principles:
1. **No logging**: Silent operation by design
2. **Fail fast**: Clear exceptions with meaningful messages
3. **Defensive coding**: Validate all inputs
4. **Production-ready**: Retries, timeouts, and error handling
5. **Consistent API**: Same interface across all providers

## 📄 License

See the main project LICENSE file for details.

## 👤 Author

**CodexJitin**

## 📦 Repository

**GitHub**: [CodexJitin/Codemni](https://github.com/CodexJitin/Codemni)

This LLM module is part of the Codemni repository and is located in the `llm` subdirectory.

## 🔖 Version

**v1.0.0**

---

**Note**: This package is designed for production use with minimal dependencies. Only install the provider SDKs you actually need to keep your environment lean.
