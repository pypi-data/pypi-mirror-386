from enum import Enum


class FlowStatusFailureModuleAgentActionsItemType2Type(str, Enum):
    MESSAGE = "message"

    def __str__(self) -> str:
        return str(self.value)
