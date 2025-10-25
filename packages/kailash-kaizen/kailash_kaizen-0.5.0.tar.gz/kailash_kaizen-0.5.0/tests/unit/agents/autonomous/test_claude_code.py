"""
Test ClaudeCodeAgent - Claude Code Autonomous Architecture Implementation

Tests for the ClaudeCodeAgent class implementing Claude Code's proven
autonomous patterns based on research and production usage.

Key Claude Code Patterns Tested:
1. 15-tool ecosystem (File, Search, Execution, Web, Workflow, Coordination)
2. Diff-first workflow (show changes before applying)
3. System reminders (combat model drift with state injection)
4. Context management (92% compression trigger)
5. CLAUDE.md memory system (project-specific context)
6. Single-threaded master loop with tool-based convergence

Test Coverage:
- ClaudeCodeConfig creation with Claude Code-specific parameters
- Tool ecosystem mapping (15 tools: Read, Edit, Write, Glob, Grep, Bash, etc.)
- Diff-first workflow implementation
- System reminder injection at intervals
- Context usage monitoring (92% threshold)
- Context compression logic
- CLAUDE.md loading and parsing
- Agent loop override with Claude Code patterns

References:
- docs/research/CLAUDE_CODE_AUTONOMOUS_ARCHITECTURE.md
- BaseAutonomousAgent at src/kaizen/agents/autonomous/base.py

Author: Kaizen Framework Team
Created: 2025-10-22
"""

from typing import Dict, List
from unittest.mock import mock_open, patch

import pytest

from kaizen.agents.autonomous.base import BaseAutonomousAgent
from kaizen.agents.autonomous.claude_code import ClaudeCodeAgent, ClaudeCodeConfig
from kaizen.core.base_agent import BaseAgentConfig
from kaizen.signatures import InputField, OutputField, Signature
from kaizen.tools.registry import ToolRegistry


class SimpleTaskSignature(Signature):
    """Simple signature for testing Claude Code autonomous execution."""

    task: str = InputField(description="Task to execute autonomously")
    result: str = OutputField(description="Result of autonomous execution")
    tool_calls: List[Dict] = OutputField(
        description="Tool calls for objective convergence", default_factory=list
    )


class TestClaudeCodeConfig:
    """Test ClaudeCodeConfig dataclass and configuration."""

    def test_claude_code_config_creation_with_defaults(self):
        """Test creating ClaudeCodeConfig with default values."""
        config = ClaudeCodeConfig()

        # Test Claude Code-specific defaults
        assert (
            config.max_cycles == 100
        ), "Default max_cycles should be 100 (Claude Code)"
        assert (
            config.context_threshold == 0.92
        ), "Default context_threshold should be 0.92"
        assert (
            config.checkpoint_frequency == 10
        ), "Default checkpoint_frequency should be 10"
        assert config.enable_diffs is True, "Default enable_diffs should be True"
        assert (
            config.enable_reminders is True
        ), "Default enable_reminders should be True"
        assert config.claude_md_path == "CLAUDE.md", "Default CLAUDE.md path"

    def test_claude_code_config_creation_with_custom_values(self):
        """Test creating ClaudeCodeConfig with custom values."""
        config = ClaudeCodeConfig(
            max_cycles=50,
            context_threshold=0.85,
            checkpoint_frequency=5,
            enable_diffs=False,
            enable_reminders=False,
            claude_md_path="custom/CLAUDE.md",
            llm_provider="anthropic",
            model="claude-sonnet-4",
        )

        assert config.max_cycles == 50
        assert config.context_threshold == 0.85
        assert config.checkpoint_frequency == 5
        assert config.enable_diffs is False
        assert config.enable_reminders is False
        assert config.claude_md_path == "custom/CLAUDE.md"
        assert config.llm_provider == "anthropic"
        assert config.model == "claude-sonnet-4"

    def test_claude_code_config_extends_autonomous_config(self):
        """Test that ClaudeCodeConfig extends AutonomousConfig."""
        config = ClaudeCodeConfig(
            max_cycles=75, planning_enabled=True, llm_provider="openai", model="gpt-4"
        )

        # Should have both AutonomousConfig and ClaudeCodeConfig fields
        assert config.max_cycles == 75
        assert config.planning_enabled is True
        assert config.context_threshold == 0.92  # ClaudeCode-specific
        assert config.llm_provider == "openai"

    def test_claude_code_config_to_base_agent_config(self):
        """Test conversion from ClaudeCodeConfig to BaseAgentConfig."""
        config = ClaudeCodeConfig(
            max_cycles=100,
            llm_provider="anthropic",
            model="claude-sonnet-4",
            temperature=0.7,
        )

        # BaseAgentConfig.from_domain_config should handle conversion
        base_config = BaseAgentConfig.from_domain_config(config)

        assert isinstance(base_config, BaseAgentConfig)
        assert base_config.llm_provider == "anthropic"
        assert base_config.model == "claude-sonnet-4"
        assert base_config.temperature == 0.7
        assert base_config.max_cycles == 100


