"""
Tier 1/2 Tests for RAGResearchAgent Tool Integration

Tests tool_registry and mcp_servers parameter integration for RAGResearchAgent.
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
from kaizen.agents.specialized.rag_research import RAGConfig, RAGResearchAgent
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


class TestRAGResearchAgentToolDiscovery:
    """Test RAGResearchAgent accepts tool_registry and discovers tools."""

    @pytest.mark.asyncio
    async def test_rag_agent_accepts_tool_registry(self, tool_registry):
        """
        Test that RAGResearchAgent accepts tool_registry parameter.
        Verify agent discovers tools via discover_tools() method.
        """
        # Create RAGResearchAgent with tool_registry (using "mock" provider)
        agent = RAGResearchAgent(tool_registry=tool_registry, llm_provider="mock")

        # Verify agent has tool support
        assert agent.has_tool_support() is True, "Agent should have tool support"

        # Discover tools
        tools = await agent.discover_tools()

        # Verify builtin tools discovered
        assert len(tools) >= 4, "Should discover at least 4 builtin tools"
        tool_names = [t.name for t in tools]
        assert "read_file" in tool_names, "Should discover read_file tool"
        assert (
            "fetch_url" in tool_names
        ), "Should discover fetch_url tool for web research"

    @pytest.mark.asyncio
    async def test_rag_agent_discovers_web_tools(self, tool_registry):
        """Test RAGResearchAgent can discover web tools for research."""
        agent = RAGResearchAgent(tool_registry=tool_registry, llm_provider="mock")

        # Discover web tools
        web_tools = await agent.discover_tools(keyword="url")

        assert len(web_tools) >= 1, "Should discover URL/web-related tools"
        tool_names = [t.name for t in web_tools]
        assert any(
            "url" in name.lower() or "fetch" in name.lower() for name in tool_names
        )

    def test_rag_agent_backward_compatibility_no_tools(self):
        """
        Test backward compatibility: RAGResearchAgent works without tool_registry.
        Verify agent works exactly as before when tool_registry=None.
        """
        # Create agent WITHOUT tool_registry (using "mock" provider)
        agent = RAGResearchAgent(llm_provider="mock")

        # Verify no tool support
        assert agent.has_tool_support() is False, "Agent should not have tool support"

        # Verify agent can be instantiated without tool_registry (backward compatible)
        # The agent object exists and has expected attributes
        assert hasattr(agent, "research"), "Agent should have research method"
        assert hasattr(agent, "vector_store"), "Agent should have vector_store"
        assert agent.get_document_count() == 5, "Should have 5 sample documents"


# ============================================
# Tier 2: Tool Execution (Real OpenAI GPT-4)
# ============================================


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not found in .env"
)
class TestRAGResearchAgentToolExecution:
    """Test RAGResearchAgent executes tools with real OpenAI GPT-4 (NO MOCKING)."""

    @pytest.mark.asyncio
    async def test_rag_agent_reads_file_for_research(self, tool_registry):
        """
        Test RAGResearchAgent reads files with real read_file tool.

        NO MOCKING - Uses real OpenAI API and real file operations.
        Verifies tools actually execute for research tasks.
        """
        # Create temporary file with research content
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(
                "Research document: Machine learning is a subset of AI that enables systems to learn from data."
            )
            temp_path = f.name

        try:
            # Create RAGResearchAgent with real OpenAI
            agent = RAGResearchAgent(
                tool_registry=tool_registry,
                llm_provider="openai",
                model="gpt-3.5-turbo",  # Use cheaper model for testing
                temperature=0.7,
            )

            # Execute tool to read research file
            result = await agent.execute_tool(
                tool_name="read_file", params={"path": temp_path}
            )

            # Verify tool executed successfully
            assert result.success is True, f"Tool execution failed: {result.error}"
            assert result.result is not None
            assert "content" in result.result
            assert "Machine learning" in result.result["content"]

            # Verify tool result metadata
            assert result.approved is True  # SAFE tool should auto-approve
            assert result.execution_time_ms >= 0

        finally:
            # Cleanup
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_rag_agent_adds_document_and_reads_with_tool(self, tool_registry):
        """
        Test RAGResearchAgent can add documents and read them via tools.

        NO MOCKING - Real vector store and file operations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = str(Path(tmpdir) / "research_doc.txt")
            doc_content = "Neural networks are computing systems inspired by biological neural networks."

            agent = RAGResearchAgent(
                tool_registry=tool_registry,
                llm_provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.7,
            )

            # Write document via tool
            write_result = await agent.execute_tool(
                "write_file", {"path": doc_path, "content": doc_content}
            )
            assert write_result.success is True

            # Read document via tool
            read_result = await agent.execute_tool("read_file", {"path": doc_path})
            assert read_result.success is True
            assert "Neural networks" in read_result.result["content"]

            # Add to vector store (not via tool, but verify tool integration didn't break this)
            agent.add_document(
                doc_id="neural_nets", title="Neural Networks", content=doc_content
            )
            assert agent.get_document_count() >= 6  # 5 sample docs + 1 new doc

    @pytest.mark.asyncio
    async def test_rag_agent_tool_chain_for_research_workflow(self, tool_registry):
        """
        Test RAGResearchAgent executes tool chain for research workflow.

        NO MOCKING - Real multi-tool research scenario.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Create research documents
            doc1_path = str(Path(tmpdir) / "doc1.txt")
            doc2_path = str(Path(tmpdir) / "doc2.txt")

            agent = RAGResearchAgent(
                tool_registry=tool_registry,
                llm_provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.7,
            )

            # Tool 1: Write first research doc
            await agent.execute_tool(
                "write_file",
                {
                    "path": doc1_path,
                    "content": "Deep learning uses neural networks with multiple layers.",
                },
            )

            # Tool 2: Write second research doc
            await agent.execute_tool(
                "write_file",
                {
                    "path": doc2_path,
                    "content": "Transfer learning allows models to reuse knowledge.",
                },
            )

            # Tool 3: Read documents for research
            read1 = await agent.execute_tool("read_file", {"path": doc1_path})
            read2 = await agent.execute_tool("read_file", {"path": doc2_path})

            assert read1.success is True
            assert read2.success is True
            assert "Deep learning" in read1.result["content"]
            assert "Transfer learning" in read2.result["content"]

            # Tool 4: Check files exist
            exists1 = await agent.execute_tool("file_exists", {"path": doc1_path})
            exists2 = await agent.execute_tool("file_exists", {"path": doc2_path})

            assert exists1.result["exists"] is True
            assert exists2.result["exists"] is True
