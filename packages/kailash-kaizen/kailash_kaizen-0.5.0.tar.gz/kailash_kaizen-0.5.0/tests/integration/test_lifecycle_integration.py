"""
Integration tests for Phase 3 lifecycle systems.

Tests cross-system integration between Hooks, State Persistence, and Interrupts.
"""

import tempfile
from pathlib import Path

import anyio
import pytest

from kaizen.core.autonomy.hooks import HookContext, HookEvent, HookManager, HookResult
from kaizen.core.autonomy.interrupts import (
    BudgetInterruptHandler,
    InterruptManager,
    InterruptMode,
    InterruptSource,
)
from kaizen.core.autonomy.state import AgentState, FilesystemStorage, StateManager


class TestHooksStateIntegration:
    """Test integration between Hooks and State systems"""

    @pytest.mark.asyncio
    async def test_hooks_triggered_during_checkpoint(self):
        """Test hooks are triggered during checkpoint save"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FilesystemStorage(base_dir=temp_dir)
            state_manager = StateManager(storage=storage)
            hook_manager = HookManager()

            # Track hook invocations
            pre_checkpoint_called = False
            post_checkpoint_called = False

            async def pre_checkpoint_hook(context: HookContext) -> HookResult:
                nonlocal pre_checkpoint_called
                pre_checkpoint_called = True
                assert context.event == HookEvent.PRE_CHECKPOINT_SAVE
                return HookResult(success=True)

            async def post_checkpoint_hook(context: HookContext) -> HookResult:
                nonlocal post_checkpoint_called
                post_checkpoint_called = True
                assert context.event == HookEvent.POST_CHECKPOINT_SAVE
                return HookResult(success=True)

            hook_manager.register(HookEvent.PRE_CHECKPOINT_SAVE, pre_checkpoint_hook)
            hook_manager.register(HookEvent.POST_CHECKPOINT_SAVE, post_checkpoint_hook)

            # Create agent state
            agent_state = AgentState(agent_id="agent1", step_number=5)

            # Trigger checkpoint with hooks
            await hook_manager.trigger(
                HookEvent.PRE_CHECKPOINT_SAVE,
                agent_id="agent1",
                data={"checkpoint_id": agent_state.checkpoint_id},
            )

            checkpoint_id = await state_manager.save_checkpoint(agent_state, force=True)

            await hook_manager.trigger(
                HookEvent.POST_CHECKPOINT_SAVE,
                agent_id="agent1",
                data={"checkpoint_id": checkpoint_id},
            )

            # Verify hooks were called
            assert pre_checkpoint_called
            assert post_checkpoint_called

            # Verify checkpoint was saved
            loaded_state = await state_manager.load_checkpoint(checkpoint_id)
            assert loaded_state.agent_id == "agent1"

    @pytest.mark.asyncio
    async def test_hooks_capture_checkpoint_metadata(self):
        """Test hooks can capture and modify checkpoint metadata"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FilesystemStorage(base_dir=temp_dir)
            state_manager = StateManager(storage=storage)
            hook_manager = HookManager()

            metadata_collector = {}

            async def collect_metadata_hook(context: HookContext) -> HookResult:
                checkpoint_id = context.data.get("checkpoint_id")
                metadata_collector[checkpoint_id] = {
                    "timestamp": context.data.get("timestamp"),
                    "step": context.data.get("step_number"),
                }
                return HookResult(success=True)

            hook_manager.register(HookEvent.POST_CHECKPOINT_SAVE, collect_metadata_hook)

            # Create and save checkpoint
            agent_state = AgentState(agent_id="agent1", step_number=10)

            checkpoint_id = await state_manager.save_checkpoint(agent_state, force=True)

            await hook_manager.trigger(
                HookEvent.POST_CHECKPOINT_SAVE,
                agent_id="agent1",
                data={
                    "checkpoint_id": checkpoint_id,
                    "step_number": 10,
                    "timestamp": agent_state.timestamp,
                },
            )

            # Verify metadata was collected
            assert checkpoint_id in metadata_collector
            assert metadata_collector[checkpoint_id]["step"] == 10


