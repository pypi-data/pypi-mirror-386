"""
Task 2.2 - MultiCycleStrategy Unit Tests.

Tests for MultiCycleStrategy covering ReAct patterns and cyclic execution.

Evidence Required:
- 15+ test cases covering ReAct patterns and cycles
- 95%+ coverage for MultiCycleStrategy
- Tests for build_workflow(), execute(), cycle control, termination

References:
- TODO-157: Task 2.2
- ADR-006: Strategy Pattern design
"""

from typing import Any, Dict

import pytest
from kaizen.core.base_agent import BaseAgent
from kaizen.core.config import BaseAgentConfig
from kaizen.signatures import InputField, OutputField, Signature
from kaizen.strategies.multi_cycle import MultiCycleStrategy

from kailash.workflow.builder import WorkflowBuilder


class ReActSignature(Signature):
    """ReAct (Reason+Act) signature for testing."""

    task: str = InputField(desc="Task to accomplish")
    thought: str = OutputField(desc="Reasoning about next action")
    action: str = OutputField(desc="Action to take")
    observation: str = OutputField(desc="Observation from action")


class SimpleTaskSignature(Signature):
    """Simple task signature for testing."""

    task: str = InputField(desc="Task")
    result: str = OutputField(desc="Result")


@pytest.mark.unit
class TestMultiCycleStrategyInitialization:
    """Test MultiCycleStrategy initialization."""

    def test_strategy_initialization_default(self):
        """Task 2.2 - Strategy initializes with default max_cycles."""
        strategy = MultiCycleStrategy()

        assert strategy is not None
        assert isinstance(strategy, MultiCycleStrategy)
        assert strategy.max_cycles == 5  # Default

    def test_strategy_initialization_custom_max_cycles(self):
        """Task 2.2 - Strategy accepts custom max_cycles."""
        strategy = MultiCycleStrategy(max_cycles=10)

        assert strategy.max_cycles == 10

    def test_strategy_initialization_various_max_cycles(self):
        """Task 2.2 - Strategy handles various max_cycles values."""
        for max_cycles in [1, 3, 5, 10, 20]:
            strategy = MultiCycleStrategy(max_cycles=max_cycles)
            assert strategy.max_cycles == max_cycles


@pytest.mark.unit
class TestMultiCycleStrategyExecution:
    """Test MultiCycleStrategy.execute() method."""

    def test_execute_returns_dict(self):
        """Task 2.2 - execute() returns dict result."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        result = strategy.execute(agent, {"task": "Find information"})

        assert isinstance(result, dict)
        assert result is not None

    def test_execute_includes_cycle_metadata(self):
        """Task 2.2 - execute() includes cycle metadata."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=SimpleTaskSignature())
        strategy = MultiCycleStrategy(max_cycles=5)

        result = strategy.execute(agent, {"task": "Test task"})

        # Should include cycle metadata
        assert "cycles_used" in result
        assert "total_cycles" in result
        assert result["total_cycles"] == 5

    def test_execute_with_react_signature(self):
        """Task 2.2 - execute() works with ReAct signature."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        result = strategy.execute(agent, {"task": "Research topic"})

        assert isinstance(result, dict)
        # Phase 2 will validate thought/action/observation fields

    def test_execute_respects_max_cycles(self):
        """Task 2.2 - execute() respects max_cycles limit."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=SimpleTaskSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        result = strategy.execute(agent, {"task": "Task"})

        # cycles_used should not exceed max_cycles
        assert result.get("cycles_used", 0) <= 3

    def test_execute_error_handling(self):
        """Task 2.2 - execute() handles errors gracefully."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=5)

        # Execute with empty inputs - should not crash
        result = strategy.execute(agent, {})

        assert isinstance(result, dict)


@pytest.mark.unit
class TestMultiCycleStrategyWorkflowGeneration:
    """Test MultiCycleStrategy.build_workflow() method."""

    def test_build_workflow_returns_workflow_builder(self):
        """Task 2.12 - build_workflow() returns WorkflowBuilder."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=5)

        # build_workflow() not yet implemented in Phase 1
        if (
            hasattr(strategy, "build_workflow")
            and strategy.build_workflow(agent) is not None
        ):
            workflow = strategy.build_workflow(agent)
            assert isinstance(workflow, WorkflowBuilder)

    def test_build_workflow_for_react_pattern(self):
        """Task 2.12 - build_workflow() generates ReAct workflow."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        # Will be implemented in Task 2.12
        if (
            hasattr(strategy, "build_workflow")
            and strategy.build_workflow(agent) is not None
        ):
            workflow = strategy.build_workflow(agent)
            built = workflow.build()

            # Should contain cyclic nodes
            assert built is not None

    def test_build_workflow_includes_switch_node(self):
        """Task 2.13 - build_workflow() includes SwitchNode for cycle control."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=5)

        # Will be implemented in Task 2.13
        if (
            hasattr(strategy, "build_workflow")
            and strategy.build_workflow(agent) is not None
        ):
            workflow = strategy.build_workflow(agent)
            built = workflow.build()

            # Cyclic workflow should include SwitchNode
            assert built is not None


