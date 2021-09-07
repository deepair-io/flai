from flai.envs.seatsmart.models.analyst import Observation
from flai.envs.seatsmart.game import PricingGame
from flai.utils import np_random
from flai import Env
import yaml
import json
import logging
logger = logging.getLogger('SeatSmart')


class ActionSpace:

    def __init__(self, zone_price):
        self.zone_price = zone_price

    def sample(self, seed=None):
        """Sample an action from the action space.

        Args:
            seed (int) : seed to control randomness

        Note: Seed functionality is not implemented right now
        """
        _action = {}
        for key, val in self.zone_price.items():
            _action[key] = np_random.rng.randint(low=val['MinPrice'],
                                                 high=val['MaxPrice'])
        return _action

    def __contains__(self, x: dict):
        """To check if the action is present in the
        action space.
        """
        # TODO
        assert isinstance(x, dict), 'Action should be of type dict'

        return True

    def __repr__(self):
        """To represent action variables as json
        with key as instance variables and value as dtype
        """
        info = dict()
        for key, value in self.zone_price.items():
            info[key] = "Price (default:{}) between Min:{} - Max:{}".format(
                value['Price'], value['MinPrice'], value['MaxPrice'])
        return json.dumps(info)


class SeatSmartEnv(Env):
    """The main environment for SeatSmart Game. This environment
    is an extension of the base core environment ENV. To check
    the available API calls, please refer to the base environemnt. 

    This environment can run on modes:
    Available modes : None

    Example :
        env = SeatSmartEnv(mode="U0_A321")
    """

    def __init__(self,
                 config_path: str = None):

        self.config = {}
        if not config_path is None:
            with open(config_path) as f:
                self.config = yaml.load(f, Loader=yaml.FullLoader)
            logger.debug('Loading configuration: {}'.format(self.config))

    @property
    def observation_space(self):
        """Observation Space variable to extend ENV

        Returns: ObservationSpace object for analyst
        from the game.
        """

        return Observation

    @property
    def action_space(self):
        """Action Space Varirable to extend ENV

        Returns: ActionSpace object for analyst
        from the game.
        """
        # TODO
        return ActionSpace(self.game.flight.zone_price)

    def render(self, mode='human'):
        """Renders the environment. Check ENV for
        more documentations.
        """
        # TODO: Remove this function
        pass

    def step(self, action):
        """To take a step in the environment.
        Check ENV for more documentations
        """

        # Perform action in the game
        done, rev = self.game.act(action) or self.quit

        # Get the observations from the game
        observation = self.game.analyst_observation

        # Setting up the reward
        self._score += rev
        reward = rev

        # Information (Aux)
        info = None

        return observation, reward, done, info

    def reset(self):
        """To reset the environment.
        Check ENV for more documentations
        """

        # Create an instance of the Game class
        self.game = PricingGame(config=self.config)

        # Tracking Score (Private Variable)
        self._score = 0

        return self.game.analyst_observation

    def seed(self, seed=None):
        """To set the seed in the game.

        Args:
            seed (int) : Random seed value for controlled experiments
        """
        if seed is not None:
            np_random.rng.seed([seed])

    def close(self):
        """To close the environment.
        Check ENV for more documentations
        """

        pass
