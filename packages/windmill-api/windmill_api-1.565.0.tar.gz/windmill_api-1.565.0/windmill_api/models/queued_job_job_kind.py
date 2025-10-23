from enum import Enum


class QueuedJobJobKind(str, Enum):
    AIAGENT = "aiagent"
    APPDEPENDENCIES = "appdependencies"
    APPSCRIPT = "appscript"
    DEPENDENCIES = "dependencies"
    DEPLOYMENTCALLBACK = "deploymentcallback"
    FLOW = "flow"
    FLOWDEPENDENCIES = "flowdependencies"
    FLOWNODE = "flownode"
    FLOWPREVIEW = "flowpreview"
    FLOWSCRIPT = "flowscript"
    IDENTITY = "identity"
    PREVIEW = "preview"
    SCRIPT = "script"
    SCRIPT_HUB = "script_hub"
    SINGLESTEPFLOW = "singlestepflow"

    def __str__(self) -> str:
        return str(self.value)
