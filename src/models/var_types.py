from enum import StrEnum, auto


class VarTypes(StrEnum):
    EXPOSURE = auto()
    OUTCOME = auto()
    ADJUSTED = auto()
    UNOBSERVED = auto()
