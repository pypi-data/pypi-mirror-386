from enum import Enum


class UpdateHttpTriggerJsonBodyRequestType(str, Enum):
    ASYNC = "async"
    SYNC = "sync"
    SYNC_SSE = "sync_sse"

    def __str__(self) -> str:
        return str(self.value)
