"""
Tier 1 Unit Tests for BaseAgent MCP Integration

Tests MCP (Model Context Protocol) integration with BaseAgent:
- MCP server configuration in __init__
- Tool discovery from MCP servers
- Tool execution with server routing
- Resource and prompt discovery
- Error handling and validation

Coverage Target: 100% for new MCP methods
Test Strategy: TDD - Tests written BEFORE implementation
Infrastructure: Mocked MCPClient for fast tests
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from kaizen.core.base_agent import BaseAgent, BaseAgentConfig
from kaizen.signatures import InputField, OutputField, Signature

# ============================================
# Test Fixtures
# ============================================


@pytest.fixture
def simple_signature():
    """Create a simple test signature."""

    class TestSignature(Signature):
        question: str = InputField(description="Question to answer")
        answer: str = OutputField(description="Answer to question")

    return TestSignature()


@pytest.fixture
def base_config():
    """Create basic BaseAgentConfig."""
    return BaseAgentConfig(
        llm_provider="mock", model="test-model", temperature=0.7, logging_enabled=False
    )


@pytest.fixture
def mcp_servers():
    """Sample MCP server configurations."""
    return [
        {
            "name": "filesystem",
            "transport": "stdio",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-filesystem", "/data"],
        },
        {
            "name": "api-tools",
            "transport": "http",
            "url": "http://localhost:8080",
            "headers": {"Authorization": "Bearer token123"},
        },
    ]


@pytest.fixture
def mock_mcp_tools():
    """Sample MCP tools returned by discover_tools."""
    return [
        {
            "name": "read_file",
            "description": "Read file from filesystem",
            "parameters": {"path": {"type": "string", "required": True}},
        },
        {
            "name": "list_directory",
            "description": "List directory contents",
            "parameters": {"path": {"type": "string", "required": True}},
        },
    ]


# ============================================
# Initialization Tests
# ============================================


def test_init_with_mcp_servers(simple_signature, base_config, mcp_servers):
    """Test: BaseAgent initializes MCP client when mcp_servers provided."""
    agent = BaseAgent(
        config=base_config, signature=simple_signature, mcp_servers=mcp_servers
    )

    # Verify MCP client initialized
    assert hasattr(agent, "_mcp_client")
    assert hasattr(agent, "_mcp_servers")
    assert agent._mcp_servers == mcp_servers

    # Verify discovery caches initialized
    assert hasattr(agent, "_discovered_mcp_tools")
    assert hasattr(agent, "_discovered_mcp_resources")
    assert hasattr(agent, "_discovered_mcp_prompts")
    assert isinstance(agent._discovered_mcp_tools, dict)
    assert isinstance(agent._discovered_mcp_resources, dict)
    assert isinstance(agent._discovered_mcp_prompts, dict)


def test_init_without_mcp_servers(simple_signature, base_config):
    """Test: BaseAgent without mcp_servers doesn't create MCP client."""
    agent = BaseAgent(config=base_config, signature=simple_signature)

    # Verify no MCP client created
    assert hasattr(agent, "_mcp_client")
    assert agent._mcp_client is None
    assert hasattr(agent, "_mcp_servers")
    assert agent._mcp_servers is None


# ============================================
# MCP Support Detection Tests
# ============================================


def test_has_mcp_support_true(simple_signature, base_config, mcp_servers):
    """Test: has_mcp_support returns True when MCP configured."""
    agent = BaseAgent(
        config=base_config, signature=simple_signature, mcp_servers=mcp_servers
    )

    assert agent.has_mcp_support() is True


def test_has_mcp_support_false(simple_signature, base_config):
    """Test: has_mcp_support returns False when MCP not configured."""
    agent = BaseAgent(config=base_config, signature=simple_signature)

    assert agent.has_mcp_support() is False


# ============================================
# MCP Tool Discovery Tests
# ============================================


@pytest.mark.asyncio
async def test_discover_mcp_tools_no_config_raises(simple_signature, base_config):
    """Test: discover_mcp_tools raises RuntimeError if MCP not configured."""
    agent = BaseAgent(config=base_config, signature=simple_signature)

    with pytest.raises(RuntimeError, match="MCP not configured.*mcp_servers parameter"):
        await agent.discover_mcp_tools()


