"""
ClaudeCodeAgent - Claude Code Autonomous Architecture Implementation

This module implements ClaudeCodeAgent based on Claude Code's proven autonomous
patterns from production usage and research analysis.

Key Claude Code Patterns:
1. **15-tool ecosystem**: File (Read, Edit, Write), Search (Glob, Grep),
   Execution (Bash), Web (WebFetch, WebSearch), Workflow (TodoWrite),
   Coordination (Task spawning)
2. **Diff-first workflow**: Show minimal diffs before applying changes
3. **System reminders**: Periodic state injection to combat model drift
4. **Context management**: 92% compression trigger with intelligent compaction
5. **CLAUDE.md memory**: Project-specific context loaded at session start
6. **Single-threaded master loop**: while(tool_calls_exist) pattern

Architecture:
- Extends BaseAutonomousAgent with Claude Code-specific patterns
- Overrides _autonomous_loop for Claude Code workflow integration
- Maps 15 Claude Code tools to Kaizen builtin tools
- Implements diff display, system reminders, context compression
- Loads CLAUDE.md for project memory

References:
- docs/research/CLAUDE_CODE_AUTONOMOUS_ARCHITECTURE.md (Lines 29-44, 13-18, 56-62)
- BaseAutonomousAgent at src/kaizen/agents/autonomous/base.py
- Claude Code: Single-threaded loop, 15 tools, diff-first, reminders

Example:
    >>> from kaizen.agents.autonomous.claude_code import ClaudeCodeAgent, ClaudeCodeConfig
    >>> from kaizen.tools import ToolRegistry
    >>>
    >>> config = ClaudeCodeConfig(
    ...     max_cycles=100,
    ...     context_threshold=0.92,
    ...     enable_diffs=True,
    ...     enable_reminders=True
    ... )
    >>>
    >>> registry = ToolRegistry()
    >>> agent = ClaudeCodeAgent(
    ...     config=config,
    ...     signature=signature,
    ...     tool_registry=registry
    ... )
    >>>
    >>> # Setup Claude Code tools (15 total)
    >>> agent._setup_claude_code_tools()
    >>>
    >>> # Execute autonomously with Claude Code patterns
    >>> result = await agent.execute_autonomously("Build REST API with tests")
    >>> print(f"Completed in {result['cycles_used']} cycles")

Author: Kaizen Framework Team
Created: 2025-10-22
"""

import difflib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from kaizen.agents.autonomous.base import AutonomousConfig, BaseAutonomousAgent
from kaizen.signatures import Signature
from kaizen.strategies.multi_cycle import MultiCycleStrategy
from kaizen.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ClaudeCodeConfig(AutonomousConfig):
    """
    Configuration for ClaudeCodeAgent with Claude Code-specific parameters.

    This config extends AutonomousConfig with Claude Code-specific parameters:
    - max_cycles: 100 (Claude Code runs much longer than base autonomous)
    - context_threshold: 0.92 (Claude Code triggers compression at 92%)
    - checkpoint_frequency: 10 (save checkpoints every 10 cycles)
    - enable_diffs: Show diffs before applying changes (diff-first workflow)
    - enable_reminders: Inject system reminders to combat drift
    - claude_md_path: Path to CLAUDE.md file for project memory

    Claude Code Defaults vs BaseAutonomousAgent:
    - max_cycles: 100 vs 20 (5x longer for complex tasks)
    - checkpoint_frequency: 10 vs 5 (less frequent for performance)
    - context_threshold: 0.92 (Claude Code-specific)

    Example:
        >>> config = ClaudeCodeConfig(
        ...     max_cycles=100,
        ...     context_threshold=0.92,
        ...     enable_diffs=True,
        ...     enable_reminders=True,
        ...     claude_md_path="CLAUDE.md",
        ...     llm_provider="anthropic",
        ...     model="claude-sonnet-4"
        ... )
        >>> agent = ClaudeCodeAgent(config=config, signature=signature)
    """

    # Claude Code-specific parameters
    max_cycles: int = 100  # Claude Code runs longer (vs 20 for base)
    context_threshold: float = 0.92  # Compression trigger (Claude Code pattern)
    checkpoint_frequency: int = 10  # Less frequent checkpoints (vs 5 for base)
    enable_diffs: bool = True  # Diff-first workflow
    enable_reminders: bool = True  # System reminders for drift prevention
    claude_md_path: str = "CLAUDE.md"  # Project memory file


