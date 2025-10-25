# -*- coding: utf-8 -*-
"""
Common chat interface for MassGen agents.

Defines the standard interface that both individual agents and the orchestrator implement,
allowing seamless interaction regardless of whether you're talking to a single agent
or a coordinated multi-agent system.

# TODO: Consider how to best handle stateful vs stateless backends in this interface.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from .backend.base import LLMBackend, StreamChunk
from .stream_chunk import ChunkType
from .utils import CoordinationStage


class ChatAgent(ABC):
    """
    Abstract base class defining the common chat interface.

    This interface is implemented by both individual agents and the MassGen orchestrator,
    providing a unified way to interact with any type of agent system.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"chat_session_{uuid.uuid4().hex[:8]}"
        self.conversation_history: List[Dict[str, Any]] = []

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        reset_chat: bool = False,
        clear_history: bool = False,
        current_stage: CoordinationStage = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Enhanced chat interface supporting tool calls and responses.

        Args:
            messages: List of conversation messages including:
                - {"role": "user", "content": "..."}
                - {"role": "assistant", "content": "...", "tool_calls": [...]}
                - {"role": "tool", "tool_call_id": "...", "content": "..."}
                Or a single string for backwards compatibility
            tools: Optional tools to provide to the agent
            reset_chat: If True, reset the agent's conversation history to the provided messages
            clear_history: If True, clear history but keep system message before processing messages
            current_stage: Optional current coordination stage for orchestrator use

        Yields:
            StreamChunk: Streaming response chunks
        """

    async def chat_simple(self, user_message: str) -> AsyncGenerator[StreamChunk, None]:
        """
        Backwards compatible simple chat interface.

        Args:
            user_message: Simple string message from user

        Yields:
            StreamChunk: Streaming response chunks
        """
        messages = [{"role": "user", "content": user_message}]
        async for chunk in self.chat(messages):
            yield chunk

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and state."""

    @abstractmethod
    async def reset(self) -> None:
        """Reset agent state for new conversation."""

    @abstractmethod
    def get_configurable_system_message(self) -> Optional[str]:
        """
        Get the user-configurable part of the system message.

        Returns the domain expertise, role definition, or custom instructions
        that were configured for this agent, without backend-specific details.

        Returns:
            The configurable system message if available, None otherwise
        """

    # Common conversation management
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history."""
        return self.conversation_history.copy()

    def add_to_history(self, role: str, content: str, **kwargs) -> None:
        """Add message to conversation history."""
        message = {"role": role, "content": content}
        message.update(kwargs)  # Support tool_calls, tool_call_id, etc.
        self.conversation_history.append(message)

    def add_tool_message(self, tool_call_id: str, result: str) -> None:
        """Add tool result to conversation history."""
        self.add_to_history("tool", result, tool_call_id=tool_call_id)

    def get_last_tool_calls(self) -> List[Dict[str, Any]]:
        """Get tool calls from the last assistant message."""
        for message in reversed(self.conversation_history):
            if message.get("role") == "assistant" and "tool_calls" in message:
                return message["tool_calls"]
        return []

    def get_session_id(self) -> str:
        """Get session identifier."""
        return self.session_id


class SingleAgent(ChatAgent):
    """
    Individual agent implementation with direct backend communication.

    This class wraps a single LLM backend and provides the standard chat interface,
    making it interchangeable with the MassGen orchestrator from the user's perspective.
    """

    def __init__(
        self,
        backend: LLMBackend,
        agent_id: Optional[str] = None,
        system_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize single agent.

        Args:
            backend: LLM backend for this agent
            agent_id: Optional agent identifier
            system_message: Optional system message for the agent
            session_id: Optional session identifier
        """
        super().__init__(session_id)
        self.backend = backend
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.system_message = system_message

        # Add system message to history if provided
        if self.system_message:
            self.conversation_history.append({"role": "system", "content": self.system_message})

    @staticmethod
    def _get_chunk_type_value(chunk) -> str:
        """
        Extract chunk type as string, handling both legacy and typed chunks.

        Args:
            chunk: StreamChunk, TextStreamChunk, or MultimodalStreamChunk

        Returns:
            String representation of chunk type (e.g., "content", "tool_calls")
        """
        chunk_type = chunk.type

        if isinstance(chunk_type, ChunkType):
            return chunk_type.value

        return str(chunk_type)

    async def _process_stream(self, backend_stream, tools: List[Dict[str, Any]] = None) -> AsyncGenerator[StreamChunk, None]:
        """Common streaming logic for processing backend responses."""
        assistant_response = ""
        tool_calls = []
        complete_message = None

        try:
            async for chunk in backend_stream:
                chunk_type = self._get_chunk_type_value(chunk)
                if chunk_type == "content":
                    assistant_response += chunk.content
                    yield chunk
                elif chunk_type == "tool_calls":
                    chunk_tool_calls = getattr(chunk, "tool_calls", []) or []
                    tool_calls.extend(chunk_tool_calls)
                    yield chunk
                elif chunk_type == "complete_message":
                    # Backend provided the complete message structure
                    complete_message = chunk.complete_message
                    # Don't yield this - it's for internal use
                elif chunk_type == "complete_response":
                    # Backend provided the raw Responses API response
                    if chunk.response:
                        complete_message = chunk.response

                        # Extract and yield tool calls for orchestrator processing
                        if isinstance(chunk.response, dict) and "output" in chunk.response:
                            response_tool_calls = []
                            for output_item in chunk.response["output"]:
                                if output_item.get("type") == "function_call":
                                    response_tool_calls.append(output_item)
                                    tool_calls.append(output_item)  # Also store for fallback

                            # Yield tool calls so orchestrator can process them
                            if response_tool_calls:
                                yield StreamChunk(type="tool_calls", tool_calls=response_tool_calls)
                    # Complete response is for internal use - don't yield it
                elif chunk_type == "done":
                    # Add complete response to history
                    if complete_message:
                        # For Responses API: complete_message is the response object with 'output' array
                        # Each item in output should be added to conversation history individually
                        if isinstance(complete_message, dict) and "output" in complete_message:
                            self.conversation_history.extend(complete_message["output"])
                        else:
                            # Fallback if it's already in message format
                            self.conversation_history.append(complete_message)
                    elif assistant_response.strip() or tool_calls:
                        # Fallback for legacy backends
                        message_data = {
                            "role": "assistant",
                            "content": assistant_response.strip(),
                        }
                        if tool_calls:
                            message_data["tool_calls"] = tool_calls
                        self.conversation_history.append(message_data)
                    yield chunk
                else:
                    yield chunk

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.add_to_history("assistant", error_msg)
            yield StreamChunk(type="content", content=error_msg)
            yield StreamChunk(type="error", error=str(e))

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        reset_chat: bool = False,
        clear_history: bool = False,
        current_stage: CoordinationStage = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        # print("Agent: ", self.agent_id)
        # for message in messages:
        #     print(f"Message: {message}\n")
        # print("Messages End. \n")
        """Process messages through single backend with tool support."""
        if clear_history:
            # Clear history but keep system message if it exists
            system_messages = [msg for msg in self.conversation_history if msg.get("role") == "system"]
            self.conversation_history = system_messages.copy()
            # Clear backend history while maintaining session
            if self.backend.is_stateful():
                await self.backend.clear_history()

        if reset_chat:
            # Reset conversation history to the provided messages
            self.conversation_history = messages.copy()
            # Reset backend state completely
            if self.backend.is_stateful():
                await self.backend.reset_state()
            backend_messages = self.conversation_history.copy()
        else:
            # Regular conversation - append new messages to agent's history
            self.conversation_history.extend(messages)
            # Handle stateful vs stateless backends differently
            if self.backend.is_stateful():
                # Stateful: only send new messages, backend maintains context
                backend_messages = messages.copy()
            else:
                # Stateless: send full conversation history
                backend_messages = self.conversation_history.copy()

        if current_stage:
            self.backend.set_stage(current_stage)

        # Create backend stream and process it
        backend_stream = self.backend.stream_with_tools(
            messages=backend_messages,
            tools=tools,  # Use provided tools (for MassGen workflow)
            agent_id=self.agent_id,
            session_id=self.session_id,
            **self._get_backend_params(),
        )

        async for chunk in self._process_stream(backend_stream, tools):
            yield chunk

    def _get_backend_params(self) -> Dict[str, Any]:
        """Get additional backend parameters. Override in subclasses."""
        return {}

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_type": "single",
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "system_message": self.system_message,
            "conversation_length": len(self.conversation_history),
        }

    async def reset(self) -> None:
        """Reset conversation for new chat."""
        self.conversation_history.clear()

        # Reset stateful backend if needed
        if self.backend.is_stateful():
            await self.backend.reset_state()

        # Re-add system message if it exists
        if self.system_message:
            self.conversation_history.append({"role": "system", "content": self.system_message})

    def get_configurable_system_message(self) -> Optional[str]:
        """Get the user-configurable part of the system message."""
        return self.system_message

    def set_model(self, model: str) -> None:
        """Set the model for this agent."""
        self.model = model

    def set_system_message(self, system_message: str) -> None:
        """Set or update the system message."""
        self.system_message = system_message

        # Remove old system message if exists
        if self.conversation_history and self.conversation_history[0].get("role") == "system":
            self.conversation_history.pop(0)

        # Add new system message at the beginning
        self.conversation_history.insert(0, {"role": "system", "content": system_message})


