from enum import Enum


class MigManTransformStep(Enum):
    JOINS = "10_joins"
    DUPLICATES = "20_duplicates"
    MAPPINGS = "30_mappings"
    NONEMPTY = "40_nonempty"