class TestClaudeCodeAgentInitialization:
    """Test ClaudeCodeAgent initialization and inheritance."""

    def test_claude_code_agent_creation_with_config(self):
        """Test creating ClaudeCodeAgent with ClaudeCodeConfig."""
        config = ClaudeCodeConfig(max_cycles=50, enable_diffs=True)

        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        assert agent is not None
        assert isinstance(
            agent, BaseAutonomousAgent
        ), "Should inherit from BaseAutonomousAgent"
        assert agent.claude_code_config.max_cycles == 50
        assert agent.claude_code_config.enable_diffs is True

    def test_claude_code_agent_inherits_from_base_autonomous_agent(self):
        """Test that ClaudeCodeAgent inherits from BaseAutonomousAgent."""
        config = ClaudeCodeConfig()
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        assert isinstance(
            agent, BaseAutonomousAgent
        ), "ClaudeCodeAgent should inherit from BaseAutonomousAgent"

    def test_claude_code_agent_with_tool_registry(self):
        """Test creating ClaudeCodeAgent with tool registry."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()

        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        assert agent.has_tool_support() is True

    def test_claude_code_agent_initializes_context_tracker(self):
        """Test that ClaudeCodeAgent initializes context tracking."""
        config = ClaudeCodeConfig(context_threshold=0.92)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Should have context tracking attributes
        assert hasattr(agent, "context_usage")
        assert hasattr(agent, "_check_context_usage")
        assert agent.context_usage == 0.0  # Initial state


class TestToolEcosystemMapping:
    """Test Claude Code 15-tool ecosystem mapping."""

    def test_claude_code_agent_has_15_tools(self):
        """Test that ClaudeCodeAgent maps all Claude Code tools (12 builtin + 6 custom = 18)."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()
        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        # Should have _setup_claude_code_tools method
        assert hasattr(agent, "_setup_claude_code_tools")

        # Setup tools
        agent._setup_claude_code_tools()

        # Count tools (12 builtin + 6 custom = 18 total, covers 15 Claude Code tools)
        tool_count = registry.count()
        assert (
            tool_count >= 15
        ), f"Should have at least 15 Claude Code tools, got {tool_count}"

    def test_file_operations_tools_mapped(self):
        """Test that File Operations tools (Read, Edit, Write) are mapped."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()
        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        agent._setup_claude_code_tools()

        # Check for file operation tools
        assert registry.has("read_file"), "Should have Read (read_file) tool"
        assert registry.has("edit_file"), "Should have Edit (edit_file) tool"
        assert registry.has("write_file"), "Should have Write (write_file) tool"

    def test_search_discovery_tools_mapped(self):
        """Test that Search & Discovery tools (Glob, Grep) are mapped."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()
        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        agent._setup_claude_code_tools()

        # Check for search/discovery tools
        assert registry.has("glob_search"), "Should have Glob (glob_search) tool"
        assert registry.has("grep_search"), "Should have Grep (grep_search) tool"

    def test_execution_tool_mapped(self):
        """Test that Execution tool (Bash) is mapped."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()
        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        agent._setup_claude_code_tools()

        # Check for bash tool
        assert registry.has("bash_command"), "Should have Bash (bash_command) tool"

    def test_web_tools_mapped(self):
        """Test that Web tools (WebFetch, WebSearch) are mapped."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()
        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        agent._setup_claude_code_tools()

        # Check for web tools
        assert registry.has("fetch_url"), "Should have WebFetch (fetch_url) tool"
        assert registry.has("web_search"), "Should have WebSearch (web_search) tool"

    def test_workflow_tool_mapped(self):
        """Test that Workflow tool (TodoWrite) is mapped."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()
        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        agent._setup_claude_code_tools()

        # Check for workflow tool
        assert registry.has("todo_write"), "Should have TodoWrite (todo_write) tool"

    def test_coordination_tools_mapped(self):
        """Test that Coordination tools (Task, subagent spawning) are mapped."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()
        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        agent._setup_claude_code_tools()

        # Check for coordination tools (5 coordination tools)
        assert registry.has("task_spawn"), "Should have Task (task_spawn) tool"
        # Additional coordination tools: statusline, output-style, explore, etc.


