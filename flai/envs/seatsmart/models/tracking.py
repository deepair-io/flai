import datetime
from pydantic import BaseModel, validator
from typing import Optional, List
from flai.envs.seatsmart.models.action import CustomerAction


class ClockState(BaseModel):
    StartUTC: datetime.datetime = datetime.datetime(2020, 1, 1)
    StopUTC: datetime.datetime = datetime.datetime(2021, 1, 1)


class ArrivalContext(BaseModel):
    Index: int = 0
    UTCTimeStamp: datetime.datetime
    Valid: bool = True
    CustomerSelected: Optional[List[tuple]]


class EpisodeState(BaseModel):
    Clock: ClockState = ClockState()
    Demand: int = 180
    CurrentContext: ArrivalContext = None
    HistoryEvents: List[ArrivalContext] = []

    '''
    validate
    1. CurrentContext (if not None) then
        valid must be correct
    '''
