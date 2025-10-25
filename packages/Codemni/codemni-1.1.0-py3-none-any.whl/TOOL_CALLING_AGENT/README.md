# ToolCalling Agent

A powerful and flexible AI agent framework that enables Large Language Models (LLMs) to intelligently select and execute tools based on user queries. The agent supports multiple LLM providers and optional conversation memory for context-aware interactions.

⚠️ **Note**: This agent is designed for standard LLM models and **does not support reasoning models** (e.g., OpenAI o1, o3). Reasoning models use different response formats that are incompatible with this framework's tool-calling mechanism.

## Features

- 🤖 **Multi-LLM Support**: Compatible with OpenAI, Google Gemini, Anthropic Claude, Groq, and Ollama
- 🔧 **Dynamic Tool Execution**: Automatically selects and executes appropriate tools
- 💾 **Optional Memory**: Maintains conversation history with multiple memory strategies
- 🎨 **Custom Prompts**: Support for custom system prompts
- 📊 **Verbose Mode**: Detailed logging for debugging and monitoring
- 🔌 **Extensible**: Easy to add custom tools and memory types

## Installation

```bash
# Install from PyPI
pip install Codemni

# Or install with all LLM providers
pip install Codemni[all]
```

## Quick Start

### Basic Usage

```python
from Codemni.TOOL_CALLING_AGENT.agent import Create_ToolCalling_Agent
from Codemni.llm.Google_llm import GoogleLLM

# Initialize your LLM
llm = GoogleLLM(
    model="gemini-2.0-flash-exp",
    api_key="YOUR_API_KEY_HERE"
)

# Create the agent
agent = Create_ToolCalling_Agent(llm=llm, verbose=True)

# Define and add a tool
def calculator(expression):
    """Evaluate a mathematical expression"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

agent.add_tool(
    name="calculator",
    description="Evaluate mathematical expressions",
    function=calculator
)

# Use the agent
response = agent.invoke("What is 125 multiplied by 48?")
print(response)
```

### Usage with Memory

```python
from Codemni.TOOL_CALLING_AGENT.agent import Create_ToolCalling_Agent
from Codemni.llm.Google_llm import GoogleLLM
from Codemni.memory.conversational_buffer_memory import ConversationalBufferMemory

# Initialize LLM and memory
llm = GoogleLLM(model="gemini-2.0-flash-exp", api_key="YOUR_API_KEY_HERE")
memory = ConversationalBufferMemory()

# Create agent with memory
agent = Create_ToolCalling_Agent(
    llm=llm,
    verbose=True,
    memory=memory
)

# Add tools
agent.add_tool("calculator", "Evaluate mathematical expressions", calculator)

# Multi-turn conversation with context
response1 = agent.invoke("Calculate 50 + 25")
# Agent responds: "75"

response2 = agent.invoke("Now multiply that result by 2")
# Agent remembers the previous result and responds: "150"
```

## API Reference

### Create_ToolCalling_Agent

Main agent class for tool-calling functionality.

#### Constructor

```python
Create_ToolCalling_Agent(
    llm,
    verbose=False,
    prompt=None,
    memory=None
)
```

**Parameters:**

- `llm` (required): LLM object with a `generate_response(prompt)` method
  - Use LLM classes from the `llm` folder (GoogleLLM, OpenAILLM, AnthropicLLM, GroqLLM, OllamaLLM)

- `verbose` (optional): Enable detailed logging output
  - Type: `bool`
  - Default: `False`

- `prompt` (optional): Custom agent introduction (personality/role only)
  - Type: `str` or `None`
  - Default: `None` (uses built-in agent introduction)
  - ⚠️ **WARNING**: Should ONLY contain agent personality or role description (e.g., "You are a helpful math tutor")
  - Do NOT include tool instructions or response format - these are added automatically
  - Example: `"You are a friendly financial advisor assistant."`

- `memory` (optional): Memory object for conversation history
  - Type: Memory object or `None`
  - Default: `None`
  - Supported types: ConversationalBufferMemory, ConversationalWindowMemory, ConversationalTokenBufferMemory, ConversationalSummaryMemory

#### Methods

##### `add_llm(llm)`

Set or update the LLM instance.

**Parameters:**
- `llm`: LLM object with `generate_response(prompt)` method

**Returns:** None

**Example:**
```python
agent.add_llm(new_llm)
```

---

##### `add_tool(name, description, function)`

Register a tool that the agent can use.

**Parameters:**
- `name` (str): Unique identifier for the tool
- `description` (str): Clear description of what the tool does (used by LLM to decide when to use it)
- `function` (callable): Function to execute when tool is called

**Returns:** None

**Example:**
```python
def weather(location):
    return f"Weather in {location}: Sunny, 25°C"

agent.add_tool(
    name="weather",
    description="Get current weather for a location",
    function=weather
)
```

---

##### `add_memory(memory)`

Set or update the memory instance.

**Parameters:**
- `memory`: Memory object from the memory module

**Returns:** None

**Example:**
```python
from memory.conversational_window_memory import ConversationalWindowMemory

memory = ConversationalWindowMemory(window_size=5)
agent.add_memory(memory)
```

