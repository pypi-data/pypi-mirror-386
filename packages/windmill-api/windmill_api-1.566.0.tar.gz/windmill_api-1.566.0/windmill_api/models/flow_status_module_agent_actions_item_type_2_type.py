from enum import Enum


class FlowStatusModuleAgentActionsItemType2Type(str, Enum):
    MESSAGE = "message"

    def __str__(self) -> str:
        return str(self.value)
