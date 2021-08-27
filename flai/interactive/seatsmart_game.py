from flai.envs.seatsmart.game_entities import *
from flai.logger import console
import logging
logger = logging.getLogger()
# import pygame
# Global Constants

# SCREEN SIZE
SCREEN_WIDTH = 1035
SCREEN_HEIGHT = 600


class Display(object):

    @staticmethod
    def blocks(msg=[{"Head": "up arrow :arrow_up:", "Body": "increase price by 5"}, {"Head": "up down", "Body": "decrease price by 5"}]):
        from rich.columns import Columns
        from rich.panel import Panel
        user_renderables = [Panel(
            "[b]{}[/b]\n[yellow]{}".format(x["Head"], x["Body"]), expand=True) for x in msg]
        return Panel(Columns(user_renderables))


KEYS_DICT = [{
    "Head": ":arrow_up: Up Arrow",
    "Body": "Increase price"
},
    {
    "Head": ":arrow_down: Down Arrow",
    "Body": "Decrease price"
},
    {
    "Head": ":x: Stop",
    "Body": "Close Window"
},
    {
    "Head": "Space Bar",
    "Body": ":hatching_chick: Spawn new customer"
}
]


def game():
    """ Main program function. """
    # setting logger
    logger.setLevel(logging.INFO)

    # Initialize Pygame and set up the window
    pygame.init()

    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("SeatSmart")

    # Create our objects and set the data
    done = False
    clock = pygame.time.Clock()

    # Create an instance of the Game class
    game = Game()

    # discplay
    console.print(Display.blocks(KEYS_DICT))

    # Main game loop
    with console.status("[green]Running simulation ...") as status:
        while not done:

            # Process events (keystrokes, mouse clicks, etc)
            done = game.process_events()

            # Update object positions, check for collisions
            game.run_logic()

            # Draw the current frame
            game.display_frame(screen)

            # Pause for the next frame
            clock.tick(60)

    # Close window and exit
    pygame.quit()
