from enum import Enum


class GetAppByPathResponse200ExecutionMode(str, Enum):
    ANONYMOUS = "anonymous"
    PUBLISHER = "publisher"
    VIEWER = "viewer"

    def __str__(self) -> str:
        return str(self.value)
