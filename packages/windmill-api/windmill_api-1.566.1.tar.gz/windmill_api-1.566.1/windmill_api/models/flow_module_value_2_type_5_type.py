from enum import Enum


class FlowModuleValue2Type5Type(str, Enum):
    BRANCHONE = "branchone"

    def __str__(self) -> str:
        return str(self.value)
