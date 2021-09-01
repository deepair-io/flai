import datetime
from flai.envs.seatsmart.models import customer

from flai.utils import np_random

from abc import ABC, abstractmethod

import numpy as np
from scipy.ndimage.morphology import binary_erosion, binary_opening
from scipy.spatial.distance import cdist


class BaseCustomer(ABC):
    """This is the base class for the customer. This
    class can be integrated with the Game. The API
    calls are:

    - spaw
    - action
    - observe

    Note : customer should be initialized with a config
    and return a publish data object (more info below)
    in order for game to plugin.

    Some helper attributes (pydantic models):

    - self.config : data class to create an instance
    of the customer class. This is used as argument in
    the customer class constructor aka "__init__"

    - self.publish : data class that returns published
    customer class. This is used as return object
    in the customer class constructor aka "__init__"

    - self.observation_space : data class to hold the
    data that customer can observe. This data is used
    as argument in action function.

    - self.action_space : data class to hold the action
    performed by the spawned customer. Used as a return
    for action function

    - self.spawn_info : data class for spawing getting
    the spawning information in spawn function.

    -self.spawn_context : data class to hold the spawn
    context information. This is used as return type in
    both spawn function as well as observation 

    """

    observation_space = customer.Observation
    action_space = customer.Action
    config = customer.Configuration
    publish = customer.Publish
    spawn_info = customer.SpawnInfo
    spawn_context = customer.SpawnContext

    @abstractmethod
    def spawn(self,
              spawn_info: customer.SpawnInfo,
              seed: int = None) -> customer.SpawnContext:
        """This function should initialize a customer
        by initializing its attributes such that it is
        ready for action API call.
        """

    @abstractmethod
    def action(self, observation: customer.Observation) -> customer.Action:
        """Function which returns action based on
        provided observation.

        Args:
            observations (self.observation_space) : The
                seat map and price observation.

        Returns:
            Action Space object (self.action_space)
        """

    @abstractmethod
    def observe(self) -> customer.SpawnContext:
        """observation function which return the spawn context
        for the current spawned customer.

        Returns:
            self.spawn_context object ()
        """


