from enum import Enum


class GetScriptByPathWithDraftResponse200DraftAssetsItemAltAccessType(str, Enum):
    R = "r"
    RW = "rw"
    W = "w"

    def __str__(self) -> str:
        return str(self.value)
