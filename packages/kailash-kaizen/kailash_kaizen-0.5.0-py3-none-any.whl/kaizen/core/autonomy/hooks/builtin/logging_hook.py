"""
Logging hook for structured event logging.

Logs all hook events with configurable log levels and formats (text or JSON).
Supports ELK-compatible JSON logging via structlog.
"""

import logging
from typing import ClassVar

import structlog

from ..protocol import BaseHook
from ..types import HookContext, HookEvent, HookResult

logger = logging.getLogger(__name__)


class LoggingHook(BaseHook):
    """
    Logs all hook events for debugging and audit trails.

    Supports both text and JSON (structlog) formats for ELK compatibility.

    Features:
    - Configurable log level (DEBUG, INFO, WARNING, ERROR)
    - Text format (backward compatible)
    - JSON format (ELK-compatible via structlog)
    - trace_id propagation for distributed tracing
    - Privacy-aware data logging (optional)

    Example:
        >>> # Text format (backward compatible)
        >>> hook = LoggingHook(log_level="INFO", format="text")

        >>> # JSON format for ELK
        >>> hook = LoggingHook(log_level="INFO", format="json")
    """

    # Define which events this hook handles
    events: ClassVar[list[HookEvent]] = list(HookEvent)  # All events

    def __init__(
        self, log_level: str = "INFO", include_data: bool = True, format: str = "text"
    ):
        """
        Initialize logging hook.

        Args:
            log_level: Log level (DEBUG, INFO, WARNING, ERROR)
            include_data: Whether to log event data (disable for sensitive data)
            format: Log format ("text" or "json")
        """
        super().__init__(name="logging_hook")
        self.log_level = log_level
        self.include_data = include_data
        self.format = format

        # Configure logger based on format
        if format == "json":
            # Configure structlog for JSON output
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.add_log_level,
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer(),
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
            self.logger = structlog.get_logger()
        else:
            # Use standard Python logging
            self.logger = logger

    async def handle(self, context: HookContext) -> HookResult:
        """
        Log the hook event.

        Args:
            context: Hook execution context

        Returns:
            HookResult indicating success
        """
        try:
            if self.format == "json":
                # Structured JSON logging
                log_event = {
                    "event_type": context.event_type.value,
                    "agent_id": context.agent_id,
                    "trace_id": context.trace_id,
                    "timestamp": context.timestamp,
                    "level": self.log_level.lower(),
                }

                if self.include_data:
                    log_event["context"] = context.data
                    log_event["metadata"] = context.metadata

                # Log using structlog (outputs JSON)
                log_fn = getattr(self.logger, self.log_level.lower())
                log_fn("hook_event", **log_event)

            else:
                # Text format (backward compatible)
                log_fn = getattr(self.logger, self.log_level.lower())

                if self.include_data:
                    log_fn(
                        f"[{context.event_type.value}] "
                        f"Agent={context.agent_id} "
                        f"TraceID={context.trace_id} "
                        f"Data={context.data}"
                    )
                else:
                    log_fn(
                        f"[{context.event_type.value}] "
                        f"Agent={context.agent_id} "
                        f"TraceID={context.trace_id}"
                    )

            return HookResult(success=True)

        except Exception as e:
            # Even logging can fail!
            return HookResult(success=False, error=str(e))

    async def on_error(self, error: Exception, context: HookContext) -> None:
        """Log errors to stderr"""
        logger.error(f"LoggingHook failed for {context.event_type.value}: {error}")