class ConfigurableAgent(SingleAgent):
    """
    Single agent that uses AgentConfig for advanced configuration.

    This bridges the gap between SingleAgent and the MassGen system by supporting
    all the advanced configuration options (web search, code execution, etc.)
    while maintaining the simple chat interface.

    TODO: Consider merging with SingleAgent. The main difference is:
    - SingleAgent: backend parameters passed directly to constructor/methods
    - ConfigurableAgent: backend parameters come from AgentConfig object

    Could be unified by making SingleAgent accept an optional config parameter
    and using _get_backend_params() pattern for all parameter sources.
    """

    def __init__(
        self,
        config,  # AgentConfig - avoid circular import
        backend: LLMBackend,
        session_id: Optional[str] = None,
    ):
        """
        Initialize configurable agent.

        Args:
            config: AgentConfig with all settings
            backend: LLM backend
            session_id: Optional session identifier
        """
        # Extract system message without triggering deprecation warning
        system_message = None
        if hasattr(config, "_custom_system_instruction"):
            system_message = config._custom_system_instruction

        super().__init__(
            backend=backend,
            agent_id=config.agent_id,
            system_message=system_message,
            session_id=session_id,
        )
        self.config = config

        # ConfigurableAgent relies on backend_params for model configuration

    def _get_backend_params(self) -> Dict[str, Any]:
        """Get backend parameters from config."""
        return self.config.get_backend_params()

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status with config details."""
        status = super().get_status()
        status.update(
            {
                "agent_type": "configurable",
                "config": self.config.to_dict(),
                "capabilities": {
                    "web_search": self.config.backend_params.get("enable_web_search", False),
                    "code_execution": self.config.backend_params.get("enable_code_interpreter", False),
                },
            },
        )
        return status

    def get_configurable_system_message(self) -> Optional[str]:
        """Get the user-configurable part of the system message for ConfigurableAgent."""
        # Try multiple sources in order of preference

        # First check if backend has system prompt configuration
        if self.config and self.config.backend_params:
            backend_params = self.config.backend_params

            # For Claude Code: prefer system_prompt (complete override)
            if "system_prompt" in backend_params:
                return backend_params["system_prompt"]

            # Then append_system_prompt (additive)
            if "append_system_prompt" in backend_params:
                return backend_params["append_system_prompt"]

        # Fall back to custom_system_instruction (deprecated but still supported)
        # Access private attribute directly to avoid deprecation warning
        if self.config and hasattr(self.config, "_custom_system_instruction") and self.config._custom_system_instruction:
            return self.config._custom_system_instruction

        # Finally fall back to parent class implementation
        return super().get_configurable_system_message()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_simple_agent(backend: LLMBackend, system_message: str = None, agent_id: str = None) -> SingleAgent:
    """Create a simple single agent."""
    # Use MassGen evaluation system message if no custom system message provided
    if system_message is None:
        from .message_templates import MessageTemplates

        templates = MessageTemplates()
        system_message = templates.evaluation_system_message()
    return SingleAgent(backend=backend, agent_id=agent_id, system_message=system_message)


def create_expert_agent(domain: str, backend: LLMBackend, model: str = "gpt-4o-mini") -> ConfigurableAgent:
    """Create an expert agent for a specific domain."""
    from .agent_config import AgentConfig

    config = AgentConfig.for_expert_domain(domain, model=model)
    return ConfigurableAgent(config=config, backend=backend)


def create_research_agent(backend: LLMBackend, model: str = "gpt-4o-mini") -> ConfigurableAgent:
    """Create a research agent with web search capabilities."""
    from .agent_config import AgentConfig

    config = AgentConfig.for_research_task(model=model)
    return ConfigurableAgent(config=config, backend=backend)


def create_computational_agent(backend: LLMBackend, model: str = "gpt-4o-mini") -> ConfigurableAgent:
    """Create a computational agent with code execution."""
    from .agent_config import AgentConfig

    config = AgentConfig.for_computational_task(model=model)
    return ConfigurableAgent(config=config, backend=backend)
