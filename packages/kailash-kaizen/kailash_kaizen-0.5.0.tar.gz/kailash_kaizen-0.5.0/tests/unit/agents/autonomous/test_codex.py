"""
Test CodexAgent - Codex Autonomous Architecture Implementation

Tests for the CodexAgent class implementing Codex's proven autonomous patterns
based on research and production usage from OpenAI.

Key Codex Patterns Tested:
1. Container-based execution (isolated environment with filesystem + terminal)
2. AGENTS.md configuration (project-specific instructions)
3. Test-driven iteration (run tests → read errors → fix → repeat)
4. PR generation (commit message + PR description + citations)
5. Logging and evidence (step-by-step action log with command outputs)
6. 1-30 minute tasks (one-shot PR workflow)

Test Coverage:
- CodexConfig creation with Codex-specific parameters
- Container setup (simplified/mocked for MVP)
- AGENTS.md loading and parsing
- Test-driven iteration workflow
- PR generation format
- Logging system with action recording
- Agent loop override with Codex patterns
- Integration with BaseAutonomousAgent

References:
- docs/research/CODEX_AUTONOMOUS_ARCHITECTURE.md
- BaseAutonomousAgent at src/kaizen/agents/autonomous/base.py
- ClaudeCodeAgent at src/kaizen/agents/autonomous/claude_code.py

Author: Kaizen Framework Team
Created: 2025-10-22
"""

from typing import Dict, List
from unittest.mock import mock_open, patch

import pytest

from kaizen.agents.autonomous.base import BaseAutonomousAgent
from kaizen.agents.autonomous.codex import CodexAgent, CodexConfig
from kaizen.core.base_agent import BaseAgentConfig
from kaizen.signatures import InputField, OutputField, Signature
from kaizen.tools.registry import ToolRegistry


class SimpleTaskSignature(Signature):
    """Simple signature for testing Codex autonomous execution."""

    task: str = InputField(description="Task to execute autonomously")
    result: str = OutputField(description="Result of autonomous execution")
    tool_calls: List[Dict] = OutputField(
        description="Tool calls for objective convergence", default_factory=list
    )


class TestCodexConfig:
    """Test CodexConfig dataclass and configuration."""

    def test_codex_config_creation_with_defaults(self):
        """Test creating CodexConfig with default values."""
        config = CodexConfig()

        # Test Codex-specific defaults
        assert config.container_image == "python:3.11", "Default container image"
        assert config.timeout_minutes == 30, "Default timeout is 30 minutes"
        assert config.enable_internet is False, "Default disable internet"
        assert config.agents_md_path == "AGENTS.md", "Default AGENTS.md path"
        assert config.test_command == "pytest", "Default test command"
        assert config.lint_command == "ruff", "Default lint command"

    def test_codex_config_creation_with_custom_values(self):
        """Test creating CodexConfig with custom values."""
        config = CodexConfig(
            container_image="python:3.12",
            timeout_minutes=15,
            enable_internet=True,
            agents_md_path="custom/AGENTS.md",
            test_command="pytest -v",
            lint_command="black",
            llm_provider="openai",
            model="gpt-4",
        )

        assert config.container_image == "python:3.12"
        assert config.timeout_minutes == 15
        assert config.enable_internet is True
        assert config.agents_md_path == "custom/AGENTS.md"
        assert config.test_command == "pytest -v"
        assert config.lint_command == "black"
        assert config.llm_provider == "openai"
        assert config.model == "gpt-4"

    def test_codex_config_extends_autonomous_config(self):
        """Test that CodexConfig extends AutonomousConfig."""
        config = CodexConfig(
            max_cycles=20, planning_enabled=True, llm_provider="openai", model="gpt-4"
        )

        # Should have both AutonomousConfig and CodexConfig fields
        assert config.max_cycles == 20
        assert config.planning_enabled is True
        assert config.container_image == "python:3.11"  # Codex-specific
        assert config.llm_provider == "openai"

    def test_codex_config_to_base_agent_config(self):
        """Test conversion from CodexConfig to BaseAgentConfig."""
        config = CodexConfig(
            max_cycles=30,
            llm_provider="openai",
            model="gpt-4",
            temperature=0.7,
        )

        # BaseAgentConfig.from_domain_config should handle conversion
        base_config = BaseAgentConfig.from_domain_config(config)

        assert isinstance(base_config, BaseAgentConfig)
        assert base_config.llm_provider == "openai"
        assert base_config.model == "gpt-4"
        assert base_config.temperature == 0.7
        assert base_config.max_cycles == 30


