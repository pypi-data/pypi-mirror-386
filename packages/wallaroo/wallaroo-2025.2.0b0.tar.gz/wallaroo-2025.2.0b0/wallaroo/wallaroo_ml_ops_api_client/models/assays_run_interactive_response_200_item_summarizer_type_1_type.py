from enum import Enum


class AssaysRunInteractiveResponse200ItemSummarizerType1Type(str, Enum):
    MULTIVARIATECONTINUOUS = "MultivariateContinuous"

    def __str__(self) -> str:
        return str(self.value)
