"""Buyable play-style attributes and the Main / Secondary effect math.

Every bonus the game uses comes from `effect(player, key)`, so attribute
balance lives in this one file (plus SECONDARY_PCT in settings).
"""
from . import settings as S

# Effect values are per level.
ATTRIBUTES = {
    "sharpshooter": {
        "name": "Sharpshooter",
        "desc": "Better from behind the arc and a wider green zone on the shot meter.",
        "effects": {"deep": 0.035, "meter": 0.012},
    },
    "dunker": {
        "name": "Dunker",
        "desc": "Press SPACE near the rim to dunk. Dunks are hard to block and go in more.",
        "effects": {"dunk": 0.05, "finish": 0.02},
    },
    "lockdown": {
        "name": "Lockdown",
        "desc": "Steals work more often and the shooters you guard miss more.",
        "effects": {"steal": 0.035, "contest": 0.03},
    },
    "glass": {
        "name": "Glass Cleaner",
        "desc": "Win more rebounds and grab them from farther away.",
        "effects": {"rebound": 0.15, "reach": 3.0},
    },
    "playmaker": {
        "name": "Playmaker",
        "desc": "Faster passes that get picked off less, and crossovers that break ankles.",
        "effects": {"pass": 0.08, "cross": 0.05},
    },
    "speedster": {
        "name": "Speedster",
        "desc": "Higher top speed on both ends of the court.",
        "effects": {"speed": 0.035},
    },
}
ATTR_ORDER = list(ATTRIBUTES)

MAIN_COSTS = [100, 150, 300, 550, 900]     # cost to reach level 1..5
SECONDARY_COSTS = [200, 400, 700]          # cost to reach level 1..3


def max_level(slot):
    return S.MAIN_MAX_LEVEL if slot == "main" else S.SECONDARY_MAX_LEVEL


def upgrade_cost(slot, current_level):
    """Cost to go from current_level to current_level + 1, or None if maxed."""
    costs = MAIN_COSTS if slot == "main" else SECONDARY_COSTS
    if current_level >= len(costs):
        return None
    return costs[current_level]


def effect(player, key):
    """Total bonus for `key`: full value from the Main, SECONDARY_PCT of it from the Secondary."""
    total = 0.0
    if player.main_attr:
        total += ATTRIBUTES[player.main_attr]["effects"].get(key, 0.0) * player.main_lvl
    if player.sec_attr:
        total += (ATTRIBUTES[player.sec_attr]["effects"].get(key, 0.0)
                  * player.sec_lvl * S.SECONDARY_PCT)
    return total


def can_dunk(player):
    return ((player.main_attr == "dunker" and player.main_lvl > 0)
            or (player.sec_attr == "dunker" and player.sec_lvl > 0))


def label(player):
    parts = []
    if player.main_attr and player.main_lvl:
        parts.append(f"{ATTRIBUTES[player.main_attr]['name']} {player.main_lvl}")
    if player.sec_attr and player.sec_lvl:
        parts.append(f"{ATTRIBUTES[player.sec_attr]['name']} {player.sec_lvl} (2nd)")
    return " / ".join(parts) or "No attributes"