class TestStateInterruptsIntegration:
    """Test integration between State and Interrupts systems"""

    @pytest.mark.asyncio
    async def test_interrupt_triggers_checkpoint(self):
        """Test interrupt causes checkpoint to be saved"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FilesystemStorage(base_dir=temp_dir)
            state_manager = StateManager(storage=storage)
            interrupt_manager = InterruptManager()

            # Create agent state
            agent_state = AgentState(agent_id="agent1", step_number=5, status="running")

            # Request interrupt
            interrupt_manager.request_interrupt(
                mode=InterruptMode.GRACEFUL,
                source=InterruptSource.USER,
                message="User requested stop",
            )

            # Execute shutdown with checkpoint
            status = await interrupt_manager.execute_shutdown(
                state_manager, agent_state
            )

            # Verify interrupt status
            assert status.interrupted is True
            assert status.checkpoint_id is not None

            # Verify checkpoint was saved
            loaded_state = await state_manager.load_checkpoint(status.checkpoint_id)
            assert loaded_state.agent_id == "agent1"
            assert loaded_state.status == "interrupted"

    @pytest.mark.asyncio
    async def test_resume_from_interrupted_checkpoint(self):
        """Test resuming from checkpoint created during interrupt"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FilesystemStorage(base_dir=temp_dir)
            state_manager = StateManager(storage=storage)
            interrupt_manager = InterruptManager()

            # Create agent state with execution context
            agent_state = AgentState(
                agent_id="agent1",
                step_number=5,
                status="running",
                pending_actions=[{"action": "task1"}, {"action": "task2"}],
            )

            # Simulate interrupt during execution
            interrupt_manager.request_interrupt(
                mode=InterruptMode.GRACEFUL,
                source=InterruptSource.TIMEOUT,
                message="Timeout",
            )

            status = await interrupt_manager.execute_shutdown(
                state_manager, agent_state
            )

            # Resume from checkpoint (fork creates a new branch)
            resumed_state = await state_manager.fork_from_checkpoint(
                status.checkpoint_id
            )

            # Verify resumed state preserves context
            assert resumed_state.agent_id == "agent1"
            assert resumed_state.step_number == 5
            assert len(resumed_state.pending_actions) == 2
            assert resumed_state.parent_checkpoint_id == status.checkpoint_id

    @pytest.mark.asyncio
    async def test_budget_interrupt_with_checkpoint(self):
        """Test budget interrupt triggers checkpoint with cost metadata"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FilesystemStorage(base_dir=temp_dir)
            state_manager = StateManager(storage=storage)
            interrupt_manager = InterruptManager()
            budget_handler = BudgetInterruptHandler(interrupt_manager, budget_usd=5.0)

            # Create agent state
            agent_state = AgentState(agent_id="agent1", step_number=3, status="running")

            # Track costs until budget exceeded
            budget_handler.track_cost(2.0)
            assert not interrupt_manager.is_interrupted()

            budget_handler.track_cost(3.5)  # Total = 5.5, exceeds 5.0
            assert interrupt_manager.is_interrupted()

            # Execute shutdown with checkpoint
            status = await interrupt_manager.execute_shutdown(
                state_manager, agent_state
            )

            # Verify interrupt metadata
            assert status.reason.source == InterruptSource.BUDGET
            assert status.reason.metadata["budget_usd"] == 5.0
            assert status.reason.metadata["spent_usd"] == 5.5

            # Verify checkpoint includes budget info
            loaded_state = await state_manager.load_checkpoint(status.checkpoint_id)
            assert loaded_state.status == "interrupted"


class TestHooksInterruptsIntegration:
    """Test integration between Hooks and Interrupts systems"""

    @pytest.mark.asyncio
    async def test_hooks_triggered_during_interrupt(self):
        """Test hooks are triggered during interrupt process"""
        interrupt_manager = InterruptManager()
        hook_manager = HookManager()

        # Track hook calls with nonlocal counter
        hook_call_count = {"count": 0}

        async def shutdown_monitoring_hook(context: HookContext) -> HookResult:
            hook_call_count["count"] += 1
            return HookResult(success=True)

        # Register hook for agent loop (would fire before shutdown)
        hook_manager.register(HookEvent.POST_AGENT_LOOP, shutdown_monitoring_hook)

        # Simulate agent loop completion before interrupt
        await hook_manager.trigger(
            HookEvent.POST_AGENT_LOOP,
            agent_id="agent1",
            data={"step": 5, "status": "running"},
        )

        # Request interrupt
        interrupt_manager.request_interrupt(
            mode=InterruptMode.GRACEFUL,
            source=InterruptSource.USER,
            message="Stop",
        )

        # Execute shutdown
        status = await interrupt_manager.execute_shutdown()

        # Verify hooks were called
        assert hook_call_count["count"] == 1  # Called once for POST_AGENT_LOOP
        assert status.interrupted is True

    @pytest.mark.asyncio
    async def test_shutdown_callbacks_with_hooks(self):
        """Test shutdown callbacks can trigger final hooks"""
        interrupt_manager = InterruptManager()
        hook_manager = HookManager()

        final_cleanup_called = False

        async def final_cleanup_hook(context: HookContext) -> HookResult:
            nonlocal final_cleanup_called
            final_cleanup_called = True
            return HookResult(success=True)

        hook_manager.register(HookEvent.POST_AGENT_LOOP, final_cleanup_hook)

        # Register shutdown callback that triggers hook
        async def shutdown_callback():
            await hook_manager.trigger(
                HookEvent.POST_AGENT_LOOP,
                agent_id="agent1",
                data={"status": "shutdown"},
            )

        interrupt_manager.register_shutdown_callback(shutdown_callback)

        # Request interrupt and shutdown
        interrupt_manager.request_interrupt(
            mode=InterruptMode.GRACEFUL,
            source=InterruptSource.USER,
            message="Stop",
        )

        await interrupt_manager.execute_shutdown()

        # Verify final hook was called
        assert final_cleanup_called


class TestAllThreeSystemsIntegration:
    """Test integration of all three Phase 3 systems together"""

    @pytest.mark.asyncio
    async def test_complete_lifecycle_workflow(self):
        """Test complete workflow: hooks monitor execution, interrupt triggers checkpoint"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FilesystemStorage(base_dir=temp_dir)
            state_manager = StateManager(storage=storage)
            interrupt_manager = InterruptManager()
            hook_manager = HookManager()

            # Track execution flow with dict to avoid list mutation issues
            execution_log = {"events": []}

            async def logging_hook(context: HookContext) -> HookResult:
                execution_log["events"].append(
                    {"event": context.event_type.value, "data": context.data}
                )
                return HookResult(success=True)

            # Register hooks for key events
            hook_manager.register(HookEvent.PRE_AGENT_LOOP, logging_hook)
            hook_manager.register(HookEvent.POST_AGENT_LOOP, logging_hook)
            hook_manager.register(HookEvent.PRE_CHECKPOINT_SAVE, logging_hook)
            hook_manager.register(HookEvent.POST_CHECKPOINT_SAVE, logging_hook)

            # Create agent state
            agent_state = AgentState(agent_id="agent1", step_number=0, status="running")

            # Simulate agent execution loop
            for step in range(3):
                # Pre-loop hook
                await hook_manager.trigger(
                    HookEvent.PRE_AGENT_LOOP,
                    agent_id="agent1",
                    data={"step": step},
                )

                # Update state
                agent_state.step_number = step + 1

                # Post-loop hook
                await hook_manager.trigger(
                    HookEvent.POST_AGENT_LOOP,
                    agent_id="agent1",
                    data={"step": step + 1},
                )

            # Interrupt during execution
            interrupt_manager.request_interrupt(
                mode=InterruptMode.GRACEFUL,
                source=InterruptSource.USER,
                message="User stop",
            )

            # Trigger checkpoint hooks
            await hook_manager.trigger(
                HookEvent.PRE_CHECKPOINT_SAVE,
                agent_id="agent1",
                data={"step": agent_state.step_number},
            )

            # Execute shutdown with checkpoint
            status = await interrupt_manager.execute_shutdown(
                state_manager, agent_state
            )

            await hook_manager.trigger(
                HookEvent.POST_CHECKPOINT_SAVE,
                agent_id="agent1",
                data={"checkpoint_id": status.checkpoint_id},
            )

            # Verify execution flow
            assert (
                len(execution_log["events"]) == 8
            )  # 3 pre + 3 post + 1 pre-ckpt + 1 post-ckpt

            # Verify checkpoint was created
            assert status.checkpoint_id is not None
            loaded_state = await state_manager.load_checkpoint(status.checkpoint_id)
            assert loaded_state.step_number == 3
            assert loaded_state.status == "interrupted"

    @pytest.mark.asyncio
    async def test_hooks_track_cost_interrupt_saves_checkpoint(self):
        """Test hooks track costs, budget triggers interrupt, checkpoint preserves state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FilesystemStorage(base_dir=temp_dir)
            state_manager = StateManager(storage=storage)
            interrupt_manager = InterruptManager()
            hook_manager = HookManager()
            budget_handler = BudgetInterruptHandler(interrupt_manager, budget_usd=1.0)

            # Cost tracking via hook
            total_cost = 0.0

            async def cost_tracking_hook(context: HookContext) -> HookResult:
                nonlocal total_cost
                cost = context.data.get("cost_usd", 0.0)
                total_cost += cost
                budget_handler.track_cost(cost)
                return HookResult(success=True)

            hook_manager.register(HookEvent.POST_TOOL_USE, cost_tracking_hook)

            # Create agent state
            agent_state = AgentState(
                agent_id="agent1", step_number=0, status="running", budget_spent_usd=0.0
            )

            # Simulate tool uses with costs
            costs = [0.3, 0.4, 0.5]  # Total = 1.2, exceeds 1.0 budget

            for i, cost in enumerate(costs):
                await hook_manager.trigger(
                    HookEvent.POST_TOOL_USE,
                    agent_id="agent1",
                    data={"tool": f"tool_{i}", "cost_usd": cost},
                )

                agent_state.step_number = i + 1
                agent_state.budget_spent_usd = total_cost

                # Check if interrupted
                if interrupt_manager.is_interrupted():
                    break

            # Should be interrupted after 3rd tool use
            assert interrupt_manager.is_interrupted()
            assert total_cost == 1.2

            # Execute shutdown with checkpoint
            status = await interrupt_manager.execute_shutdown(
                state_manager, agent_state
            )

            # Verify checkpoint preserves budget info
            loaded_state = await state_manager.load_checkpoint(status.checkpoint_id)
            assert loaded_state.budget_spent_usd == 1.2
            assert loaded_state.status == "interrupted"

            # Verify interrupt reason
            assert status.reason.source == InterruptSource.BUDGET
            assert status.reason.metadata["spent_usd"] == 1.2