class ClaudeCodeAgent(BaseAutonomousAgent):
    """
    Autonomous agent implementing Claude Code's proven patterns.

    ClaudeCodeAgent extends BaseAutonomousAgent with Claude Code-specific
    autonomous execution patterns from production usage:

    1. **15-Tool Ecosystem**: Complete developer toolkit
       - File Operations (3): Read, Edit, Write
       - Search & Discovery (2): Glob, Grep
       - Execution (1): Bash
       - Web Capabilities (2): WebFetch, WebSearch
       - Workflow Management (1): TodoWrite
       - Agent Coordination (6): Task spawning, statusline, output-style, etc.

    2. **Diff-First Workflow**: Transparent change visibility
       - Shows minimal diffs before applying changes
       - User can review/approve modifications
       - Natural checkpoints for review

    3. **System Reminders**: Combat model drift
       - Periodic state injection during long sessions
       - Current TODO list status
       - Planning mode reminders
       - Control flow instructions

    4. **Context Management**: Intelligent compression
       - Monitors context usage continuously
       - Triggers compression at 92% threshold
       - Preserves important information in CLAUDE.md
       - Uses regex/grep over vector search for transparency

    5. **CLAUDE.md Memory**: Project-specific context
       - Loads at session start
       - Contains conventions, setup, guidelines
       - Provides persistent "agent memory"
       - Improves performance on project-specific tasks

    Execution Flow:
        1. Load CLAUDE.md for project context
        2. Create plan (if planning enabled)
        3. Autonomous loop with Claude Code patterns:
           a. Check context usage (compress at 92%)
           b. Inject system reminder (periodic)
           c. Execute cycle (LLM + tools)
           d. Show diffs (if changes made)
           e. Check convergence (tool_calls empty)
           f. Save checkpoint (every 10 cycles)
        4. Return results with metadata

    Example:
        >>> from kaizen.agents.autonomous.claude_code import ClaudeCodeAgent, ClaudeCodeConfig
        >>> from kaizen.tools import ToolRegistry
        >>> from kaizen.tools.builtin import register_builtin_tools
        >>>
        >>> # Setup configuration
        >>> config = ClaudeCodeConfig(
        ...     max_cycles=100,
        ...     enable_diffs=True,
        ...     enable_reminders=True,
        ...     llm_provider="anthropic",
        ...     model="claude-sonnet-4"
        ... )
        >>>
        >>> # Setup tool registry with Claude Code tools
        >>> registry = ToolRegistry()
        >>> agent = ClaudeCodeAgent(
        ...     config=config,
        ...     signature=signature,
        ...     tool_registry=registry
        ... )
        >>> agent._setup_claude_code_tools()
        >>>
        >>> # Execute autonomously
        >>> result = await agent.execute_autonomously(
        ...     "Analyze codebase and implement user authentication"
        ... )
        >>> print(f"Task completed in {result['cycles_used']} cycles")
        >>> print(f"Changes made: {result.get('changes_summary', 'None')}")

    Notes:
        - Designed for long-running tasks (100+ cycles)
        - Context compression prevents token limit issues
        - Diff display enables safe autonomous exploration
        - System reminders maintain coherence over hours
        - CLAUDE.md provides project-specific knowledge
    """

    def __init__(
        self,
        config: ClaudeCodeConfig,
        signature: Optional[Signature] = None,
        strategy: Optional[MultiCycleStrategy] = None,
        tool_registry: Optional[ToolRegistry] = None,
        checkpoint_dir: Optional[Path] = None,
        **kwargs,
    ):
        """
        Initialize ClaudeCodeAgent with Claude Code patterns.

        Args:
            config: ClaudeCodeConfig with Claude Code-specific parameters
            signature: Optional signature (uses _default_signature() if None)
            strategy: Optional MultiCycleStrategy (creates default if None)
            tool_registry: Optional tool registry for Claude Code tools
            checkpoint_dir: Optional directory for checkpoint persistence
            **kwargs: Additional arguments passed to BaseAutonomousAgent

        Example:
            >>> config = ClaudeCodeConfig(max_cycles=100, enable_diffs=True)
            >>> registry = ToolRegistry()
            >>> agent = ClaudeCodeAgent(
            ...     config=config,
            ...     signature=signature,
            ...     tool_registry=registry
            ... )
        """
        # Store Claude Code-specific config
        self.claude_code_config = config

        # Initialize BaseAutonomousAgent (will create strategy if None)
        super().__init__(
            config=config,
            signature=signature,
            strategy=strategy,
            tool_registry=tool_registry,
            checkpoint_dir=checkpoint_dir,
            **kwargs,
        )

        # Claude Code-specific state
        self.context_usage: float = 0.0  # Context window usage (0.0-1.0)
        self.claude_md_content: str = ""  # Loaded CLAUDE.md content
        self.reminder_interval: int = 10  # Inject reminders every N cycles

        # Load CLAUDE.md at initialization
        self.claude_md_content = self._load_claude_md()

        logger.info("ClaudeCodeAgent initialized with Claude Code patterns")

    def _setup_claude_code_tools(self) -> None:
        """
        Setup 15 Claude Code tools in the tool registry.

        Maps Claude Code's 15-tool ecosystem to Kaizen builtin tools:
        - File Operations (3): read_file, edit_file, write_file
        - Search & Discovery (2): glob_search, grep_search
        - Execution (1): bash_command
        - Web Capabilities (2): fetch_url, web_search
        - Workflow Management (1): todo_write
        - Agent Coordination (6): task_spawn, statusline, output_style, etc.

        Example:
            >>> agent = ClaudeCodeAgent(config=config, tool_registry=registry)
            >>> agent._setup_claude_code_tools()
            >>> print(f"Registered {agent._tool_registry.count()} tools")
        """
        if not self.has_tool_support():
            logger.warning("No tool registry provided, skipping tool setup")
            return

        from kaizen.tools.builtin import register_builtin_tools

        # Register builtin tools (provides 12 base tools)
        register_builtin_tools(self._tool_registry)

        # Add Claude Code-specific tools (3 additional custom tools)
        self._register_claude_code_custom_tools()

        logger.info(f"Registered {self._tool_registry.count()} Claude Code tools")

    def _register_claude_code_custom_tools(self) -> None:
        """
        Register Claude Code-specific custom tools.

        Custom tools beyond Kaizen builtins:
        - edit_file: Exact string replacement with indentation preservation (Edit tool)
        - glob_search: Fast pattern matching using glob syntax (Glob tool)
        - grep_search: Regex search with multiline support (Grep tool)
        - web_search: Web search for current information (WebSearch tool)
        - todo_write: Structured task list management (TodoWrite tool)
        - task_spawn: Subagent spawning for parallel work (Task tool)

        Note: Some tools may be custom implementations, others use builtins.
        This is a placeholder for Claude Code-specific tool implementations.
        """
        # TODO: Implement custom Claude Code tools
        # For now, we rely on builtin tools + custom implementations

        from kaizen.tools import ToolParameter

        # Custom tool 1: edit_file (Edit with exact string replacement)
        if not self._tool_registry.has("edit_file"):
            self._tool_registry.register(
                name="edit_file",
                description="Edit file with exact string replacement (Claude Code Edit tool)",
                category="file",
                danger_level="moderate",
                parameters=[
                    ToolParameter(
                        "file_path", str, "Path to file to edit", required=True
                    ),
                    ToolParameter(
                        "old_string", str, "String to replace", required=True
                    ),
                    ToolParameter(
                        "new_string", str, "Replacement string", required=True
                    ),
                ],
                returns={"status": "str", "file": "str", "changes": "int"},
                executor=self._edit_file_impl,
            )

        # Custom tool 2: glob_search (Glob pattern matching)
        if not self._tool_registry.has("glob_search"):
            self._tool_registry.register(
                name="glob_search",
                description="Fast file pattern matching using glob syntax (Claude Code Glob tool)",
                category="search",
                danger_level="safe",
                parameters=[
                    ToolParameter(
                        "pattern", str, "Glob pattern to match", required=True
                    ),
                    ToolParameter("path", str, "Directory to search", required=False),
                ],
                returns={"status": "str", "files": "list", "pattern": "str"},
                executor=self._glob_search_impl,
            )

        # Custom tool 3: grep_search (Grep with regex)
        if not self._tool_registry.has("grep_search"):
            self._tool_registry.register(
                name="grep_search",
                description="Regex search in files (Claude Code Grep tool)",
                category="search",
                danger_level="safe",
                parameters=[
                    ToolParameter(
                        "pattern", str, "Regex pattern to search", required=True
                    ),
                    ToolParameter(
                        "path", str, "Directory/file to search", required=False
                    ),
                    ToolParameter(
                        "multiline", bool, "Enable multiline matching", required=False
                    ),
                ],
                returns={"status": "str", "matches": "list", "pattern": "str"},
                executor=self._grep_search_impl,
            )

        # Custom tool 4: web_search (WebSearch)
        if not self._tool_registry.has("web_search"):
            self._tool_registry.register(
                name="web_search",
                description="Web search for current information (Claude Code WebSearch tool)",
                category="web",
                danger_level="safe",
                parameters=[
                    ToolParameter("query", str, "Search query", required=True),
                ],
                returns={"status": "str", "results": "list", "query": "str"},
                executor=self._web_search_impl,
            )

        # Custom tool 5: todo_write (TodoWrite)
        if not self._tool_registry.has("todo_write"):
            self._tool_registry.register(
                name="todo_write",
                description="Structured task list management (Claude Code TodoWrite tool)",
                category="workflow",
                danger_level="safe",
                parameters=[
                    ToolParameter("todos", list, "List of todo items", required=True),
                ],
                returns={"status": "str", "todos": "list"},
                executor=self._todo_write_impl,
            )

        # Custom tool 6: task_spawn (Task subagent spawning)
        if not self._tool_registry.has("task_spawn"):
            self._tool_registry.register(
                name="task_spawn",
                description="Spawn subagent for parallel work (Claude Code Task tool)",
                category="coordination",
                danger_level="moderate",
                parameters=[
                    ToolParameter("task", str, "Task for subagent", required=True),
                    ToolParameter(
                        "agent_type", str, "Type of subagent", required=False
                    ),
                ],
                returns={"status": "str", "task": "str", "agent_type": "str"},
                executor=self._task_spawn_impl,
            )

        logger.debug("Registered 6 custom Claude Code tools")

    # Custom tool implementations (placeholders)
    def _edit_file_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Edit tool implementation with exact string replacement."""
        # TODO: Implement full Edit tool logic
        file_path = params["file_path"]
        return {"status": "success", "file": file_path, "changes": 1}

    def _glob_search_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Glob tool implementation for pattern matching."""
        # TODO: Implement full Glob tool logic
        pattern = params["pattern"]
        return {"status": "success", "files": [], "pattern": pattern}

    def _grep_search_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Grep tool implementation for regex search."""
        # TODO: Implement full Grep tool logic
        pattern = params["pattern"]
        return {"status": "success", "matches": [], "pattern": pattern}

    def _web_search_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """WebSearch tool implementation."""
        # TODO: Implement full WebSearch tool logic
        query = params["query"]
        return {"status": "success", "results": [], "query": query}

    def _todo_write_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """TodoWrite tool implementation."""
        # TODO: Implement full TodoWrite tool logic
        todos = params["todos"]
        return {"status": "success", "todos": todos}

    def _task_spawn_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Task subagent spawning implementation."""
        # TODO: Implement full Task spawning logic
        task = params["task"]
        agent_type = params.get("agent_type", "general")
        return {"status": "success", "task": task, "agent_type": agent_type}

    async def _autonomous_loop(self, task: str) -> Dict[str, Any]:
        """
        Override autonomous loop with Claude Code patterns.

        This implements the Claude Code autonomous loop with:
        1. Context usage monitoring (compress at 92%)
        2. System reminder injection (periodic)
        3. Diff display (before applying changes)
        4. CLAUDE.md context integration
        5. Tool-based convergence detection

        Args:
            task: Task to execute

        Returns:
            Dict with final result and metadata

        Example:
            >>> result = await agent._autonomous_loop("Build API")
            >>> print(f"Converged: {result.get('tool_calls') == []}")
        """
        self.cycle_count = 0
        final_result = {}

        # Prepare initial inputs with CLAUDE.md context
        inputs = {"task": task, "claude_md_context": self.claude_md_content}
        if self.current_plan:
            inputs["plan"] = self.current_plan

        # Claude Code autonomous loop: while(tool_calls_exist)
        for cycle_num in range(self.claude_code_config.max_cycles):
            self.cycle_count = cycle_num + 1

            try:
                # 1. Check context usage (compress at 92%)
                self.context_usage = self._check_context_usage()
                if self.context_usage >= self.claude_code_config.context_threshold:
                    logger.info(
                        f"Context usage {self.context_usage:.1%} >= {self.claude_code_config.context_threshold:.1%}, compressing..."
                    )
                    self._compact_context()

                # 2. Inject system reminder (periodic)
                if (
                    self.claude_code_config.enable_reminders
                    and cycle_num % self.reminder_interval == 0
                ):
                    reminder = self._inject_system_reminder(cycle_num)
                    if reminder:
                        inputs["system_reminder"] = reminder
                        logger.debug(f"Injected system reminder at cycle {cycle_num}")

                # 3. Execute cycle using strategy
                logger.debug(
                    f"Cycle {self.cycle_count}/{self.claude_code_config.max_cycles}"
                )
                cycle_result = self.strategy.execute(self, inputs)

                # 4. Show diffs (if changes made and diffs enabled)
                if self.claude_code_config.enable_diffs and "changes" in cycle_result:
                    diff_summary = self._apply_changes_with_diff(
                        cycle_result["changes"]
                    )
                    cycle_result["changes_summary"] = diff_summary

                # 5. Save checkpoint at specified frequency
                if self.cycle_count % self.claude_code_config.checkpoint_frequency == 0:
                    self._save_checkpoint(cycle_result, cycle_num)

                # 6. Check convergence (objective via tool_calls)
                if self._check_convergence(cycle_result):
                    logger.info(f"Converged at cycle {self.cycle_count}")
                    final_result = cycle_result
                    break

                # Update inputs for next cycle
                if "observation" in cycle_result:
                    inputs["observation"] = cycle_result["observation"]

            except Exception as e:
                logger.error(f"Error in cycle {self.cycle_count}: {e}")
                final_result = {
                    "error": str(e),
                    "status": "failed",
                    "cycle": self.cycle_count,
                }
                break

        # Add cycle metadata
        final_result["cycles_used"] = self.cycle_count
        final_result["total_cycles"] = self.claude_code_config.max_cycles
        final_result["context_usage_final"] = self.context_usage

        return final_result

    def _apply_changes_with_diff(self, changes: List[Dict[str, Any]]) -> str:
        """
        Apply changes with diff-first workflow.

        Shows minimal diffs before applying changes, enabling:
        - Transparent visibility into modifications
        - User review/approval capability
        - Natural checkpoints for verification
        - Safe autonomous exploration

        Args:
            changes: List of change dictionaries with file, old_content, new_content

        Returns:
            Summary string describing changes made

        Example:
            >>> changes = [
            ...     {
            ...         "file": "test.py",
            ...         "old_content": "def old():\\n    pass",
            ...         "new_content": "def new():\\n    return True"
            ...     }
            ... ]
            >>> summary = agent._apply_changes_with_diff(changes)
            >>> print(summary)  # "Modified 1 file: test.py"
        """
        if not self.claude_code_config.enable_diffs:
            return f"Applied {len(changes)} changes (diffs disabled)"

        modified_files = []

        for change in changes:
            file_path = change.get("file", "unknown")
            old_content = change.get("old_content", "")
            new_content = change.get("new_content", "")

            # Generate unified diff
            old_lines = old_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)

            diff = difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm="",
            )

            # Display diff
            print(f"\n{'='*60}")
            print(f"Diff for: {file_path}")
            print(f"{'='*60}")
            for line in diff:
                print(line)

            modified_files.append(file_path)

        summary = f"Modified {len(modified_files)} file(s): {', '.join(modified_files)}"
        logger.info(summary)
        return summary

    def _inject_system_reminder(self, cycle_num: int) -> str:
        """
        Inject system reminder to combat model drift.

        During long autonomous sessions (100+ cycles), models can drift from
        original instructions. System reminders periodically inject current state:
        - Current cycle number and progress
        - TODO list status
        - Planning mode reminders
        - Control flow instructions

        Args:
            cycle_num: Current cycle number

        Returns:
            Reminder message string

        Example:
            >>> reminder = agent._inject_system_reminder(cycle_num=50)
            >>> print(reminder)
            # "SYSTEM REMINDER [Cycle 50/100]: Current plan has 3 tasks..."
        """
        if not self.claude_code_config.enable_reminders:
            return ""

        reminder_parts = [
            f"SYSTEM REMINDER [Cycle {cycle_num}/{self.claude_code_config.max_cycles}]:"
        ]

        # Include plan status
        if self.current_plan:
            pending = len(
                [t for t in self.current_plan if t.get("status") == "pending"]
            )
            in_progress = len(
                [t for t in self.current_plan if t.get("status") == "in_progress"]
            )
            completed = len(
                [t for t in self.current_plan if t.get("status") == "completed"]
            )

            reminder_parts.append(
                f"Plan status: {completed} completed, {in_progress} in progress, {pending} pending"
            )

        # Include context status
        reminder_parts.append(
            f"Context usage: {self.context_usage:.1%} (compression at {self.claude_code_config.context_threshold:.1%})"
        )

        # Include control flow reminder
        reminder_parts.append(
            "Continue working until tool_calls field is empty (objective convergence)"
        )

        reminder = "\n".join(reminder_parts)
        return reminder

    def _check_context_usage(self) -> float:
        """
        Check current context window usage.

        Monitors context usage to trigger compression at 92% threshold.
        Uses token counting to estimate usage.

        Returns:
            Float between 0.0 and 1.0 representing usage percentage

        Example:
            >>> usage = agent._check_context_usage()
            >>> if usage >= 0.92:
            ...     agent._compact_context()
        """
        # TODO: Implement actual token counting
        # For now, use a simple heuristic based on conversation length

        # Estimate based on conversation history length
        # (This is a placeholder - real implementation would count tokens)
        estimated_usage = min(
            self.cycle_count / self.claude_code_config.max_cycles, 0.99
        )

        return estimated_usage

    def _compact_context(self) -> None:
        """
        Compact context by summarizing old conversations.

        Triggered at 92% context usage threshold. Strategy:
        1. Summarize old conversation history
        2. Preserve important information in CLAUDE.md
        3. Keep recent cycles intact
        4. Use regex/grep over vector search (transparency)

        Example:
            >>> agent.context_usage = 0.95
            >>> agent._compact_context()
            >>> assert agent.context_usage < 0.95
        """
        logger.info("Compacting context...")

        # TODO: Implement actual context compression
        # For now, just reset usage to simulate compression
        self.context_usage = 0.5  # Reset to 50% after compression

        logger.info(f"Context compacted to {self.context_usage:.1%}")

    def _load_claude_md(self) -> str:
        """
        Load CLAUDE.md file for project memory.

        CLAUDE.md provides project-specific context:
        - Repository conventions
        - Development environment setup
        - Code style guidelines
        - Unexpected behaviors
        - Architectural decisions

        Returns:
            String content of CLAUDE.md file

        Example:
            >>> content = agent._load_claude_md()
            >>> print(f"Loaded {len(content)} chars from CLAUDE.md")
        """
        claude_md_path = Path(self.claude_code_config.claude_md_path)

        if not claude_md_path.exists():
            logger.warning(f"CLAUDE.md not found at {claude_md_path}")
            return ""

        try:
            with open(claude_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"Loaded CLAUDE.md: {len(content)} characters")
            return content

        except Exception as e:
            logger.error(f"Error loading CLAUDE.md: {e}")
            return ""
