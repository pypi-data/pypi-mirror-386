from enum import Enum


class OsidbApiV2FlawsListRequiresCveDescription(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUESTED = "REQUESTED"
    VALUE_0 = ""

    def __str__(self) -> str:
        return str(self.value)
