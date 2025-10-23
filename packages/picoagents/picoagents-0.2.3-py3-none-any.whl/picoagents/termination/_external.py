"""
External termination condition.
"""

from typing import Callable, Optional, Sequence

from ..messages import Message
from ..types import StopMessage
from ._base import BaseTermination


class ExternalTermination(BaseTermination):
    """Terminates based on external signal."""

    def __init__(self, check_callback: Callable[[], bool]):
        super().__init__()
        self.check_callback = check_callback

    def check(self, new_messages: Sequence[Message]) -> Optional[StopMessage]:
        """Check external termination signal."""
        try:
            if self.check_callback():
                return self._set_termination(
                    "External termination signal received",
                    {"source": "external_callback"},
                )
        except Exception:
            # Don't let callback errors stop orchestration
            pass

        return None