class SeatCustomer_MNL(BaseCustomer):
    """Customer Choice Model with seat preference
    """

    def __init__(self,
                 config=customer.Configuration(
                     CustomerTypes=[
                         customer.CustomerType(
                             Name="Regular", SpawnProba=0.8, ArrivalAlpha=1.5, ArrivalBeta=2.5,
                             Parameters={
                                 "beta_group_seat": [0, 0.3, 0.2, 0.1],
                                 "beta_price_sensitivity": -0.01,
                                 "beta_nobuy_sensitivity": 0.03,
                                 "beta_forward": 1.5,
                                 "beta_window": 0.75,
                                 "beta_aisle": 0.5,
                                 "beta_extra_legroom": 0.75,
                                 "beta_isolation": 0.75,
                                 "beta_constant": 1.4,
                                 "groupsize_probability": [0.5, 0.5],
                             }
                         ),
                         customer.CustomerType(
                             Name="Business", SpawnProba=0.2, ArrivalAlpha=8, ArrivalBeta=1.2,
                             Parameters={
                                 "beta_group_seat": [0, 0.3, 0.2, 0.1],
                                 "beta_price_sensitivity": -0.01,
                                 "beta_nobuy_sensitivity": 0.03,
                                 "beta_forward": 1.5,
                                 "beta_window": 0.75,
                                 "beta_aisle": 0.5,
                                 "beta_extra_legroom": 0.75,
                                 "beta_isolation": 0.75,
                                 "beta_constant": 1.4,
                                 "groupsize_probability": [0.5, 0.5],
                             }
                         )
                     ]
                 )):

        # build customer_type
        self._type_list = config.CustomerTypes
        self._name_to_index = {}
        for i, c in enumerate(config.CustomerTypes):
            self._name_to_index[c.Name] = i

        # Static Parameter
        self.choice_N = 3

        self._spawn_context = None
        self._publish = self.publish(CustomerTypes=config.CustomerTypes)

    def spawn(self, spawn_info, seed=None):
        self.customer = self._type_list[self._name_to_index[spawn_info.CustomerTypeName]]
        # self.groupsize = np_random.rng.choice(
        #     [1, 2], p=self.customer.Parameters['groupsize_probability'])
        self.groupsize = 1
        self._spawn_context = self.spawn_context(GroupSize=self.groupsize)
        return self._spawn_context

    def _dist_from_edge(self, img):
        """Calculate the distance to nearest occupied seat."""
        interior = binary_erosion(img, border_value=1)  # Interior mask
        C = img - interior              # Contour mask
        # Setup o/p and assign cityblock distances
        out = C.astype(int)

        try:
            out[interior] = cdist(np.argwhere(C), np.argwhere(
                interior), 'cityblock').min(0) + 1
            return out / np.max(out)
        except:
            return out

    def _pick_preferred_seat(self, avail, preference, no_buy):
        avail_prob = np.ma.MaskedArray(preference, avail == 0).filled(0)
        avail_prob = avail_prob.flatten()
        avail_prob = np.append(avail_prob, no_buy)
        top_N = np.argpartition(avail_prob, -self.choice_N)[-self.choice_N:]
        top_N_prob = avail_prob[top_N]
        top_N_prob /= np.sum(top_N_prob)
        seat = top_N[np_random.rng.choice(top_N_prob.size, p=top_N_prob)]
        if seat == len(avail_prob) - 1:
            return None
        else:
            row = seat // 6
            col = seat % 6
            return (row, col)

    def _scan_groupseats(self, img, size=1):
        """This function scans the seat map and finds the seats that have
        neighboring seats empty. The scan is performed based on the size
        of the group that we are trying to accomodate

        Arguments:
            img {np.array} -- the binary matrix coded. for example 0 could
            represents seats that are unavailable and 1 could represents
            seats that are available

        Keyword Arguments:
            size {int} -- the size of the group that we are trying to
            accommodate (default: {1})

        Examples:
            if img = array([[0, 0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 1, 1, 0, 0],
                            [0, 0, 1, 1, 1, 0, 0],
                            [0, 0, 1, 0, 1, 0, 0],
                            [0, 1, 1, 0, 1, 0, 0],
                            [0, 0, 1, 0, 1, 0, 0],
                            [0, 0, 0, 0, 0, 0, 1]])
            and size = 2
            then the result will be
                        array([[0, 0, 0, 0, 0, 0, 0],
                               [0, 0, 1, 1, 1, 0, 0],
                               [0, 0, 1, 1, 1, 0, 0],
                               [0, 0, 0, 0, 0, 0, 0],
                               [0, 1, 1, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 0]])
        """
        structure = np.ones((1, size))
        return binary_opening(img, structure=structure).astype(img.dtype)

    def action(self, observations):

        seat_prices_matrix = np.array(observations.Seats)
        seat_availability_matrix = np.zeros_like(seat_prices_matrix)
        seat_availability_matrix[seat_prices_matrix > 0] = 1

        rows, cols = seat_availability_matrix.shape

        # Intialize with zeros
        preference = np.zeros(shape=(rows, cols))

        # Add a constant utility value
        preference += self.customer.Parameters['beta_constant']

        # Set customers opinion of the seat prices based on customer
        # characteristics. People prefer seats next to empty seats
        preference += self.customer.Parameters['beta_isolation'] * \
            self._dist_from_edge(seat_availability_matrix)

        # Preference for window seats
        preference[:, observations.WindowCols] += self.customer.Parameters['beta_window']

        # Preference for aisle seats
        preference[:, observations.AisleCols
                   ] += self.customer.Parameters['beta_aisle']

        # Preference for exit row (or extra legroom) seats
        preference[observations.ExitRows
                   ] += self.customer.Parameters['beta_extra_legroom']

        # Preference for forwarward seats
        preference += np.tile(np.linspace(1, 0, rows),
                              (cols, 1)).T * self.customer.Parameters['beta_forward']

        for size, beta in enumerate(self.customer.Parameters['beta_group_seat']):
            if size > 0:
                preference += beta * self._scan_groupseats(
                    seat_availability_matrix, size+1)

        temp_ma = np.ma.MaskedArray(
            preference, seat_availability_matrix == 0).filled(0)

        # Utility of Worst Seat on plane, will be used for no-buy option
        if bool(temp_ma[np.nonzero(temp_ma)].shape[0]):
            worst_choice = np.min(temp_ma[np.nonzero(temp_ma)])
            worst_choice_price = np.min(seat_prices_matrix
                                        [np.nonzero(seat_prices_matrix)])
        else:
            worst_choice = 0
            worst_choice_price = 0

        worst_choice += worst_choice_price * \
            self.customer.Parameters['beta_nobuy_sensitivity']

        # Preference for less expensive seats
        preference += np.clip(seat_prices_matrix
                              - worst_choice_price,
                              a_min=0, a_max=None) * self.customer.Parameters['beta_price_sensitivity']

        # Exponential of all values
        preference = np.exp(preference)
        # Add option of not selecting any seat
        nobuy_preference = np.exp(worst_choice)

        # Only offer seats that are available
        preference = np.ma.MaskedArray(
            preference, seat_availability_matrix == 0)

        # Get the optimum seat for customer
        taken_seats = preference.mask
        seat_probs = preference.filled(0)**(1)

        # Remove chances of selecting a taken seat and flatten
        seat_probs[taken_seats] = 0

        action = self.action_space()
        action.MetaInfo = [(np.ma.MaskedArray(
            preference-nobuy_preference, seat_availability_matrix == 0).filled(0)).tolist()]

        if self.groupsize == 1:
            avail = seat_availability_matrix
            select = self._pick_preferred_seat(avail, preference,
                                               nobuy_preference)
            if not select is None:
                action.Selected = [select]

        else:  # self.groupsize == 2
            avail = self._scan_groupseats(
                seat_availability_matrix, 2)
            if np.sum(avail) > 0:
                # There is at least one pair of seats next to each other.
                select = self._pick_preferred_seat(avail, preference,
                                                   nobuy_preference)
                if select is None:
                    # ASSUMPTION: If the first customer doesnt select a seat,
                    # the second customer also doesnt buy.
                    select_n = None
                else:
                    # If the first customer picks a seat, the second customer
                    # will pick a neighboring seat on the same row.
                    row = select[0]
                    col = select[1]
                    row_n = row     # Same row
                    if col == 0:    # Window seat
                        col_n = 1   # Middle seat
                    elif col == 5:  # Window seat
                        col_n = 4   # Middle seat
                    else:
                        if avail[row, col-1] == 1:  # Is seat to left avail?
                            col_n = col-1
                        else:  # Is seat to right avail?
                            col_n = col+1
                    select_n = (row_n, col_n)
            else:
                # There are no pairs available, so customers split
                avail = seat_availability_matrix
                select = self._pick_preferred_seat(avail, preference,
                                                   nobuy_preference)
                if select is not None:
                    avail[select[0], select[1]] = 0
                    select_n = self._pick_preferred_seat(avail, preference,
                                                         nobuy_preference)

                    action.Selected = [select, select_n]

        return action

    def observe(self):
        return self._publish