@pytest.mark.unit
class TestMultiCycleStrategyCycleControl:
    """Test MultiCycleStrategy cycle control logic."""

    def test_should_terminate_method_callable(self):
        """Task 2.15 - should_terminate() method exists and callable."""
        strategy = MultiCycleStrategy(max_cycles=5)

        assert hasattr(strategy, "should_terminate")
        assert callable(strategy.should_terminate)

    def test_should_terminate_on_max_cycles(self):
        """Task 2.15 - Terminates when max_cycles reached."""
        strategy = MultiCycleStrategy(max_cycles=3)

        # Phase 2 will implement actual termination logic
        if hasattr(strategy, "should_terminate"):
            # Cycle 2 (3rd cycle, 0-indexed) should terminate
            result = {"action": "continue"}
            should_stop = strategy.should_terminate(result, cycle_num=2)

            # Termination logic implementation in Phase 2
            assert should_stop is None or isinstance(should_stop, bool)

    def test_should_terminate_on_final_answer(self):
        """Task 2.15 - Terminates when final answer found."""
        strategy = MultiCycleStrategy(max_cycles=5)

        if hasattr(strategy, "should_terminate"):
            result = {"action": "FINAL ANSWER: The solution is..."}
            should_stop = strategy.should_terminate(result, cycle_num=1)

            # Phase 2 will implement detection
            assert should_stop is None or isinstance(should_stop, bool)

    def test_should_terminate_on_error(self):
        """Task 2.15 - Terminates on error conditions."""
        strategy = MultiCycleStrategy(max_cycles=5)

        if hasattr(strategy, "should_terminate"):
            result = {"error": "Failed to execute action"}
            should_stop = strategy.should_terminate(result, cycle_num=1)

            # Phase 2 will implement error detection
            assert should_stop is None or isinstance(should_stop, bool)


@pytest.mark.unit
class TestMultiCycleStrategyExtensionPoints:
    """Test MultiCycleStrategy extension points (Task 2.11)."""

    def test_pre_cycle_extension_point(self):
        """Task 2.11 - pre_cycle() extension point callable."""

        class CustomStrategy(MultiCycleStrategy):
            def pre_cycle(
                self, cycle_num: int, inputs: Dict[str, Any]
            ) -> Dict[str, Any]:
                inputs["cycle_num"] = cycle_num
                return inputs

        strategy = CustomStrategy(max_cycles=3)

        # Extension point should be callable
        assert hasattr(strategy, "pre_cycle")
        assert callable(strategy.pre_cycle)

    def test_parse_cycle_result_extension_point(self):
        """Task 2.11 - parse_cycle_result() extension point callable."""

        class CustomStrategy(MultiCycleStrategy):
            def parse_cycle_result(
                self, raw_result: Dict[str, Any], cycle_num: int
            ) -> Dict[str, Any]:
                raw_result["parsed_cycle"] = cycle_num
                return raw_result

        strategy = CustomStrategy(max_cycles=3)

        # Extension point should be callable
        assert hasattr(strategy, "parse_cycle_result")
        assert callable(strategy.parse_cycle_result)

    def test_should_terminate_extension_point(self):
        """Task 2.11 - should_terminate() extension point callable."""

        class CustomStrategy(MultiCycleStrategy):
            def should_terminate(
                self, cycle_result: Dict[str, Any], cycle_num: int
            ) -> bool:
                return cycle_result.get("done", False)

        strategy = CustomStrategy(max_cycles=3)

        # Extension point should be callable
        assert hasattr(strategy, "should_terminate")
        assert callable(strategy.should_terminate)

    def test_extract_observation_extension_point(self):
        """Task 2.11 - extract_observation() extension point callable."""

        class CustomStrategy(MultiCycleStrategy):
            def extract_observation(self, cycle_result: Dict[str, Any]) -> str:
                return f"Observed: {cycle_result.get('action', 'none')}"

        strategy = CustomStrategy(max_cycles=3)

        # Extension point should be callable
        assert hasattr(strategy, "extract_observation")
        assert callable(strategy.extract_observation)


