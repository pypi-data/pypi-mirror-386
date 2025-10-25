"""
BaseAutonomousAgent - Autonomous execution with tool-calling loops.

This module implements the BaseAutonomousAgent class that extends BaseAgent with
autonomous execution capabilities based on Claude Code and Codex research patterns.

Key Features:
1. Single-threaded while(tool_calls_exist) loop (Claude Code pattern)
2. TODO-based planning system for structured task decomposition
3. JSONL checkpoint format for state persistence
4. Objective convergence detection via tool_calls field (ADR-013)

Architecture:
- Extends BaseAgent with autonomous execution methods
- Uses MultiCycleStrategy for iterative execution
- Supports tool calling with convergence detection
- Optional planning system for complex tasks
- Checkpoint persistence for long-running tasks

References:
- docs/research/CLAUDE_CODE_AUTONOMOUS_ARCHITECTURE.md
- docs/research/CODEX_AUTONOMOUS_ARCHITECTURE.md
- ADR-013: Objective Convergence Detection
- TODO-163: Autonomous Patterns Implementation

Author: Kaizen Framework Team
Created: 2025-10-22
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from kaizen.core.base_agent import BaseAgent
from kaizen.signatures import Signature
from kaizen.strategies.multi_cycle import MultiCycleStrategy
from kaizen.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class AutonomousConfig:
    """
    Configuration for autonomous agent execution.

    This config extends BaseAgentConfig with autonomous-specific parameters:
    - max_cycles: Maximum iteration cycles for autonomous loop
    - planning_enabled: Enable TODO-based planning system
    - checkpoint_frequency: Save state every N cycles

    The config can be automatically converted to BaseAgentConfig using
    BaseAgentConfig.from_domain_config(), enabling seamless integration
    with the BaseAgent architecture.

    Example:
        >>> config = AutonomousConfig(
        ...     max_cycles=20,
        ...     planning_enabled=True,
        ...     checkpoint_frequency=5,
        ...     llm_provider="openai",
        ...     model="gpt-4"
        ... )
        >>> agent = BaseAutonomousAgent(config=config, signature=signature)
    """

    # Autonomous-specific parameters
    max_cycles: int = 20
    planning_enabled: bool = True
    checkpoint_frequency: int = 5

    # BaseAgentConfig parameters (for conversion)
    llm_provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    provider_config: Optional[Dict[str, Any]] = None

    # Feature flags
    logging_enabled: bool = True
    performance_enabled: bool = False
    error_handling_enabled: bool = True
    batch_processing_enabled: bool = False
    memory_enabled: bool = False
    transparency_enabled: bool = False
    mcp_enabled: bool = False

    # Strategy configuration
    strategy_type: str = "multi_cycle"


class BaseAutonomousAgent(BaseAgent):
    """
    Autonomous agent with tool-calling loops and planning capabilities.

    BaseAutonomousAgent extends BaseAgent with autonomous execution patterns
    inspired by Claude Code and Codex:

    1. **Autonomous Loop**: Single-threaded while(tool_calls_exist) pattern
    2. **Objective Convergence**: Uses tool_calls field for convergence detection
    3. **Planning System**: Optional TODO-based task decomposition
    4. **State Persistence**: JSONL checkpoint format for recovery

    Execution Flow:
        1. create_plan() - Generate structured task list (if enabled)
        2. autonomous_loop() - Execute cycles until convergence:
           a. gather_context() - Collect current state
           b. take_action() - Execute LLM + tools
           c. verify() - Check convergence via tool_calls
           d. iterate() - Continue or terminate
        3. save_checkpoint() - Persist state (at specified frequency)

    Convergence Detection (ADR-013):
        - **Objective** (preferred): Check tool_calls field
          - Empty list [] → converged
          - Non-empty list → not converged
        - **Subjective** (fallback): Action-based detection
          - action == "finish" → converged
          - confidence > threshold → converged

    Example:
        >>> from kaizen.agents.autonomous.base import BaseAutonomousAgent, AutonomousConfig
        >>>
        >>> config = AutonomousConfig(
        ...     max_cycles=15,
        ...     planning_enabled=True,
        ...     llm_provider="openai",
        ...     model="gpt-4"
        ... )
        >>>
        >>> agent = BaseAutonomousAgent(
        ...     config=config,
        ...     signature=TaskSignature(),
        ...     tool_registry=registry
        ... )
        >>>
        >>> result = await agent.execute_autonomously("Build API integration")
        >>> print(f"Completed in {result['cycles_used']} cycles")

    Notes:
        - Uses MultiCycleStrategy for cycle management
        - Tool registry integration for autonomous tool use
        - Planning is optional (can be disabled for simple tasks)
        - Checkpoints enable recovery from failures
    """

    def __init__(
        self,
        config: AutonomousConfig,
        signature: Optional[Signature] = None,
        strategy: Optional[MultiCycleStrategy] = None,
        tool_registry: Optional[ToolRegistry] = None,
        checkpoint_dir: Optional[Path] = None,
        **kwargs,
    ):
        """
        Initialize BaseAutonomousAgent with autonomous execution capabilities.

        Args:
            config: AutonomousConfig with autonomous-specific parameters
            signature: Optional signature (uses _default_signature() if None)
            strategy: Optional MultiCycleStrategy (creates default if None)
            tool_registry: Optional tool registry for tool execution
            checkpoint_dir: Optional directory for checkpoint persistence
            **kwargs: Additional arguments passed to BaseAgent.__init__

        Example:
            >>> config = AutonomousConfig(max_cycles=20, planning_enabled=True)
            >>> agent = BaseAutonomousAgent(
            ...     config=config,
            ...     signature=signature,
            ...     tool_registry=registry
            ... )
        """
        # Store original autonomous config
        self.autonomous_config = config

        # Create MultiCycleStrategy with convergence detection
        if strategy is None:
            strategy = MultiCycleStrategy(
                max_cycles=config.max_cycles,
                convergence_check=self._check_convergence,
            )

        # Initialize BaseAgent (will auto-convert config to BaseAgentConfig)
        super().__init__(
            config=config,
            signature=signature,
            strategy=strategy,
            tool_registry=tool_registry,
            **kwargs,
        )

        # Autonomous-specific state
        self.checkpoint_dir = checkpoint_dir or Path("./checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_plan: List[Dict[str, Any]] = []
        self.cycle_count: int = 0

    async def execute_autonomously(self, task: str) -> Dict[str, Any]:
        """
        Main autonomous execution entry point.

        Executes a task autonomously using the following flow:
        1. Create plan (if planning enabled)
        2. Run autonomous loop until convergence
        3. Return results with metadata

        Args:
            task: Task description to execute autonomously

        Returns:
            Dict with execution results, including:
            - result: Final task result
            - cycles_used: Number of cycles executed
            - total_cycles: Maximum cycles allowed
            - plan: Task plan (if planning enabled)
            - checkpoints: List of checkpoint files created

        Example:
            >>> result = await agent.execute_autonomously(
            ...     "Analyze sales data and generate report"
            ... )
            >>> print(f"Task completed in {result['cycles_used']} cycles")
            >>> print(f"Result: {result['result']}")

        Raises:
            ValueError: If task is empty or invalid
            RuntimeError: If execution fails critically
        """
        if not task or not task.strip():
            raise ValueError("Task cannot be empty")

        logger.info(f"Starting autonomous execution: {task}")

        # Step 1: Create plan (if enabled)
        if self.autonomous_config.planning_enabled:
            logger.info("Creating execution plan...")
            self.current_plan = await self._create_plan(task)
            logger.info(f"Plan created with {len(self.current_plan)} tasks")
        else:
            self.current_plan = []

        # Step 2: Execute autonomous loop
        logger.info("Starting autonomous loop...")
        result = await self._autonomous_loop(task)

        # Step 3: Add metadata
        result["plan"] = self.current_plan if self.current_plan else []
        result["task"] = task

        logger.info(
            f"Autonomous execution completed in {result.get('cycles_used', 0)} cycles"
        )

        return result

    async def _autonomous_loop(self, task: str) -> Dict[str, Any]:
        """
        Autonomous execution loop following while(tool_calls_exist) pattern.

        This implements the Claude Code autonomous loop:
        1. Execute cycle (LLM reasoning + tool calls)
        2. Check convergence via tool_calls field
        3. Continue if tool_calls exist, exit if empty
        4. Enforce max_cycles limit

        Args:
            task: Task to execute

        Returns:
            Dict with final result and metadata

        Example:
            >>> result = await agent._autonomous_loop("Search and summarize")
            >>> if result.get('tool_calls') == []:
            ...     print("Task converged successfully")
        """
        self.cycle_count = 0
        final_result = {}

        # Prepare initial inputs
        inputs = {"task": task}
        if self.current_plan:
            inputs["plan"] = self.current_plan

        # Autonomous loop: while(tool_calls_exist)
        for cycle_num in range(self.autonomous_config.max_cycles):
            self.cycle_count = cycle_num + 1

            try:
                logger.debug(
                    f"Cycle {self.cycle_count}/{self.autonomous_config.max_cycles}"
                )

                # Execute cycle using strategy
                cycle_result = self.strategy.execute(self, inputs)

                # Save checkpoint at specified frequency
                if self.cycle_count % self.autonomous_config.checkpoint_frequency == 0:
                    self._save_checkpoint(cycle_result, cycle_num)

                # Check convergence (objective via tool_calls)
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
        final_result["total_cycles"] = self.autonomous_config.max_cycles

        return final_result

    def _check_convergence(self, response: Dict[str, Any]) -> bool:
        """
        Check if agent has converged using objective detection (ADR-013).

        Convergence Detection Priority:
        1. **Objective** (preferred): Check tool_calls field
           - Empty list [] → converged
           - Non-empty list → not converged
           - Missing/None → fall back to subjective

        2. **Subjective** (fallback): Action-based detection
           - action == "finish" → converged
           - confidence > 0.9 → converged
           - Default → True (safe convergence)

        Args:
            response: LLM response to check for convergence

        Returns:
            bool: True if converged (stop iteration), False if not (continue)

        Example:
            >>> response = {"result": "Done", "tool_calls": []}
            >>> converged = agent._check_convergence(response)
            >>> assert converged is True

            >>> response = {"result": "Need tool", "tool_calls": [{"name": "search"}]}
            >>> converged = agent._check_convergence(response)
            >>> assert converged is False
        """
        # OBJECTIVE DETECTION (preferred): Check tool_calls field
        if "tool_calls" in response:
            tool_calls = response.get("tool_calls")

            # Handle None case
            if tool_calls is None:
                logger.debug("tool_calls is None, falling back to subjective")
            # Check if tool_calls is a list
            elif isinstance(tool_calls, list):
                # Empty list = converged
                if not tool_calls:
                    logger.debug("Objective convergence: tool_calls is empty")
                    return True
                # Non-empty list = not converged
                else:
                    logger.debug(
                        f"Objective non-convergence: {len(tool_calls)} tool_calls"
                    )
                    return False
            # Malformed tool_calls (not a list)
            else:
                logger.warning(
                    f"Malformed tool_calls field (type: {type(tool_calls)}), falling back"
                )

        # SUBJECTIVE DETECTION (fallback): Action-based detection
        logger.debug("Using subjective convergence detection")

        # Check for finish action
        action = response.get("action", "")
        if action == "finish":
            logger.debug("Subjective convergence: action == 'finish'")
            return True

        # Check for high confidence
        confidence = response.get("confidence", 0.0)
        if confidence > 0.9:
            logger.debug(f"Subjective convergence: confidence = {confidence}")
            return True

        # Default: converged (safe fallback when no clear signals)
        logger.debug("Default convergence: no clear signals")
        return True

    async def _create_plan(self, task: str) -> List[Dict[str, Any]]:
        """
        Generate TODO-style structured task plan.

        Uses LLM to decompose the task into a list of subtasks with
        TODO-style structure (task, status, priority, etc.).

        Args:
            task: Task to create plan for

        Returns:
            List of task dictionaries with TODO structure:
            - task: Task description
            - status: "pending", "in_progress", or "completed"
            - priority: "low", "medium", or "high"
            - estimated_cycles: Estimated cycles needed

        Example:
            >>> plan = await agent._create_plan("Build REST API")
            >>> print(plan)
            [
                {"task": "Design API schema", "status": "pending", "priority": "high"},
                {"task": "Implement endpoints", "status": "pending", "priority": "high"},
                {"task": "Write tests", "status": "pending", "priority": "medium"}
            ]
        """
        # If planning is disabled, return empty plan
        if not self.autonomous_config.planning_enabled:
            return []

        # Generate plan from LLM
        plan = await self._generate_plan_from_llm(task)
        return plan

    async def _generate_plan_from_llm(self, task: str) -> List[Dict[str, Any]]:
        """
        Use LLM to generate a structured task plan.

        This is a placeholder that will use the LLM to decompose
        the task into subtasks. For now, returns a simple plan structure.

        Args:
            task: Task to plan

        Returns:
            List of task dictionaries

        Note:
            Full LLM integration will be added in future enhancement.
            Current implementation provides basic structure.
        """
        # TODO: Implement full LLM-based planning
        # For now, return simple plan structure
        return [
            {
                "task": f"Execute: {task}",
                "status": "pending",
                "priority": "high",
                "estimated_cycles": 5,
            }
        ]

    def _save_checkpoint(self, state: Dict[str, Any], cycle_num: int) -> None:
        """
        Save execution checkpoint in JSONL format.

        Checkpoints enable recovery from failures and provide audit trail.
        Saved in JSONL format (one JSON object per line) for easy parsing.

        Args:
            state: Current execution state
            cycle_num: Current cycle number

        Example:
            >>> agent._save_checkpoint(result, cycle_num=5)
            # Saves to: ./checkpoints/task_<timestamp>_cycle_5.jsonl
        """
        checkpoint_file = (
            self.checkpoint_dir / f"checkpoint_cycle_{cycle_num:03d}.jsonl"
        )

        checkpoint_data = {
            "cycle": cycle_num,
            "state": state,
            "plan": self.current_plan,
        }

        try:
            with open(checkpoint_file, "a") as f:
                f.write(json.dumps(checkpoint_data) + "\n")

            logger.debug(f"Checkpoint saved: {checkpoint_file}")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self, cycle_num: int) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint from JSONL file.

        Args:
            cycle_num: Cycle number to load

        Returns:
            Checkpoint data or None if not found

        Example:
            >>> state = agent._load_checkpoint(cycle_num=5)
            >>> if state:
            ...     print(f"Restored from cycle {state['cycle']}")
        """
        checkpoint_file = (
            self.checkpoint_dir / f"checkpoint_cycle_{cycle_num:03d}.jsonl"
        )

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, "r") as f:
                # Read last line (most recent checkpoint)
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")

        return None