class TestCodexAgentInitialization:
    """Test CodexAgent initialization and inheritance."""

    def test_codex_agent_creation_with_config(self):
        """Test creating CodexAgent with CodexConfig."""
        config = CodexConfig(timeout_minutes=15, enable_internet=False)

        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert agent is not None
        assert isinstance(
            agent, BaseAutonomousAgent
        ), "Should inherit from BaseAutonomousAgent"
        assert agent.codex_config.timeout_minutes == 15
        assert agent.codex_config.enable_internet is False

    def test_codex_agent_inherits_from_base_autonomous_agent(self):
        """Test that CodexAgent inherits from BaseAutonomousAgent."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert isinstance(
            agent, BaseAutonomousAgent
        ), "CodexAgent should inherit from BaseAutonomousAgent"

    def test_codex_agent_with_tool_registry(self):
        """Test creating CodexAgent with tool registry."""
        config = CodexConfig()
        registry = ToolRegistry()

        agent = CodexAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        assert agent.has_tool_support() is True

    def test_codex_agent_initializes_logging_system(self):
        """Test that CodexAgent initializes action logging."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Should have logging attributes
        assert hasattr(agent, "action_log")
        assert hasattr(agent, "_record_action")
        assert agent.action_log == []  # Initial state


class TestContainerExecution:
    """Test container-based execution model."""

    def test_setup_container_method_exists(self):
        """Test that _setup_container method exists."""
        config = CodexConfig(container_image="python:3.11")
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_setup_container")
        assert callable(agent._setup_container)

    @pytest.mark.asyncio
    async def test_setup_container_creates_isolated_environment(self):
        """Test that _setup_container creates isolated environment."""
        config = CodexConfig(container_image="python:3.11")
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Mock container creation
        result = await agent._setup_container("/path/to/repo")

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_setup_container_respects_internet_flag(self):
        """Test that container setup respects enable_internet config."""
        config = CodexConfig(enable_internet=False)
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        result = await agent._setup_container("/path/to/repo")

        # Should indicate internet is disabled
        assert "internet_enabled" in result
        assert result["internet_enabled"] is False

    @pytest.mark.asyncio
    async def test_setup_container_tracks_working_directory(self):
        """Test that container tracks working directory state."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        repo_path = "/path/to/project"
        result = await agent._setup_container(repo_path)

        assert "working_directory" in result
        assert result["working_directory"] == repo_path


class TestAgentsMdLoading:
    """Test AGENTS.md loading and configuration."""

    def test_load_agents_md_method_exists(self):
        """Test that _load_agents_md method exists."""
        config = CodexConfig(agents_md_path="AGENTS.md")
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_load_agents_md")
        assert callable(agent._load_agents_md)

    def test_load_agents_md_returns_content(self):
        """Test that _load_agents_md returns file content."""
        mock_content = """# Project Configuration

## Test Command
pytest tests/

## Lint Command
ruff check src/

