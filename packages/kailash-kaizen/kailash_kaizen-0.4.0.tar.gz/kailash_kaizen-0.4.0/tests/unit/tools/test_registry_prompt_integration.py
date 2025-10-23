"""
Unit tests for ToolRegistry prompt integration methods.

Tests the new list_tools() and format_for_prompt() methods added for
TODO-162 Phase 1: Tool Registry Introspection.
"""

import pytest
from kaizen.tools.registry import ToolRegistry
from kaizen.tools.types import DangerLevel, ToolCategory, ToolParameter


class TestToolRegistryPromptIntegration:
    """Test ToolRegistry methods for LLM prompt integration."""

    @pytest.fixture
    def registry_with_tools(self):
        """Create registry with sample tools for testing."""
        registry = ToolRegistry()

        # Register sample FILE tool
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

        # Register sample NETWORK tool
        registry.register(
            name="http_get",
            description="Make an HTTP GET request",
            category=ToolCategory.NETWORK,
            danger_level=DangerLevel.LOW,
            parameters=[
                ToolParameter("url", str, "URL to fetch", required=True),
                ToolParameter("headers", dict, "HTTP headers", required=False),
            ],
            returns={"status": "int", "body": "str"},
            executor=lambda url, headers=None: {"status": 200, "body": "OK"},
            examples=[
                {
                    "name": "http_get",
                    "params": {"url": "https://api.example.com/data"},
                    "result": {"status": 200, "body": '{"data": "value"}'},
                }
            ],
        )

        # Register sample DATA tool
        registry.register(
            name="extract_links",
            description="Extract links from HTML",
            category=ToolCategory.DATA,
            danger_level=DangerLevel.SAFE,
            parameters=[ToolParameter("html", str, "HTML content", required=True)],
            returns={"links": "list"},
            executor=lambda html: {"links": []},
        )

        return registry

    def test_list_tools_all(self, registry_with_tools):
        """Test list_tools() returns all tools."""
        tools = registry_with_tools.list_tools()

        assert len(tools) == 3, "Should return all 3 tools"
        assert all(isinstance(t, dict) for t in tools), "Should return dicts"

        # Check required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "danger_level" in tool
            assert "parameters" in tool

        # Check tool names
        names = {t["name"] for t in tools}
        assert names == {"read_file", "http_get", "extract_links"}

    def test_list_tools_by_category(self, registry_with_tools):
        """Test list_tools() with category filter."""
        # Filter by NETWORK
        network_tools = registry_with_tools.list_tools(category=ToolCategory.NETWORK)

        assert len(network_tools) == 1, "Should return 1 NETWORK tool"
        assert network_tools[0]["name"] == "http_get"

        # Filter by DATA
        data_tools = registry_with_tools.list_tools(category=ToolCategory.DATA)

        assert len(data_tools) == 1, "Should return 1 DATA tool"
        assert data_tools[0]["name"] == "extract_links"

    def test_list_tools_includes_examples(self, registry_with_tools):
        """Test list_tools() includes examples when available."""
        tools = registry_with_tools.list_tools()

        # read_file has example
        read_file = next(t for t in tools if t["name"] == "read_file")
        assert "example" in read_file, "Should include example"
        assert read_file["example"]["name"] == "read_file"
        assert read_file["example"]["params"]["path"] == "data.txt"

        # extract_links has no example
        extract_links = next(t for t in tools if t["name"] == "extract_links")
        assert "example" not in extract_links, "Should not include example if missing"

    def test_list_tools_parameter_format(self, registry_with_tools):
        """Test list_tools() formats parameters correctly."""
        tools = registry_with_tools.list_tools()

        http_get = next(t for t in tools if t["name"] == "http_get")

        assert len(http_get["parameters"]) == 2, "Should have 2 parameters"

        # Check url parameter
        url_param = http_get["parameters"][0]
        assert url_param["name"] == "url"
        assert url_param["type"] == "str"
        assert url_param["description"] == "URL to fetch"
        assert url_param["required"] is True

        # Check headers parameter
        headers_param = http_get["parameters"][1]
        assert headers_param["name"] == "headers"
        assert headers_param["type"] == "dict"
        assert headers_param["description"] == "HTTP headers"
        assert headers_param["required"] is False

    def test_format_for_prompt_all_tools(self, registry_with_tools):
        """Test format_for_prompt() with all tools."""
        prompt = registry_with_tools.format_for_prompt()

        # Check structure
        assert "Available Tools:" in prompt
        assert (
            "SYSTEM TOOLS:" in prompt
            or "NETWORK TOOLS:" in prompt
            or "DATA TOOLS:" in prompt
        )

        # Check tool names
        assert "read_file" in prompt
        assert "http_get" in prompt
        assert "extract_links" in prompt

        # Check descriptions
        assert "Read contents of a file" in prompt
        assert "Make an HTTP GET request" in prompt
        assert "Extract links from HTML" in prompt

    def test_format_for_prompt_by_category(self, registry_with_tools):
        """Test format_for_prompt() with category filter."""
        # Filter by NETWORK
        prompt = registry_with_tools.format_for_prompt(category=ToolCategory.NETWORK)

        assert "http_get" in prompt, "Should include http_get"
        assert "read_file" not in prompt, "Should not include read_file"
        assert "extract_links" not in prompt, "Should not include extract_links"

    def test_format_for_prompt_includes_parameters(self, registry_with_tools):
        """Test format_for_prompt() includes parameter details."""
        prompt = registry_with_tools.format_for_prompt(include_parameters=True)

        # Check parameter names
        assert "path" in prompt, "Should include 'path' parameter"
        assert "url" in prompt, "Should include 'url' parameter"
        assert "headers" in prompt, "Should include 'headers' parameter"

        # Check required/optional
        assert "required" in prompt, "Should indicate required parameters"
        assert "optional" in prompt, "Should indicate optional parameters"

    def test_format_for_prompt_excludes_parameters(self, registry_with_tools):
        """Test format_for_prompt() can exclude parameters."""
        prompt = registry_with_tools.format_for_prompt(include_parameters=False)

        # Tool names and descriptions should still be present
        assert "read_file" in prompt
        assert "Read contents of a file" in prompt

        # Parameters should not be detailed
        assert "Parameters:" not in prompt

    def test_format_for_prompt_includes_examples(self, registry_with_tools):
        """Test format_for_prompt() includes usage examples."""
        prompt = registry_with_tools.format_for_prompt(include_examples=True)

        # Check example markers
        assert "Example:" in prompt, "Should include example section"

        # Check example content
        assert "data.txt" in prompt, "Should include example file path"
        assert "https://api.example.com/data" in prompt, "Should include example URL"

    def test_format_for_prompt_excludes_examples(self, registry_with_tools):
        """Test format_for_prompt() can exclude examples."""
        prompt = registry_with_tools.format_for_prompt(include_examples=False)

        # Tool info should still be present
        assert "read_file" in prompt
        assert "http_get" in prompt

        # Examples should not be present
        assert "Example:" not in prompt

    def test_format_for_prompt_empty_registry(self):
        """Test format_for_prompt() with empty registry."""
        empty_registry = ToolRegistry()
        prompt = empty_registry.format_for_prompt()

        assert prompt == "No tools available.", "Should handle empty registry"

    def test_format_for_prompt_danger_levels(self, registry_with_tools):
        """Test format_for_prompt() shows danger levels."""
        prompt = registry_with_tools.format_for_prompt()

        # Check danger level indicators
        assert "[SAFE]" in prompt, "Should show SAFE danger level"
        assert "[LOW]" in prompt, "Should show LOW danger level"

    def test_list_tools_empty_registry(self):
        """Test list_tools() with empty registry."""
        empty_registry = ToolRegistry()
        tools = empty_registry.list_tools()

        assert tools == [], "Should return empty list for empty registry"

    def test_integration_prompt_for_llm(self, registry_with_tools):
        """Test full integration: format prompt for LLM usage."""
        # Get formatted prompt
        tools_text = registry_with_tools.format_for_prompt()

        # Build LLM prompt
        system_prompt = f"""
You are an AI assistant with access to tools.

{tools_text}

To use a tool, respond with JSON:
{{"tool_calls": [{{"name": "tool_name", "params": {{"param": "value"}}}}]}}

When task is complete, respond with:
{{"tool_calls": []}}
"""

        # Verify prompt structure
        assert "Available Tools:" in system_prompt
        assert "read_file" in system_prompt
        assert "http_get" in system_prompt
        assert "tool_calls" in system_prompt
        assert len(system_prompt) > 200, "Prompt should be comprehensive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
