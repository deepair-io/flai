from abc import ABC, abstractmethod
import json
import math
import numpy as np
from flai.utils import np_random


class Env(ABC):
    """The main Environment class. It encapsulates an environment with
    arbitrary behind-the-scenes dynamics. An environment can be
    partially or fully observed.
    The main API methods that users of this class need to know are:
        step
        reset
        render
        close
        seed
    And set the following attributes:
        action_space: The Space object corresponding to valid actions
        observation_space: The Space object corresponding to valid observations
        reward_range: A tuple corresponding to the min and max possible rewards
    Note: a default reward range set to [-inf,+inf] already exists. Set it if
    you want a narrower range.
    The methods are accessed publicly as "step", "reset", etc...
    """
    # Set this in SOME subclasses
    reward_range = (-float('inf'), float('inf'))

    # Set these in ALL subclasses
    action_space = None
    observation_space = None

    @abstractmethod
    def step(self, action):
        """Run one timestep of the environment's dynamics. When end of
        episode is reached, you are responsible for calling `reset()`
        to reset this environment's state.
        Accepts an action and returns a tuple (observation, reward, done, info)
        Args:
            action (object): an action provided by the agent
        Returns:
            observation (object): agent's observation of the current
            environment
            reward (float) : amount of reward returned after previous action
            done (bool): whether the episode has ended, in which case further
            step() calls will return undefined results
            info (dict): contains auxiliary diagnostic information (helpful
            for debugging, and sometimes learning)
        """

    @abstractmethod
    def reset(self):
        """Resets the state of the environment & returns an initial observation
        Returns:
            observation (object): the initial observation.
        """

    @abstractmethod
    def render(self, mode='human'):
        """Renders the environment.
        The set of supported modes varies per environment. (And some
        environments do not support rendering at all.) By convention,
        if mode is:
        - human: render to the current display or terminal and
          return nothing. Usually for human consumption.
        - rgb_array: Return an numpy.ndarray with shape (x, y, 3),
          representing RGB values for an x-by-y pixel image, suitable
          for turning into a video.
        - ansi: Return a string (str) or StringIO.StringIO containing a
          terminal-style text representation. The text can include newlines
          and ANSI escape sequences (e.g. for colors).
        Note:
            Make sure that your class's metadata 'render.modes' key includes
              the list of supported modes. It's recommended to call super()
              in implementations to use the functionality of this method.
        Args:
            mode (str): the mode to render with
        Example:
        class MyEnv(Env):
            metadata = {'render.modes': ['human', 'rgb_array']}
            def render(self, mode='human'):
                if mode == 'rgb_array':
                    return np.array(...) # return RGB frame suitable for video
                elif mode == 'human':
                    # pop up a window and render
                else:
                    # just raise an exception
                    super(MyEnv, self).render(mode=mode)
        """

    def close(self):
        """Override close in your subclass to perform any necessary cleanup.
        Environments will automatically close() themselves when
        garbage collected or when the program exits.
        """
        pass

    def seed(self, seed=None):
        """Sets the seed for this env's random number generator(s).
        Note:
            Some environments use multiple pseudorandom number generators.
            We want to capture all such seeds used in order to ensure that
            there aren't accidental correlations between multiple generators.
        Returns:
            list<bigint>: Returns the list of seeds used in this env's random
              number generators. The first value in the list should be the
              "main" seed, or the value which a reproducer should pass to
              'seed'. Often, the main seed equals the provided 'seed', but
              this won't be true if seed=None, for example.
        """
        return


