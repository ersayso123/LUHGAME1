"""Career mode: fame tiers, courts and crews, cash, recruiting, upgrades and saving."""
import json
import random
from pathlib import Path

from . import settings as S
from .attributes import ATTR_ORDER, max_level, upgrade_cost
from .player import Player

# One tier per court. You earn fame at a court to unlock its boss crew;
# beating the boss moves you up a tier and opens the next court.
TIERS = [
    {"title": "Nobody", "court": "Rusty Rim Park", "base": 36, "boss_fame": 40,
     "crews": ["Corner Kids", "Rec League Rejects", "The Rust Kings"]},
    {"title": "Local", "court": "Southside Blacktop", "base": 48, "boss_fame": 130,
     "crews": ["Southside Swingers", "Block Party", "Blacktop Bullies"]},
    {"title": "Neighborhood Name", "court": "Pier Courts", "base": 60, "boss_fame": 280,
     "crews": ["Salt Water Squad", "Dock Boyz", "The Tide"]},
    {"title": "City Legend", "court": "Downtown Cage", "base": 72, "boss_fame": 480,
     "crews": ["Chain Link Gang", "Night Shift", "Cage Kings"]},
    {"title": "City Legend", "court": "The Throne", "base": 84, "boss_fame": 750,
     "crews": ["Crown Chasers", "Royal Court", "The Last King"]},
]
KING_TITLE = "King of the Courts"
CREW_OFFSETS = [0, 3, 7]  # regular, tougher, boss

FIRST_NAMES = ["Tay", "Dre", "Mook", "Jojo", "Kev", "Rell", "Dom", "Zay", "Bishop", "Ty",
               "Nate", "Juice", "Smoke", "Pooh", "Ant", "Deuce", "Rico", "Moe", "Stretch",
               "Quan", "Boogie", "Skip", "Hops", "Jamal", "Beans", "Cheese", "Ronnie"]
PREFIXES = ["Lil", "Big", "Young", "Slim", "Sweet", "Downtown", "Air", "Pistol", "Easy"]


def random_name(rng):
    first = rng.choice(FIRST_NAMES)
    return f"{rng.choice(PREFIXES)} {first}" if rng.random() < 0.5 else first


