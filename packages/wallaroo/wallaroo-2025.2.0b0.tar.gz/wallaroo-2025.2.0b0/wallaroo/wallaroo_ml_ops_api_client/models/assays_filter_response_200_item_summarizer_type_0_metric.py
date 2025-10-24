from enum import Enum


class AssaysFilterResponse200ItemSummarizerType0Metric(str, Enum):
    MAXDIFF = "MaxDiff"
    PSI = "PSI"
    SUMDIFF = "SumDiff"

    def __str__(self) -> str:
        return str(self.value)
