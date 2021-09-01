import datetime
from pydantic import BaseModel, validator
from typing import Optional, List

from flai.envs.seatsmart.models.customer import CustomerType


class ClockState(BaseModel):
    StartUTC: datetime.datetime = datetime.datetime(2020, 1, 1)
    StopUTC: datetime.datetime = datetime.datetime(2021, 1, 1)


class ArrivalContext(BaseModel):
    UTCTimeStamp: datetime.datetime
    Valid: bool = True
    CustomerContext: Optional[List[tuple]]


class EventState(BaseModel):
    Clock: ClockState = ClockState()
    Demand: int = 180
    CustomerTypes: List[CustomerType]
