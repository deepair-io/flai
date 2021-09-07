# Getting Started with Flai

**Flai is a toolkit for developing and comparing reinforcement learning algorithms.** It is inspired by OpenAI Gym and has been modified for travel's needs.

The flai library is a collection of test problems — environments — that you can use to work out your reinforcement learning algorithms. These environments have a shared interface, allowing you to write general algorithms.

## Requirements
Flai makes no assumptions about the structure of your agent, and is compatible with any numerical computation library, such as TensorFlow, Pytorch, sklearn etc. Only requirement to run flai environments is python with version 3.8 and above.

## Installation

To get started, you’ll need to have Python 3.8+ installed. Simply install `flai` using `pip`:

```
pip install flai
```

And you’re good to go!


### Building from source
If you prefer, you can also clone the Flai repository directly from `github`. This is particularly useful when you’re working on modifying Flai itself or adding environments without using config.

Download and install using:

```
git clone https://github.com/deepair-io/flai.git
cd flai
```

> [!TIP]
> We recommend you create a virtual environment and install all the requirements using [poetry](https://python-poetry.org/) commands 

## Environments
Here’s a bare minimum example of getting something running. This will run an instance of the SeatSmart Environment for 30 event steps, rendering the environment at each step:

```python
from flai import SeatSmartEnv
env = SeatSmartEnv()
env.reset()
for _ in range(30):
    env.step(env.action_space.sample()) # take a random action
env.close()
```

## Observation
If we ever want to do better than take random actions at each step, it'd probably be good to actually know what our actions are doing to the environment.

The environment’s `step` function returns exactly what we need. In fact, step returns four values. These are:

1. `observation` (**object**): an environment-specific object representing your observation of the environment. 
2. `reward` (**float**): amount of reward achieved by the previous action. The scale varies between environments, but the goal is always to increase your total reward.
3. `done` (**boolean**): whether it's time to reset the environment again. All games are divided up into well-defined episodes, and `done` being `True` indicates the episode has terminated. (For example, perhaps the flight is sold-out or it is time for the flight to depart)
4. `info` (**dict**): diagnostic information useful for debugging. It can sometimes be useful for learning (for example, it might contain the raw probabilities behind the environment’s last state change). However, official evaluations of your agent are not allowed to use this for learning.

The process gets started by calling `reset()`, which returns an initial observation. So a more proper way of writing the previous code would be to respect the done flag:

```
from flai import SeatSmartEnv
env = SeatSmartEnv()
for i_episode in range(20):
    observation = env.reset()
    done = False
    while not done:
        print(observation)
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        print(reward)
env.close()
```

## Spaces
In the examples above, we’ve been sampling random actions from the environment’s action space. But what actually are those actions? Every environment comes with an `action_space` and an `observation_space`. These attributes are data classes using [pydantic](https://pydantic-docs.helpmanual.io/) and its instance is used for each episode. 

### Observation space
Observation space is a data class that contains the information about the observation. When an agent takes a step in the environment, the environment returns `observation`, `reward`, `done` and `info` as shown above. Here, `observation` is an instance of Observation space.

#### Schema
To get the information about the structure of `observation` and what to expect, we can use the following with the environment of your choice instead of `<EnvironmentName>`:

```python
from flai import <EnvironmentName>
env = <EnvironmentName>()
print(env.observation_space.schema())
```

The schema will vary depending on the environment.

#### Type conversion
Since we are using [pydantic](https://pydantic-docs.helpmanual.io/) data classes, we can use efficient type conversion from object to `json` and `dict` using `observation.json()` and `observation.dict()`. 

### Action space
Action space is a data class that is used for performing action in the environment. In order to take a `step`, agent need to perform an action. Every environment has `action_space` which can be instantiated to create an action. Additionally, we can use `env.action_space.sample()` to sample a valid action.

