from enum import Enum


class MigManExtractStep(Enum):
    INFORCOM = "inforcom"
    SAPECC = "sapecc"
    GENERICODBC = "genericodbc"


class MigManTransformStep(Enum):
    JOINS = "10_joins"
    MAPPINGS = "20_mappings"
    DUPLICATES = "30_duplicates"
    NONEMPTY = "40_nonempty"
