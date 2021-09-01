import datetime
from pydantic import BaseModel, validator
from typing import Optional, List

from flai.envs.seatsmart.models.flight import SeatMap, Seat, PriceRule


# class Zone(BaseModel):
#     Name: str
#     PriceRule: PriceRule


# class Seat(BaseModel):
#     Available: bool = True
#     Blocked: bool = False
#     Ghost: bool = False
#     Row: int = 0
#     Col: int = 0
#     Zone: Zone


class SegmentProduct(BaseModel):
    Name: str = "XXX"
    Sold: int = 0
    Available: int = 0
    Revenue: int = 0
    Price: float = 1.0
    MinPrice: float = 0.0
    MaxPrice: float = 2.0


class Segment(BaseModel):
    SegmentIndex: int = 0
    FlightNumber: int = 100
    CarrierCode: str = "XXX"
    DurationInSec: datetime.timedelta = datetime.timedelta(0, 10800, 0)
    DepartureAirport: str = "XXX"
    ArrivalAirport: str = "XXX"
    DepartureDate: datetime.datetime = datetime.datetime(2020, 1, 1)
    ArrivalDate: datetime.datetime = datetime.datetime(2020, 1, 1)
    SeatMap: SeatMap = SeatMap()
    SegmentProducts: List[SegmentProduct] = [SegmentProduct()]


class Fare(BaseModel):
    pass


class Journey(BaseModel):
    OfferJourneyIndex: int = 0
    OriginCityCode: str = "XXX"
    DestinationCityCode: str = "XXX"
    OriginAirportCode: str = "XXX"
    DestinationAirportCode: str = "XXX"
    DepartureDate: datetime.datetime = datetime.datetime(2020, 1, 1)
    ArrivalDate: datetime.datetime = datetime.datetime(2020, 1, 1)
    Selected: bool = True
    Segments: List[Segment] = [Segment()]


class Request(BaseModel):
    RequestJourneyIndex: int = 0
    Journeys: List[Journey] = [Journey()]


class Observation(BaseModel):
    RequestUTCTimeStamp: datetime.datetime = datetime.datetime(2020, 1, 1)
    CurrencyCode: str = "HKD"
    Requests: List[Request] = [Request()]
    Grid: List[List[Seat]]
