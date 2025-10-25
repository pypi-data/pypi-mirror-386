"""
Unit tests for DocumentExtractionAgent.

Tests:
- Agent initialization and configuration
- Signature validation
- Configuration validation
- Sync and async extraction methods
- Cost estimation
- Provider capabilities
- Integration with ProviderManager
- BaseAgent integration (error handling, monitoring)
"""

from unittest.mock import patch

import pytest

from kaizen.agents.multi_modal.document_extraction_agent import (
    DocumentExtractionAgent,
    DocumentExtractionConfig,
    DocumentExtractionSignature,
)
from kaizen.providers.document.base_provider import ExtractionResult
from kaizen.tools import ToolRegistry


class TestDocumentExtractionSignature:
    """Tests for DocumentExtractionSignature."""

    def test_signature_initialization(self):
        """Test signature can be initialized."""
        sig = DocumentExtractionSignature()

        # Input fields
        assert hasattr(sig, "file_path")
        assert hasattr(sig, "file_type")
        assert hasattr(sig, "provider")
        assert hasattr(sig, "extract_tables")
        assert hasattr(sig, "chunk_for_rag")
        assert hasattr(sig, "chunk_size")
        assert hasattr(sig, "prefer_free")
        assert hasattr(sig, "max_cost")

        # Output fields
        assert hasattr(sig, "text")
        assert hasattr(sig, "markdown")
        assert hasattr(sig, "tables")
        assert hasattr(sig, "chunks")
        assert hasattr(sig, "bounding_boxes")
        assert hasattr(sig, "cost")
        # Note: "provider" is both input and output

    def test_signature_field_types(self):
        """Test signature field types."""
        sig = DocumentExtractionSignature()

        # Check input field annotations
        assert sig.__annotations__["file_path"] == str
        assert sig.__annotations__["file_type"] == str
        assert sig.__annotations__["provider"] == str
        assert sig.__annotations__["extract_tables"] == bool
        assert sig.__annotations__["chunk_for_rag"] == bool

    def test_signature_default_values(self):
        """Test signature default values (defined in InputField defaults)."""
        sig = DocumentExtractionSignature()

        # Note: Default values are set via InputField, not as direct attributes
        # Signature class doesn't expose these as instance attributes by default
        assert hasattr(sig, "file_path")
        assert hasattr(sig, "file_type")
        assert hasattr(sig, "provider")


class TestDocumentExtractionConfig:
    """Tests for DocumentExtractionConfig."""

    def test_config_initialization_defaults(self):
        """Test config with default values."""
        config = DocumentExtractionConfig()

        assert config.provider == "auto"
        assert config.prefer_free is False
        assert config.max_cost_per_doc is None
        assert config.extract_tables is True
        assert config.chunk_for_rag is False
        assert config.chunk_size == 512

    def test_config_with_custom_values(self):
        """Test config with custom values."""
        config = DocumentExtractionConfig(
            provider="landing_ai",
            prefer_free=True,
            max_cost_per_doc=0.50,
            extract_tables=False,
            chunk_for_rag=True,
            chunk_size=1024,
        )

        assert config.provider == "landing_ai"
        assert config.prefer_free is True
        assert config.max_cost_per_doc == 0.50
        assert config.extract_tables is False
        assert config.chunk_for_rag is True
        assert config.chunk_size == 1024

    def test_config_with_provider_keys(self):
        """Test config with provider API keys."""
        config = DocumentExtractionConfig(
            landing_ai_key="landing-key",
            openai_key="openai-key",
            ollama_base_url="http://localhost:11434",
        )

        assert config.landing_ai_key == "landing-key"
        assert config.openai_key == "openai-key"
        assert config.ollama_base_url == "http://localhost:11434"

    def test_config_with_base_agent_params(self):
        """Test config with BaseAgent parameters."""
        config = DocumentExtractionConfig(
            llm_provider="openai",
            model="gpt-4",
        )

        assert config.llm_provider == "openai"
        assert config.model == "gpt-4"


