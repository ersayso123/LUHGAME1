"""Rule-based decisions for every player the human isn't controlling."""
import math

from . import settings as S
from .attributes import can_dunk
from .geometry import beyond_arc, clamp_to_court, dist, norm

# Where off-ball offense likes to stand
OFF_SPOTS = [(250, 190), (750, 190), (330, 360), (670, 360), (500, 420),
             (430, 170), (570, 170), (190, 110), (810, 110)]
# Spots beyond the arc, used while the ball still has to be cleared
DEEP_SPOTS = [(270, 400), (730, 400), (500, 480), (170, 230), (830, 230)]


def toward(a, pt, slow_radius=18.0):
    dx, dy = pt[0] - a.x, pt[1] - a.y
    d = math.hypot(dx, dy)
    if d < 4:
        return (0.0, 0.0)
    k = min(1.0, d / slow_radius)
    return (dx / d * k, dy / d * k)


def ai_quality(m, a):
    """How well an AI player times their release (-1..1)."""
    mean = (a.p.stats["shooting"] - 50) / 80 + a.eff("meter") * 4
    return max(-1.0, min(1.0, m.rng.gauss(mean, 0.45)))


def decide(m, a, dt):
    from .match import Intent
    b = m.ball
    if b.state == "held" and b.holder is a:
        return _with_ball(m, a, dt, Intent)
    a.hold_t = 0.0
    if b.state == "pass" and b.receiver is a:
        return Intent(move=toward(a, (b.x, b.y), 4))
    if b.state == "loose":
        return _loose(m, a, Intent)
    if b.state == "shot":
        return _rebound(m, a, Intent)
    if a.team == m.offense:
        return _off_ball(m, a, dt, Intent)
    return _defend(m, a, dt, Intent)


def _with_ball(m, a, dt, Intent):
    a.hold_t += dt
    hoop = S.HOOP
    d = dist(a.pos, hoop)
    nd, dfd = m.nearest_opponent(a)
    rnd = m.rng.random

    if m.needs_clear and not beyond_arc(a.pos, 25):
        ux, uy = norm(a.x - hoop[0], a.y - hoop[1])
        if uy < 0.2:  # never try to clear toward the baseline
            ux, uy = norm(ux, 0.6)
        tgt = clamp_to_court(hoop[0] + ux * (S.ARC_RADIUS + 60), hoop[1] + uy * (S.ARC_RADIUS + 60))
        return Intent(move=toward(a, tgt))

    a.think -= dt
    if a.think > 0:
        return Intent(move=toward(a, a.spot) if a.spot else (0.0, 0.0))
    a.think = m.rng.uniform(0.2, 0.4)

    if not m.needs_clear:
        if can_dunk(a.p) and d <= S.DUNK_RANGE:
            return Intent(action="shoot")
        if d <= S.LAYUP_RANGE and (nd > 25 or rnd() < 0.5):
            return Intent(action="shoot", quality=ai_quality(m, a))
        desperate = a.hold_t > 5 or m.shot_clock < 2.5
        open_look = nd > 42 and d < S.ARC_RADIUS + 70
        bias = a.p.stats["shooting"] / 99 + a.eff("deep") * 4
        if desperate or (open_look and rnd() < 0.25 + 0.35 * bias):
            return Intent(action="shoot", quality=ai_quality(m, a))

    mates = [t for t in m.team(a.team) if t is not a]
    best = max(mates, key=m.openness)
    if m.openness(best) > nd + 35 and rnd() < 0.35 + a.eff("pass"):
        return Intent(action="pass", target=best)
    if m.needs_clear and a.hold_t > 2.5 and rnd() < 0.3:
        return Intent(action="pass", target=best)

    if dfd and nd < 40 and a.cool <= 0 and rnd() < 0.25 + a.eff("cross"):
        return Intent(action="cross", move=toward(a, hoop))

    if m.needs_clear:
        a.spot = clamp_to_court(a.x + m.rng.uniform(-80, 80), a.y + m.rng.uniform(-20, 40))
    else:
        lateral = m.rng.uniform(-60, 60)
        if dfd and nd < 40:
            lateral += 70 if dfd.x < a.x else -70
        a.spot = clamp_to_court(hoop[0] + lateral + (a.x - hoop[0]) * 0.3, hoop[1] + 50)
    return Intent(move=toward(a, a.spot))


def _off_ball(m, a, dt, Intent):
    a.spot_t -= dt
    if a.spot is None or a.spot_t <= 0:
        spots = DEEP_SPOTS if m.needs_clear else OFF_SPOTS
        taken = [t.spot for t in m.team(a.team) if t is not a and t.spot]
        options = [s for s in spots if all(dist(s, t) > 120 for t in taken)] or spots
        a.spot = m.rng.choice(options)
        a.spot_t = m.rng.uniform(1.5, 3.5)
    return Intent(move=toward(a, a.spot))


def _defend(m, a, dt, Intent):
    man = m.team(1 - a.team)[a.slot]
    b = m.ball
    on_ball = b.state == "held" and b.holder is man
    tight = 26 if on_ball else 55
    ux, uy = norm(S.HOOP[0] - man.x, S.HOOP[1] - man.y)
    gp = (man.x + ux * tight, man.y + uy * tight)
    it = Intent(move=toward(a, gp, 10))
    if on_ball and a.cool <= 0 and dist(a.pos, man.pos) < S.STEAL_RANGE:
        rate = 0.6 * (a.p.stats["defense"] / 99 + a.eff("steal") * 3)
        if m.rng.random() < rate * dt:
            it.action = "steal"
    return it


def _rebound(m, a, Intent):
    ang = math.atan2(a.y - S.HOOP[1], a.x - S.HOOP[0])
    r = 60 if a.team != m.ball.shooter.team else 80
    spot = (S.HOOP[0] + math.cos(ang) * r, S.HOOP[1] + max(20, math.sin(ang) * r))
    it = Intent(move=toward(a, spot))
    b = m.ball
    if b.dur - b.t < 0.15 and dist(a.pos, S.HOOP) < 100:
        it.action = "jump"
    return it


def _loose(m, a, Intent):
    b = m.ball
    bp = (b.x + b.vx * 0.2, b.y + b.vy * 0.2)
    chasers = sorted(m.team(a.team), key=lambda t: dist(t.pos, bp))[:2]
    if a in chasers:
        return Intent(move=toward(a, bp, 4))
    return Intent(move=toward(a, (S.HOOP[0], S.HOOP[1] + 150)))
