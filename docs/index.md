**[Home]** | **[Experiments]** |  **[Tutorial]** |


## Observations
If we ever want to do better than take random actions at each step, it’d probably be good to actually know what our actions are doing to the environment.

The environment’s `step` function returns exactly what we need. In fact, step returns four values. These are:

1. `observation` (object): an environment-specific object representing your observation of the environment. For example, `Seatmap` realated context like seatmap status, number of tickets sold, number of seats sold by zone. `Customer` related context like size of the group that is going to come in the next timestep. `Time` related context like how many days to departure
1. `reward` (float): amount of reward achieved by the previous action. The scale varies between environments, but the goal is always to increase your total reward.
1. `done` (boolean): whether it’s time to reset the environment again. All games are divided up into well-defined episodes, and `done` being `True` indicates the episode has terminated. (For example, perhaps the flight is sold-out or it is time for the flight to depart)
1. `info` (dict): diagnostic information useful for debugging. It can sometimes be useful for learning (for example, it might contain the raw probabilities behind the environment’s last state change). However, official evaluations of your agent are not allowed to use this for learning.
This is just an implementation of the classic “agent-environment loop”. Each timestep, the agent chooses an action, and the environment returns an observation and a reward.

The process gets started by calling `reset()`, which returns an initial observation. So a more proper way of writing the previous code would be to respect the done flag:

```
from flai import SeatSmartEnv
env = SeatSmartEnv()
for i_episode in range(20):
    observation = env.reset()
    done = False
    while not done:
        env.render()
        print(observation)
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        print(reward)
env.close()
```

This should give a video and output like the following. You should be able to see where the resets happen.

![Reset Demo](./assets/gifs/demo2.gif)

## Spaces
In the examples above, we’ve been sampling random actions from the environment’s action space. But what actually are those actions? Every environment comes with an action_space and an observation_space. These attributes are of type ActionSpace and ObservationSpace respective, and they describe the format of valid actions and observations:

```
>>> from flai import SeatSmartEnv
pygame 2.0.0.dev6 (SDL 2.0.10, python 3.7.3)
Hello from the pygame community. https://www.pygame.org/contribute.html

>>> env = SeatSmartEnv()
[INFO]: New customer spawned

>>> env.observation_space
{"seats": "list", "availability": "list", "ticket_availability": "int", "current_price": "list", "sold": "list", "revenue": "list", "ticket_sold": "int", "ticket_revenue": "int", "advanced_purchase": "int", "groupsize": "int64"}

>>> env.action_space
{"upper": "ndarray", "lower": "ndarray"}
```
The `ObservationSpace` is a generic object where lots of information can be stored and in this case the environmen't observation space has the context of the flight, seatmap, customer and time. You can further analyze the observation_space for futher details.

```
>>> env.observation_space.groupsize
1
>>> env.observation_space.advanced_purchase
364
>>> env.observation_space.availability
[138, 24, 18]
```

Similary ActionSpace is a box that is defined by upper and lower bound arrays. In the context of `SeatSmart` this represents the lower and upper bound of price for each seating zone. We can check the Box's bounds:

```
>>> env.action_space.lower
array([ 30,  65, 120], dtype=int32)
>>> env.action_space.upper
array([145, 300, 480], dtype=int32)
```

It is also important to note that ActionSpace enforces that the price follow a strict heirarchy.

`zone1 < zone2 < zone3`

you can query the ActionSpace to check if an action is valid:

```
>>> [25,100,200] in env.action_space
False
>>> [45,100,200] in env.action_space
True
```

and finally, if you want to convert your action into a valid action, you can let actionspace take care of it by calling the `valid` fucntion.

```
>>> env.action_space.valid([25,100,200])
array([ 30, 100, 200], dtype=int32)
```

In the above example, since 25 was not a valid price for zone1, it was automatically boxed into the upper and lower limit.

Fortunately, the better your learning algorithm, the less you’ll have to try to interpret these numbers yourself.

## Available Environments and Modes
 `SeatSmart` has many different pre-built modes. Here is a list of the modes that are available.

1. `UO_A320` mode - this creates a game for a typical A320 seatmap. This is also the default mode.
2. `UO_A321` mode - this creates a game for a typical A321 seatmap.
3. `UO_A320NEO` mode - this creates a game for a typical A320-NEO seatmap.

### User defined configurations:
All user defined config(s) needs to be placed at `~/.config/flai/seatsmart/config/` directory and all the plugins can be placed at `~/.config/flai/seatsmart/`

#### Mode
Mode config is named `modes.json`. [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/config/modes.json) you can checkout the default `modes.json` file that comes with flai.

A typical mode contains 6 attributes:

    "default": {
        "theme": "default",
        "seat_map_layout": "UO_A320",
        "pricing_rules": "default",
        "demand": 180,
        "arrival_distribution": "default",
        "customer": "SeatCustomer_MNL"
    },