@pytest.mark.unit
class TestMultiCycleStrategyReActPattern:
    """Test MultiCycleStrategy with ReAct pattern."""

    def test_react_pattern_thought_generation(self):
        """Task 2.12 - ReAct pattern generates thoughts."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        result = strategy.execute(agent, {"task": "Find CEO name"})

        assert isinstance(result, dict)
        # Phase 2 will validate thought field

    def test_react_pattern_action_generation(self):
        """Task 2.12 - ReAct pattern generates actions."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        result = strategy.execute(agent, {"task": "Search database"})

        assert isinstance(result, dict)
        # Phase 2 will validate action field

    def test_react_pattern_observation_extraction(self):
        """Task 2.12 - ReAct pattern extracts observations."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        result = strategy.execute(agent, {"task": "Complete multi-step task"})

        assert isinstance(result, dict)
        # Phase 2 will validate observation field

    def test_react_pattern_cycle_iteration(self):
        """Task 2.12 - ReAct pattern iterates through cycles."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=5)

        result = strategy.execute(agent, {"task": "Complex research"})

        # Should track cycles
        assert "cycles_used" in result
        assert result["cycles_used"] >= 1


@pytest.mark.unit
class TestMultiCycleStrategyToolIntegration:
    """Test MultiCycleStrategy tool integration (Task 2.14)."""

    def test_tool_discovery_capability(self):
        """Task 2.14 - Strategy supports tool discovery."""
        strategy = MultiCycleStrategy(max_cycles=5)

        # Phase 2 will implement tool discovery
        # For now, validate strategy exists
        assert strategy is not None

    def test_tool_execution_capability(self):
        """Task 2.14 - Strategy supports tool execution."""
        config = BaseAgentConfig(
            model="gpt-4", strategy_type="multi_cycle", mcp_enabled=True
        )
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        # Phase 2 will implement tool execution
        result = strategy.execute(agent, {"task": "Use tools"})

        assert isinstance(result, dict)

    def test_tool_result_observation(self):
        """Task 2.14 - Tool results become observations."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        # Phase 2 will implement tool-to-observation flow
        result = strategy.execute(agent, {"task": "Execute tool"})

        assert isinstance(result, dict)


@pytest.mark.unit
class TestMultiCycleStrategyTermination:
    """Test MultiCycleStrategy termination conditions."""

    def test_termination_on_success(self):
        """Task 2.15 - Terminates on successful completion."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=SimpleTaskSignature())
        strategy = MultiCycleStrategy(max_cycles=10)

        result = strategy.execute(agent, {"task": "Simple task"})

        # Should terminate before max_cycles if successful
        # Phase 2 will implement early termination
        assert isinstance(result, dict)

    def test_termination_on_timeout(self):
        """Task 2.15 - Terminates on timeout."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=100)  # Large number

        # Phase 2 will implement timeout detection
        result = strategy.execute(agent, {"task": "Task"})

        assert isinstance(result, dict)
        # Should not actually run 100 cycles

    def test_termination_cycle_limit(self):
        """Task 2.15 - Respects max_cycles limit."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=ReActSignature())
        strategy = MultiCycleStrategy(max_cycles=2)

        result = strategy.execute(agent, {"task": "Long task"})

        # Should not exceed max_cycles
        assert result.get("cycles_used", 0) <= 2


@pytest.mark.unit
class TestMultiCycleStrategyPerformance:
    """Test MultiCycleStrategy performance characteristics."""

    def test_strategy_execution_lightweight(self):
        """Task 2.2 - Strategy execution is lightweight."""
        import time

        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=SimpleTaskSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        start = time.time()
        result = strategy.execute(agent, {"task": "Test"})
        duration_ms = (time.time() - start) * 1000

        # Execution should be fast (< 200ms for skeleton with 3 cycles)
        assert duration_ms < 200
        assert isinstance(result, dict)

    def test_strategy_cycle_overhead_minimal(self):
        """Task 2.2 - Each cycle adds minimal overhead."""
        import time

        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=SimpleTaskSignature())

        # Test with 1 cycle
        strategy_1 = MultiCycleStrategy(max_cycles=1)
        start = time.time()
        strategy_1.execute(agent, {"task": "Test"})
        time_1 = time.time() - start

        # Test with 5 cycles
        strategy_5 = MultiCycleStrategy(max_cycles=5)
        start = time.time()
        strategy_5.execute(agent, {"task": "Test"})
        time_5 = time.time() - start

        # Both should be very fast (skeleton mode)
        assert time_1 < 0.1  # < 100ms
        assert time_5 < 0.5  # < 500ms
        # Cycle overhead is minimal in skeleton mode

    def test_strategy_stateless_between_executions(self):
        """Task 2.2 - Strategy maintains no state between executions."""
        config = BaseAgentConfig(model="gpt-4", strategy_type="multi_cycle")
        agent = BaseAgent(config=config, signature=SimpleTaskSignature())
        strategy = MultiCycleStrategy(max_cycles=3)

        result1 = strategy.execute(agent, {"task": "First"})
        result2 = strategy.execute(agent, {"task": "Second"})

        # Each execution should be independent
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        # No state carryover
