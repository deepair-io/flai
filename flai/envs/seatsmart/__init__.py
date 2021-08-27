from rich.logging import RichHandler
from flai.envs.seatsmart.game import PricingGame
from flai.logger import console
import logging

logger = logging.getLogger('SeatSmart')
# logger.setLevel(logging.DEBUG)

rich_handler = RichHandler(
    console=console, show_time=False, rich_tracebacks=True)

# rich_handler.setLevel(logging.DEBUG)
logger.addHandler(rich_handler)
