from enum import Enum


class OsidbApiV2FlawsListReferencesType(str, Enum):
    ARTICLE = "ARTICLE"
    EXTERNAL = "EXTERNAL"
    SOURCE = "SOURCE"
    UPSTREAM = "UPSTREAM"

    def __str__(self) -> str:
        return str(self.value)
