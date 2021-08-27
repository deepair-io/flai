import datetime
from flai.envs.seatsmart.models.tracking import EpisodeState, ArrivalContext
import math
from flai.utils import np_random


def each_day(state):
    '''
    Given a Episode state, this function creates a
    valid arrival context and return state

    Args:
        state

    Returns: 
        arrival date (datetime.datetime)
    '''
    return state.CurrentContext.UTCTimeStamp + datetime.timedelta(days=1)


def poission(state):
    '''
    Resource : https://towardsdatascience.com/the-poisson-process-everything-you-need-to-know-322aa0ab9e9a

    Args:
        state

    Returns:
        arrival date (datetime.datetime)
    '''

    _num_arrivals = state.Demand
    _lambda = _num_arrivals / (state.Clock.StopUTC - state.Clock.StartUTC).days
    p = np_random.rng.random()
    _inter_arrival_time = -math.log(1.0 - p)/_lambda

    return state.CurrentContext.UTCTimeStamp + datetime.timedelta(days=_inter_arrival_time)


class Episodes:
    '''
    This is an event creator class. This class can create
    event timeline for you. This is an object independent
    class i.e. you don't need to create instance or 
    objects out of it. All the methods are static methods.

    Episodes holds two following variables

        STATE (EpisodeState):  State of the episode
        CREATE_CONTEXT : function to create next arrival
                        context. For now, context just
                        contains arrival datetime
    '''

    state = EpisodeState()
    create_context = None
    History = False

    @staticmethod
    def _create_context(state):
        if state.CurrentContext:
            state.CurrentContext.Index += 1
            # call the create context
            state.CurrentContext.UTCTimeStamp = Episodes.create_context(state)
        else:
            state.CurrentContext = ArrivalContext(
                UTCTimeStamp=state.Clock.StartUTC)

        if (state.Clock.StopUTC < state.CurrentContext.UTCTimeStamp) or (state.Demand <= state.CurrentContext.Index):
            state.CurrentContext.Valid = False

        return state

    @staticmethod
    def event():
        assert not Episodes.create_context is None, 'need to assign context creator'

        current_state = Episodes.state  # .copy(deep=True)

        new_state = Episodes._create_context(Episodes.state.copy(deep=True))
        new_state.CurrentContext.CustomerSelected = None
        if current_state.CurrentContext and Episodes.History:
            new_state.HistoryEvents.append(
                current_state.CurrentContext.copy(deep=True))

        Episodes.state = new_state

        return Episodes.state.CurrentContext.Valid

    @staticmethod
    def event_gen():
        yield Episodes.event()
        while Episodes.state.CurrentContext.Valid:
            yield Episodes.event()

    @staticmethod
    def init(state=EpisodeState(), create_context=poission):
        Episodes.state = state
        Episodes.create_context = create_context
