"""
Interrupt manager for graceful shutdown coordination.

Manages interrupt signals, shutdown callbacks, and checkpoint integration.
"""

import logging
import signal
from typing import Any, Awaitable, Callable

import anyio

from .types import InterruptMode, InterruptReason, InterruptSource, InterruptStatus

logger = logging.getLogger(__name__)


class InterruptManager:
    """
    Manages interrupt signals and graceful shutdown.

    Handles OS signals (SIGINT, SIGTERM), programmatic interrupts,
    and coordinates shutdown sequence with checkpointing.
    """

    def __init__(self):
        """Initialize interrupt manager"""
        self._interrupted = anyio.Event()
        self._interrupt_reason: InterruptReason | None = None
        self._shutdown_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._signal_handlers_installed = False
        self._original_handlers: dict[int, Any] = {}

    def install_signal_handlers(self) -> None:
        """
        Install OS signal handlers (SIGINT, SIGTERM, SIGUSR1).

        Idempotent - can be called multiple times safely.
        """
        if self._signal_handlers_installed:
            logger.debug("Signal handlers already installed")
            return

        # Handle Ctrl+C (SIGINT)
        self._original_handlers[signal.SIGINT] = signal.signal(
            signal.SIGINT, self._handle_signal
        )

        # Handle termination (SIGTERM)
        self._original_handlers[signal.SIGTERM] = signal.signal(
            signal.SIGTERM, self._handle_signal
        )

        # Handle user signal 1 (SIGUSR1) - optional, for custom interrupts
        try:
            self._original_handlers[signal.SIGUSR1] = signal.signal(
                signal.SIGUSR1, self._handle_signal
            )
        except (AttributeError, ValueError):
            # SIGUSR1 not available on Windows
            logger.debug("SIGUSR1 not available on this platform")

        self._signal_handlers_installed = True
        logger.info("Signal handlers installed (SIGINT, SIGTERM, SIGUSR1)")

    def uninstall_signal_handlers(self) -> None:
        """
        Restore original signal handlers.

        Call during cleanup or testing.
        """
        if not self._signal_handlers_installed:
            return

        for signum, handler in self._original_handlers.items():
            if handler is not None:
                signal.signal(signum, handler)

        self._signal_handlers_installed = False
        self._original_handlers.clear()
        logger.info("Signal handlers uninstalled")

    def _handle_signal(self, signum: int, frame) -> None:
        """
        Signal handler (called by OS).

        Must be thread-safe and non-blocking.
        """
        try:
            signal_name = signal.Signals(signum).name
        except ValueError:
            signal_name = f"Signal-{signum}"

        logger.warning(f"Received {signal_name}, requesting graceful shutdown")

        # Request graceful interrupt
        # Note: Can't use async in signal handler, so we use thread-safe Event
        self.request_interrupt(
            mode=InterruptMode.GRACEFUL,
            source=InterruptSource.SIGNAL,
            message=f"Interrupted by signal {signal_name}",
            metadata={"signal": signum, "signal_name": signal_name},
        )

    def request_interrupt(
        self,
        mode: InterruptMode,
        source: InterruptSource,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Request interrupt (thread-safe).

        Can be called from signal handlers, async code, or other threads.

        Args:
            mode: How to handle interrupt (GRACEFUL or IMMEDIATE)
            source: Source of interrupt
            message: Human-readable reason
            metadata: Additional context
        """
        # Don't allow overwriting an existing interrupt
        if self._interrupt_reason is not None:
            logger.debug("Interrupt already requested, ignoring duplicate request")
            return

        self._interrupt_reason = InterruptReason(
            source=source,
            mode=mode,
            message=message,
            metadata=metadata or {},
        )

        # Set interrupt flag (thread-safe)
        # anyio.Event.set() works from any context (sync or async)
        self._interrupted.set()

        logger.warning(
            f"Interrupt requested: {message} "
            f"(mode={mode.value}, source={source.value})"
        )

    def is_interrupted(self) -> bool:
        """
        Check if interrupt has been requested (non-blocking).

        Returns:
            True if interrupt requested
        """
        return self._interrupted.is_set()

    async def wait_for_interrupt(
        self, timeout: float | None = None
    ) -> InterruptReason | None:
        """
        Wait for interrupt signal (blocking).

        Args:
            timeout: Maximum time to wait (None = wait forever)

        Returns:
            InterruptReason if interrupted, None if timeout
        """
        try:
            if timeout:
                with anyio.fail_after(timeout):
                    await self._interrupted.wait()
            else:
                await self._interrupted.wait()

            return self._interrupt_reason

        except TimeoutError:
            return None

    def register_shutdown_callback(
        self, callback: Callable[[], Awaitable[None]]
    ) -> None:
        """
        Register callback to run before shutdown.

        Callbacks are executed in registration order during shutdown.

        Args:
            callback: Async function to call during shutdown
        """
        self._shutdown_callbacks.append(callback)
        logger.debug(f"Registered shutdown callback: {callback.__name__}")

    async def execute_shutdown_callbacks(self) -> None:
        """
        Execute all shutdown callbacks.

        Continues execution even if callbacks fail.
        """
        if not self._shutdown_callbacks:
            return

        logger.info(f"Executing {len(self._shutdown_callbacks)} shutdown callbacks...")

        for i, callback in enumerate(self._shutdown_callbacks):
            try:
                await callback()
                logger.debug(f"Shutdown callback {i+1} completed")
            except Exception as e:
                logger.error(f"Shutdown callback {i+1} failed: {e}", exc_info=True)

        logger.info("All shutdown callbacks executed")

    async def execute_shutdown(
        self, state_manager: Any = None, agent_state: Any = None
    ) -> InterruptStatus:
        """
        Execute graceful shutdown sequence.

        1. Execute shutdown callbacks
        2. Save checkpoint (if state_manager provided)
        3. Return interrupt status

        Args:
            state_manager: Optional StateManager for checkpointing
            agent_state: Optional AgentState to checkpoint

        Returns:
            InterruptStatus with checkpoint information
        """
        if not self._interrupt_reason:
            raise RuntimeError("No interrupt reason set")

        logger.info(f"Starting graceful shutdown: {self._interrupt_reason.message}")

        # Execute shutdown callbacks
        await self.execute_shutdown_callbacks()

        # Save checkpoint if state manager available
        checkpoint_id = None
        if state_manager and agent_state:
            try:
                logger.info("Saving checkpoint before shutdown...")

                # Mark state as interrupted
                agent_state.status = "interrupted"
                agent_state.metadata["interrupt_reason"] = (
                    self._interrupt_reason.to_dict()
                )

                # Save checkpoint
                checkpoint_id = await state_manager.save_checkpoint(
                    agent_state, force=True
                )

                logger.info(f"Checkpoint saved: {checkpoint_id}")

            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}", exc_info=True)

        # Create interrupt status
        status = InterruptStatus(
            interrupted=True,
            reason=self._interrupt_reason,
            checkpoint_id=checkpoint_id,
        )

        logger.info(
            f"Graceful shutdown complete " f"(checkpoint={checkpoint_id or 'none'})"
        )

        return status

    def reset(self) -> None:
        """
        Reset interrupt state.

        Use for testing or when resuming execution.
        """
        self._interrupted = anyio.Event()
        self._interrupt_reason = None
        logger.debug("Interrupt state reset")

    def get_interrupt_reason(self) -> InterruptReason | None:
        """
        Get current interrupt reason.

        Returns:
            InterruptReason if interrupted, None otherwise
        """
        return self._interrupt_reason


# Export all public types
__all__ = [
    "InterruptManager",
]
