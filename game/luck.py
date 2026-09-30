"""Luck: the slot-style Luck Machine, Mystery Baller packs and match wagers. In-game cash only."""
from .career import TIERS, generate_player

SYMBOLS = ["BRICK", "BALL", "SHOE", "CASH", "CROWN"]
WEIGHTS = [35, 25, 20, 13, 7]
BET_OPTIONS = [10, 25, 50, 100, 250, 500]


def spin(rng):
    return [rng.choices(SYMBOLS, WEIGHTS)[0] for _ in range(3)]


def payout_multiplier(reels):
    """3 crowns 20x, any other 3 of a kind 5x, a pair of CASH/CROWN 2x,
    any other pair (not bricks) gets your bet back, otherwise nothing."""
    counts = {s: reels.count(s) for s in set(reels)}
    sym, n = max(counts.items(), key=lambda kv: kv[1])
    if n == 3:
        return 20 if sym == "CROWN" else 5
    if n == 2:
        if sym in ("CASH", "CROWN"):
            return 2
        if sym != "BRICK":
            return 1
    return 0


def expected_return():
    """Average cash back per $1 bet (under 1 = the machine wins over time)."""
    total = sum(WEIGHTS)
    p = {s: w / total for s, w in zip(SYMBOLS, WEIGHTS)}
    ev = 0.0
    for a in SYMBOLS:
        for b in SYMBOLS:
            for c in SYMBOLS:
                ev += p[a] * p[b] * p[c] * payout_multiplier([a, b, c])
    return ev


def play_slots(career, bet, rng):
    """Returns (reels, winnings) or None if the bet isn't allowed."""
    if bet <= 0 or bet > career.cash:
        return None
    career.cash -= bet
    reels = spin(rng)
    win = bet * payout_multiplier(reels)
    career.cash += win
    return reels, win


# Mystery Baller: (rarity, chance %, rating offset from the current tier's level)
RARITIES = [("Bum", 40, -14), ("Solid", 35, -2), ("Baller", 20, 8), ("Legend", 5, 18)]


def mystery_cost(tier):
    return 150 + 120 * tier


def roll_mystery(career, rng):
    """Pay for a random recruit. Returns (rarity, player) or None if not allowed."""
    from . import settings as S
    cost = mystery_cost(career.tier)
    if career.cash < cost or len(career.crew) >= S.CREW_MAX:
        return None
    career.cash -= cost
    rarity, _, offset = rng.choices(RARITIES, [r[1] for r in RARITIES])[0]
    player = generate_player(rng, TIERS[career.tier]["base"] + offset)
    career.crew.append(player)
    return rarity, player


def wager_multiplier(team_ovr, opp_ovr):
    """Payout on a won bet: bigger against a tougher crew."""
    return round(max(1.2, min(4.0, 1.6 + (opp_ovr - team_ovr) / 12)), 1)


def place_bet(career, bet):
    if bet < 0 or bet > career.cash:
        return False
    career.cash -= bet
    return True
