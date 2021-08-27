import importlib
import matplotlib.backends.backend_agg as agg
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from os import path
import json
import random
import pygame
from os.path import expanduser
import os
import inspect
from flai.utils import np_random
from flai.envs.seatsmart.network_entities import SeatMap, MetricsTracker,\
    Episode
from flai import ObservationSpace, ActionSpace  # , logger
import logging
logger = logging.getLogger("SeatSmart" + "." + __name__)

matplotlib.use("Agg")


class SeatSprite(pygame.sprite.Sprite):
    """ This class represents an individual seat image shown in the seatmap """

    def __init__(self):
        """ Constructor, create the image of the seat. Note that the image has
        to be 20X20 pixel
        """
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()

    def set_image(self, image):
        """ Set the image of the sprite.

        The image changes based on the status of the flight like if it is
        blocked, taken, available. This image should always be 20X20 pixel

        Arguments:
            image {pygame.image} -- The image to be placed
        """
        self.image = image


class Stat(pygame.sprite.Sprite):
    """A sprite to show a statistic or a number

    This class extends a pygame.sprite base class and is used to show
    numbers or statistics across the game.

    Once the sprite is created its position can be changed using
    spriteObject.rect.x and spriteObject.rect.y values

    """

    def __init__(
            self, text, text_color, text_font, bg_color, bg_width=100,
            bg_height=40):
        """A constructor for a Stat Sprite.

        Arguments:
            text {str} -- The value that needs to be rendered
            text_color {tuple} -- The color in which text is rendered (R,G,B)
            text_font {pygame.font.Font} -- The font in which the text is
            rendenered. The font size and font is pre-configured before passing
            it on here.
            bg_color {tuple} -- The color of the background (R,G,B)

        Keyword Arguments:
            bg_width {int} -- The width of the background (default: {100})
            bg_height {int} -- The height of the background (default: {40})
        """
        super().__init__()

        # Create the background
        self.image = pygame.Surface((bg_width, bg_height))
        self.rect = self.image.get_rect()
        self.bg_color = bg_color
        self._set_background()

        self.text_font = text_font
        self.text = text
        self.text_color = text_color
        self.update_text(self.text)

    def _set_background(self):
        """ re-render background color """
        self.image.fill(self.bg_color)

    def update_text(self, text):
        """Update the text of the sprite with right alignment

        Arguments:
            text {str} -- The str that has be rendered.
            the text is always right aligned.
        """
        self._set_background()
        self.text = text

        # Render the text
        _text = self.text_font.render(self.text, True, self.text_color)
        _text_rect = _text.get_rect()

        # Place the text right algined with 10 pixels padding
        _text_x = self.rect.w - _text_rect.w - 10
        _text_y = self.rect.h/2 - _text_rect.h/2
        self.image.blit(_text, (_text_x, _text_y))


class Label(pygame.sprite.Sprite):
    """Label Sprites is used for static texts in the game.
    """

    def __init__(self, text, color, font):
        """Constructor to create the sprite

        Arguments:
            text {str} -- The text to be rendered.
            color {tuple} -- The color in which text is rendered (R,G,B)
            font {pygame.font.Font} -- The font in which the text is
            rendenered. The font size and font is pre-configured before passing
            it on here.
        """
        super().__init__()
        self.text = text
        self.font = font
        self.color = color
        self.rerender()
        self.rect = self.image.get_rect()

    def update_text(self, text):
        """Update the text.

        This should be seldom used because Label is mainly used for sprites
        that are static

        Arguments:
            text {[type]} -- [description]
        """
        self.text = text
        self.rerender()

    def rerender(self):
        """Rerender the text in the sprite
        """
        self.image = self.font.render(self.text, True, self.color)


class Message(pygame.sprite.Sprite):
    """A Message sprite to be placed in the center of the screen.

    The Message has to fit in one line.
    """

    def __init__(self, text, font, color):
        """Constructor of the message sprite

        Arguments:
            text {str} -- The text to be rendered.
            color {tuple} -- The color in which text is rendered (R,G,B)
            font {pygame.font.Font} -- The font in which the text is
            rendenered. The font size and font is pre-configured before passing
            it on here.
        """
        super().__init__()
        self.text = text
        self.font = font
        self.color = color
        self.rerender()
        self.rect = self.image.get_rect()

    def rerender(self):
        """re-render the sprite, it is always placed on a translucent black
        background in the center of the screen.
        """
        text = self.font.render(self.text, True, self.color)
        text_rect = text.get_rect()

        bg_h = text_rect.h*2
        bg_w = text_rect.w*2
        self.image = pygame.Surface((bg_w, bg_h)).convert_alpha()
        self.image.fill((0, 0, 0, 200))
        self.image.blit(text, (bg_w/2 - text_rect.w/2, bg_h/2 - text_rect.h/2))