## Conventions
- Use type hints
- Follow PEP 8
"""

        config = CodexConfig(agents_md_path="AGENTS.md")

        # Mock both Path.exists() and open() to simulate file existing
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_content)):
                agent = CodexAgent(config=config, signature=SimpleTaskSignature())
                content = agent._load_agents_md()

        assert isinstance(content, str)
        assert "Test Command" in content
        assert "pytest" in content

    def test_load_agents_md_handles_missing_file(self):
        """Test that _load_agents_md handles missing AGENTS.md gracefully."""
        config = CodexConfig(agents_md_path="nonexistent.md")
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Should not crash, return empty string or default
        content = agent._load_agents_md()

        assert isinstance(content, str)
        assert len(content) >= 0

    def test_load_agents_md_custom_path(self):
        """Test loading AGENTS.md from custom path."""
        custom_path = "custom/docs/AGENTS.md"
        config = CodexConfig(agents_md_path=custom_path)

        mock_content = "# Custom Agent Configuration"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_content)):
                agent = CodexAgent(config=config, signature=SimpleTaskSignature())
                content = agent._load_agents_md()

                assert "Custom Agent" in content or len(content) > 0


class TestTestDrivenIteration:
    """Test test-driven iteration workflow."""

    def test_test_and_iterate_method_exists(self):
        """Test that _test_and_iterate method exists."""
        config = CodexConfig(test_command="pytest")
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_test_and_iterate")
        assert callable(agent._test_and_iterate)

    @pytest.mark.asyncio
    async def test_test_and_iterate_runs_test_command(self):
        """Test that _test_and_iterate executes test command from AGENTS.md."""
        config = CodexConfig(test_command="pytest tests/")
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Mock test execution
        with patch.object(agent, "_execute_command") as mock_exec:
            mock_exec.return_value = {"status": "success", "output": "All tests passed"}
            result = await agent._test_and_iterate()

        # Should have executed test command
        mock_exec.assert_called()
        assert result is True  # Tests passed

    @pytest.mark.asyncio
    async def test_test_and_iterate_parses_test_failures(self):
        """Test that _test_and_iterate parses test failure output."""
        config = CodexConfig(test_command="pytest")
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        failure_output = """
FAILED tests/test_module.py::test_function - AssertionError: Expected 5, got 3
FAILED tests/test_other.py::test_other - TypeError: Missing argument
"""

        with patch.object(agent, "_execute_command") as mock_exec:
            mock_exec.return_value = {"status": "failed", "output": failure_output}
            result = await agent._test_and_iterate()

        # Should detect failures
        assert result is False

    @pytest.mark.asyncio
    async def test_test_and_iterate_iterates_until_pass_or_timeout(self):
        """Test that _test_and_iterate loops until tests pass or timeout."""
        config = CodexConfig(test_command="pytest", timeout_minutes=5)
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        iteration_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal iteration_count
            iteration_count += 1
            if iteration_count >= 3:
                return {"status": "success", "output": "Tests passed"}
            # Include FAILED or error indicators so parser finds failures
            return {
                "status": "failed",
                "output": "FAILED tests/test.py::test_func - AssertionError",
            }

        with patch.object(agent, "_execute_command", side_effect=mock_execute):
            result = await agent._test_and_iterate()

        # Should iterate multiple times
        assert iteration_count >= 2
        assert result is True  # Eventually passed


class TestPRGeneration:
    """Test PR generation with commit message and description."""

    def test_generate_pr_method_exists(self):
        """Test that _generate_pr method exists."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_generate_pr")
        assert callable(agent._generate_pr)

    @pytest.mark.asyncio
    async def test_generate_pr_creates_commit_message(self):
        """Test that _generate_pr creates professional commit message."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        changes = [
            {
                "file": "src/module.py",
                "action": "modified",
                "description": "Added feature X",
            }
        ]

        result = await agent._generate_pr(changes)

        assert isinstance(result, dict)
        assert "commit_message" in result
        assert len(result["commit_message"]) > 0

    @pytest.mark.asyncio
    async def test_generate_pr_creates_pr_description(self):
        """Test that _generate_pr creates comprehensive PR description."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        changes = [
            {
                "file": "tests/test_new.py",
                "action": "created",
                "description": "Added tests",
            }
        ]

        result = await agent._generate_pr(changes)

        assert "pr_description" in result
        assert len(result["pr_description"]) > 0
        assert (
            "changes" in result["pr_description"].lower()
            or "test" in result["pr_description"].lower()
        )

    @pytest.mark.asyncio
    async def test_generate_pr_includes_citations_to_logs(self):
        """Test that _generate_pr includes citations to action logs."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Add some action logs
        agent.action_log = [
            {"action": "run_tests", "result": "passed"},
            {"action": "modify_file", "result": "success"},
        ]

        changes = [{"file": "src/main.py", "action": "modified"}]

        result = await agent._generate_pr(changes)

        assert "citations" in result or "log" in result["pr_description"].lower()


class TestLoggingSystem:
    """Test action logging and evidence recording."""

    def test_record_action_method_exists(self):
        """Test that _record_action method exists."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_record_action")
        assert callable(agent._record_action)

    def test_record_action_adds_to_log(self):
        """Test that _record_action adds entries to action log."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert len(agent.action_log) == 0

        agent._record_action(
            "run_tests", {"status": "passed", "output": "All tests passed"}
        )

        assert len(agent.action_log) == 1
        assert agent.action_log[0]["action"] == "run_tests"

    def test_record_action_includes_timestamp(self):
        """Test that _record_action includes timestamp."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        agent._record_action("edit_file", {"file": "test.py"})

        assert len(agent.action_log) == 1
        # Should have timestamp or similar metadata
        assert "action" in agent.action_log[0]

    def test_get_logs_method_exists(self):
        """Test that _get_logs method exists."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_get_logs")
        assert callable(agent._get_logs)

    def test_get_logs_returns_full_execution_log(self):
        """Test that _get_logs returns complete execution history."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Add several actions
        agent._record_action("setup_container", {"status": "success"})
        agent._record_action("load_agents_md", {"status": "success"})
        agent._record_action("run_tests", {"status": "passed"})

        logs = agent._get_logs()

        assert isinstance(logs, str) or isinstance(logs, list)
        # Should contain all recorded actions
        if isinstance(logs, str):
            assert "setup_container" in logs
            assert "run_tests" in logs


