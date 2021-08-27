from flai.envs.seatsmart.flight import Flight
from flai.envs.seatsmart.tracking import Episodes
from flai.envs.seatsmart.models.tracking import EpisodeState
from flai.envs.seatsmart.models.flight import GameState, SeatMap, FlightBaseState, Snapshot, Experience
from flai.envs.seatsmart.models.observation import CustomerObservation, AnalystObservation, CFlightContext

import logging
logger = logging.getLogger("SeatSmart")


def customer_loader():
    pass


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
    EPISODES = Episodes
    SNAPSHOT = Snapshot()

    def __init__(self, config: dict = {}, snapshot: bool = False):

        # To create snapshots or not
        self._snapshot = snapshot

        self.CONFIG = GameState(**config)
        logger.debug('Game state config: {}'.format(self.CONFIG.dict()))

        flight_base_state = FlightBaseState(SeatMap=self.CONFIG.SeatMap,
                                            Information=self.CONFIG.Information)

        # Create a flight
        self.flight = Flight(flight_base_state)
        logger.debug('Initializing flight with seat map config : {}'.format(
            flight_base_state.SeatMap.dict()))

        # Create total seat revenue
        self.total_seat_revenue = self.CONFIG.TotalSeatRevenue
        logger.debug('Initializing flight with total seat revenue : {}'.format(
            self.total_seat_revenue))

        # Demand should be created from flight base state availability
        self.CONFIG.EpisodeState.Demand = self.flight.tickets
        self.EPISODES.init(state=self.CONFIG.EpisodeState)
        logger.debug('Initializing episodes with episode state : {}'.format(
            self.EPISODES.state.dict()))

        from flai.envs.seatsmart.customer import SeatCustomer_MNL
        self.seat_customer = SeatCustomer_MNL()

        # Create an event in episode
        self.game_over = not self.EPISODES.event()

        # Spawn a customer
        self.customer_context = self.seat_customer.spawn(
            spawn_time=self.EPISODES.state.CurrentContext.UTCTimeStamp)
        logger.debug('Spawning a new customer with the context : {}'.format(
            self.customer_context))

    def transaction(self, customer_context) -> bool:

        groupsize = customer_context['GroupSize']

        # Check if 1. tickect availability >= group size and flight status is true
        if (self.flight.tickets >= groupsize) and self.EPISODES.state.CurrentContext.Valid:
            logger.debug('Initiating transaction')

            if self._snapshot:
                _flight_state = self.flight.state.copy(deep=True)

            # First Sell a Ticket to the group
            self.flight.sell_ticket(groupsize)
            logger.debug('Customer purchasing flight tickets')

            # send observation to the customer and ask for action
            customer_observation = self.customer_observation

            customer_actions = self.seat_customer.action(customer_observation)
            logger.debug('Customer responded with action : {}'.format(
                customer_actions.dict()))

            # One action is taken update the flight state
            seat_revenue = 0

            for row, col in customer_actions.Selected:
                single_seat_revenue = self.flight.sell_seat(row, col)
                assert (not single_seat_revenue is None), 'Unable to process action'
                seat_revenue += single_seat_revenue
                logger.debug('Seat [{}, {}] sold for {}'.format(
                    row, col, single_seat_revenue))

            # Add Cutomer's action to Episde History
            self.EPISODES.state.CurrentContext.CustomerSelected = customer_actions.Selected

            # Record a snapshot
            if self._snapshot:
                self.SNAPSHOT.Experience.append(Experience(FlightState=_flight_state,
                                                           TotalSeatRevenue=self.total_seat_revenue + seat_revenue,
                                                           CustomerResponse=customer_actions,
                                                           Episode=self.EPISODES.state.copy(deep=True)))
                logger.debug('Taking a snapshot')

            # Create a new event in the game
            game_over = not ((self.EPISODES.event())
                             and (self.flight.tickets > 0))

            return game_over, seat_revenue
        else:
            return True, 0

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
            logger.info('Zone prices: {}'.format(self.flight.zone_price))

            # Do a complete transaction
            self.game_over, seat_revenue = self.transaction(
                self.customer_context)
            logger.info('Seat revenue generated: {}'.format(seat_revenue))

            # Update total seat revenue
            self.total_seat_revenue += seat_revenue
            logger.debug('Flight total seat revenue : {}'.format(
                self.total_seat_revenue))

            # Spawn a customer
            self.customer_context = self.seat_customer.spawn(
                spawn_time=self.EPISODES.state.CurrentContext.UTCTimeStamp)
            logger.debug('Spawning a new customer with the context : {}'.format(
                self.customer_context))

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

        observation = AnalystObservation(Episodes=self.EPISODES.state,
                                         SeatMap=state.SeatMap,
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

        return CustomerObservation(Context=CFlightContext(DepartureDatetimeUTC=self.EPISODES.state.Clock.StopUTC),
                                   Seats=Seats,
                                   WindowCols=state.SeatMap.WindowCols,
                                   AisleCols=state.SeatMap.AisleCols,
                                   ExitRows=state.SeatMap.ExitRows)
