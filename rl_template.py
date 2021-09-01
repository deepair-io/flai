from flai import SeatSmartEnv
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if __name__ == "__main__":

    env = SeatSmartEnv()
    observation = env.reset()
    done = False
    while not done:
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        break
