from dataclasses import dataclass
from typing import Tuple

@dataclass
class MindiResult:
    class_idx: int
    indices: Tuple[int, int]
    ndi_criteria: float
    class_criteria: float