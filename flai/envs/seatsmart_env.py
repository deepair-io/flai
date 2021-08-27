from flai.envs.seatsmart.game import PricingGame
from flai.utils import np_random
from flai import Env
import yaml
import json
import logging
logger = logging.getLogger()


class SeatSmartEnvOld(Env):
    """The main environment for SeatSmart Game. This environment
    is an extension of the base core environment ENV. To check
    the available API calls, please refer to the base environemnt.

    This environment can run on modes:
    Available modes : default, UO_A321, UO_A320NEO

    Example :
        env = SeatSmartEnv(mode="U0_A321")
    """

    def __init__(self, mode="default"):
        from flai.envs.seatsmart.game_entities import Game
        import pygame

        # Setting mode and screen
        self.mode = mode
        self.screen = None

        # Pygame variables
        pygame.init()
        SCREEN_WIDTH = 1035
        SCREEN_HEIGHT = 600
        self.size = [SCREEN_WIDTH, SCREEN_HEIGHT]

        # Create an instance of the Game class
        self.game = Game(self.mode)
        logger.debug('[{}] Game mode {} created'.format(
            self.__class__.__name__, mode))

        # Tracking Score (Private Variable)
        self._score = self.game.score
        logger.debug('[{}] Assigned score {}'.format(
            self.__class__.__name__, self._score))

        # screen based on render option
        self._screen = None

        # quit variable for exiting the game
        self.quit = False

    @property
    def screen(self):
        return self._screen

    @screen.setter
    def screen(self, size):
        if size:
            self._screen = pygame.display.set_mode(size)
            pygame.display.set_caption("SeatSmart")
            self.quit = self.game.process_events_auto()
            self.game.display_frame(self._screen)
        else:
            self._size = None

    @property
    def observation_space(self):
        """Observation Space variable to extend ENV

        Returns: ObservationSpace object for analyst
        from the game.
        """

        return self.game.observe()

    @property
    def action_space(self):
        """Action Space Varirable to extend ENV

        Returns: ActionSpace object for analyst
        from the game.
        """

        return self.game.action_space

    def render(self, mode='human'):
        """Renders the environment. Check ENV for
        more documentations.
        """

        # Human (visual) mode
        if mode == 'human':
            logger.debug('[{}] Render mode {}'.format(
                self.__class__.__name__, mode))
            self.screen = self.size
            self.game.render_frame()
            self.game.display_frame(self.screen)
            self.quit = self.game.process_events_auto()
            if self.quit:
                self.close()

        # CMD mode
        elif mode == 'background':
            logger.debug('[{}] Render mode {}'.format(
                self.__class__.__name__, mode))
            pass

        # Invalid modes
        else:
            logger.error('invalid mode {}'.format(mode))
            raise Exception('invalid mode {}'.format(mode))

    def step(self, action):
        """To take a step in the environment.
        Check ENV for more documentations
        """

        # Perform action in the game
        done = self.game.act(action) or self.quit

        # Get the observations from the game
        observation = self.game.observe()

        # Setting up the reward
        score = self.game.score
        reward = score - self._score
        self._score = score

        # Information (Aux)
        info = None
        return observation, reward, done, info

    def reset(self):
        """To reset the environment.
        Check ENV for more documentations
        """

        logger.debug('[{}] Resetting environment'.format(
            self.__class__.__name__))
        self.game = Game(self.mode)
        self._score = self.game.score
        return self.game.observe()

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

        logger.debug('[{}] Terminated'.format(
            self.__class__.__name__))
        pygame.quit()


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

    This is version 2. 

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

    @property
    def observation_space(self):
        """Observation Space variable to extend ENV

        Returns: ObservationSpace object for analyst
        from the game.
        """

        return self.game.analyst_observation

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
        if self.game._snapshot:
            info = self.game.SNAPSHOT.Experience[-1]
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
