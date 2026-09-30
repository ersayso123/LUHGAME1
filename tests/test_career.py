import random

import pytest

from game import luck
from game import settings as S
from game.attributes import can_dunk, effect
from game.career import TIERS, Career, crew_players, new_career
from game.player import Player


@pytest.fixture
def career():
    return new_career("Tester", "sharpshooter", random.Random(1))


def test_new_career_starts_low(career):
    assert career.title == "Nobody"
    assert career.tier == 0 and career.fame == 0
    assert career.me.main_attr == "sharpshooter" and career.me.main_lvl == 1
    assert len(career.crew) == 2 and len(career.lineup()) == 3


def test_boss_needs_fame_and_beating_it_moves_up_a_tier(career):
    assert not career.boss_unlocked(0)
    career.fame = TIERS[0]["boss_fame"]
    assert career.boss_unlocked(0)
    r = career.apply_result(0, "0:2", True, won=True)
    assert r["tier_up"] and career.tier == 1 and career.title == "Local"
    assert career.unlocked_courts() == [0, 1]


def test_beating_the_throne_crowns_you(career):
    career.tier = len(TIERS) - 1
    r = career.apply_result(career.tier, "4:2", True, won=True)
    assert r["crowned"] and career.champion and career.title == "King of the Courts"


def test_loss_still_pays_a_little(career):
    cash, fame = career.cash, career.fame
    career.apply_result(0, "0:0", False, won=False)
    assert career.cash > cash and career.fame > fame


def test_crews_are_the_same_every_visit():
    a = [p.to_dict() for p in crew_players(1, 0)]
    b = [p.to_dict() for p in crew_players(1, 0)]
    assert a == b
    assert sum(p.overall() for p in crew_players(4, 2)) > sum(p.overall() for p in crew_players(0, 0))


def test_stat_upgrade_costs_cash(career):
    career.cash = 1000
    before = career.me.stats["shooting"]
    cost = career.stat_cost(before)
    assert career.buy_stat("shooting")
    assert career.me.stats["shooting"] == before + S.STAT_STEP
    assert career.cash == 1000 - cost
    career.cash = 0
    assert not career.buy_stat("shooting")


def test_secondary_is_locked_until_local(career):
    career.cash = 10_000
    ok, _ = career.buy_attr("sec", "lockdown")
    assert not ok
    career.tier = 1
    ok, _ = career.buy_attr("sec", "sharpshooter")   # same as Main
    assert not ok
    ok, _ = career.buy_attr("sec", "lockdown")
    assert ok and career.me.sec_attr == "lockdown" and career.me.sec_lvl == 1


def test_secondary_gets_half_effect_and_caps_at_3(career):
    career.cash = 100_000
    career.tier = 1
    for _ in range(10):
        career.buy_attr("sec", "sharpshooter" if career.me.main_attr != "sharpshooter" else "lockdown")
    assert career.me.sec_lvl == S.SECONDARY_MAX_LEVEL
    for _ in range(10):
        career.buy_attr("main")
    assert career.me.main_lvl == S.MAIN_MAX_LEVEL

    main_only = Player("A", 1, main_attr="sharpshooter", main_lvl=2)
    sec_only = Player("B", 2, main_attr="lockdown", main_lvl=1, sec_attr="sharpshooter", sec_lvl=2)
    assert effect(sec_only, "deep") == pytest.approx(effect(main_only, "deep") * S.SECONDARY_PCT)


def test_dunking_needs_the_dunker_attribute():
    assert not can_dunk(Player("A", 1, main_attr="sharpshooter", main_lvl=1))
    assert can_dunk(Player("B", 1, main_attr="dunker", main_lvl=1))
    assert can_dunk(Player("C", 1, main_attr="lockdown", main_lvl=1, sec_attr="dunker", sec_lvl=1))


def test_recruit_and_release(career):
    career.cash = 10_000
    target = crew_players(0, 0)[0]
    assert career.recruit(target)
    assert len(career.crew) == 3
    career.toggle_starter(2)
    assert 2 in career.starters and len(career.starters) == 2
    assert career.release(2)
    assert len(career.starters) == 2 and all(i < len(career.crew) for i in career.starters)
    assert not career.release(0)  # need at least 2


def test_save_load_round_trip(career, tmp_path):
    career.fame, career.cash, career.tier = 99, 321, 1
    career.beaten.add("0:1")
    path = tmp_path / "save.json"
    career.save(path)
    loaded = Career.load(path)
    assert loaded.to_dict() == career.to_dict()


def test_luck_machine_payouts():
    assert luck.payout_multiplier(["CROWN"] * 3) == 20
    assert luck.payout_multiplier(["SHOE"] * 3) == 5
    assert luck.payout_multiplier(["CASH", "CASH", "BALL"]) == 2
    assert luck.payout_multiplier(["BALL", "SHOE", "BALL"]) == 1
    assert luck.payout_multiplier(["BRICK", "BRICK", "BALL"]) == 0
    assert luck.payout_multiplier(["BRICK", "BALL", "SHOE"]) == 0
    assert 0.5 < luck.expected_return() < 1.0   # the house wins over time


def test_cannot_bet_more_than_you_have(career):
    career.cash = 40
    assert luck.play_slots(career, 50, random.Random(1)) is None
    assert career.cash == 40
    assert not luck.place_bet(career, 41)
    reels, win = luck.play_slots(career, 25, random.Random(1))
    assert career.cash == 40 - 25 + win


def test_mystery_baller(career):
    career.cash = luck.mystery_cost(0) - 1
    assert luck.roll_mystery(career, random.Random(1)) is None
    career.cash = 10_000
    rarity, p = luck.roll_mystery(career, random.Random(1))
    assert rarity in [r[0] for r in luck.RARITIES]
    assert career.crew[-1] is p


def test_wager_pays_more_against_tougher_crews():
    assert luck.wager_multiplier(40, 60) > luck.wager_multiplier(40, 40) >= 1.2