class ObservationSpace(object):
    """The main Observation Space class. It encapsulates an observation space
    with arbitrary behind-the-scenes dynamics.
    The main API methods that users of this class need to know are:
        assign

    Example Usage:
        [1]observation_space = ObservationSpace()
        [2]obsercation_space.assign(x=1, name='Myname')
        [3]print(observation_space)
        >>> {"x": "int", "name": "str"}
        [4]x in observation_space
        >>> True
        [5]y in observation_space
        >>> False
        [6]observation_space.name
        >>> 'Myname'
    """

    def assign(self, **kwargs):
        """Assigns a keyword argument to the instance variable

        Example:
            observation_space = ObservationSpace()
            observation_space.assign(x=1)
            observation_space.x
            >>> 1
        """
        for key, value in kwargs.items():
            self.__dict__[key] = value

    def __contains__(self, x):
        """To check if the observation is present in the
        observation space. 
        """
        return x in set(self.__dict__.keys())

    def __repr__(self):
        """To represent observation variables as json
        with key as instance variables and value as dtype
        """
        info = dict()
        for key, value in self.__dict__.items():
            info[key] = type(value).__name__
        return json.dumps(info)


class ActionSpace(object):
    """The main Action Space class. It encapsulates an action space
    with arbitrary behind-the-scenes dynamics. This action space is
    creates a box space (very similar to OpenAI's Box Space which
    inculed lower bound and upper bound along all the axis) with an
    additional constraint, that is, x[i+1] >= x[i] for all i in x in
    space. For example [1, 2, 3] is valid but [1, 3, 2] is not valid
    sample. 
    The main API methods that users of this class need to know are:
        sample
        valid

    Example Usage:
        action_space = ActionSpace(upper=[-1, -1, -1], [1, 1, 1])
    """

    def __init__(self, upper=None, lower=None):

        self._upper = np.array(upper, dtype=np.int32)
        self._lower = np.array(lower, dtype=np.int32)

        assert (self._upper.shape ==
                self._lower.shape), 'upper and lower limit shape mismatch'
        assert (self._upper - self._lower >=
                0).all(), 'lower limit is greater than upper limit'

        assert (np.all(np.diff(self._upper) >= 0)
                ), 'upper limit must be in increasing order'
        assert (np.all(np.diff(self._lower) >= 0)
                ), 'lower limit must be in increasing order'

    @property
    def upper(self):
        return self._upper

    @property
    def lower(self):
        return self._lower

    def sample(self, seed=None):
        """Sample an action from the action space.

        Args:
            seed (int) : seed to control randomness

        Note: Seed functionality is not implemented right now
        """
        result = []

        # Creates a lower limit as -oo
        current_lower_bound = -math.inf

        for i in range(self.upper.shape[0]):

            # create lower and higher limit for one sampling
            low = self.lower[i] if current_lower_bound < self.lower[i] else current_lower_bound
            high = self.upper[i]

            # random sample
            price = np_random.rng.randint(low=low, high=high)
            result.append(price)

            # update the lower limit for next round of sampling
            current_lower_bound = max(low, price)

        return np.array(result, dtype=np.int32)

    def valid(self, x):
        """Brings an out of bounds invalid sample into the
        closest valid bounds.

        Args:
            x (list/np.array) : action with same dimentionality as
                of the box.

        Returns:
            A valid sample with the closest match to x. (np.array)
        """
        if isinstance(x, list):
            x = np.array(x, dtype=np.int32)

        # assert the shape of the input
        assert (x.shape == self.lower.shape), 'x shape is {} and required is {}'.format(
            x.shape, self.lower.shape)

        x[x > self.upper] = self.upper[x > self.upper]
        x[x < self.lower] = self.lower[x < self.lower]
        return x

    def __contains__(self, x):
        """To check if the action is present in the
        action space. 
        """
        if isinstance(x, list):
            x = np.array(x, dtype=np.int32)
        return (x.shape == self.upper.shape) and (self.upper >= x).all()\
            and (self.lower <= x).all() and (np.diff(x) >= 0).all()

    def __repr__(self):
        """To represent action variables as json
        with key as instance variables and value as dtype
        """
        info = dict()
        for key, value in self.__dict__.items():
            info[key] = type(value).__name__
        return json.dumps(info)