def generate_player(rng, base, name=None):
    stats = {s: max(20, min(S.STAT_MAX, base + rng.randint(-8, 8))) for s in S.STAT_NAMES}
    main = rng.choice(ATTR_ORDER)
    sec = rng.choice([a for a in ATTR_ORDER if a != main])
    main_lvl = max(0, min(S.MAIN_MAX_LEVEL, round((base - 30) / 14)))
    sec_lvl = 0 if base < 50 else max(0, min(S.SECONDARY_MAX_LEVEL, (base - 44) // 14))
    return Player(name or random_name(rng), rng.randint(0, 55), stats,
                  main if main_lvl else None, main_lvl, sec if sec_lvl else None, sec_lvl)


def crew_players(court_i, crew_i):
    """Crews are the same every time you visit (seeded by court + crew)."""
    rng = random.Random(f"{TIERS[court_i]['court']}|{TIERS[court_i]['crews'][crew_i]}")
    base = TIERS[court_i]["base"] + CREW_OFFSETS[crew_i]
    return [generate_player(rng, base) for _ in range(3)]


def team_overall(players):
    return round(sum(p.overall() for p in players) / len(players))


class Career:
    def __init__(self, me, crew, cash=100, fame=0, tier=0, beaten=None,
                 champion=False, starters=None):
        self.me = me
        self.crew = crew
        self.cash = cash
        self.fame = fame
        self.tier = tier                  # highest court unlocked (0..4)
        self.beaten = set(beaten or [])   # "court:crew" ids
        self.champion = champion
        self.starters = list(starters) if starters else [0, 1]

    # ---- status --------------------------------------------------------
    @property
    def title(self):
        return KING_TITLE if self.champion else TIERS[self.tier]["title"]

    def unlocked_courts(self):
        return list(range(self.tier + 1))

    def boss_unlocked(self, court_i):
        return self.fame >= TIERS[court_i]["boss_fame"]

    def crews_for(self, court_i):
        out = []
        for crew_i, name in enumerate(TIERS[court_i]["crews"]):
            players = crew_players(court_i, crew_i)
            out.append({"id": f"{court_i}:{crew_i}", "court": court_i, "name": name,
                        "players": players, "boss": crew_i == 2,
                        "ovr": team_overall(players),
                        "beaten": f"{court_i}:{crew_i}" in self.beaten})
        return out

    def lineup(self):
        return [self.me] + [self.crew[i] for i in self.starters]

    def secondary_unlocked(self):
        return self.tier >= S.SECONDARY_UNLOCK_TIER or self.champion

    # ---- results -------------------------------------------------------
    def apply_result(self, court_i, crew_id, is_boss, won, margin=0, bet=0, mult=1.0):
        """Give out fame and cash for a game. The bet was already paid before tip-off."""
        r = {"fame": 0, "cash": 0, "bet_win": 0, "tier_up": False, "crowned": False}
        if won:
            r["fame"] = 12 + 6 * court_i + margin // 2
            r["cash"] = 60 + 40 * court_i
            if is_boss:
                r["fame"] += 40 + 10 * court_i
                r["cash"] += 200 + 150 * court_i
                if court_i == self.tier and self.tier < len(TIERS) - 1:
                    self.tier += 1
                    r["tier_up"] = True
                elif court_i == len(TIERS) - 1 and not self.champion:
                    self.champion = True
                    r["crowned"] = True
            self.beaten.add(crew_id)
            if bet:
                r["bet_win"] = round(bet * mult)
        else:
            r["fame"] = 3
            r["cash"] = 10
        self.fame += r["fame"]
        self.cash += r["cash"] + r["bet_win"]
        return r

    # ---- spending ------------------------------------------------------
    @staticmethod
    def stat_cost(value):
        return int(10 + value * 1.5)

    def buy_stat(self, stat):
        v = self.me.stats[stat]
        cost = self.stat_cost(v)
        if v >= S.STAT_MAX or self.cash < cost:
            return False
        self.cash -= cost
        self.me.stats[stat] = min(S.STAT_MAX, v + S.STAT_STEP)
        return True

    def attr_cost(self, slot):
        lvl = self.me.main_lvl if slot == "main" else self.me.sec_lvl
        return upgrade_cost(slot, lvl)

    def buy_attr(self, slot, key=None):
        """Returns (ok, message)."""
        me = self.me
        if slot == "sec":
            if not self.secondary_unlocked():
                return False, "Secondary unlocks at Local fame."
            if me.sec_lvl == 0:
                if key is None or key == me.main_attr:
                    return False, "Pick a Secondary different from your Main."
            lvl = me.sec_lvl
        else:
            lvl = me.main_lvl
        if lvl >= max_level(slot):
            return False, "Already maxed."
        cost = upgrade_cost(slot, lvl)
        if self.cash < cost:
            return False, f"Need ${cost}."
        self.cash -= cost
        if slot == "main":
            me.main_lvl += 1
        else:
            if me.sec_lvl == 0:
                me.sec_attr = key
            me.sec_lvl += 1
        return True, "Upgraded!"

    @staticmethod
    def recruit_cost(player):
        return player.overall() * 4

    def recruit(self, player):
        cost = self.recruit_cost(player)
        if len(self.crew) >= S.CREW_MAX or self.cash < cost:
            return False
        self.cash -= cost
        self.crew.append(player.copy())
        return True

    def release(self, i):
        if len(self.crew) <= 2:
            return False
        del self.crew[i]
        self.starters = [s - (s > i) for s in self.starters if s != i]
        for j in range(len(self.crew)):
            if len(self.starters) >= 2:
                break
            if j not in self.starters:
                self.starters.append(j)
        return True

    def toggle_starter(self, i):
        if i in self.starters:
            return
        self.starters = [self.starters[-1], i]

    # ---- saving --------------------------------------------------------
    def to_dict(self):
        return {"me": self.me.to_dict(), "crew": [p.to_dict() for p in self.crew],
                "cash": self.cash, "fame": self.fame, "tier": self.tier,
                "beaten": sorted(self.beaten), "champion": self.champion,
                "starters": self.starters}

    @classmethod
    def from_dict(cls, d):
        return cls(Player.from_dict(d["me"]), [Player.from_dict(p) for p in d["crew"]],
                   d["cash"], d["fame"], d["tier"], d["beaten"], d["champion"], d["starters"])

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text()))


def new_career(name, main_attr, rng=None):
    rng = rng or random.Random()
    me = Player(name, rng.randint(0, 55), {s: 40 for s in S.STAT_NAMES}, main_attr, 1)
    crew = [generate_player(rng, 32) for _ in range(2)]
    return Career(me, crew)
