"""Small math helpers shared by the match rules and the AI."""
import math

from . import settings as S


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def norm(x, y):
    d = math.hypot(x, y)
    return (x / d, y / d) if d > 1e-6 else (0.0, 0.0)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def shot_points(pos):
    """2 from outside the arc, 1 from inside."""
    return 2 if dist(pos, S.HOOP) > S.ARC_RADIUS else 1


def beyond_arc(pos, margin=0.0):
    return dist(pos, S.HOOP) > S.ARC_RADIUS + margin


def clamp_to_court(x, y, pad=S.PLAYER_RADIUS):
    return (clamp(x, S.COURT_LEFT + pad, S.COURT_RIGHT - pad),
            clamp(y, S.COURT_TOP + pad, S.COURT_BOTTOM - pad))
