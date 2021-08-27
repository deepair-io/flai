import datetime
from pydantic import BaseModel, validator
from typing import Optional, List

from flai.envs.seatsmart.models.tracking import EpisodeState
from flai.envs.seatsmart.models.flight import SeatMap, Seat, PriceRule


class CFlightContext(BaseModel):
    DepartureDatetimeUTC: datetime.datetime


class CustomerObservation(BaseModel):
    Context: CFlightContext
    Seats: List[List[float]]
    WindowCols: List[int]
    AisleCols: List[int]
    ExitRows: List[int]

# Analyst observation


class Zone(BaseModel):
    Name: str
    PriceRule: PriceRule


class ASeat(BaseModel):
    Available: bool = True
    Blocked: bool = False
    Ghost: bool = False
    Row: int = 0
    Col: int = 0
    Zone: Zone


class AnalystObservation(BaseModel):
    Episodes: EpisodeState
    SeatMap: SeatMap
    Grid: List[List[Seat]]
