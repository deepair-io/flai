from pydantic import BaseModel, validator
from typing import Optional, List, Tuple

import numpy as np


class CustomerAction(BaseModel):
    Selected: List[tuple] = []
    MetaInfo: Optional[list]

    @validator('Selected')
    def numpy_dtype(cls, v):
        if len(v):
            v = [(int(row), int(col)) for row, col in v]
        return v

    class Config:
        validate_assignment = True
