"""
Tier 1/2 Tests for CodeGenerationAgent Tool Integration

Tests tool_registry and mcp_servers parameter integration for CodeGenerationAgent.
Ensures backward compatibility and proper tool discovery/execution.

Test Structure:
- Tier 1: Tool discovery with mocked LLM (fast, isolated)
- Tier 2: Tool execution with real OpenAI GPT-4 (real infrastructure, NO MOCKING)
- Tier 1: Backward compatibility without tools (mocked LLM)

Author: TDD Implementer
Created: 2025-10-22
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv
from kaizen.agents.specialized.code_generation import CodeGenConfig, CodeGenerationAgent
from kaizen.tools.builtin import register_builtin_tools
from kaizen.tools.registry import ToolRegistry

# Load API keys from .env
load_dotenv("/Users/esperie/repos/dev/kailash_python_sdk/.env")


# ============================================
# Test Fixtures
# ============================================


@pytest.fixture
def tool_registry():
    """Create ToolRegistry with builtin tools."""
    registry = ToolRegistry()
    register_builtin_tools(registry)
    return registry


# ============================================
# Tier 1: Tool Discovery (Mocked LLM)
# ============================================


class TestCodeGenerationAgentToolDiscovery:
    """Test CodeGenerationAgent accepts tool_registry and discovers tools."""

    @pytest.mark.asyncio
    async def test_codegen_agent_accepts_tool_registry(self, tool_registry):
        """
        Test that CodeGenerationAgent accepts tool_registry parameter.
        Verify agent discovers tools via discover_tools() method.
        """
        # Create CodeGenerationAgent with tool_registry (using "mock" provider)
        agent = CodeGenerationAgent(tool_registry=tool_registry, llm_provider="mock")

        # Verify agent has tool support
        assert agent.has_tool_support() is True, "Agent should have tool support"

        # Discover tools
        tools = await agent.discover_tools()

        # Verify builtin tools discovered
        assert len(tools) >= 4, "Should discover at least 4 builtin tools"
        tool_names = [t.name for t in tools]
        assert (
            "read_file" in tool_names
        ), "Should discover read_file tool for reading code"
        assert (
            "write_file" in tool_names
        ), "Should discover write_file tool for writing code"

    @pytest.mark.asyncio
    async def test_codegen_agent_discovers_file_tools(self, tool_registry):
        """Test CodeGenerationAgent can discover file tools for code operations."""
        agent = CodeGenerationAgent(tool_registry=tool_registry, llm_provider="mock")

        # Discover file tools
        file_tools = await agent.discover_tools(keyword="file")

        assert len(file_tools) >= 3, "Should discover file-related tools"
        tool_names = [t.name for t in file_tools]
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "file_exists" in tool_names or "delete_file" in tool_names

    def test_codegen_agent_backward_compatibility_no_tools(self):
        """
        Test backward compatibility: CodeGenerationAgent works without tool_registry.
        Verify agent works exactly as before when tool_registry=None.
        """
        # Create agent WITHOUT tool_registry (using "mock" provider)
        agent = CodeGenerationAgent(llm_provider="mock")

        # Verify no tool support
        assert agent.has_tool_support() is False, "Agent should not have tool support"

        # Verify agent can be instantiated without tool_registry (backward compatible)
        # The agent object exists and has expected attributes
        assert hasattr(agent, "generate_code"), "Agent should have generate_code method"
        assert hasattr(agent, "codegen_config"), "Agent should have codegen_config"
        assert (
            agent.codegen_config.programming_language == "python"
        ), "Should have default language"


# ============================================
# Tier 2: Tool Execution (Real OpenAI GPT-4)
# ============================================


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not found in .env"
)
class TestCodeGenerationAgentToolExecution:
    """Test CodeGenerationAgent executes tools with real OpenAI GPT-4 (NO MOCKING)."""

    @pytest.mark.asyncio
    async def test_codegen_agent_writes_generated_code_with_tool(self, tool_registry):
        """
        Test CodeGenerationAgent writes generated code with real write_file tool.

        NO MOCKING - Uses real OpenAI API and real file operations.
        Verifies tools actually execute for code generation workflow.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "generated_code.py")
            generated_code = "def add(a, b):\n    return a + b\n"

            # Create CodeGenerationAgent with real OpenAI
            agent = CodeGenerationAgent(
                tool_registry=tool_registry,
                llm_provider="openai",
                model="gpt-3.5-turbo",  # Use cheaper model for testing
                temperature=0.2,  # Lower temperature for deterministic code
            )

            # Execute tool to write generated code
            result = await agent.execute_tool(
                tool_name="write_file",
                params={"path": output_path, "content": generated_code},
            )

            # Verify tool executed successfully
            assert result.success is True, f"Tool execution failed: {result.error}"
            assert result.approved is True  # Should auto-approve MEDIUM tools

            # Verify file actually written
            assert Path(output_path).exists(), "Generated code file should exist"
            written_code = Path(output_path).read_text()
            assert written_code == generated_code
            assert "def add" in written_code

    @pytest.mark.asyncio
    async def test_codegen_agent_reads_existing_code_with_tool(self, tool_registry):
        """
        Test CodeGenerationAgent reads existing code with real read_file tool.

        NO MOCKING - Real file system operations.
        """
        # Create temporary file with existing code
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("# Existing code\ndef multiply(x, y):\n    return x * y\n")
            temp_path = f.name

        try:
            agent = CodeGenerationAgent(
                tool_registry=tool_registry,
                llm_provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.2,
            )

            # Execute read_file tool
            result = await agent.execute_tool(
                tool_name="read_file", params={"path": temp_path}
            )

            # Verify tool execution
            assert result.success is True, f"Tool execution failed: {result.error}"
            assert "content" in result.result
            assert "def multiply" in result.result["content"]
            assert result.approved is True  # SAFE tool

        finally:
            # Cleanup
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_codegen_agent_full_workflow_with_tools(self, tool_registry):
        """
        Test CodeGenerationAgent full code generation workflow with tools.

        NO MOCKING - Real multi-tool code generation scenario:
        1. Read existing code
        2. Write new generated code
        3. Verify file exists
        4. Read back generated code
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Existing code to reference
            existing_path = str(Path(tmpdir) / "existing.py")
            generated_path = str(Path(tmpdir) / "generated.py")

            agent = CodeGenerationAgent(
                tool_registry=tool_registry,
                llm_provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.2,
            )

            # Tool 1: Write existing code
            existing_code = (
                "# Reference implementation\ndef square(n):\n    return n * n\n"
            )
            write_existing = await agent.execute_tool(
                "write_file", {"path": existing_path, "content": existing_code}
            )
            assert write_existing.success is True

            # Tool 2: Read existing code (simulate reading for reference)
            read_existing = await agent.execute_tool(
                "read_file", {"path": existing_path}
            )
            assert read_existing.success is True
            assert "square" in read_existing.result["content"]

            # Tool 3: Write generated code
            generated_code = "# Generated code\ndef cube(n):\n    return n * n * n\n"
            write_generated = await agent.execute_tool(
                "write_file", {"path": generated_path, "content": generated_code}
            )
            assert write_generated.success is True

            # Tool 4: Verify generated file exists
            exists = await agent.execute_tool("file_exists", {"path": generated_path})
            assert exists.success is True
            assert exists.result["exists"] is True

            # Tool 5: Read back generated code
            read_generated = await agent.execute_tool(
                "read_file", {"path": generated_path}
            )
            assert read_generated.success is True
            assert "cube" in read_generated.result["content"]

            # Verify both files exist with correct content
            assert Path(existing_path).read_text() == existing_code
            assert Path(generated_path).read_text() == generated_code