---

##### `clear_memory()`

Clear the conversation history stored in memory.

**Parameters:** None

**Returns:** None

**Example:**
```python
agent.clear_memory()
```

---

##### `get_memory_history()`

Retrieve the conversation history from memory.

**Parameters:** None

**Returns:** List of message dictionaries with `role` and `content` keys, or empty list if no memory

**Example:**
```python
history = agent.get_memory_history()
for msg in history:
    print(f"{msg['role']}: {msg['content']}")
```

---

##### `invoke(query)`

Execute the agent with a user query. This is the main method for interacting with the agent.

**Parameters:**
- `query` (str): User's question or request

**Returns:** String containing the agent's final response

**Raises:**
- `ValueError`: If LLM is not set or no tools are added

**Example:**
```python
response = agent.invoke("What is the weather in New York?")
print(response)
```

## Memory Types

The agent supports four different memory strategies:

### 1. ConversationalBufferMemory

Stores all conversation messages without any limit.

**Best for:** Short to medium conversations where complete context is needed

```python
from Codemni.memory.conversational_buffer_memory import ConversationalBufferMemory

memory = ConversationalBufferMemory()
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

### 2. ConversationalWindowMemory

Keeps only the last N message pairs.

**Best for:** Ongoing conversations with focus on recent context

```python
from Codemni.memory.conversational_window_memory import ConversationalWindowMemory

# Keep only last 5 exchanges
memory = ConversationalWindowMemory(window_size=5)
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

### 3. ConversationalTokenBufferMemory

Limits memory by token count.

**Best for:** Cost-sensitive applications where token usage matters

```python
from Codemni.memory.conversational_token_buffer_memory import ConversationalTokenBufferMemory

# Keep up to 1000 tokens
memory = ConversationalTokenBufferMemory(max_tokens=1000)
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

### 4. ConversationalSummaryMemory

Summarizes older conversations to save space.

**Best for:** Very long conversation sessions

```python
from Codemni.memory.conversational_summary_memory import ConversationalSummaryMemory

# Summarize after every 10 messages
memory = ConversationalSummaryMemory(summarization_threshold=10)
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

**Best for:** Ongoing conversations with focus on recent context

```python
from memory.conversational_window_memory import ConversationalWindowMemory

memory = ConversationalWindowMemory(window_size=5)  # Keep last 5 exchanges
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

### 3. ConversationalTokenBufferMemory

Limits memory by token count.

**Best for:** Cost-sensitive applications where token usage matters

```python
from memory.conversational_token_buffer_memory import ConversationalTokenBufferMemory

memory = ConversationalTokenBufferMemory(max_tokens=1000)
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

### 4. ConversationalSummaryMemory

Summarizes older conversations to save space.

**Best for:** Very long conversation sessions

```python
from memory.conversational_summary_memory import ConversationalSummaryMemory

memory = ConversationalSummaryMemory(summarization_threshold=10)
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

## Supported LLM Providers

⚠️ **Important**: Use standard instruction-following models only. **Reasoning models are NOT supported** (e.g., OpenAI o1, o3-mini). These models have different response formats incompatible with the tool-calling framework.

### OpenAI

```python
from Codemni.llm.OpenAI_llm import OpenAILLM

# ✅ Supported models: gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.
llm = OpenAILLM(
    model="gpt-4",  # Use standard models
    api_key="YOUR_OPENAI_API_KEY",
    temperature=0.7
)

# ❌ NOT supported: o1, o1-preview, o1-mini, o3, o3-mini (reasoning models)
```

### Google Gemini

```python
from Codemni.llm.Google_llm import GoogleLLM

# ✅ Supported: All Gemini models (Flash, Pro, etc.)
llm = GoogleLLM(
    model="gemini-2.0-flash-exp",
    api_key="YOUR_GOOGLE_API_KEY"
)
```

### Anthropic Claude

```python
from Codemni.llm.Anthropic_llm import AnthropicLLM

# ✅ Supported: All Claude models
llm = AnthropicLLM(
    model="claude-3-5-sonnet-20241022",
    api_key="YOUR_ANTHROPIC_API_KEY"
)
```

### Groq

```python
from Codemni.llm.Groq_llm import GroqLLM

llm = GroqLLM(
    model="llama-3.3-70b-versatile",
    api_key="YOUR_GROQ_API_KEY"
)
```

### Ollama (Local)

```python
from Codemni.llm.Ollama_llm import OllamaLLM

llm = OllamaLLM(
    model="llama2",
    base_url="http://localhost:11434"
)
```

## Tool Definition Guidelines

Tools should be Python functions that:

1. Accept string or simple parameters
2. Return string values (or values convertible to strings)
3. Have clear, descriptive names
4. Include helpful docstrings

**Example:**

```python
def search_database(query):
    """Search the database for relevant information"""
    # Your implementation here
    results = database.search(query)
    return f"Found {len(results)} results: {results}"

