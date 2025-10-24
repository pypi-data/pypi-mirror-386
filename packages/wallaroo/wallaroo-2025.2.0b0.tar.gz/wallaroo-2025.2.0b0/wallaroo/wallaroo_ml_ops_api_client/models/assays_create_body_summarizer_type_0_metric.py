from enum import Enum


class AssaysCreateBodySummarizerType0Metric(str, Enum):
    MAXDIFF = "MaxDiff"
    PSI = "PSI"
    SUMDIFF = "SumDiff"

    def __str__(self) -> str:
        return str(self.value)
