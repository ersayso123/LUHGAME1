import random

from game import settings as S
from game.geometry import shot_points
from game.match import Inputs, Match
from game.player import Player


def make_team(base, attrs=(None, None, None), seed=0):
    rng = random.Random(seed)
    return [Player(f"P{i}", i, {s: base + rng.randint(-3, 3) for s in S.STAT_NAMES},
                   a, 1 if a else 0) for i, a in enumerate(attrs)]


def test_shot_points_by_distance():
    hx, hy = S.HOOP
    assert shot_points((hx, hy + 60)) == 1
    assert shot_points((hx, hy + S.ARC_RADIUS - 1)) == 1
    assert shot_points((hx, hy + S.ARC_RADIUS + 1)) == 2


def test_ai_match_finishes_with_a_winner():
    for seed in range(3):
        m = Match(make_team(45, ("sharpshooter", "dunker", "lockdown")), make_team(45, seed=seed + 1),
                  rng=random.Random(seed), human=False)
        for _ in range(60 * 60 * 15):
            m.update(1 / 60)
            if m.phase == "over":
                break
        assert m.phase == "over"
        assert max(m.score) >= S.GAME_TO
        assert m.score[m.winner] == max(m.score)


def test_human_inputs_do_not_crash():
    m = Match(make_team(50, ("dunker", None, None)), make_team(45), rng=random.Random(7), human=True)
    for f in range(60 * 60):
        t = f % 120
        inp = Inputs(move=(0.0, -1.0) if t < 60 else (1.0, 0.0),
                     shoot_pressed=t == 70, shoot_down=70 <= t < 118,
                     pass_pressed=t == 30, move_pressed=t == 10, switch_pressed=t == 100)
        m.update(1 / 60, inp)
        if m.phase == "over":
            break
    assert sum(m.score) > 0


def test_needs_clear_blocks_shots():
    m = Match(make_team(50), make_team(50), rng=random.Random(1), human=True)
    m.phase = "live"
    m.needs_clear = True
    me = m.main_guy
    me.x, me.y = S.HOOP[0], S.HOOP[1] + 100   # inside the arc
    m.ball.set_held(me)
    m.update(1 / 60, Inputs(shoot_pressed=True, shoot_down=True))
    assert m.meter is None
    assert m.ball.state == "held"


def test_perfect_release_beats_bad_release():
    m = Match(make_team(50), make_team(50), rng=random.Random(1), human=False)
    a = m.main_guy
    good = m.meter_quality(a, S.METER_SWEET)
    bad = m.meter_quality(a, 0.2)
    assert good == 1.0 and bad < 0
    assert m.make_chance(a, good) > m.make_chance(a, bad)
