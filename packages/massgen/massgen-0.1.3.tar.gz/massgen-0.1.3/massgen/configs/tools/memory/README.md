# Memory and Context Window Management Examples

This directory contains example configurations and tests for MassGen's memory system and automatic context window management.

## Features Demonstrated

- **Automatic Context Compression**: When conversation history approaches 75% of the model's context window, older messages are automatically compressed
- **Token-Aware Management**: System keeps most recent messages within 40% token budget
- **Persistent Memory Integration**: Compressed messages stored in long-term memory using mem0
- **Graceful Degradation**: Works with or without persistent memory (with appropriate warnings)

## Files

### Configuration Files

#### `gpt5mini_gemini_context_window_management.yaml`
Example configuration showing how to configure memory directly in YAML.

Features two agents:
- **agent_a**: GPT-5-mini with medium reasoning
- **agent_b**: Gemini 2.5 Flash

**Memory Control** - Configure directly in YAML:
```yaml
memory:
  enabled: true  # Master switch

  conversation_memory:
    enabled: true  # Short-term tracking

  persistent_memory:
    enabled: true  # Long-term storage (set to false to disable)
    on_disk: true
    agent_name: "storyteller_agent"
    # session_name: "test_session"  # Optional - auto-generated if not specified

  compression:
    trigger_threshold: 0.75  # Compress at 75%
    target_ratio: 0.40       # Target 40% after
```

**Session Management:**
- If `session_name` is not specified, a unique ID is auto-generated (e.g., `agent_storyteller_20251023_143022_a1b2c3`)
- Each new run gets a fresh session by default
- To continue a previous session, specify the `session_name` explicitly

To disable persistent memory, set `memory.persistent_memory.enabled: false`

#### `gpt5mini_gemini_no_persistent_memory.yaml`
Example showing what happens when persistent memory is disabled.

**Key difference**: Sets `memory.persistent_memory.enabled: false` to demonstrate warning messages when context fills up without long-term storage.

### Test Script

#### `test_context_window_management.py`
Complete test script demonstrating:
- Setup of ConversationMemory and PersistentMemory
- Integration with SingleAgent
- Both scenarios (with/without persistent memory)
- Logging of compression events

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install massgen mem0ai

# Set up API keys - Create a .env file in project root:
cat > .env << EOF
OPENAI_API_KEY='your-key-here'
GOOGLE_API_KEY='your-key-here'  # Optional, for Gemini
EOF

# Or export directly:
export OPENAI_API_KEY='your-key-here'
```

The test script automatically loads `.env` files from:
- Project root
- Current directory
- Script directory

### Run the Test

```bash
# Run with default config (memory enabled)
python massgen/configs/tools/memory/test_context_window_management.py

# Run with custom config
python massgen/configs/tools/memory/test_context_window_management.py --config path/to/config.yaml
```

The test script reads the `memory` section from YAML and:
- If `persistent_memory.enabled: true` → Runs Test 1 (with persistent memory)
- If `persistent_memory.enabled: false` → Runs Test 2 (without persistent memory)

### Expected Output

**With Persistent Memory:**
```
📊 Context usage: 96,000 / 128,000 tokens (75.0%) - compressing old context
📦 Compressed 15 messages (60,000 tokens) into long-term memory
   Kept 8 messages (36,000 tokens) in context
```

**Without Persistent Memory:**
```
📊 Context usage: 96,000 / 128,000 tokens (75.0%) - compressing old context
⚠️  Warning: Dropping 15 messages (60,000 tokens)
   No persistent memory configured to retain this information
   Consider adding persistent_memory to avoid losing context
```

## How It Works

### Token Budget Allocation

After compression, the context window is allocated as follows:

| Component | Allocation | Purpose |
|-----------|------------|---------|
| Conversation History | 40% | Most recent messages kept in active context |
| New User Messages | 20% | Room for incoming requests |
| Retrieved Memories | 10% | Injected relevant facts from persistent memory |
| System Prompt | 10% | Overhead for instructions |
| Response Generation | 20% | Space for model output |

### Compression Strategy

1. **Threshold**: Compression triggers at **75%** of context window
2. **Target**: Reduces to **40%** of context window after compression
3. **Selection**: Keeps most recent messages that fit within budget
4. **Preservation**: System messages always kept (never compressed)

### Model Context Windows

The system automatically detects context limits for each model:

| Model | Context Window | Compression at | Target After |
|-------|----------------|----------------|--------------|
| GPT-4o | 128K | 96K tokens | 51K tokens |
| GPT-4o-mini | 128K | 96K tokens | 51K tokens |
| Claude Sonnet 4 | 200K | 150K tokens | 80K tokens |
| Gemini 2.5 Flash | 1M | 750K tokens | 400K tokens |
| DeepSeek R1 | 128K | 96K tokens | 51K tokens |

## Programmatic Usage

To use memory in your own code:

```python
from massgen.backend.chat_completions import ChatCompletionsBackend
from massgen.chat_agent import SingleAgent
from massgen.memory import ConversationMemory, PersistentMemory

# Create backends
llm = ChatCompletionsBackend(type="openai", model="gpt-4o-mini", api_key="...")
embedding = ChatCompletionsBackend(type="openai", model="text-embedding-3-small", api_key="...")

# Initialize memory
conversation_memory = ConversationMemory()
persistent_memory = PersistentMemory(
    agent_name="my_agent",
    session_name="session_1",
    llm_backend=llm,
    embedding_backend=embedding,
    on_disk=True,  # Persist across restarts
)

# Create agent with memory
agent = SingleAgent(
    backend=llm,
    agent_id="my_agent",
    system_message="You are a helpful assistant",
    conversation_memory=conversation_memory,
    persistent_memory=persistent_memory,
)

# Use normally - compression happens automatically
async for chunk in agent.chat([{"role": "user", "content": "Hello!"}]):
    if chunk.type == "content":
        print(chunk.content, end="")
```

## Related Documentation

- [Memory System Design](../../../massgen/memory/docs/DESIGN.md)
- [Memory Quickstart](../../../massgen/memory/docs/QUICKSTART.md)
- [Single Agent Memory Integration](../../../massgen/memory/docs/agent_use_memory.md)
- [Orchestrator Shared Memory](../../../massgen/memory/docs/orchestrator_use_memory.md)

## Related Issues

- [Issue #347](https://github.com/Leezekun/MassGen/issues/347): Handle context limit with summarization
- [Issue #348](https://github.com/Leezekun/MassGen/issues/348): Ensure memory persists across restarts ✅
- [Issue #349](https://github.com/Leezekun/MassGen/issues/349): File caching with memory (future work)
