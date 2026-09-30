"""Screen, court, control and balance settings. Tweak numbers here to rebalance the game."""

WIDTH, HEIGHT = 1000, 700
FPS = 60
TITLE = "Streetball Kingdom"

# Court (top-down half court, hoop at the top)
COURT_LEFT, COURT_TOP, COURT_RIGHT, COURT_BOTTOM = 100, 60, 900, 640
HOOP = (500.0, 115.0)
ARC_RADIUS = 250.0          # shots from farther than this are worth 2, inside are worth 1
PAINT_HALF_WIDTH = 80
PAINT_DEPTH = 190
CHECK_SPOT = (500.0, 450.0)

# Game rules
GAME_TO = 11
SHOT_CLOCK = 14.0

# Movement and actions
PLAYER_RADIUS = 14
BASE_SPEED = 130.0          # px/sec at 0 speed
SPEED_PER_STAT = 1.5        # extra px/sec per speed point
PASS_SPEED = 520.0
METER_TIME = 0.9            # seconds to fill the shot meter
METER_SWEET = 0.8           # where the perfect release is on the meter (0..1)
METER_WINDOW = 0.07         # half-width of the green zone
DUNK_RANGE = 80
DUNK_BASE = 0.72
LAYUP_RANGE = 70
STEAL_RANGE = 36
STEAL_BASE = 0.16
BLOCK_RANGE = 36
BLOCK_BASE = 0.10
GRAB_RADIUS = 20.0

# Attributes
MAIN_MAX_LEVEL = 5
SECONDARY_MAX_LEVEL = 3
SECONDARY_PCT = 0.5         # a Secondary attribute gets this share of the effect
SECONDARY_UNLOCK_TIER = 1   # fame tier where the Secondary slot opens (1 = Local)

# Career
CREW_MAX = 6
STAT_NAMES = ["shooting", "speed", "handles", "defense", "rebounding"]
STAT_LABELS = {"shooting": "Shooting", "speed": "Speed", "handles": "Handles",
               "defense": "Defense", "rebounding": "Rebounding"}
STAT_MAX = 99
STAT_STEP = 2

# Colors
WHITE = (240, 240, 240)
BLACK = (15, 15, 18)
GREY = (140, 140, 150)
DARK = (28, 28, 34)
GOLD = (245, 200, 60)
GREEN = (90, 210, 110)
RED = (225, 80, 70)
ORANGE = (235, 130, 40)
BLUE = (80, 150, 240)
PURPLE = (170, 110, 230)
TEAM_COLORS = [(60, 130, 235), (215, 65, 60)]
