from enum import Enum


class NewScriptWithDraftDraftAssetsItemAccessType(str, Enum):
    R = "r"
    RW = "rw"
    W = "w"

    def __str__(self) -> str:
        return str(self.value)
