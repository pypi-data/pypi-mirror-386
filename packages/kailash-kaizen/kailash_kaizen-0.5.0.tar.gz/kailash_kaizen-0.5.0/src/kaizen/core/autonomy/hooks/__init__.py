"""Hook system for autonomous agents."""

from kaizen.core.autonomy.hooks.manager import HookManager
from kaizen.core.autonomy.hooks.protocol import BaseHook, HookHandler
from kaizen.core.autonomy.hooks.types import (
    HookContext,
    HookEvent,
    HookPriority,
    HookResult,
)

__all__ = [
    "HookEvent",
    "HookContext",
    "HookResult",
    "HookPriority",
    "BaseHook",
    "HookHandler",
    "HookManager",
]
