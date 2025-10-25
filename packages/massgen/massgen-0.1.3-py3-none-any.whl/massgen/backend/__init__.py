# -*- coding: utf-8 -*-
"""
MassGen Backend System - Multi-Provider LLM Integration

Supports multiple LLM providers with standardized StreamChunk interface:
- ChatCompletions (OpenAI-compatible for Cerebras AI, etc.)
- Response API (OpenAI Response API with reasoning support)
- Grok (xAI API with live search capabilities)
- Claude (Messages API with multi-tool support)
- Gemini (structured output for coordination)
- Claude Code (claude-code-sdk streaming integration)

TODO:

- Gemini CLI (command-line interface integration)
- Clean up StreamChunk design (too many optional fields for reasoning/provider features)
- Check if we indeed need to pass agent_id & session_id to backends
"""

from .base import LLMBackend, StreamChunk, TokenUsage
from .chat_completions import ChatCompletionsBackend
from .claude import ClaudeBackend

# from .claude_code_cli import ClaudeCodeCLIBackend  # File removed
from .claude_code import ClaudeCodeBackend
from .cli_base import CLIBackend
from .gemini import GeminiBackend
from .grok import GrokBackend
from .lmstudio import LMStudioBackend
from .response import ResponseBackend

# from .gemini_cli import GeminiCLIBackend

# Azure OpenAI backend (optional)
try:
    from .azure_openai import AzureOpenAIBackend

    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False
    AzureOpenAIBackend = None

__all__ = [
    "LLMBackend",
    "StreamChunk",
    "TokenUsage",
    "ChatCompletionsBackend",
    "ResponseBackend",
    "GrokBackend",
    "LMStudioBackend",
    "ClaudeBackend",
    "GeminiBackend",
    "CLIBackend",
    "ClaudeCodeBackend",
    # "GeminiCLIBackend",
]

# Add Azure OpenAI if available
if AZURE_OPENAI_AVAILABLE:
    __all__.append("AzureOpenAIBackend")
