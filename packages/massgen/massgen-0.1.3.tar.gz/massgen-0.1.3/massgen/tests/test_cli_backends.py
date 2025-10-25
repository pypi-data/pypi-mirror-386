#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for CLI backends - Claude Code CLI and Gemini CLI integration.

This script tests the basic functionality of CLI backends without requiring
the actual CLI tools to be installed (mocked for testing).

TODO: This file is outdated - ClaudeCodeCLIBackend was removed, only SDK-based ClaudeCodeBackend remains.
Update tests to reflect current backend architecture.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # from massgen.backend.claude_code_cli import ClaudeCodeCLIBackend  # File removed
    from massgen.backend.cli_base import CLIBackend
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class MockCLIBackend(CLIBackend):
    """Mock CLI backend for testing purposes."""

    def __init__(self, cli_command: str, mock_output: str = "Mock response", **kwargs):
        self.mock_output = mock_output
        # Skip the actual CLI tool check
        self.cli_command = cli_command
        self.working_dir = kwargs.get("working_dir", Path.cwd())
        self.timeout = kwargs.get("timeout", 300)
        self.config = kwargs
        from massgen.backend.base import TokenUsage

        self.token_usage = TokenUsage()

    def _build_command(self, messages, tools, **kwargs):
        return ["echo", "mock command"]

    def _parse_output(self, output):
        return {"content": self.mock_output, "tool_calls": [], "raw_response": output}

    async def _execute_cli_command(self, command):
        """Mock command execution."""
        await asyncio.sleep(0.1)  # Simulate some delay
        return self.mock_output

    def get_cost_per_token(self):
        """Mock cost per token."""
        return {"input": 0.001, "output": 0.002}


async def test_cli_base_functionality():
    """Test the CLI base class functionality."""
    print("🧪 Testing CLI base functionality...")

    backend = MockCLIBackend("mock-cli", "Hello from mock CLI!")

    messages = [{"role": "user", "content": "Test message"}]
    tools = []

    chunks = []
    async for chunk in backend.stream_with_tools(messages, tools):
        chunks.append(chunk)

    assert len(chunks) > 0, "Should produce at least one chunk"
    assert any(chunk.type == "content" for chunk in chunks), "Should have content chunk"
    assert any(chunk.type == "done" for chunk in chunks), "Should have done chunk"

    print("✅ CLI base functionality test passed")


def test_claude_code_cli_command_building():
    """Test Claude Code CLI command building (without executing) - SKIPPED: File removed."""
    print("🧪 Testing Claude Code CLI command building... SKIPPED (file removed)")
    print("✅ Claude Code CLI command building test skipped")

    # NOTE: ClaudeCodeCLIBackend was removed, only ClaudeCodeBackend (SDK-based) remains


def test_configuration_files():
    """Test that configuration files are valid."""
    print("🧪 Testing configuration files...")

    import yaml

    config_files = [
        "massgen/configs/claude_code_cli.yaml",
        "massgen/configs/cli_backends_mixed.yaml",
    ]

    for config_file in config_files:
        if Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                assert config is not None, f"Config {config_file} should not be empty"
                print(f"✅ {config_file} is valid")
            except Exception as e:
                print(f"❌ {config_file} is invalid: {e}")
                raise
        else:
            print(f"⚠️  {config_file} not found, skipping")


async def test_end_to_end_mock():
    """Test end-to-end functionality with mocked CLI execution."""
    print("🧪 Testing end-to-end with mock execution...")

    # Test Claude Code CLI mock
    claude_backend = MockCLIBackend("claude", '{"response": "4", "reasoning": "2+2 equals 4"}')

    messages = [{"role": "user", "content": "What is 2+2?"}]
    tools = []

    chunks = []
    async for chunk in claude_backend.stream_with_tools(messages, tools):
        chunks.append(chunk)
        print(f"  📝 Chunk: {chunk.type} - {chunk.content}")

    assert len(chunks) >= 3, "Should have content, complete_message, and done chunks"

    print("✅ End-to-end mock test passed")


async def main():
    """Run all tests."""
    print("🚀 Starting CLI backend tests...\n")

    try:
        # Test basic functionality
        await test_cli_base_functionality()
        print()

        # Test command building
        test_claude_code_cli_command_building()
        print()

        # Test configuration files
        test_configuration_files()
        print()

        # Test end-to-end mock
        await test_end_to_end_mock()
        print()

        print("🎉 All CLI backend tests passed!")

        # Show usage information
        print("\n📋 Usage Information:")
        print("CLI backends are now available in MassGen!")
        print()
        print("Prerequisites:")
        print("  • Claude Code CLI: npm install -g @anthropic-ai/claude-code")
        print("  • Gemini CLI: npm install -g @google/gemini-cli")
        print()
        print("Usage examples:")
        print("  # Claude Code (SDK-based)")
        print("  uv run python -m massgen.cli --backend claude_code --model claude-sonnet-4-20250514 'What is 2+2?'")
        print()
        print("  # Mixed CLI backends")
        print("  uv run python -m massgen.cli --config massgen/configs/cli_backends_mixed.yaml 'Complex question'")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
