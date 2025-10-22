"""
Unit tests for BaseAgent tool documentation in system prompts.

Tests TODO-162 Phase 2: BaseAgent Prompt Integration.
"""

import pytest
from kaizen.core.base_agent import BaseAgent
from kaizen.core.config import BaseAgentConfig
from kaizen.signatures import InputField, OutputField, Signature
from kaizen.tools.registry import ToolRegistry
from kaizen.tools.types import DangerLevel, ToolCategory, ToolParameter


class SampleSignature(Signature):
    """Sample signature for prompt generation testing."""

    query: str = InputField(desc="User query")
    answer: str = OutputField(desc="Agent answer")
    tool_calls: list = OutputField(desc="Tools to call")


class TestBaseAgentToolPrompts:
    """Test BaseAgent includes tool documentation in system prompts."""

    @pytest.fixture
    def config(self):
        """Create base agent config."""
        return BaseAgentConfig(
            llm_provider="openai", model="gpt-3.5-turbo", temperature=0.7
        )

    @pytest.fixture
    def tool_registry(self):
        """Create tool registry with sample tools."""
        registry = ToolRegistry()

        # Register file reading tool
        registry.register(
            name="read_file",
            description="Read contents of a file",
            category=ToolCategory.SYSTEM,
            danger_level=DangerLevel.LOW,
            parameters=[ToolParameter("path", str, "File path to read", required=True)],
            returns={"content": "str"},
            executor=lambda path: {"content": f"File: {path}"},
            examples=[
                {
                    "name": "read_file",
                    "params": {"path": "data.txt"},
                    "result": {"content": "Hello World"},
                }
            ],
        )

        # Register HTTP GET tool
        registry.register(
            name="http_get",
            description="Make an HTTP GET request",
            category=ToolCategory.NETWORK,
            danger_level=DangerLevel.LOW,
            parameters=[ToolParameter("url", str, "URL to fetch", required=True)],
            returns={"status": "int", "body": "str"},
            executor=lambda url: {"status": 200, "body": "OK"},
        )

        return registry

    def test_system_prompt_without_tools(self, config):
        """Test system prompt when no tool registry is provided."""
        agent = BaseAgent(config=config, signature=SampleSignature())

        prompt = agent._generate_system_prompt()

        # Should have basic task description
        assert "query" in prompt
        assert "answer" in prompt
        assert "tool_calls" in prompt

        # Should NOT have tool documentation
        assert "Available Tools:" not in prompt
        assert "read_file" not in prompt

    def test_system_prompt_with_empty_registry(self, config):
        """Test system prompt with empty tool registry."""
        empty_registry = ToolRegistry()
        agent = BaseAgent(
            config=config, signature=SampleSignature(), tool_registry=empty_registry
        )

        prompt = agent._generate_system_prompt()

        # Should have basic task description (no tools to add)
        assert "query" in prompt
        assert "answer" in prompt

        # Should NOT have tool documentation (registry empty)
        assert "Available Tools:" not in prompt

    def test_system_prompt_with_tools(self, config, tool_registry):
        """Test system prompt includes tool documentation."""
        agent = BaseAgent(
            config=config, signature=SampleSignature(), tool_registry=tool_registry
        )

        prompt = agent._generate_system_prompt()

        # Should have basic task description
        assert "query" in prompt
        assert "answer" in prompt
        assert "tool_calls" in prompt

        # Should have tool documentation header
        assert "Available Tools:" in prompt

        # Should have tool names
        assert "read_file" in prompt
        assert "http_get" in prompt

        # Should have tool descriptions
        assert "Read contents of a file" in prompt
        assert "Make an HTTP GET request" in prompt

        # Should have tool calling instructions
        assert "Tool Calling Instructions" in prompt
        assert '{"tool_calls":' in prompt

        # Should have convergence instructions
        assert "When the task is complete" in prompt
        assert '{"tool_calls": []}' in prompt

    def test_system_prompt_includes_parameters(self, config, tool_registry):
        """Test system prompt includes parameter details."""
        agent = BaseAgent(
            config=config, signature=SampleSignature(), tool_registry=tool_registry
        )

        prompt = agent._generate_system_prompt()

        # Should have parameter names
        assert "path" in prompt
        assert "url" in prompt

        # Should indicate parameter types
        assert "str" in prompt

        # Should indicate required parameters
        assert "required" in prompt

    def test_system_prompt_includes_examples(self, config, tool_registry):
        """Test system prompt includes usage examples."""
        agent = BaseAgent(
            config=config, signature=SampleSignature(), tool_registry=tool_registry
        )

        prompt = agent._generate_system_prompt()

        # Should have example section
        assert "Example:" in prompt

        # Should have example content from read_file
        assert "data.txt" in prompt

    def test_system_prompt_danger_levels(self, config, tool_registry):
        """Test system prompt shows danger levels."""
        agent = BaseAgent(
            config=config, signature=SampleSignature(), tool_registry=tool_registry
        )

        prompt = agent._generate_system_prompt()

        # Should show danger levels
        assert "[LOW]" in prompt

    def test_system_prompt_preserves_base_prompt(self, config, tool_registry):
        """Test system prompt preserves base task description."""
        agent = BaseAgent(
            config=config, signature=SampleSignature(), tool_registry=tool_registry
        )

        prompt = agent._generate_system_prompt()

        # Should start with task description
        assert prompt.startswith("Task: Given")

        # Tool documentation should come after
        prompt_lines = prompt.split("\n")
        task_line_idx = 0
        tools_line_idx = next(
            i for i, line in enumerate(prompt_lines) if "Available Tools:" in line
        )

        assert (
            task_line_idx < tools_line_idx
        ), "Task description should come before tools"

    def test_system_prompt_integration(self, config, tool_registry):
        """Test full integration: prompt enables tool calling."""
        agent = BaseAgent(
            config=config, signature=SampleSignature(), tool_registry=tool_registry
        )

        prompt = agent._generate_system_prompt()

        # Verify prompt structure for LLM usage
        assert "Task:" in prompt  # Base task
        assert "Available Tools:" in prompt  # Tools section
        assert "read_file" in prompt  # Specific tool
        assert "Tool Calling Instructions" in prompt  # Usage instructions
        assert '{"tool_calls":' in prompt  # JSON format
        assert "[]" in prompt  # Convergence signal

        # Verify prompt is comprehensive
        assert len(prompt) > 500, "Prompt should be detailed enough for LLM"

        # Verify all registered tools are included
        assert "read_file" in prompt
        assert "http_get" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
