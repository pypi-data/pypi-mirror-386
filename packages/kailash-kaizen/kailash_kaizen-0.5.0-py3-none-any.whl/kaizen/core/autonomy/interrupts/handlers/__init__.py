"""
Interrupt handlers for automatic interrupt triggering.

Provides specialized handlers for timeout and budget-based interrupts.
"""

from .budget import BudgetInterruptHandler
from .timeout import TimeoutInterruptHandler

__all__ = [
    "TimeoutInterruptHandler",
    "BudgetInterruptHandler",
]
