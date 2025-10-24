import enum
from dataclasses import dataclass
from typing import Any, Optional

from dojo_sdk_core.ws_types import HistoryStep


class ResponseStatus(enum.Enum):
    # INITIALIZING = "INITIALIZING"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class NoRunnersAvailableError(Exception):
    """Error when no runners are available"""

    pass


@dataclass
class TaskResponse:
    """Response from task status endpoint"""

    status: ResponseStatus
    screenshot: Optional[str]
    history: Optional[list[HistoryStep]]
    step: Optional[int]
    state: Optional[dict[str, Any]] = None