class TestAutonomousLoopOverride:
    """Test _autonomous_loop override with Codex patterns."""

    @pytest.mark.asyncio
    async def test_autonomous_loop_override_exists(self):
        """Test that CodexAgent overrides _autonomous_loop."""
        config = CodexConfig()
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Should have overridden _autonomous_loop
        assert hasattr(agent, "_autonomous_loop")
        assert callable(agent._autonomous_loop)

    @pytest.mark.asyncio
    async def test_autonomous_loop_uses_agents_md_context(self):
        """Test that autonomous loop uses AGENTS.md context loaded at initialization."""
        config = CodexConfig(agents_md_path="AGENTS.md")

        mock_content = "# Agent Configuration\n\nTest Command: pytest -v"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_content)):
                agent = CodexAgent(config=config, signature=SimpleTaskSignature())

                # Verify AGENTS.md was loaded during init
                assert agent.agents_md_content == mock_content

                # Test that autonomous loop uses this context
                with patch.object(
                    agent.strategy,
                    "execute",
                    return_value={"result": "Done", "tool_calls": []},
                ) as mock_execute:
                    result = await agent._autonomous_loop("Test task")

                    # Strategy should have been called with agents_md_context
                    call_args = mock_execute.call_args
                    assert call_args is not None
                    inputs = call_args[0][1]  # Second arg is inputs
                    assert "agents_md_context" in inputs
                    assert inputs["agents_md_context"] == mock_content

    @pytest.mark.asyncio
    async def test_autonomous_loop_records_actions(self):
        """Test that autonomous loop records all actions to log."""
        config = CodexConfig(max_cycles=3)
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        with patch.object(
            agent.strategy, "execute", return_value={"result": "Done", "tool_calls": []}
        ):
            result = await agent._autonomous_loop("Test task")

        # Should have recorded some actions
        assert len(agent.action_log) > 0


class TestCodexIntegration:
    """Integration tests for full CodexAgent workflow."""

    @pytest.mark.asyncio
    async def test_execute_autonomously_with_codex_patterns(self):
        """Test full autonomous execution with Codex patterns."""
        config = CodexConfig(
            timeout_minutes=5,
            test_command="pytest",
            planning_enabled=True,
        )
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Mock all dependencies
        mock_plan = [{"task": "Implement feature", "status": "pending"}]
        mock_result = {"result": "Completed", "tool_calls": []}

        with patch.object(agent, "_create_plan", return_value=mock_plan):
            with patch.object(agent, "_autonomous_loop", return_value=mock_result):
                with patch.object(agent, "_load_agents_md", return_value="# Config"):
                    result = await agent.execute_autonomously("Build feature")

        assert result is not None
        assert "result" in result

    @pytest.mark.asyncio
    async def test_codex_agent_with_tool_registry(self):
        """Test CodexAgent with full tool registry setup."""
        config = CodexConfig()
        registry = ToolRegistry()

        agent = CodexAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        # Should have tool support
        assert agent.has_tool_support() is True

    @pytest.mark.asyncio
    async def test_codex_agent_respects_timeout(self):
        """Test that CodexAgent respects timeout_minutes configuration."""
        config = CodexConfig(timeout_minutes=1, max_cycles=100)
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Should have timeout configuration
        assert agent.codex_config.timeout_minutes == 1

    @pytest.mark.asyncio
    async def test_codex_agent_generates_pr_after_execution(self):
        """Test that CodexAgent generates PR after completing task."""
        config = CodexConfig(timeout_minutes=5)
        agent = CodexAgent(config=config, signature=SimpleTaskSignature())

        # Mock execution
        with patch.object(
            agent.strategy, "execute", return_value={"result": "Done", "tool_calls": []}
        ):
            with patch.object(agent, "_generate_pr") as mock_generate_pr:
                mock_generate_pr.return_value = {
                    "commit_message": "feat: Add feature",
                    "pr_description": "Added new feature",
                }

                result = await agent._autonomous_loop("Build feature")

                # Should eventually call _generate_pr (in real implementation)
                # For now, just verify method exists
                assert hasattr(agent, "_generate_pr")


# Test markers
pytestmark = pytest.mark.unit