1. **`theme`**: That defines the look and feel of the pygame. This is picked up from `themes.json` file. [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/config/themes.json) you can checkout the default `themes.json` file that comes with flai. Currently we have only "default" theme for pygame. We will soon add more themes. 
2. **`seat_map_layout`**: This is the layout of the seatmap as defined in the `seatmaps.json` file. [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/config/seatmaps.json) you can checkout the default `seatmaps.json` file that comes with flai. Choose any of the available seatmaps available or simply define your own (and place it at `~/.config/flai/seatsmart/config/seatmaps.json`).
3. **`pricing_rules`**: This defines the minimum and maximum price for each zone that is defined in the seat_map_layout. We use `pricing_rules.json` file for this and [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/config/pricing_rules.json) you can checkout the default `pricing_rules.json` file that comes with flai. Choose an existing pricing rule or create a new one in `pricing_rules.json` file (also, please place it at `~/.config/flai/seatsmart/config/pricing_rules.json`). 
4. **`demand`**: Number of transactions you want to simulate for every game episode. Please note that every customer will buy a ticket on the flight. But if the customer will buy a seat or not depends on your actions and the customer choice model that is defined in the mode.
5. **`arrival_distribution`**: This attribute controls the weekly arrival rate of customer during the game. A game lasts for one episode, which is 364 days or 52 weeks. Every time the game proceed by one step, a customer is spawned and the time moves based on the arrival rate. The sampling of arrival rate follows a poisson distribution. We use `arrival_distribution.json` file for this and [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/config/arrival_distribution.json) you can checkout the default `arrival_distribution.json` file that comes with flai. You can change the arrival rate so that you can train the agent for various real-life scenarios like "early booking" flight or "late booking" flight. These different distributions will be made available within `arrival_distributions.json` file. If you dont find what you are looking for, feel free to create one and add it to your custom mode (also, please place it at `~/.config/flai/seatsmart/config/arrival_distribution.json`).
6. **`customer`**: This attribute points the class that defines the customer purchase logic. The reinforcement learning agent trying to beat this customer. Currently we have two classes available ("SeatCustomer" and "SeatCustomer_MNL") and you can find these classes [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/customers.py). Feel free to pick one of the exiting customer models or create your own in `customers.py` file as a plugin and place it at `~/.config/flai/seatsmart/customers.py`. 

As you can see, you have complete control on which game you want to play. The reason for keep the game configurable is because we are still evolving the environment so we wanted to make sure the environment is open both "game designers" and "RL agent designers". Ideally you should be training your reinforcement learning algorithm to train in all the different modes.

#### SeatCustomer_MNL Parameters

We use `customer_parameters.json` to control one of the customer model's parameter, namely "SeatCustomer_MNL" model. [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/config/customer_parameters.json) you can checkout the default `customer_parameters.json` file that comes with flai. You can create your own `customer_parameters.json` and place it at `~/.config/flai/seatsmart/config/customer_parameters.json`

```
{
    "SeatCustomer_MNL": {
        "MyCustomer": {
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
    }
}
```

1. **beta_group_seat** : Not sure what this is but either you can check the source code [Here](https://bitbucket.org/deepair/flai/src/master/flai/envs/seatsmart/customers.py) or ping arinbjorn@deepair.io
2. **beta_price_sensitivity** : sensitivity to the price of the seat (please add negative in front, we will fix it in the next upgrade)
3. **beta_nobuy_sensitivity** : sensitivity to no purchase option
4. **beta_forward** : sensitivity towards seats that are in front
5. **beta_window** : sensitivity towards window seats
6. **beta_aisle** : sensitivity towards aisle seats
7. **beta_extra_legroom** : sensitivity towards leg room
8. **beta_constant** : Not sure :( 
9. **groupsize_probability** : list of size two with group size probability 
10. **spawn_probability** : probability of spawning this customer

> **Note** : you can create a customer with just one attribute change. For example if you want to create "MyNewCustomer" and only change "beta_forward" from 1.5 to 0. The rest of the parameters will be picked up from default (as shown above in MyCustomer). Then the following json should suffice:

```
{
    "SeatCustomer_MNL": {
        "MyNewCustomer": {
            "beta_forward": 0,
            "spawn_probability": 1
        }
    }
}
```

## Plugins

Currently we have only one plugin:

### Customer Plugin
TODO

## Interactive Game
Finally, as a fun exercise we have also provide a way to play the game in a 100% interactive mode. Where you can manually spawn customers, change the offered price and see if you can beat your RL agent. Here are is how you access the game in the interactive mode.

```
>>> from flai import game
>>> game()
```
A screen should pop-up with the game running in the interactive mode. Here are few keyboard short cuts to play the game:
1. `UP_ARROW` :arrow_up: - to increase the price.
2. `DOWN_ARROW` :arrow_down: - to reduce the price.
3. `SPACE BAR` - press the key down to spawn a customer and start the transaction, and release it to complete the transaction. You can change the price while the space-bar is down.
4. `SHIFT + SPACE_BAR` - to perform 30 transactions.

Thats it, enjoy FLAI and give us your feedback. 

Please raise issues in the repository for bug, enhancement, proposal or task.  

If you are interested in creating new environments, new modes, new games, we are accepting pull requests!

[Home]: ./index.md
[Experiments]: ./experiments.md
[Tutorial]: ./tutorial.md