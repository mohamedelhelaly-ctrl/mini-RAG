from enum import Enum

class vectorDBEnums(Enum):
    QDRANT = "QDRANT"

class DistanceMethodEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"