@pytest.mark.asyncio
async def test_discover_mcp_tools_success(
    simple_signature, base_config, mcp_servers, mock_mcp_tools
):
    """Test: discover_mcp_tools calls MCPClient and returns tools with proper naming."""
    with patch("kaizen.core.base_agent.MCPClient") as mock_client_class:
        # Setup mock
        mock_client = Mock()
        mock_client.discover_tools = AsyncMock(return_value=mock_mcp_tools)
        mock_client_class.return_value = mock_client

        agent = BaseAgent(
            config=base_config, signature=simple_signature, mcp_servers=mcp_servers
        )

        # Discover tools (discovers from ALL servers)
        tools = await agent.discover_mcp_tools()

        # Verify MCPClient.discover_tools called for both servers
        assert mock_client.discover_tools.called
        assert mock_client.discover_tools.call_count == 2

        # Verify naming convention: mcp__<serverName>__<toolName>
        # 2 tools × 2 servers = 4 total tools
        assert len(tools) == 4

        # Check first server tools
        assert tools[0]["name"] == "mcp__filesystem__read_file"
        assert tools[1]["name"] == "mcp__filesystem__list_directory"

        # Check second server tools
        assert tools[2]["name"] == "mcp__api-tools__read_file"
        assert tools[3]["name"] == "mcp__api-tools__list_directory"

        # Verify original description preserved
        assert tools[0]["description"] == "Read file from filesystem"


@pytest.mark.asyncio
async def test_discover_mcp_tools_specific_server(
    simple_signature, base_config, mcp_servers, mock_mcp_tools
):
    """Test: discover_mcp_tools filters by server_name."""
    with patch("kaizen.core.base_agent.MCPClient") as mock_client_class:
        mock_client = Mock()
        mock_client.discover_tools = AsyncMock(return_value=mock_mcp_tools)
        mock_client_class.return_value = mock_client

        agent = BaseAgent(
            config=base_config, signature=simple_signature, mcp_servers=mcp_servers
        )

        # Discover tools from specific server
        tools = await agent.discover_mcp_tools(server_name="api-tools")

        # Verify only api-tools server queried
        assert len(tools) == 2
        assert all("mcp__api-tools__" in tool["name"] for tool in tools)


@pytest.mark.asyncio
async def test_discover_mcp_tools_force_refresh(
    simple_signature, base_config, mcp_servers, mock_mcp_tools
):
    """Test: discover_mcp_tools bypasses cache with force_refresh=True."""
    with patch("kaizen.core.base_agent.MCPClient") as mock_client_class:
        mock_client = Mock()
        mock_client.discover_tools = AsyncMock(return_value=mock_mcp_tools)
        mock_client_class.return_value = mock_client

        agent = BaseAgent(
            config=base_config, signature=simple_signature, mcp_servers=mcp_servers
        )

        # First discovery
        await agent.discover_mcp_tools()
        first_call_count = mock_client.discover_tools.call_count

        # Second discovery without force_refresh (should use cache)
        await agent.discover_mcp_tools()
        assert mock_client.discover_tools.call_count == first_call_count

        # Third discovery with force_refresh (should bypass cache)
        await agent.discover_mcp_tools(force_refresh=True)
        assert mock_client.discover_tools.call_count > first_call_count


# ============================================
# MCP Tool Execution Tests
# ============================================


@pytest.mark.asyncio
async def test_execute_mcp_tool_success(
    simple_signature, base_config, mcp_servers, mock_mcp_tools
):
    """Test: execute_mcp_tool routes to correct server and calls tool."""
    with patch("kaizen.core.base_agent.MCPClient") as mock_client_class:
        mock_client = Mock()
        mock_client.discover_tools = AsyncMock(return_value=mock_mcp_tools)
        mock_client.call_tool = AsyncMock(
            return_value={"content": "file contents", "success": True}
        )
        mock_client_class.return_value = mock_client

        agent = BaseAgent(
            config=base_config, signature=simple_signature, mcp_servers=mcp_servers
        )

        # Execute tool with proper naming
        result = await agent.execute_mcp_tool(
            "mcp__filesystem__read_file", {"path": "/data/test.txt"}
        )

        # Verify MCPClient.call_tool called with correct server
        assert mock_client.call_tool.called
        call_args = mock_client.call_tool.call_args
        assert call_args[0][0] == mcp_servers[0]  # filesystem server
        assert call_args[0][1] == "read_file"  # original tool name
        assert call_args[0][2] == {"path": "/data/test.txt"}

        # Verify result returned
        assert result["content"] == "file contents"
        assert result["success"] is True


@pytest.mark.asyncio
async def test_execute_mcp_tool_invalid_name_raises(
    simple_signature, base_config, mcp_servers
):
    """Test: execute_mcp_tool raises ValueError on invalid tool name format."""
    with patch("kaizen.core.base_agent.MCPClient"):
        agent = BaseAgent(
            config=base_config, signature=simple_signature, mcp_servers=mcp_servers
        )

        # Invalid format (missing mcp__ prefix)
        with pytest.raises(ValueError, match="Invalid MCP tool name format"):
            await agent.execute_mcp_tool("read_file", {})

        # Invalid format (only one __)
        with pytest.raises(ValueError, match="Invalid MCP tool name format"):
            await agent.execute_mcp_tool("mcp__read_file", {})