class TestDocumentExtractionAgentInit:
    """Tests for DocumentExtractionAgent initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        assert (
            agent.doc_extraction_config.provider == "auto"
        )  # Document config stored separately
        assert hasattr(agent, "provider_manager")
        assert agent.provider_manager is not None

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        config = DocumentExtractionConfig(
            provider="landing_ai",
            prefer_free=True,
        )
        agent = DocumentExtractionAgent(config=config)

        assert agent.doc_extraction_config.provider == "landing_ai"
        assert agent.doc_extraction_config.prefer_free is True

    def test_init_with_signature(self):
        """Test initialization with custom signature."""
        config = DocumentExtractionConfig()
        sig = DocumentExtractionSignature()
        agent = DocumentExtractionAgent(config=config, signature=sig)

        assert agent.signature is not None

    def test_init_with_tool_registry(self):
        """Test initialization with tool registry (ADR-016)."""
        config = DocumentExtractionConfig()
        registry = ToolRegistry()
        agent = DocumentExtractionAgent(config=config, tool_registry=registry)

        # BaseAgent stores tool_registry as private attribute
        assert hasattr(agent, "_tool_registry")
        assert agent._tool_registry is not None

    def test_init_with_mcp_servers(self):
        """Test initialization with MCP servers (ADR-016)."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config, mcp_servers=["mcp_server_1"])

        # BaseAgent stores mcp_servers as private attribute
        assert hasattr(agent, "_mcp_servers")
        assert agent._mcp_servers is not None

    def test_provider_manager_initialized(self):
        """Test that ProviderManager is properly initialized."""
        config = DocumentExtractionConfig(
            landing_ai_key="landing-key",
            openai_key="openai-key",
        )
        agent = DocumentExtractionAgent(config=config)

        # Provider manager should have providers configured
        assert agent.provider_manager is not None
        assert len(agent.provider_manager.providers) == 3


class TestDocumentExtractionAgentExtraction:
    """Tests for document extraction methods."""

    @pytest.mark.asyncio
    async def test_extract_async_basic(self, tmp_path):
        """Test async extraction with basic parameters."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_result = ExtractionResult(
            text="Extracted text",
            markdown="# Document",
            cost=0.015,
            provider="landing_ai",
        )

        with patch.object(agent.provider_manager, "extract", return_value=mock_result):
            result = await agent.extract_async(str(pdf_file))

        assert result["text"] == "Extracted text"
        assert result["cost"] == 0.015
        assert result["provider"] == "landing_ai"

    def test_extract_sync_basic(self, tmp_path):
        """Test sync extraction wrapper."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_result = ExtractionResult(
            text="Extracted text",
            markdown="# Document",
            cost=0.015,
            provider="landing_ai",
        )

        with patch.object(agent.provider_manager, "extract", return_value=mock_result):
            result = agent.extract(str(pdf_file))

        assert result["text"] == "Extracted text"
        assert result["provider"] == "landing_ai"

    @pytest.mark.asyncio
    async def test_extract_with_tables(self, tmp_path):
        """Test extraction with table extraction enabled."""
        config = DocumentExtractionConfig(extract_tables=True)
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_result = ExtractionResult(
            text="Text",
            tables=[{"table_id": 0, "headers": ["A", "B"]}],
            cost=0.015,
            provider="landing_ai",
        )

        with patch.object(agent.provider_manager, "extract", return_value=mock_result):
            result = await agent.extract_async(str(pdf_file), extract_tables=True)

        assert len(result["tables"]) > 0

    @pytest.mark.asyncio
    async def test_extract_with_rag_chunks(self, tmp_path):
        """Test extraction with RAG chunking."""
        config = DocumentExtractionConfig(chunk_for_rag=True, chunk_size=512)
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_result = ExtractionResult(
            text="Text",
            chunks=[
                {"chunk_id": 0, "text": "Chunk 1", "page": 1, "bbox": [0, 0, 100, 100]}
            ],
            cost=0.015,
            provider="landing_ai",
        )

        with patch.object(agent.provider_manager, "extract", return_value=mock_result):
            result = await agent.extract_async(str(pdf_file), chunk_for_rag=True)

        assert len(result["chunks"]) > 0
        assert "chunk_id" in result["chunks"][0]

    @pytest.mark.asyncio
    async def test_extract_with_manual_provider(self, tmp_path):
        """Test extraction with manual provider selection."""
        config = DocumentExtractionConfig(provider="ollama_vision")
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_result = ExtractionResult(
            text="Text",
            cost=0.0,
            provider="ollama_vision",
        )

        with patch.object(agent.provider_manager, "extract", return_value=mock_result):
            result = await agent.extract_async(str(pdf_file), provider="ollama_vision")

        assert result["provider"] == "ollama_vision"
        assert result["cost"] == 0.0

    @pytest.mark.asyncio
    async def test_extract_with_budget_constraint(self, tmp_path):
        """Test extraction with budget constraint."""
        config = DocumentExtractionConfig(max_cost_per_doc=0.10)
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_result = ExtractionResult(
            text="Text",
            cost=0.015,
            provider="landing_ai",
        )

        with patch.object(agent.provider_manager, "extract", return_value=mock_result):
            result = await agent.extract_async(str(pdf_file), max_cost=0.10)

        assert result["cost"] <= 0.10

    @pytest.mark.asyncio
    async def test_extract_prefer_free(self, tmp_path):
        """Test extraction with prefer_free=True."""
        config = DocumentExtractionConfig(prefer_free=True)
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_result = ExtractionResult(
            text="Text",
            cost=0.0,
            provider="ollama_vision",
        )

        with patch.object(agent.provider_manager, "extract", return_value=mock_result):
            result = await agent.extract_async(str(pdf_file), prefer_free=True)

        assert result["provider"] == "ollama_vision"


