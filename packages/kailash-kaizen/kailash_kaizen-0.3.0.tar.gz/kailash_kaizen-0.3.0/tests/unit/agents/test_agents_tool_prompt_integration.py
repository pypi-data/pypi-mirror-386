"""
Integration tests for tool prompt integration across specialized agents.

Verifies that ReActAgent, CodeGenerationAgent, and RAGResearchAgent
properly receive tool documentation in their system prompts when
initialized with a tool_registry.

Tests TODO-162 Phase 3: Agent Tool Prompt Integration.
"""

import pytest
from kaizen.agents.specialized.code_generation import CodeGenConfig, CodeGenerationAgent
from kaizen.agents.specialized.rag_research import RAGConfig, RAGResearchAgent
from kaizen.agents.specialized.react import ReActAgent, ReActConfig
from kaizen.tools.registry import ToolRegistry
from kaizen.tools.types import DangerLevel, ToolCategory, ToolParameter


class TestAgentsToolPromptIntegration:
    """Test that specialized agents receive tool documentation in prompts."""

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
        )

        # Register HTTP tool
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

    def test_react_agent_receives_tool_prompts(self, tool_registry):
        """Test ReActAgent receives tool documentation in prompt."""
        config = ReActConfig(
            llm_provider="openai", model="gpt-3.5-turbo", temperature=0.7
        )

        agent = ReActAgent(config=config, tool_registry=tool_registry)

        # Generate system prompt
        prompt = agent._generate_system_prompt()

        # Verify tool documentation is included
        assert "Available Tools:" in prompt, "Should include tools section"
        assert "read_file" in prompt, "Should include read_file tool"
        assert "http_get" in prompt, "Should include http_get tool"
        assert "Read contents of a file" in prompt, "Should include tool description"
        assert (
            "Tool Calling Instructions" in prompt
        ), "Should include calling instructions"
        assert '{"tool_calls":' in prompt, "Should show JSON format"

    def test_codegen_agent_receives_tool_prompts(self, tool_registry):
        """Test CodeGenerationAgent receives tool documentation in prompt."""
        config = CodeGenConfig(
            llm_provider="openai", model="gpt-3.5-turbo", temperature=0.7
        )

        agent = CodeGenerationAgent(config=config, tool_registry=tool_registry)

        # Generate system prompt
        prompt = agent._generate_system_prompt()

        # Verify tool documentation is included
        assert "Available Tools:" in prompt, "Should include tools section"
        assert "read_file" in prompt, "Should include read_file tool"
        assert "http_get" in prompt, "Should include http_get tool"
        assert (
            "Tool Calling Instructions" in prompt
        ), "Should include calling instructions"

    def test_rag_agent_receives_tool_prompts(self, tool_registry):
        """Test RAGResearchAgent receives tool documentation in prompt."""
        config = RAGConfig(
            llm_provider="openai", model="gpt-3.5-turbo", temperature=0.7
        )

        agent = RAGResearchAgent(config=config, tool_registry=tool_registry)

        # Generate system prompt
        prompt = agent._generate_system_prompt()

        # Verify tool documentation is included
        assert "Available Tools:" in prompt, "Should include tools section"
        assert "read_file" in prompt, "Should include read_file tool"
        assert "http_get" in prompt, "Should include http_get tool"
        assert (
            "Tool Calling Instructions" in prompt
        ), "Should include calling instructions"

    def test_agents_without_registry_no_tools(self):
        """Test agents without tool registry don't have tool documentation."""
        react_config = ReActConfig(llm_provider="openai", model="gpt-3.5-turbo")
        react_agent = ReActAgent(config=react_config)  # No tool_registry

        prompt = react_agent._generate_system_prompt()

        # Should NOT have tool documentation
        assert (
            "Available Tools:" not in prompt
        ), "Should not include tools without registry"
        assert "read_file" not in prompt, "Should not mention specific tools"
        assert (
            "Tool Calling Instructions" not in prompt
        ), "Should not have calling instructions"

    def test_agent_tool_prompt_includes_parameters(self, tool_registry):
        """Test tool prompts include parameter details."""
        config = ReActConfig(llm_provider="openai", model="gpt-3.5-turbo")
        agent = ReActAgent(config=config, tool_registry=tool_registry)

        prompt = agent._generate_system_prompt()

        # Should include parameter details
        assert "path" in prompt, "Should include path parameter"
        assert "url" in prompt, "Should include url parameter"
        assert "str" in prompt, "Should indicate parameter types"
        assert "required" in prompt, "Should indicate required parameters"

    def test_agent_tool_prompt_includes_danger_levels(self, tool_registry):
        """Test tool prompts show danger levels."""
        config = ReActConfig(llm_provider="openai", model="gpt-3.5-turbo")
        agent = ReActAgent(config=config, tool_registry=tool_registry)

        prompt = agent._generate_system_prompt()

        # Should show danger levels
        assert "[LOW]" in prompt, "Should show LOW danger level"

    def test_agent_tool_prompt_convergence_instructions(self, tool_registry):
        """Test tool prompts include convergence signal instructions."""
        config = ReActConfig(llm_provider="openai", model="gpt-3.5-turbo")
        agent = ReActAgent(config=config, tool_registry=tool_registry)

        prompt = agent._generate_system_prompt()

        # Should have convergence instructions
        assert "When the task is complete" in prompt, "Should explain convergence"
        assert (
            '{"tool_calls": []}' in prompt
        ), "Should show empty tool_calls for convergence"

    def test_multiple_agents_same_registry(self, tool_registry):
        """Test multiple agents can share same tool registry."""
        react_config = ReActConfig(llm_provider="openai", model="gpt-3.5-turbo")
        codegen_config = CodeGenConfig(llm_provider="openai", model="gpt-3.5-turbo")

        react_agent = ReActAgent(config=react_config, tool_registry=tool_registry)
        codegen_agent = CodeGenerationAgent(
            config=codegen_config, tool_registry=tool_registry
        )

        react_prompt = react_agent._generate_system_prompt()
        codegen_prompt = codegen_agent._generate_system_prompt()

        # Both should have same tools
        assert "read_file" in react_prompt
        assert "read_file" in codegen_prompt
        assert "http_get" in react_prompt
        assert "http_get" in codegen_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
