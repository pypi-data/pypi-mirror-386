# -*- coding: utf-8 -*-
"""
Claude API parameters handler.
Handles parameter building for Anthropic Claude Messages API format.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from ._api_params_handler_base import APIParamsHandlerBase


class ClaudeAPIParamsHandler(APIParamsHandlerBase):
    """Handler for Claude API parameters."""

    def get_excluded_params(self) -> Set[str]:
        """Get parameters to exclude from Claude API calls."""
        return self.get_base_excluded_params().union(
            {
                "enable_web_search",
                "enable_code_execution",
                "allowed_tools",
                "exclude_tools",
                "custom_tools",  # Custom tools configuration (processed separately)
                "_has_files_api_files",
            },
        )

    def get_provider_tools(self, all_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get provider tools for Claude format (server-side tools)."""
        provider_tools = []

        if all_params.get("enable_web_search", False):
            provider_tools.append(
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                },
            )

        if all_params.get("enable_code_execution", False):
            provider_tools.append(
                {
                    "type": "code_execution_20250522",
                    "name": "code_execution",
                },
            )

        return provider_tools

    async def build_api_params(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        all_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build Claude API parameters."""
        # Convert messages to Claude format and extract system message
        converted_messages, system_message = self.formatter.format_messages_and_system(messages)

        # Build base parameters
        api_params: Dict[str, Any] = {
            "messages": converted_messages,
            "stream": True,
        }

        # Add filtered parameters
        excluded = self.get_excluded_params()
        for key, value in all_params.items():
            if key not in excluded and value is not None:
                api_params[key] = value

        # Claude API requires max_tokens - add default if not provided
        if "max_tokens" not in api_params:
            api_params["max_tokens"] = 4096

        # Handle multiple betas (code execution and files API)
        betas_list = []
        if all_params.get("enable_code_execution"):
            betas_list.append("code-execution-2025-05-22")
        if all_params.get("_has_files_api_files"):
            betas_list.append("files-api-2025-04-14")
        if betas_list:
            api_params["betas"] = betas_list

        # Remove internal flag so it doesn't leak
        all_params.pop("_has_files_api_files", None)

        # Add system message if present
        if system_message:
            api_params["system"] = system_message

        combined_tools = []

        # Server-side tools (provider tools) go first
        provider_tools = self.get_provider_tools(all_params)
        if provider_tools:
            combined_tools.extend(provider_tools)

        # Workflow tools
        if tools:
            converted_tools = self.formatter.format_tools(tools)
            combined_tools.extend(converted_tools)

        # Add custom tools
        custom_tools = self.custom_tool_manager.registered_tools
        if custom_tools:
            converted_custom_tools = self.formatter.format_custom_tools(custom_tools)
            combined_tools.extend(converted_custom_tools)

        # MCP tools
        mcp_tools = self.get_mcp_tools()
        if mcp_tools:
            combined_tools.extend(mcp_tools)

        if combined_tools:
            api_params["tools"] = combined_tools

        return api_params
