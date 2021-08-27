import datetime
from flai.envs.seatsmart.models.observation import CustomerObservation
from flai.envs.seatsmart.models.action import CustomerAction

from flai.utils import np_random

from abc import ABC, abstractmethod

import random
import numpy as np
from scipy.ndimage.morphology import binary_erosion, binary_opening
from scipy.spatial.distance import cdist


class BaseCustomer(ABC):
    """This is the base class for the customer. This
    class can be integrated with the Game. The API
    calls are

    - spaw
    - action
    - observe
    """

    observation_space = CustomerObservation
    action_space = CustomerAction

    @abstractmethod
    def spawn(self,
              spawn_time: datetime.datetime = None,
              seed: int = None) -> dict:
        """This function should initialize a customer
        by initializing its attributes such that it is
        ready for action API call.
        """

    @abstractmethod
    def action(self, observation):
        """Function which returns action based on
        provided observation.

        Args:
            observations (self.observation_space) : The
                seat map and price observation.

        Returns:
            Action Space object (self.action_space)
        """

    @abstractmethod
    def observe(self, observer):
        """observation function which can return the observation
        space object for a specified observer.

        Args:
            observer (string) : type of observer

        Returns:
            observation space object ()
        """


class DummyCustomer:

    def __init__(self):
        pass

    def spawn(self, seed=None, spawn_time=None):
        return {'GroupSize': 1}

    def action(self, observation):
        action = None
        import pdb
        pdb.set_trace()

        return action


class SeatCustomer_MNL(BaseCustomer):
    """Customer Choice Model with seat preference
    """

    _default_config_ = {
        "beta_group_seat": [
            0,
            0.3,
            0.2,
            0.1
        ],
        "beta_price_sensitivity": -0.01,
        "beta_nobuy_sensitivity": 0.03,
        "beta_forward": 1.5,
        "beta_window": 0.75,
        "beta_aisle": 0.5,
        "beta_extra_legroom": 0.75,
        "beta_isolation": 0.75,
        "beta_constant": 1.4,
        "groupsize_probability": [
            0.5,
            0.5
        ],
        "spawn_probability": -1
    }

    def __init__(self, config=None):

        if config is None:
            config = {"average_customer": self._default_config_.copy()}

        # build customer_type
        self.customer_type_list, self.customer_type_proba_list = self._build_customer_type(
            config)

        # Static Parameter
        self.choice_N = 3

        # Observation Space
        # self.observation_space = ObservationSpace()

        # # Initialize the customer
        # self.spawn()

    def _build_customer_type(self, config):
        """Builds the configs for the customer_type and
        assigns the spawn_probability

        Args:
            config (dict) : same config as init

        Returns:
            customer type list of dict (list), spawn probabilities (list)
        """

        types = []
        probs = []
        _default_p_flag = True  # To track default spawn_probability values

        # build customer_type from config
        for key in config.keys():
            _customer_type = self._default_config_.copy()
            _customer_type.update(config[key])
            _customer_type['name'] = key

            # make flag false if we see non negative probabily
            if (float(_customer_type['spawn_probability']) >= 0 and _default_p_flag):
                _default_p_flag = False

            # In the future we can add more customer types
            types.append(_customer_type)
            probs.append(float(_customer_type['spawn_probability']))

        # Normalizing probabilities
        if _default_p_flag:
            _len = len(probs)
            _probs = probs

            probs = [1/_len]*_len
        else:
            # Replace negative values with 0
            probs = np.clip(np.array(probs), a_min=0, a_max=None)
            assert (probs > 0).any(), "All spawn probabilites can not be zero"

            # Normalizing
            _probs = probs
            probs = probs / probs.sum()
            if (_probs != probs).any():
                logger.warning('Spawn probabilities for agents {} are not normalized. Converting {} to {}'.format(
                    [x['name'] for x in types], _probs, probs))

        return list(types), list(probs)

    def spawn(self, spawn_time, seed=None):
        self.customer = np_random.rng.choice(
            self.customer_type_list, p=self.customer_type_proba_list)
        self.groupsize = np_random.rng.choice(
            [1, 2], p=self.customer['groupsize_probability'])
        return {'GroupSize': self.groupsize}

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
        preference += self.customer['beta_constant']

        # Set customers opinion of the seat prices based on customer
        # characteristics. People prefer seats next to empty seats
        preference += self.customer['beta_isolation'] * \
            self._dist_from_edge(seat_availability_matrix)

        # Preference for window seats
        preference[:, observations.WindowCols] += self.customer['beta_window']

        # Preference for aisle seats
        preference[:, observations.AisleCols
                   ] += self.customer['beta_aisle']

        # Preference for exit row (or extra legroom) seats
        preference[observations.ExitRows
                   ] += self.customer['beta_extra_legroom']

        # Preference for forwarward seats
        preference += np.tile(np.linspace(1, 0, rows),
                              (cols, 1)).T * self.customer['beta_forward']

        for size, beta in enumerate(self.customer['beta_group_seat']):
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
            self.customer['beta_nobuy_sensitivity']

        # Preference for less expensive seats
        preference += np.clip(seat_prices_matrix
                              - worst_choice_price,
                              a_min=0, a_max=None) * self.customer['beta_price_sensitivity']

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
        pass
