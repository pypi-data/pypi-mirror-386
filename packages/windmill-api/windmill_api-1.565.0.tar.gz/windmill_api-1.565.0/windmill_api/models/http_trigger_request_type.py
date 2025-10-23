from enum import Enum


class HttpTriggerRequestType(str, Enum):
    ASYNC = "async"
    SYNC = "sync"
    SYNC_SSE = "sync_sse"

    def __str__(self) -> str:
        return str(self.value)