@pytest.mark.asyncio
async def test_execute_mcp_tool_server_not_found_raises(
    simple_signature, base_config, mcp_servers
):
    """Test: execute_mcp_tool raises ValueError when server not found."""
    with patch("kaizen.core.base_agent.MCPClient"):
        agent = BaseAgent(
            config=base_config, signature=simple_signature, mcp_servers=mcp_servers
        )

        # Server not in mcp_servers list
        with pytest.raises(ValueError, match="MCP server.*not found"):
            await agent.execute_mcp_tool("mcp__unknown__read_file", {})


# ============================================
# discover_tools Integration Tests
# ============================================


@pytest.mark.asyncio
async def test_discover_tools_merges_builtin_and_mcp(
    simple_signature, base_config, mcp_servers, mock_mcp_tools
):
    """Test: discover_tools merges builtin tools and MCP tools when include_mcp=True."""
    from kaizen.tools.registry import ToolRegistry

    # Create agent with both tool registry and MCP
    tool_registry = ToolRegistry()

    def read_local_impl(params: Dict[str, Any]) -> dict:
        return {"content": "local content"}

    tool_registry.register(
        name="read_local_file",
        description="Read local file",
        category="system",
        danger_level="safe",
        parameters=[],
        returns={},
        executor=read_local_impl,
    )

    with patch("kaizen.core.base_agent.MCPClient") as mock_client_class:
        mock_client = Mock()
        mock_client.discover_tools = AsyncMock(return_value=mock_mcp_tools)
        mock_client_class.return_value = mock_client

        agent = BaseAgent(
            config=base_config,
            signature=simple_signature,
            tool_registry=tool_registry,
            mcp_servers=mcp_servers,
        )

        # Discover all tools
        tools = await agent.discover_tools(include_mcp=True)

        # Verify both builtin and MCP tools included
        tool_names = [t.name for t in tools]
        assert "read_local_file" in tool_names  # builtin
        assert "mcp__filesystem__read_file" in tool_names  # MCP


@pytest.mark.asyncio
async def test_discover_tools_builtin_only(
    simple_signature, base_config, mcp_servers, mock_mcp_tools
):
    """Test: discover_tools excludes MCP tools when include_mcp=False."""
    from kaizen.tools.registry import ToolRegistry

    tool_registry = ToolRegistry()

    def read_local_impl(params: Dict[str, Any]) -> dict:
        return {"content": "local content"}

    tool_registry.register(
        name="read_local_file",
        description="Read local file",
        category="system",
        danger_level="safe",
        parameters=[],
        returns={},
        executor=read_local_impl,
    )

    with patch("kaizen.core.base_agent.MCPClient") as mock_client_class:
        mock_client = Mock()
        mock_client.discover_tools = AsyncMock(return_value=mock_mcp_tools)
        mock_client_class.return_value = mock_client

        agent = BaseAgent(
            config=base_config,
            signature=simple_signature,
            tool_registry=tool_registry,
            mcp_servers=mcp_servers,
        )

        # Discover builtin tools only
        tools = await agent.discover_tools(include_mcp=False)

        # Verify only builtin tools included
        tool_names = [t.name for t in tools]
        assert "read_local_file" in tool_names
        assert not any("mcp__" in name for name in tool_names)


# ============================================
# MCP Resource Discovery Tests
# ============================================


@pytest.mark.asyncio
async def test_discover_mcp_resources_requires_mcp(simple_signature, base_config):
    """Test: discover_mcp_resources raises RuntimeError if MCP not configured."""
    agent = BaseAgent(config=base_config, signature=simple_signature)

    with pytest.raises(RuntimeError, match="MCP not configured"):
        await agent.discover_mcp_resources("filesystem")


# ============================================
# MCP Resource Read Tests
# ============================================


@pytest.mark.asyncio
async def test_read_mcp_resource_requires_mcp(simple_signature, base_config):
    """Test: read_mcp_resource raises RuntimeError if MCP not configured."""
    agent = BaseAgent(config=base_config, signature=simple_signature)

    with pytest.raises(RuntimeError, match="MCP not configured"):
        await agent.read_mcp_resource("filesystem", "file:///data/test.txt")


# ============================================
# Summary
# ============================================
# Total Tests: 15 (minimum requirement met)
# Coverage Areas:
# - Initialization: 2 tests
# - MCP Support Detection: 2 tests
# - Tool Discovery: 4 tests
# - Tool Execution: 3 tests
# - discover_tools Integration: 2 tests
# - Resource Discovery/Read: 2 tests