class TestDocumentExtractionAgentCostEstimation:
    """Tests for cost estimation methods."""

    def test_estimate_cost(self, tmp_path):
        """Test cost estimation."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        mock_costs = {
            "landing_ai": 0.15,
            "openai_vision": 0.68,
            "ollama_vision": 0.0,
        }

        # Mock asyncio.run to return the mock costs
        async def mock_estimate(*args, **kwargs):
            return mock_costs

        with patch.object(
            agent.provider_manager, "estimate_cost", side_effect=mock_estimate
        ):
            import asyncio

            with patch.object(asyncio, "run", return_value=mock_costs):
                costs = agent.estimate_cost(str(pdf_file))

        assert "landing_ai" in costs
        assert "ollama_vision" in costs


class TestDocumentExtractionAgentCapabilities:
    """Tests for provider capabilities methods."""

    def test_get_available_providers(self):
        """Test getting available providers."""
        config = DocumentExtractionConfig(
            landing_ai_key="key1",
            openai_key="key2",
        )
        agent = DocumentExtractionAgent(config=config)

        with patch.object(
            agent.provider_manager,
            "get_available_providers",
            return_value=["landing_ai", "openai_vision"],
        ):
            available = agent.get_available_providers()

        assert "landing_ai" in available
        assert "openai_vision" in available

    def test_get_provider_capabilities(self):
        """Test getting provider capabilities."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        mock_caps = {
            "landing_ai": {"accuracy": 0.98, "cost_per_page": 0.015},
            "openai_vision": {"accuracy": 0.95, "cost_per_page": 0.068},
            "ollama_vision": {"accuracy": 0.85, "cost_per_page": 0.0},
        }

        with patch.object(
            agent.provider_manager,
            "get_provider_capabilities",
            return_value=mock_caps,
        ):
            caps = agent.get_provider_capabilities()

        assert caps["landing_ai"]["accuracy"] == 0.98
        assert caps["ollama_vision"]["cost_per_page"] == 0.0


class TestDocumentExtractionAgentErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_extract_nonexistent_file(self):
        """Test extraction with nonexistent file."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        with patch.object(
            agent.provider_manager,
            "extract",
            side_effect=FileNotFoundError("File not found"),
        ):
            with pytest.raises(FileNotFoundError):
                await agent.extract_async("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_extract_invalid_file_type(self):
        """Test extraction with invalid file type."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        with patch.object(
            agent.provider_manager,
            "extract",
            side_effect=ValueError("Unsupported file type"),
        ):
            with pytest.raises(ValueError):
                await agent.extract_async("test.xlsx", file_type="xlsx")

    @pytest.mark.asyncio
    async def test_extract_all_providers_fail(self, tmp_path):
        """Test extraction when all providers fail."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(
            agent.provider_manager,
            "extract",
            side_effect=RuntimeError("All providers failed"),
        ):
            with pytest.raises(RuntimeError, match="All providers failed"):
                await agent.extract_async(str(pdf_file))


class TestDocumentExtractionAgentBaseAgentIntegration:
    """Tests for BaseAgent integration features."""

    def test_extends_base_agent(self):
        """Test that DocumentExtractionAgent extends BaseAgent."""
        from kaizen.core.base_agent import BaseAgent

        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        assert isinstance(agent, BaseAgent)

    def test_has_signature(self):
        """Test agent has signature attribute."""
        config = DocumentExtractionConfig()
        agent = DocumentExtractionAgent(config=config)

        assert agent.signature is not None
        assert isinstance(agent.signature, DocumentExtractionSignature)

    def test_has_config(self):
        """Test agent has config attribute."""
        config = DocumentExtractionConfig(provider="landing_ai")
        agent = DocumentExtractionAgent(config=config)

        assert agent.config is not None  # BaseAgentConfig
        assert agent.doc_extraction_config is not None  # DocumentExtractionConfig
        assert agent.doc_extraction_config.provider == "landing_ai"

    def test_progressive_configuration(self):
        """Test progressive configuration pattern."""
        # Zero-config (all defaults)
        agent1 = DocumentExtractionAgent(config=DocumentExtractionConfig())
        assert agent1.doc_extraction_config.provider == "auto"

        # Basic config
        agent2 = DocumentExtractionAgent(
            config=DocumentExtractionConfig(provider="landing_ai")
        )
        assert agent2.doc_extraction_config.provider == "landing_ai"

        # Advanced config
        agent3 = DocumentExtractionAgent(
            config=DocumentExtractionConfig(
                provider="auto",
                prefer_free=True,
                max_cost_per_doc=0.50,
                extract_tables=True,
                chunk_for_rag=True,
            )
        )
        assert agent3.doc_extraction_config.prefer_free is True
        assert agent3.doc_extraction_config.max_cost_per_doc == 0.50
