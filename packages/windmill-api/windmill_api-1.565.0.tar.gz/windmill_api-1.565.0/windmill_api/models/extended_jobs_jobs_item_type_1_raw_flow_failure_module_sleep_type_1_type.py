from enum import Enum


class ExtendedJobsJobsItemType1RawFlowFailureModuleSleepType1Type(str, Enum):
    JAVASCRIPT = "javascript"

    def __str__(self) -> str:
        return str(self.value)
