from enum import Enum


class MigManExtractStep(Enum):
    NONE = "none"
    GENERICODBC = "genericodbc"
    INFORCOM = "inforcom"
    SAPECC = "sapecc"
    PROALPHA = "proalpha"


class MigManTransformStep(Enum):
    JOINS = "10_joins"
    MAPPINGS = "20_mappings"
    DUPLICATES = "30_duplicates"
    NONEMPTY = "40_nonempty"
