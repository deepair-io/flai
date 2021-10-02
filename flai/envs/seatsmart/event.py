from collections import OrderedDict
from flai.envs.seatsmart.models.event import EventState
from flai.envs.seatsmart.models.customer import SpawnInfo
import math
from flai.utils import np_random
import numpy as np
import scipy.stats as ss
import datetime

import logging
logger = logging.getLogger("SeatSmart")


class NHPP_Thinning:
    '''Thinning algorithm to sample random variates from non homogeneous poisson process.

    URL: https://onlinelibrary.wiley.com/doi/10.1002/9780470400531.eorms0356

    Agrs:
        N (int): Total number of arrivals to simulate
        a (float): beta function first parameter
        b (float): beta function second parameter
        threshold_time (float): time percentile to stop recursion and deliver time
    '''

    def __init__(self, N=100, a=1, b=1, threshold_time=0.95):
        self.N = N
        self.a = a
        self.b = b
        self.t = 0
        self.threshold_time = threshold_time
        self.lambda_u = self.get_max_intensity()

    def get_max_intensity(self, start=0, stop=1, intervals=5000):
        '''Calculates the max intensity from intensity function

        Args:
            start (int:0): start point in linespace
            stop (int:1): stop point in linespace
            intervals (int:5000): breakpoints from start to stop in linespace

        Returns:
            int: maximum value in intensity function
        '''
        return max(self.intensity_function(np.linspace(start, stop, intervals)))

    def intensity_function(self, x):
        '''Rate of arrival function $\lambda(t)$

        Intensity function (aka rate of arrival function)
        We use beta distribution to model this rate of arrivals.
        Look at section 1.2 in the following paper.
        URL: https://pubsonline.informs.org/doi/abs/10.1287/trsc.27.3.239

        Args:
            x (float): time percentile of arrival

        Returns:
            float: intensity value. Calculated as N x beta(x;a,b)
        '''
        return self.N*ss.beta.pdf(x, self.a, self.b, 0, 1)

    def inter_arrival_time(self, p, _lambda):
        '''Inter arrival time based on inverse CDF

        To find out more look at tutorial below.
        URL: https://towardsdatascience.com/the-poisson-process-everything-you-need-to-know-322aa0ab9e9a

        Args:
            p (float): uniform random value from 0 to 1.
            _lambda (float): arrival rate

        Returns:
            float: inter arrival time. Calculate as -log(p)/lambda
        '''
        assert (0 < p < 1), 'Invalid probability value: %s' & p
        assert (_lambda > 0), 'Lambda > 0 but it is %s' % _lambda
        return np.divide(-math.log(p), _lambda)

    def arrival_time(self, current_time):
        '''Next arrival time. Main logic.

        Args:
            current_time (float): Time percentile

        Returns:
            float: next arrival time
        '''
        u1 = np_random.rng.random()

        _time = current_time + self.inter_arrival_time(u1, self.lambda_u)
        lambda_ = self.intensity_function(_time)

        u2 = np_random.rng.random()
        if u2 <= (lambda_/self.lambda_u) or _time > self.threshold_time:
            return _time
        else:
            return self.arrival_time(_time)

    def spawn(self):
        '''Spawn time creator.

        Returns:
            float: spawn time percentile.
        '''
        self.t = self.arrival_time(self.t)
        return self.t


class EventCreator:
    '''
    This is an event creator class. This class can create
    event timeline for you. This is an object dependent
    class i.e. you do need to create instance or 
    objects out of it. 

    Args:
        EventState(EventState) : State holder for Event Creator
    '''

    def __init__(self, EventState):
        self.state = EventState
        self.delta = EventState.Clock.StopUTC - EventState.Clock.StartUTC
        self.future = self.generate(EventState.CustomerTypes)
        self.valid_customer = True
        self.spawned_time = None

    def tick(self):
        '''
        Main logic to create an event.

        Returns:
            tuple: Customer Spawn Info (BaseModel), Game Over (Bool)
        '''

        spawned_time, spawned_customer = datetime.datetime.min, 'None'

        try:
            key = next(iter(self.future))
            spawned_customer = self.future[key]
            self.future.pop(key)
            spawned_time = self.state.Clock.StartUTC + (key*self.delta)

            if spawned_time > self.state.Clock.StopUTC:
                self.valid_customer = False
        except Exception as e:
            logger.error(e)
            self.valid_customer = False

        self.spawned_time = spawned_time
        return SpawnInfo(Time=spawned_time,
                         CustomerTypeName=spawned_customer),  self.valid_customer

    def generate(self, CustomerTypes):
        '''
        '''
        events = {}
        for customer in CustomerTypes:
            _demand = round(self.state.Demand * customer.SpawnProba)
            spawner = NHPP_Thinning(
                N=_demand, a=customer.ArrivalAlpha, b=customer.ArrivalBeta)
            arrival_percentile = [spawner.spawn() for _ in range(_demand)]
            events.update(dict.fromkeys(arrival_percentile, customer.Name))
        return OrderedDict(sorted(events.items()))

    def refresh(self):
        self.future = self.generate(EventState.CustomerTypes)