class SimpleImage(pygame.sprite.Sprite):
    """A sprite to render a simple image.
    """

    def __init__(self, image):
        super().__init__()
        self.rerender(image)
        self.rect = self.image.get_rect()

    def rerender(self, image):
        self.image = image


def get_abs_path(filepath):
    return os.path.join(os.path.dirname(__file__), filepath)


class Game(object):
    """Main Game Class
    """

    observation_space = dict()
    action_space = None

    def __init__(self, mode="default"):
        """Constructor of the Game object.
        """
        # This variable determines if the game is over or not
        self.game_over = False

        # Load all configs
        modepath = os.path.join(os.path.dirname(__file__),
                                "config", "modes.json")
        with open(modepath, 'r') as target:
            mode_config = json.load(target)

        # Try loading user config
        user_modepath = os.path.join(expanduser(
            "~"), ".config/flai/seatsmart/config", "modes.json")
        if os.path.exists(user_modepath):
            try:
                with open(user_modepath, 'r') as target:
                    user_mode_config = json.load(target)
                mode_config.update(user_mode_config)
                logger.debug('User config loaded: {}'.format(user_modepath))
            except Exception as error:
                logger.exception('User defined mode is not loaded. Skipping file present at {} due to following error : {}'.format(
                    user_modepath, error))

        self.mode_config = mode_config[mode]
        logger.debug('Model config: {}'.format(self.mode_config))

        # Load THEME configuration
        themepath = os.path.join(os.path.dirname(__file__),
                                 "config", "themes.json")
        with open(themepath, 'r') as target:
            theme_config = json.load(target)
        theme_config = theme_config[self.mode_config['theme']]
        logger.debug('Theme config: {}'.format(theme_config))

        # Load Seatmap Layout configuration
        layoutpath = os.path.join(os.path.dirname(__file__),
                                  "config", "seatmaps.json")
        with open(layoutpath, 'r') as target:
            layout_config = json.load(target)
        layout_config = layout_config[self.mode_config['seat_map_layout']]
        logger.debug('Layout config: {}'.format(layout_config))

        # Load Arrival Distribution config
        distpath = os.path.join(os.path.dirname(__file__),
                                "config", "arrival_distributions.json")
        with open(distpath, 'r') as target:
            dist_config = json.load(target)

        # Try loading user config
        user_distpath = os.path.join(expanduser(
            "~"), ".config/flai/seatsmart/config", "arrival_distributions.json")
        if os.path.exists(user_distpath):
            try:
                with open(user_distpath, 'r') as target:
                    user_dist_config = json.load(target)
                dist_config.update(user_dist_config)

                logger.debug('[{}] user config loaded: {}'.format(
                    self.__class__.__name__, user_distpath))
            except Exception as error:
                logger.exception('User defined arrival distribution is not loaded. Skipping file present at {} due to following error : {}'.format(
                    user_distpath, error))
        dist_config = dist_config[self.mode_config['arrival_distribution']]
        logger.debug('Arrival distribution config: {}'.format(dist_config))

        # Load Pricing Action Space Configuration
        pricing_rules_path = os.path.join(os.path.dirname(__file__),
                                          "config", "pricing_rules.json")
        with open(pricing_rules_path, 'r') as target:
            pricing_rules = json.load(target)

        # Try loading user config
        user_pricing_rulespath = os.path.join(expanduser(
            "~"), ".config/flai/seatsmart/config", "pricing_rules.json")
        if os.path.exists(user_pricing_rulespath):
            try:
                with open(user_pricing_rulespath, 'r') as target:
                    user_pricing_rules = json.load(target)
                pricing_rules.update(user_pricing_rules)

                logger.debug('[{}] user config loaded: {}'.format(
                    self.__class__.__name__, user_pricing_rulespath))
            except Exception as error:
                logger.exception('User defined pricing rules is not loaded. Skipping file present at {} due to following error : {}'.format(
                    user_pricing_rulespath, error))
        pricing_rules = pricing_rules[self.mode_config['pricing_rules']]
        logger.debug('Pricing rule config: {}'.format(pricing_rules))
        # After loading all the configs, it is time to load the objects
        # with these configs.

        self._load_theme(theme_config)

        # Load Game Mode
        self.seat_map_x = 30
        self.seat_map_y = 100
        self.seat_pad = 5
        self.aisle_pad = 10

        # Create stripe lists
        self.all_sprites_list = pygame.sprite.Group()

        # Initialize Seatmap
        # Load the seat_map configuration for the game
        self.seat_map = SeatMap(layout_config, pricing_rules=pricing_rules)

        # Create customer
        # Dynamically get set of customer class names that are available
        # by default in flai.
        mod = importlib.import_module("flai.envs.seatsmart.customers")
        _default_class = set(
            [m for m in mod.__dict__.keys() if 'Customer' in m])

        if self.mode_config['customer'] in _default_class:
            # lazy load
            class_ = getattr(mod, self.mode_config['customer'])
        else:
            # Plugin file must be present
            class_plugin_path = os.path.join(expanduser(
                "~"), ".config/flai/seatsmart", "customers.py")
            assert os.path.exists(class_plugin_path), "Plugin file missing for {} customer type. Plugin file location: {}".format(
                self.mode_config['customer'], class_plugin_path)

            # Plugin class must be present
            spec = importlib.util.spec_from_file_location(
                "customers", class_plugin_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            assert self.mode_config['customer'] in set(mod.__dict__.keys(
            )), "Plugin class missing for {} customer type. Plugin file location:{}".format(self.mode_config['customer'], class_plugin_path)

            # lazy load
            class_ = getattr(mod, self.mode_config['customer'])
            from flai.envs.seatsmart.customers import BaseCustomer
            assert issubclass(class_, BaseCustomer), "Class {} is not built on BaseCustomer class".format(
                self.mode_config['customer'])

        # Check if config is required as an argument to the class
        if 'config' in set(inspect.getfullargspec(class_.__init__).args):
            customer_parameterspath = os.path.join(os.path.dirname(__file__),
                                                   "config", "customer_parameters.json")
            with open(customer_parameterspath, 'r') as target:
                customer_parameters = json.load(target)

            # Try loading user config
            user_customer_parameterspath = os.path.join(expanduser(
                "~"), ".config/flai/seatsmart/config", "customer_parameters.json")
            if os.path.exists(user_customer_parameterspath):
                try:
                    with open(user_customer_parameterspath, 'r') as target:
                        user_customer_parameters = json.load(target)
                    customer_parameters.update(user_customer_parameters)

                    logger.debug('User config loaded: {}'.format(
                        user_customer_parameterspath))
                except Exception as error:
                    logger.exception('User defined customer parameters is not loaded. Skipping file present at {} due to following error : {}'.format(
                        user_customer_parameterspath, error))
            self.seat_customer = class_(
                config=customer_parameters[self.mode_config['customer']])
            logger.debug('Customer config: {}'.format(customer_parameters))
        else:
            self.seat_customer = class_()

        # Spawn a new customer with a groupsize
        self.seat_customer.spawn()
        logger.info('New customer spawned')

        # Create Episode
        self.game_episode = Episode(demand=self.mode_config['demand'],
                                    distribution=dist_config)

        # Create Metrics Tracker that tracks the episode and state of seatmap
        self.game_tracker = MetricsTracker(self.seat_map, self.game_episode)

        # Actions
        self.price_change = 0
        self.sell_seats = 0
        self.customer_awake = False

        self.action_space = ActionSpace(upper=self.seat_map.max_price,
                                        lower=self.seat_map.min_price)

        self.observation_space['analyst'] = ObservationSpace()

        # Render the frame
        self.render_frame()

    def _load_theme(self, theme_config):

        # Colors used in the
        _colors = theme_config['colors']
        self.COLOR_ZONE3 = _colors['COLOR_ZONE3']
        self.COLOR_ZONE2 = _colors['COLOR_ZONE2']
        self.COLOR_ZONE1 = _colors['COLOR_ZONE1']
        self.COLOR_DEEPAIR_RED = _colors['COLOR_DEEPAIR_RED']
        self.COLOR_DEEPAIR_GREEN = _colors['COLOR_DEEPAIR_GREEN']
        self.COLOR_LIGHT_FONT = _colors['COLOR_LIGHT_FONT']
        self.COLOR_DARK_FONT = _colors['COLOR_DARK_FONT']
        self.COLOR_WHITE = _colors['COLOR_WHITE']
        self.COLOR_BLACK = _colors['COLOR_BLACK']

        # Images used the game
        _images = theme_config['images']
        self.ZONE3_AVAIL_IMG = pygame.image.load(
            get_abs_path(_images['ZONE3_AVAIL_IMG']))
        self.ZONE3_TAKEN_IMG = pygame.image.load(
            get_abs_path(_images['ZONE3_TAKEN_IMG']))
        self.ZONE2_AVAIL_IMG = pygame.image.load(
            get_abs_path(_images['ZONE2_AVAIL_IMG']))
        self.ZONE2_TAKEN_IMG = pygame.image.load(
            get_abs_path(_images['ZONE2_TAKEN_IMG']))
        self.ZONE1_AVAIL_IMG = pygame.image.load(
            get_abs_path(_images['ZONE1_AVAIL_IMG']))
        self.ZONE1_TAKEN_IMG = pygame.image.load(
            get_abs_path(_images['ZONE1_TAKEN_IMG']))
        self.BLOCKED_SEAT_IMG = pygame.image.load(
            get_abs_path(_images['BLOCKED_SEAT_IMG']))
        self.CUST_AWAKE_IMG = pygame.image.load(
            get_abs_path(_images['CUST_AWAKE_IMG']))
        self.CUST_SLEEP_IMG = pygame.image.load(
            get_abs_path(_images['CUST_SLEEP_IMG']))
        self.BACKGROUND_IMG = pygame.image.load(
            get_abs_path(_images['BACKGROUND_IMG']))

        # Fonts used in the game
        _fonts = theme_config['fonts']
        self.TITLE_FONT = pygame.font.Font(
            get_abs_path(_fonts['TITLE_FONT']),
            _fonts['TITLE_FONT_SIZE'])
        self.HEADING_FONT = pygame.font.Font(
            get_abs_path(_fonts['HEADING_FONT']),
            _fonts['HEADING_FONT_SIZE'])
        self.STAT_LABEL_FONT = pygame.font.Font(
            get_abs_path(_fonts['STAT_LABEL_FONT']),
            _fonts['STAT_LABEL_FONT_SIZE'])
        self.STAT_FONT = pygame.font.Font(
            get_abs_path(_fonts['STAT_FONT']),
            _fonts['STAT_FONT_SIZE'])
        self.FOOTNOTE_FONT = pygame.font.Font(
            get_abs_path(_fonts['FOOTNOTE_FONT']),
            _fonts['FOOTNOTE_FONT_SIZE'])

    def render_graph(self):

        x = self.game_tracker.seats_sold_hist.time_values
        y = self.game_tracker.seats_sold_hist.metric_values
        x_f = self.game_tracker.seats_sold_fcst.time_values
        y_f = self.game_tracker.seats_sold_fcst.metric_values

        fig = plt.figure(figsize=(3, 2))
        canvas = agg.FigureCanvasAgg(fig)
        fig.tight_layout()
        fig.patch.set_facecolor('blue')
        fig.patch.set_alpha(0)

        ax = fig.add_subplot(111)
        ax.patch.set_alpha(0.3)
        ax.yaxis.tick_right()
        plt.subplots_adjust(right=0.8)

        axes = plt.gca()
        axes.set_xlim([365, 0])
        axes.set_ylim([0, 200])

        ax.plot(x, y, linewidth=1, linestyle='-', color='#1EA896')
        if len(x) > 0:
            ax.plot(x[0], y[0], marker='o', markersize=10, color='#1EA896')
            ax.text(x[0]+40, y[0]+10, str(int(y[0])))
        ax.plot(x_f, y_f, linewidth=1, linestyle='-.', color='#1EA896')

        canvas.draw()
        renderer = canvas.get_renderer()

        raw_data = renderer.tostring_argb()
        size = canvas.get_width_height()
        plt.close('all')

        graph_image = pygame.image.fromstring(raw_data, size, "ARGB")
        graph_sprite = SimpleImage(graph_image)
        graph_sprite.rect.x = 700
        graph_sprite.rect.y = 330
        self.all_sprites_list.add(graph_sprite)

    def render_clock(self):
        clock_sprite = Label("TIME TO DEPARTURE",
                             self.COLOR_DARK_FONT, self.STAT_LABEL_FONT)
        clock_sprite.rect.x = 600
        clock_sprite.rect.y = 540
        self.all_sprites_list.add(clock_sprite)

        _days = max(round((52 - self.game_episode.clock)*7, 1), 0)

        metric = Stat(str(_days), self.COLOR_DARK_FONT,
                      self.STAT_FONT, self.COLOR_DEEPAIR_GREEN)
        metric.rect.x = clock_sprite.rect.x + clock_sprite.rect.w + 10
        metric.rect.y = clock_sprite.rect.y + (
            clock_sprite.rect.h - metric.rect.h)/2
        self.all_sprites_list.add(metric)

    def render_strategy(self):
        strategy_title = Label(
            "STRATEGY", self.COLOR_DARK_FONT, self.HEADING_FONT)
        strategy_title.rect.x = 600
        strategy_title.rect.y = 300
        self.all_sprites_list.add(strategy_title)

        price_sprite = Label("PRICE", self.COLOR_DARK_FONT,
                             self.STAT_LABEL_FONT)
        price_sprite.rect.x = strategy_title.rect.x
        price_sprite.rect.y = strategy_title.rect.y + 50
        self.all_sprites_list.add(price_sprite)

        rows = ['ZONE 1', 'ZONE 2', 'ZONE 3']
        for r, row in enumerate(rows):
            metric = self.seat_map.price[r]
            if r == 0:
                metric_bg_color = self.COLOR_ZONE1
                metric_font_color = self.COLOR_DARK_FONT
            elif r == 1:
                metric_bg_color = self.COLOR_ZONE2
                metric_font_color = self.COLOR_LIGHT_FONT
            else:
                metric_bg_color = self.COLOR_ZONE3
                metric_font_color = self.COLOR_LIGHT_FONT
            x_sprite = Stat(str(metric), metric_font_color,
                            self.STAT_FONT, metric_bg_color)
            x_sprite.rect.x = strategy_title.rect.x
            x_sprite.rect.y = strategy_title.rect.y + 50 + 40 + 50*r
            self.all_sprites_list.add(x_sprite)

    def render_context(self):
        context_title = Label(
            "CONTEXT", self.COLOR_DARK_FONT, self.HEADING_FONT)
        context_title.rect.x = 140
        context_title.rect.y = 300
        self.all_sprites_list.add(context_title)

        cols = ['AVAIL', 'SOLD', 'REV']
        for c, col in enumerate(cols):
            x_sprite = Label(col, self.COLOR_DARK_FONT, self.STAT_LABEL_FONT)
            x_sprite.rect.x = context_title.rect.x + 110*c
            x_sprite.rect.y = context_title.rect.y + 50
            self.all_sprites_list.add(x_sprite)

        rows = ['ZONE 1', 'ZONE 2', 'ZONE 3', 'TICKET']
        for r, row in enumerate(rows):

            if r == 0:
                metric_bg_color = self.COLOR_ZONE1
                metric_font_color = self.COLOR_DARK_FONT
            elif r == 1:
                metric_bg_color = self.COLOR_ZONE2
                metric_font_color = self.COLOR_LIGHT_FONT
            elif r == 2:
                metric_bg_color = self.COLOR_ZONE3
                metric_font_color = self.COLOR_LIGHT_FONT
            else:
                metric_bg_color = self.COLOR_DEEPAIR_GREEN
                metric_font_color = self.COLOR_DARK_FONT

            r_sprite = Label(row, self.COLOR_DARK_FONT, self.STAT_LABEL_FONT)
            r_sprite.rect.x = context_title.rect.x - r_sprite.rect.w - 10
            r_sprite.rect.y = context_title.rect.y + 50 + 40 + 50*r
            self.all_sprites_list.add(r_sprite)

            for c, col in enumerate(cols):
                if c == 0:
                    if r < 3:
                        metric = self.seat_map.availability[r]
                    else:
                        metric = self.seat_map.ticket_availability
                elif c == 1:
                    if r < 3:
                        metric = self.seat_map.sold[r]
                    else:
                        metric = self.seat_map.ticket_sold
                else:
                    if r < 3:
                        metric = self.seat_map.revenue[r]
                    else:
                        metric = self.seat_map.ticket_revenue
                x_sprite = Stat(str(metric), metric_font_color,
                                self.STAT_FONT, metric_bg_color)
                x_sprite.rect.x = context_title.rect.x + 110*c
                x_sprite.rect.y = r_sprite.rect.y - (
                    x_sprite.rect.h - r_sprite.rect.h)/2
                self.all_sprites_list.add(x_sprite)

    def render_header(self):
        title = Label("SEAT.SMART", self.COLOR_DEEPAIR_RED, self.TITLE_FONT)
        title.rect.x = 30
        title.rect.y = 25
        self.all_sprites_list.add(title)

        score = Label(
            str(sum(self.seat_map.revenue)),
            self.COLOR_DEEPAIR_GREEN, self.HEADING_FONT)
        score.rect.x = 900
        score.rect.y = 25
        self.all_sprites_list.add(score)

        score_label = Label(
            "TOTAL SCORE: ", self.COLOR_DARK_FONT, self.HEADING_FONT)
        score_label.rect.x = score.rect.x - score_label.rect.w - 10
        score_label.rect.y = score.rect.y + (
            score.rect.h - score_label.rect.h)/2
        self.all_sprites_list.add(score_label)

    def render_seat_map(self):

        for seat in self.seat_map.seats:
            seat_sprite = SeatSprite()

            seat_sprite.rect.x = self.seat_map_x + (
                seat_sprite.rect.w + self.seat_pad) * seat.row
            seat_sprite.rect.y = self.seat_map_y + (
                seat_sprite.rect.h + self.seat_pad) * seat.col

            if seat.col > 2:
                seat_sprite.rect.y += self.aisle_pad

            if seat.blocked or seat.ghost:
                seat_sprite.set_image(self.BLOCKED_SEAT_IMG)
            else:
                if seat.zone_index == 2:
                    if seat.available:
                        seat_sprite.set_image(self.ZONE3_AVAIL_IMG)
                    else:
                        seat_sprite.set_image(self.ZONE3_TAKEN_IMG)
                elif seat.zone_index == 1:
                    if seat.available:
                        seat_sprite.set_image(self.ZONE2_AVAIL_IMG)
                    else:
                        seat_sprite.set_image(self.ZONE2_TAKEN_IMG)
                else:
                    if seat.available:
                        seat_sprite.set_image(self.ZONE1_AVAIL_IMG)
                    else:
                        seat_sprite.set_image(self.ZONE1_TAKEN_IMG)
            self.all_sprites_list.add(seat_sprite)
        seat_map_name = Label(self.mode_config['seat_map_layout'],
                              self.COLOR_DARK_FONT, self.FOOTNOTE_FONT)
        seat_map_name.rect.x = self.seat_map_x
        seat_map_name.rect.y = self.seat_map_y\
            + (seat_sprite.rect.h + self.seat_pad) * self.seat_map.num_cols\
            + self.aisle_pad + 10
        self.all_sprites_list.add(seat_map_name)

    def render_customer(self):
        customer = SimpleImage(self.CUST_SLEEP_IMG)
        customer.rect.x = 350
        customer.rect.y = 25
        if self.customer_awake:
            customer.rerender(self.CUST_AWAKE_IMG)
        self.all_sprites_list.add(customer)

    def transaction(self):

        groupsize = self.seat_customer.groupsize

        if (self.seat_map.ticket_availability >= groupsize)\
                and (self.game_episode.status):
            # First Sell a Ticket to the group
            ticket_price = np_random.rng.randint(500, 1000)
            for _ in range(groupsize):
                self.seat_map.sell_ticket(ticket_price)

            # Default Oberserver is customer
            observation = self.seat_map.observe(observer='customer')
            logger.debug('[{}] {} observing {}'.format(
                self.__class__.__name__, 'customer', observation))
            logger.info('Price offered {}'.format(self.seat_map.price))

            action_list = self.seat_customer.action(observation)
            for action in action_list:
                if not (action is None):
                    selected_row = action[0]
                    selected_col = action[1]
                    self.seat_map.sell_seat(selected_row, selected_col)
                else:
                    logger.info('Customer did not purchase any seat')
            self.game_episode.new_arrival()
            # Spawn a new customer with a groupsize
            self.seat_customer.spawn()
            logger.info('New customer spawned')
        else:
            # GAME OVER
            logger.info('Game Over')
            self.game_over = True

    def process_events_auto(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
        return False

    def process_events(self):
        """ Process all of the events. Return a "True" if we need
            to close the window.
        """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.price_change = -1
                if event.key == pygame.K_UP:
                    self.price_change = 1
                if event.key == pygame.K_SPACE:
                    if event.mod and pygame.KMOD_SHIFT:
                        pass
                    else:
                        self.customer_awake = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    if event.mod and pygame.KMOD_SHIFT:
                        self.sell_seats = 30
                        self.customer_awake = False
                    else:
                        self.sell_seats = 1
                        self.customer_awake = False
                if event.key == pygame.K_RETURN and self.game_over:
                    self.game_over = False
                    self.__init__()
        return False

    def run_logic(self):
        """
        This method is run each time through the frame. It
        updates game state if user has taken any action.
        """
        if not self.game_over:
            if abs(self.price_change) > 0:
                self.seat_map.change_price(self.price_change)
                self.price_change = 0

            if self.sell_seats > 0:
                self.transaction()
                self.game_tracker.update_metrics()
                self.sell_seats -= 1

            self.render_frame()

    def kill_sprites(self):
        for sprite in self.all_sprites_list:
            sprite.kill()

    def render_frame(self):
        self.kill_sprites()
        self.render_header()
        self.render_customer()
        self.render_seat_map()
        self.render_context()
        self.render_strategy()
        self.render_clock()
        self.render_graph()

    def display_frame(self, screen):
        """ Display everything to the screen for the game. """

        screen.fill(self.COLOR_WHITE)

        screen.blit(self.BACKGROUND_IMG, (0, 0))

        if self.game_over:
            game_over_sprite = Message(
                "GAME OVER", self.TITLE_FONT, self.COLOR_DEEPAIR_RED)

            game_over_sprite.rect.x = screen.get_width()/2 \
                - game_over_sprite.rect.w/2

            game_over_sprite.rect.y = screen.get_height()/2 \
                - game_over_sprite.rect.h/2

            self.all_sprites_list.add(game_over_sprite)
            self.all_sprites_list.draw(screen)

        if not self.game_over:
            self.all_sprites_list.draw(screen)

        pygame.display.flip()

    def observe(self, observer='analyst'):
        """
        """
        if observer == 'analyst':
            # Aggregate all the observations
            # seatmap observations
            seatmap_observations = self.seat_map.observe(observer=observer)
            self.observation_space[observer].__dict__.update(
                seatmap_observations.__dict__)
            del seatmap_observations

            # episode observations
            episode_observations = self.game_episode.observe(observer=observer)
            self.observation_space[observer].__dict__.update(
                episode_observations.__dict__)
            del episode_observations

            # customer observations
            customer_observations = self.seat_customer.observe(
                observer=observer)
            self.observation_space[observer].__dict__.update(
                customer_observations.__dict__)
            del customer_observations

            logger.debug('[{}] {} observing {}'.format(
                self.__class__.__name__, observer, self.observation_space[observer]))

            return self.observation_space[observer]
        else:
            logger.error('Observer {} not valid'.format(observer))
            return None

    @property
    def score(self):
        return sum(self.seat_map.revenue)

    def act(self, action):
        """
        """
        if (not self.game_over):
            if (action in self.action_space):
                # perform action
                self.seat_map.price = list(action)
                self.transaction()
                self.game_tracker.update_metrics()

            else:

                # Catching correct exception
                assert ((np.diff(action) >= 0).all()
                        ), 'Prices must be in increasing order'

                assert (np.array(action).shape == self.action_space.upper.shape), 'Action shape is invalid. Expected shape  is {} but given {}'.format(
                    self.action_space.upper.shape, np.array(action).shape)

                assert((self.action_space.upper >= np.array(action)).all(
                )), 'Action taken is above the upper bound of {}. TIP: You can use action_space.valid() to clip out of bound actions'.format(self.action_space.upper)

                assert((self.action_space.lower <= np.array(action)).all(
                )), 'Action taken is below the lower bound of {}. TIP: You can use action_space.valid() to clip out of bound actions'.format(self.action_space.lower)

            if not self.game_over:
                self.game_over = not ((self.seat_map.ticket_availability > 0)
                                      and (self.game_episode.status))
            return self.game_over
        else:
            # Give warning
            return True