agent.add_tool(
    name="search_database",
    description="Search the internal database for information",
    function=search_database
)
```

## Custom Prompts

You can provide a custom agent introduction to customize the agent's personality or role.

⚠️ **IMPORTANT WARNING**: The `prompt` parameter should ONLY contain the agent's introduction/personality description. Do NOT include:
- Tool instructions or tool list format
- Response format requirements  
- Logic for when to use tools
- JSON structure requirements

These are automatically added by the framework. Your custom prompt should be simple, like:

```python
# ✅ CORRECT: Only agent introduction
custom_intro = "You are a friendly and helpful math tutor assistant. Always explain your reasoning step by step."

agent = Create_ToolCalling_Agent(
    llm=llm,
    prompt=custom_intro,  # Only agent personality
    verbose=True
)
```

```python
# ❌ WRONG: Don't include tool instructions or response format
wrong_prompt = """You are a helpful assistant.

Available tools:
{tool_list}

Use JSON format to respond...
"""
# This will break the agent!
```

**What gets added automatically:**
- Tool list formatting
- Tool usage instructions
- Response format (JSON structure)
- When to use tools vs. respond directly

**You only provide:**
- Agent personality/role
- Speaking style
- Domain expertise description

## Complete Example

```python
from Codemni.TOOL_CALLING_AGENT.agent import Create_ToolCalling_Agent
from Codemni.llm.Google_llm import GoogleLLM
from Codemni.memory.conversational_window_memory import ConversationalWindowMemory

# Initialize LLM
llm = GoogleLLM(
    model="gemini-2.0-flash-exp",
    api_key="YOUR_API_KEY_HERE"
)
    api_key="YOUR_API_KEY_HERE"
)

# Initialize memory (keeps last 5 exchanges)
memory = ConversationalWindowMemory(window_size=5)

# Create agent
agent = Create_ToolCalling_Agent(
    llm=llm,
    verbose=True,
    memory=memory
)

# Define tools
def calculator(expression):
    """Evaluate mathematical expressions"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

def weather(location):
    """Get weather information"""
    # In production, call a real weather API
    return f"Weather in {location}: Sunny, 25°C"

# Register tools
agent.add_tool("calculator", "Evaluate mathematical expressions", calculator)
agent.add_tool("weather", "Get weather for a location", weather)

# Use the agent
print("Query 1:")
response1 = agent.invoke("What's 125 * 48?")
print(f"Response: {response1}\n")

print("Query 2:")
response2 = agent.invoke("What's the weather in Paris?")
print(f"Response: {response2}\n")

print("Query 3:")
response3 = agent.invoke("What was my first calculation?")
print(f"Response: {response3}\n")

# View conversation history
print("Conversation History:")
for msg in agent.get_memory_history():
    print(f"  {msg['role'].upper()}: {msg['content']}")

# Clear memory when starting a new topic
agent.clear_memory()
```

## Best Practices

1. **Tool Descriptions**: Write clear, concise tool descriptions that help the LLM understand when to use each tool

2. **Error Handling**: Always include error handling in your tool functions to gracefully handle edge cases

3. **Memory Management**: Choose the appropriate memory type for your use case:
   - Use BufferMemory for short conversations
   - Use WindowMemory for ongoing chats
   - Use TokenBufferMemory for cost control
   - Use SummaryMemory for very long sessions

4. **Verbose Mode**: Enable verbose mode during development to understand agent behavior

5. **Security**: Never hardcode API keys in your code - use environment variables or secure configuration files

6. **Tool Design**: Keep tools focused on single tasks for better reliability

## Troubleshooting

### Agent doesn't call tools

**Possible causes:**
- Tool descriptions are unclear or don't match the query
- LLM doesn't understand when to use the tool

**Solution:** Improve tool descriptions to be more specific and include example use cases

### Memory not working

**Possible causes:**
- Memory object not passed to constructor
- Memory was not initialized properly

**Solution:** Ensure memory is created and passed to the agent:
```python
memory = ConversationalBufferMemory()
agent = Create_ToolCalling_Agent(llm=llm, memory=memory)
```

### Agent gives incorrect responses

**Possible causes:**
- LLM model not suitable for task
- Tool implementation has bugs
- Using a reasoning model (not supported)

**Solution:** Enable verbose mode to debug, check tool implementations, and consider using a more capable LLM model

### Parsing errors or unexpected behavior

**Possible causes:**
- Using reasoning models (o1, o3) which are not supported
- LLM not following the required JSON response format

**Solution:** 
- Ensure you're using standard instruction-following models (gpt-4, gpt-3.5-turbo, gemini, claude, etc.)
- Avoid reasoning models like OpenAI o1, o1-preview, o1-mini, o3, o3-mini
- Enable verbose mode to see the raw LLM responses

## Security Considerations

- **API Keys**: Never commit API keys to version control. Use environment variables:
  ```python
  import os
  api_key = os.getenv('GOOGLE_API_KEY')
  ```

- **Tool Security**: Validate inputs in your tool functions to prevent injection attacks

- **Rate Limiting**: Implement rate limiting when calling external APIs

- **Data Privacy**: Be mindful of sensitive data in conversation history

## License

See the repository's LICENSE file for details.

## Support

For issues, questions, or contributions, please refer to the main repository documentation.