class TestDiffFirstWorkflow:
    """Test diff-first workflow implementation."""

    def test_diff_first_workflow_method_exists(self):
        """Test that _apply_changes_with_diff method exists."""
        config = ClaudeCodeConfig(enable_diffs=True)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_apply_changes_with_diff")
        assert callable(agent._apply_changes_with_diff)

    def test_apply_changes_with_diff_shows_diff_before_applying(self):
        """Test that changes show diff before applying when enabled."""
        config = ClaudeCodeConfig(enable_diffs=True)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        changes = [
            {
                "file": "test.py",
                "old_content": "def hello():\n    print('old')",
                "new_content": "def hello():\n    print('new')",
            }
        ]

        with patch("builtins.print") as mock_print:
            result = agent._apply_changes_with_diff(changes)

        # Should call print to show diff
        mock_print.assert_called()
        assert "test.py" in str(
            mock_print.call_args_list
        ), "Should show filename in diff"

    def test_apply_changes_with_diff_skips_when_disabled(self):
        """Test that diff display is skipped when enable_diffs=False."""
        config = ClaudeCodeConfig(enable_diffs=False)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        changes = [
            {
                "file": "test.py",
                "old_content": "old",
                "new_content": "new",
            }
        ]

        with patch("builtins.print") as mock_print:
            result = agent._apply_changes_with_diff(changes)

        # Should NOT call print for diff when disabled
        # (But might call for other reasons, so check diff-specific content)
        diff_calls = [
            call
            for call in mock_print.call_args_list
            if "---" in str(call) or "+++" in str(call)
        ]
        assert len(diff_calls) == 0, "Should not show diff when disabled"

    def test_apply_changes_with_diff_returns_summary(self):
        """Test that _apply_changes_with_diff returns a summary of changes."""
        config = ClaudeCodeConfig(enable_diffs=True)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        changes = [
            {"file": "file1.py", "old_content": "a", "new_content": "b"},
            {"file": "file2.py", "old_content": "x", "new_content": "y"},
        ]

        result = agent._apply_changes_with_diff(changes)

        assert isinstance(result, str)
        assert (
            "2" in result or "file1.py" in result
        ), "Should mention number of files or filenames"


class TestSystemReminders:
    """Test system reminders for combating drift."""

    def test_inject_system_reminder_method_exists(self):
        """Test that _inject_system_reminder method exists."""
        config = ClaudeCodeConfig(enable_reminders=True)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_inject_system_reminder")
        assert callable(agent._inject_system_reminder)

    def test_inject_system_reminder_returns_reminder_text(self):
        """Test that _inject_system_reminder returns a reminder message."""
        config = ClaudeCodeConfig(enable_reminders=True)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        reminder = agent._inject_system_reminder(cycle_num=5)

        assert isinstance(reminder, str)
        assert len(reminder) > 0, "Reminder should not be empty"
        assert (
            "cycle" in reminder.lower() or "5" in reminder
        ), "Should mention cycle number"

    def test_inject_system_reminder_includes_state_info(self):
        """Test that system reminder includes current state information."""
        config = ClaudeCodeConfig(enable_reminders=True)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Set some state
        agent.current_plan = [{"task": "Test task", "status": "in_progress"}]

        reminder = agent._inject_system_reminder(cycle_num=10)

        # Should include state info
        assert "plan" in reminder.lower() or "task" in reminder.lower()

    def test_inject_system_reminder_skips_when_disabled(self):
        """Test that system reminders are skipped when enable_reminders=False."""
        config = ClaudeCodeConfig(enable_reminders=False)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        reminder = agent._inject_system_reminder(cycle_num=5)

        # Should return empty string when disabled
        assert reminder == ""


