from enum import Enum


class GenerateOpenapiSpecOpenapiSpecFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"

    def __str__(self) -> str:
        return str(self.value)
