import datetime
from pydantic import BaseModel, validator, root_validator
from typing import Optional, List

from flai.envs.seatsmart.models.event import ClockState


class PriceRule(BaseModel):
    Price: float = 10
    MinPrice: float = 0
    MaxPrice: float = 30

    '''
    validate the following
    1. min is less than max
    2. delta is less than max-min
    3. price in valid
    '''
    @validator('*', pre=True)
    def non_negativity(cls, v):
        if v < 0:
            raise ValueError('Non Negative value')
        return v

    @root_validator
    def max_price(cls, values):
        m, p = values.get('MaxPrice'), values.get('Price')
        if m < p:
            raise ValueError(
                'Price greater than max value are not allowed. {} < {}'.format(m, p))
        return values

    @root_validator
    def min_price(cls, values):
        m, p = values.get('MinPrice'), values.get('Price')
        if m > p:
            raise ValueError(
                'Price less than min value are not allowed. {} > {}'.format(m, p))
        return values

    class Config:
        validate_assignment = True


class Zone(BaseModel):
    Name: str
    IncludeRows: List[int] = []
    ExcludeCols: List[int] = []
    ExcludeSeats: List[tuple] = []
    PriceRule: PriceRule = PriceRule()


class SeatGroup(BaseModel):
    Rows: List[int] = []
    Cols: List[int] = []
    Seats: List[tuple] = []


class SeatMap(BaseModel):
    MaxRows: int = 30
    MaxCols: int = 6
    Zones: List[Zone] = [
        Zone(Name="StandardSeat")
    ]
    Blocked: SeatGroup = SeatGroup()
    Ghost: SeatGroup = SeatGroup()
    WindowCols: List[int] = [0, 5]
    AisleCols: List[int] = [2, 3]
    ExitRows: List[int] = [0]

    '''
    validate the following
    1. Valid seat groups for
    '''


class Seat(BaseModel):
    Available: bool = True
    Blocked: bool = False
    Ghost: bool = False
    Row: int = 0
    Col: int = 0
    Price: Optional[float]
    ZoneName: Optional[str]


class FlightInfo(BaseModel):
    Number: int = 100
    CarrierCode: str = "UO"
    DurationInSec: datetime.timedelta = datetime.timedelta(0, 10800, 0)
    ArrivalAirport: str = "HKG"
    DepartureAirport: str = "KOJ"


class RevenueInfo(BaseModel):
    TotalSeatRevenue: float = 0
    CurrencyCode: str = "HKD"


class FlightBaseState(BaseModel):
    SeatMap: SeatMap
    FlightInfo: FlightInfo
    Grid: List[List[Seat]] = None

    @ root_validator
    def grid_generator(cls, values):
        if values['Grid'] is None:
            seatmap = values['SeatMap']
            rl = []
            for _row in range(seatmap.MaxRows):
                cl = []
                for _col in range(seatmap.MaxCols):
                    # create a seat
                    seat = Seat(Row=_row, Col=_col)

                    # Ghost
                    if (_row in seatmap.Ghost.Rows) or \
                        (_col in seatmap.Ghost.Cols) or \
                            ((_row, _col) in seatmap.Ghost.Seats):
                        seat.Ghost = True
                        seat.Available = False

                    # Blocked
                    if (_row in seatmap.Blocked.Rows) or \
                        (_col in seatmap.Blocked.Cols) or \
                            ((_row, _col) in seatmap.Blocked.Seats):
                        seat.Blocked = True
                        seat.Available = False
                    cl.append(seat)
                rl.append(cl)
            values['Grid'] = rl
        return values


class GameState(BaseModel):
    SeatMap: SeatMap = SeatMap()
    ClockState: ClockState = ClockState()
    RevenueInfo: RevenueInfo = RevenueInfo()
    FlightInfo: FlightInfo = FlightInfo()
    Plugins: Optional[list]