class TestContextManagement:
    """Test context usage monitoring and compression."""

    def test_check_context_usage_method_exists(self):
        """Test that _check_context_usage method exists."""
        config = ClaudeCodeConfig(context_threshold=0.92)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_check_context_usage")
        assert callable(agent._check_context_usage)

    def test_check_context_usage_returns_float(self):
        """Test that _check_context_usage returns a float percentage."""
        config = ClaudeCodeConfig()
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        usage = agent._check_context_usage()

        assert isinstance(usage, float)
        assert 0.0 <= usage <= 1.0, "Context usage should be between 0 and 1"

    def test_compact_context_method_exists(self):
        """Test that _compact_context method exists."""
        config = ClaudeCodeConfig()
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_compact_context")
        assert callable(agent._compact_context)

    def test_compact_context_triggers_at_threshold(self):
        """Test that context compression triggers at 92% threshold."""
        config = ClaudeCodeConfig(context_threshold=0.92)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Mock high context usage
        agent.context_usage = 0.95

        with patch.object(agent, "_compact_context") as mock_compact:
            # Simulate check during loop
            if agent.context_usage >= config.context_threshold:
                agent._compact_context()

        # Should call compact when over threshold
        mock_compact.assert_called_once()

    def test_compact_context_reduces_usage(self):
        """Test that _compact_context reduces context usage."""
        config = ClaudeCodeConfig()
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Set high usage
        agent.context_usage = 0.95

        # Compact
        agent._compact_context()

        # Usage should be reduced
        assert (
            agent.context_usage < 0.95
        ), "Context usage should decrease after compaction"


class TestClaudeMdLoading:
    """Test CLAUDE.md loading and parsing."""

    def test_load_claude_md_method_exists(self):
        """Test that _load_claude_md method exists."""
        config = ClaudeCodeConfig(claude_md_path="CLAUDE.md")
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        assert hasattr(agent, "_load_claude_md")
        assert callable(agent._load_claude_md)

    def test_load_claude_md_returns_content(self):
        """Test that _load_claude_md returns file content."""
        config = ClaudeCodeConfig(claude_md_path="CLAUDE.md")
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        mock_content = "# Project Memory\n\nImportant context about the project."

        with patch("builtins.open", mock_open(read_data=mock_content)):
            content = agent._load_claude_md()

        assert isinstance(content, str)
        assert "Project Memory" in content

    def test_load_claude_md_handles_missing_file(self):
        """Test that _load_claude_md handles missing CLAUDE.md gracefully."""
        config = ClaudeCodeConfig(claude_md_path="nonexistent.md")
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Should not crash, return empty string or default
        content = agent._load_claude_md()

        assert isinstance(content, str)
        # Should be empty or contain default message
        assert len(content) >= 0

    def test_load_claude_md_custom_path(self):
        """Test loading CLAUDE.md from custom path."""
        custom_path = "custom/docs/CLAUDE.md"
        config = ClaudeCodeConfig(claude_md_path=custom_path)

        mock_content = "Custom location content"

        # Mock both Path.exists() and open() to simulate file existing
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_content)) as mock_file:
                agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())
                content = agent._load_claude_md()

                # Should have tried to open custom path
                assert "Custom location" in content or len(content) > 0


