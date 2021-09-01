from pydantic import BaseModel, validator
from typing import Optional, List, Tuple
import datetime


class CustomerType(BaseModel):
    Name: str = "Default"
    SpawnProba: float = 1
    ArrivalAlpha: float = 1
    ArrivalBeta: float = 1
    Parameters: Optional[dict]

    @validator('SpawnProba')
    def probability_range(cls, v):
        if (v < 0) or (v > 1):
            raise ValueError('Invalid probability value : {}'.format(v))
        return v

    class Config:
        validate_assignment = True


class Configuration(BaseModel):
    CustomerTypes: List[CustomerType] = [CustomerType()]
    MetaInfo: Optional[dict]


class Publish(BaseModel):
    CustomerTypes: List[CustomerType] = [CustomerType()]

    @validator('CustomerTypes')
    def probability_sum(cls, v):
        if not v is None:
            _sum = sum([x.SpawnProba for x in v])
            assert _sum == 1., "Sum of all probabilites are not 1 but {}".format(
                _sum)
        return v

    class Config:
        validate_assignment = True


class Configuration(Publish):
    MetaInfo: Optional[dict]


class SpawnInfo(BaseModel):
    Time: datetime.datetime
    CustomerTypeName: str
    MetaInfo: Optional[dict]


class SpawnContext(BaseModel):
    GroupSize: int = 1


class FlightContext(BaseModel):
    DepartureDatetimeUTC: datetime.datetime


class Observation(BaseModel):
    Context: FlightContext
    Seats: List[List[float]]
    WindowCols: List[int]
    AisleCols: List[int]
    ExitRows: List[int]


class Action(BaseModel):
    Selected: List[tuple] = []
    MetaInfo: Optional[list]

    @validator('Selected')
    def numpy_dtype(cls, v):
        if len(v):
            v = [(int(row), int(col)) for row, col in v]
        return v

    class Config:
        validate_assignment = True
