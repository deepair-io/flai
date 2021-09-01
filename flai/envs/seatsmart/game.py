from flai.envs.seatsmart.flight import Flight
from flai.envs.seatsmart.event import EventCreator
from flai.envs.seatsmart.models.event import EventState
from flai.envs.seatsmart.models.flight import GameState, SeatMap, FlightBaseState
from flai.envs.seatsmart.models import customer, analyst

import logging
logger = logging.getLogger("SeatSmart")


class PricingGame:
    '''
    This class provides a cli for the agent that
    is pricing seats in a flight. To create an
    object from this class, you need to pass GameState
    object that is present in the models module.
    Parameters of the CLI object can be changed. 
    '''

    # base config
    CONFIG: GameState = None

    def __init__(self, config: dict = {}):

        self.CONFIG = GameState(**config)
        logger.debug(':video_game: Game state config: {}'.format(
            self.CONFIG.dict()))

        flight_base_state = FlightBaseState(SeatMap=self.CONFIG.SeatMap,
                                            FlightInfo=self.CONFIG.FlightInfo)

        # Create a flight
        self.flight = Flight(flight_base_state)
        logger.debug(':airplane: Initializing flight with seat map config : {}'.format(
            flight_base_state.SeatMap.dict()))

        # Create total seat revenue
        self.total_seat_revenue = self.CONFIG.RevenueInfo.TotalSeatRevenue
        logger.debug(':money_with_wings: Initializing flight with total seat revenue : {}'.format(
            self.total_seat_revenue))

        from flai.envs.seatsmart.customer import SeatCustomer_MNL
        self.seat_customer = SeatCustomer_MNL()
        publish_hook = self.seat_customer.observe()
        logger.debug(':leftwards_arrow_with_hook: Published customer hook: {}'.format(
            publish_hook.dict()))

        # Demand should be created from flight base state availability
        # TODO: Make the demand as a sample from the distribution (gamma)
        self.event_state = EventState(Clock=self.CONFIG.ClockState,
                                      Demand=self.flight.tickets,
                                      CustomerTypes=publish_hook.CustomerTypes)
        self.event_creator = EventCreator(self.event_state)
        logger.debug(':checkered_flag: Initializing event with event state : {}'.format(
            self.event_state.dict()))

        # Create an event
        spawn_info, is_valid = self.event_creator.tick()
        self.game_over = not is_valid
        logger.debug(
            ':game_die: Created event with state: {}'.format(spawn_info))

        if self.game_over:
            logger.debug('Game over with context : {}'.format({
                "FlightInformation": self.flight(),
                "RequestUTCTimeStamp": spawn_info.Time,
                "DepartureDate": self.CONFIG.ClockState.StopUTC
            }))

        # Spawn a customer
        self.customer_context = self.seat_customer.spawn(spawn_info=spawn_info)
        logger.debug(':cat: Spawning a new customer with the context : {}'.format(
            self.customer_context.dict()))

    def transaction(self, customer_context) -> bool:

        groupsize = customer_context.GroupSize

        # Check if 1. tickect availability >= group size and flight status is true
        if (self.flight.tickets >= groupsize) and self.event_creator.valid_customer:
            logger.debug(':pager: Initiating transaction')

            # First Sell a Ticket to the group
            self.flight.sell_ticket(groupsize)
            logger.debug(':purse: Customer purchasing flight tickets')

            # send observation to the customer and ask for action
            customer_observation = self.customer_observation

            customer_actions = self.seat_customer.action(customer_observation)
            logger.debug(':credit_card: Customer responded with action : {}'.format(
                customer_actions.dict()))

            # One action is taken update the flight state
            seat_revenue = 0

            for row, col in customer_actions.Selected:
                single_seat_revenue = self.flight.sell_seat(row, col)
                assert (not single_seat_revenue is None), 'Unable to process action'
                seat_revenue += single_seat_revenue
                logger.debug('Seat [{}, {}] sold for {}'.format(
                    row, col, single_seat_revenue))

            return seat_revenue
        else:
            return 0

    def act(self, action: dict = {}):
        '''
        Pricing CLI action is to change the Zone
        price of the flight.

        Arg:
            action (dict): 

        Return: 
            (game over, seat revenue)
        '''

        if (not self.game_over):

            # Update zone prices
            self.flight.zone_price = action
            logger.info(':seat: Zone prices: {}'.format(
                self.flight.zone_price))

            # Do a complete transaction
            seat_revenue = self.transaction(
                self.customer_context)
            logger.info(
                ':money_with_wings: Seat revenue generated: {}'.format(seat_revenue))

            # Update total seat revenue
            self.total_seat_revenue += seat_revenue
            logger.debug(':moneybag: Flight total seat revenue : {}'.format(
                self.total_seat_revenue))

            # Create an event
            spawn_info, is_valid = self.event_creator.tick()
            self.game_over = not ((is_valid) and (self.flight.tickets > 0))
            logger.debug(
                ':game_die: Created event with state: {}'.format(spawn_info))

            # Spawn a customer
            self.customer_context = self.seat_customer.spawn(
                spawn_info=spawn_info)
            logger.debug(':panda_face: Spawning a new customer with the context : {}'.format(
                self.customer_context.dict()))

            if self.game_over:
                logger.debug('Game over with context : {}'.format({
                    "FlightInformation": self.flight(),
                    "RequestUTCTimeStamp": spawn_info.Time,
                    "DepartureDate": self.CONFIG.ClockState.StopUTC
                }))

            # return game status
            return self.game_over, seat_revenue

        else:
            return True, 0

    @property
    def analyst_observation(self):

        # Add Seat Grid to the observation
        # state = self.flight.state.copy(deep=True)
        state = self.flight.state
        for row in state.Grid:
            for seat in row:
                seat.ZoneName = self.flight._seat_to_zonename(state, seat)
                seat.Price = self.flight.zone_price[seat.ZoneName]['Price']

        segment = analyst.Segment(FlightNumber=self.CONFIG.FlightInfo.Number,
                                  CarrierCode=self.CONFIG.FlightInfo.CarrierCode,
                                  DurationInSec=self.CONFIG.FlightInfo.DurationInSec,
                                  DepartureAirport=self.CONFIG.FlightInfo.DepartureAirport,
                                  ArrivalAirport=self.CONFIG.FlightInfo.ArrivalAirport,
                                  SeatMap=self.CONFIG.SeatMap,
                                  SegmentProducts=self.flight())

        journey = analyst.Journey(OriginCityCode=self.CONFIG.FlightInfo.DepartureAirport,
                                  DestinationCityCode=self.CONFIG.FlightInfo.ArrivalAirport,
                                  OriginAirportCode=self.CONFIG.FlightInfo.DepartureAirport,
                                  DestinationAirportCode=self.CONFIG.FlightInfo.ArrivalAirport,
                                  DepartureDate=self.CONFIG.ClockState.StopUTC,
                                  ArrivalDate=self.CONFIG.ClockState.StopUTC+self.CONFIG.FlightInfo.DurationInSec,
                                  Segments=[segment]
                                  )

        req = analyst.Request(Journeys=[journey])

        observation = analyst.Observation(RequestUTCTimeStamp=self.event_creator.spawned_time,
                                          CurrencyCode="HKD",
                                          Requests=[req],
                                          Grid=state.Grid)
        return observation

    @property
    def customer_observation(self):

        Seats = []

        # state = self.flight.state.copy(deep=True)
        state = self.flight.state
        for row in state.Grid:
            _s = []
            for seat in row:
                if seat.Available:
                    _s.append(self.flight.zone_price[self.flight._seat_to_zonename(
                        state, seat)]['Price'])
                else:
                    _s.append(-1*seat.Ghost)
            Seats.append(_s)

        return customer.Observation(Context=customer.FlightContext(DepartureDatetimeUTC=self.CONFIG.ClockState.StopUTC),
                                    Seats=Seats,
                                    WindowCols=state.SeatMap.WindowCols,
                                    AisleCols=state.SeatMap.AisleCols,
                                    ExitRows=state.SeatMap.ExitRows)