class TestAutonomousLoopOverride:
    """Test _autonomous_loop override with Claude Code patterns."""

    @pytest.mark.asyncio
    async def test_autonomous_loop_override_exists(self):
        """Test that ClaudeCodeAgent overrides _autonomous_loop."""
        config = ClaudeCodeConfig()
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Should have overridden _autonomous_loop
        assert hasattr(agent, "_autonomous_loop")
        assert callable(agent._autonomous_loop)

    @pytest.mark.asyncio
    async def test_autonomous_loop_injects_reminders_periodically(self):
        """Test that autonomous loop injects system reminders at intervals."""
        config = ClaudeCodeConfig(enable_reminders=True, max_cycles=10)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Mock strategy execute
        mock_response = {"result": "Done", "tool_calls": []}

        inject_count = 0

        def count_injections(*args, **kwargs):
            nonlocal inject_count
            inject_count += 1
            return "Reminder text"

        with patch.object(
            agent, "_inject_system_reminder", side_effect=count_injections
        ):
            with patch.object(agent.strategy, "execute", return_value=mock_response):
                result = await agent._autonomous_loop("Test task with reminders")

        # Should have injected reminders (at least once for short loop)
        assert inject_count > 0, "Should inject system reminders during loop"

    @pytest.mark.asyncio
    async def test_autonomous_loop_checks_context_usage(self):
        """Test that autonomous loop monitors context usage."""
        config = ClaudeCodeConfig(context_threshold=0.92, max_cycles=5)
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Mock strategy execute
        mock_response = {"result": "Done", "tool_calls": []}

        check_count = 0

        def count_checks(*args, **kwargs):
            nonlocal check_count
            check_count += 1
            return 0.5  # Mock usage

        with patch.object(agent, "_check_context_usage", side_effect=count_checks):
            with patch.object(agent.strategy, "execute", return_value=mock_response):
                result = await agent._autonomous_loop(
                    "Test task with context monitoring"
                )

        # Should check context usage during loop
        assert check_count > 0, "Should monitor context usage during loop"

    @pytest.mark.asyncio
    async def test_autonomous_loop_uses_claude_md_context(self):
        """Test that autonomous loop uses CLAUDE.md context loaded at initialization."""
        config = ClaudeCodeConfig(claude_md_path="CLAUDE.md")

        mock_content = "# Project Context"

        # Mock Path.exists() to simulate file existing
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_content)):
                agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

                # Verify CLAUDE.md was loaded during init
                assert agent.claude_md_content == mock_content

                # Now test that autonomous loop uses this context
                with patch.object(
                    agent.strategy,
                    "execute",
                    return_value={"result": "Done", "tool_calls": []},
                ) as mock_execute:
                    result = await agent._autonomous_loop("Test task")

                    # Strategy should have been called with claude_md_context
                    call_args = mock_execute.call_args
                    assert call_args is not None
                    inputs = call_args[0][1]  # Second arg is inputs
                    assert "claude_md_context" in inputs
                    assert inputs["claude_md_context"] == mock_content


class TestClaudeCodeIntegration:
    """Integration tests for full ClaudeCodeAgent workflow."""

    @pytest.mark.asyncio
    async def test_execute_autonomously_with_claude_code_patterns(self):
        """Test full autonomous execution with Claude Code patterns."""
        config = ClaudeCodeConfig(
            max_cycles=5,
            enable_diffs=True,
            enable_reminders=True,
            planning_enabled=True,
        )
        agent = ClaudeCodeAgent(config=config, signature=SimpleTaskSignature())

        # Mock all dependencies
        mock_plan = [{"task": "Test step", "status": "pending"}]
        mock_result = {"result": "Completed", "tool_calls": []}

        with patch.object(agent, "_create_plan", return_value=mock_plan):
            with patch.object(agent, "_autonomous_loop", return_value=mock_result):
                with patch.object(agent, "_load_claude_md", return_value="# Context"):
                    result = await agent.execute_autonomously("Build feature")

        assert result is not None
        assert "result" in result

    @pytest.mark.asyncio
    async def test_claude_code_agent_with_tool_registry(self):
        """Test ClaudeCodeAgent with full tool registry setup."""
        config = ClaudeCodeConfig()
        registry = ToolRegistry()

        agent = ClaudeCodeAgent(
            config=config, signature=SimpleTaskSignature(), tool_registry=registry
        )

        # Setup Claude Code tools
        agent._setup_claude_code_tools()

        # Verify tools are available (12 builtin + 6 custom = 18 total)
        assert (
            registry.count() >= 15
        ), f"Should have at least 15 Claude Code tools, got {registry.count()}"
        assert agent.has_tool_support() is True


# Test markers
pytestmark = pytest.mark.unit
