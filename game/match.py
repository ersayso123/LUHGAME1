"""Rules and simulation for one 3v3 half-court game.

No pygame in here, so a whole game can be simulated and tested headless.
Team 0 is the player's team (slot 0 = the main guy), team 1 is the other crew.
"""
import math
import random
from dataclasses import dataclass

from . import ai
from . import settings as S
from .attributes import can_dunk, effect
from .ball import Ball
from .geometry import beyond_arc, clamp, clamp_to_court, dist, norm, shot_points


@dataclass
class Inputs:
    move: tuple = (0.0, 0.0)
    shoot_pressed: bool = False
    shoot_down: bool = False
    pass_pressed: bool = False
    move_pressed: bool = False     # K: crossover on offense, steal on defense
    switch_pressed: bool = False


@dataclass
class Intent:
    move: tuple = (0.0, 0.0)
    action: str | None = None      # shoot, pass, cross, steal, jump
    target: object = None
    quality: float = 0.0


class Actor:
    """A player on the floor during a match."""

    def __init__(self, player, team, slot):
        self.p = player
        self.team = team
        self.slot = slot
        self.x = self.y = 0.0
        self.fx, self.fy = 0.0, -1.0
        self.stun = self.cool = self.burst = self.jump = 0.0
        self.points = 0
        # AI memory
        self.think = 0.0
        self.spot = None
        self.spot_t = 0.0
        self.hold_t = 0.0

    @property
    def pos(self):
        return (self.x, self.y)

    def eff(self, key):
        return effect(self.p, key)

    def max_speed(self):
        s = S.BASE_SPEED + self.p.stats["speed"] * S.SPEED_PER_STAT
        s *= 1.0 + self.eff("speed")
        if self.burst > 0:
            s *= 1.35
        return s


class Match:
    def __init__(self, team_a, team_b, rng=None, human=True, game_to=S.GAME_TO):
        self.rng = rng or random.Random()
        self.human = human
        self.game_to = game_to
        self.actors = ([Actor(p, 0, i) for i, p in enumerate(team_a)]
                       + [Actor(p, 1, i) for i, p in enumerate(team_b)])
        self.ball = Ball()
        self.score = [0, 0]
        self.winner = None
        self.messages = []        # [text, seconds left]
        self.meter = None         # human shot meter 0..1 while charging
        self.last_release = None  # (meter value, quality) for the HUD
        self.controlled = self.team(0)[0]
        self.elapsed = 0.0
        self.setup_check(0)

    # ---- helpers -------------------------------------------------------
    def team(self, t):
        return [a for a in self.actors if a.team == t]

    @property
    def main_guy(self):
        return self.team(0)[0]

    def say(self, text, secs=1.6):
        self.messages.append([text, secs])
        self.messages = self.messages[-3:]

    def nearest_opponent(self, a, pos=None):
        pos = pos or a.pos
        best, bd = None, 1e9
        for o in self.team(1 - a.team):
            d = dist(o.pos, pos)
            if d < bd:
                best, bd = o, d
        return bd, best

    def openness(self, a):
        return self.nearest_opponent(a)[0]

    # ---- possession ----------------------------------------------------
    def setup_check(self, team):
        """Ball is checked at the top of the key to `team`."""
        self.offense = team
        self.phase = "check"
        self.phase_t = 1.0
        self.needs_clear = False
        self.shot_clock = S.SHOT_CLOCK
        self.meter = None
        spots = [S.CHECK_SPOT, (320.0, 330.0), (680.0, 330.0)]
        for a, sp in zip(self.team(team), spots):
            a.x, a.y = sp
            a.fx, a.fy = 0.0, -1.0
            a.stun = a.hold_t = 0.0
            a.spot = None
        for d, sp in zip(self.team(1 - team), spots):
            ux, uy = norm(S.HOOP[0] - sp[0], S.HOOP[1] - sp[1])
            d.x, d.y = sp[0] + ux * 40, sp[1] + uy * 40
            d.fx, d.fy = -ux, -uy
            d.stun = 0.0
            d.spot = None
        self.ball.set_held(self.team(team)[0])
        if self.human:
            self.controlled = self.team(0)[0]

    def turnover(self, new_team):
        """Live change of possession (steal, rebound, pick-off): ball must be cleared."""
        self.offense = new_team
        self.needs_clear = True
        self.shot_clock = S.SHOT_CLOCK
        self.meter = None
        for a in self.actors:
            a.hold_t = 0.0
            a.spot = None
        if self.human and new_team == 1:
            self.controlled = self.main_guy

    # ---- main loop -----------------------------------------------------
    def update(self, dt, inp=None):
        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]
        if self.phase == "over":
            return
        self.elapsed += dt
        self.phase_t -= dt
        if self.phase == "check":
            if self.phase_t <= 0:
                self.phase = "live"
            return
        if self.phase == "scored":
            if self.phase_t <= 0:
                self.setup_check(self.offense)
            return

        b = self.ball
        if b.state in ("held", "pass"):
            self.shot_clock -= dt
            if self.shot_clock <= 0:
                self.say("Shot clock violation!")
                self.setup_check(1 - self.offense)
                return

        if self.human and inp and inp.switch_pressed:
            self._switch()

        for a in self.actors:
            a.cool = max(0.0, a.cool - dt)
            a.burst = max(0.0, a.burst - dt)
            a.jump = max(0.0, a.jump - dt)
            if a.stun > 0:
                a.stun -= dt
                continue
            if self.human and a is self.controlled:
                it = self._human_intent(a, inp or Inputs(), dt)
            else:
                it = ai.decide(self, a, dt)
            self._move(a, it.move, dt)
            if it.action:
                self._act(a, it)
            if self.phase != "live":
                return

        self._separate()
        self._update_ball(dt)
        if self.phase != "live":
            return

        b = self.ball
        if (self.needs_clear and b.state == "held" and b.holder.team == self.offense
                and beyond_arc(b.holder.pos, 5)):
            self.needs_clear = False
            self.say("Cleared", 0.8)
        if self.human and b.state == "held" and b.holder.team == 0:
            self.controlled = b.holder

    def _move(self, a, move, dt):
        mx, my = move
        mag = math.hypot(mx, my)
        if mag > 1:
            mx, my = mx / mag, my / mag
        speed = a.max_speed()
        if self.ball.state == "held" and self.ball.holder is a:
            speed *= 0.92
            if a is self.controlled and self.meter is not None:
                speed *= 0.35
        a.x, a.y = clamp_to_court(a.x + mx * speed * dt, a.y + my * speed * dt)
        if mag > 0.1:
            a.fx, a.fy = norm(mx, my)

    def _separate(self):
        r2 = S.PLAYER_RADIUS * 2
        for i, a in enumerate(self.actors):
            for o in self.actors[i + 1:]:
                d = dist(a.pos, o.pos)
                if 0 < d < r2:
                    push = (r2 - d) / 2
                    ux, uy = (a.x - o.x) / d, (a.y - o.y) / d
                    a.x, a.y = clamp_to_court(a.x + ux * push, a.y + uy * push)
                    o.x, o.y = clamp_to_court(o.x - ux * push, o.y - uy * push)

    # ---- human control -------------------------------------------------
    def _switch(self):
        if self.ball.state == "held" and self.ball.holder.team == 0:
            return
        bp = (self.ball.x, self.ball.y)
        order = sorted(self.team(0), key=lambda a: dist(a.pos, bp))
        self.controlled = order[1] if order[0] is self.controlled else order[0]

    def _human_intent(self, a, inp, dt):
        it = Intent(move=inp.move)
        b = self.ball
        if b.state == "held" and b.holder is a:
            if self.meter is None and inp.shoot_pressed:
                if self.needs_clear:
                    self.say("Clear it past the arc first!", 1.0)
                elif can_dunk(a.p) and dist(a.pos, S.HOOP) <= S.DUNK_RANGE:
                    it.action = "shoot"
                else:
                    self.meter = 0.0
            elif self.meter is not None:
                self.meter += dt / S.METER_TIME
                if not inp.shoot_down or self.meter >= 1.0:
                    it.action = "shoot"
                    it.quality = self.meter_quality(a, min(self.meter, 1.0))
                    self.last_release = (min(self.meter, 1.0), it.quality)
                    self.meter = None
            if it.action is None and self.meter is None:
                if inp.pass_pressed:
                    it.action = "pass"
                    it.target = self.pick_pass_target(a, inp.move)
                elif inp.move_pressed:
                    it.action = "cross"
        else:
            self.meter = None
            if inp.move_pressed:
                it.action = "steal"
            elif inp.shoot_pressed:
                it.action = "jump"
        return it

    def meter_window(self, a):
        return S.METER_WINDOW + a.eff("meter")

    def meter_quality(self, a, m):
        """1 = perfect release, 0.5 = edge of green, negative = off timing."""
        w = self.meter_window(a)
        off = abs(m - S.METER_SWEET)
        if off <= w:
            return 1.0 - 0.5 * off / w
        return max(-1.0, -(off - w) / 0.25)

    def pick_pass_target(self, a, direction):
        mates = [m for m in self.team(a.team) if m is not a]
        dx, dy = norm(*direction)
        if dx or dy:
            def angle_score(m):
                ux, uy = norm(m.x - a.x, m.y - a.y)
                return -(ux * dx + uy * dy)
            return min(mates, key=angle_score)
        return max(mates, key=self.openness)

    # ---- actions -------------------------------------------------------
    def _act(self, a, it):
        b = self.ball
        has_ball = b.state == "held" and b.holder is a
        if it.action == "shoot" and has_ball:
            if self.needs_clear:
                return
            self.take_shot(a, it.quality)
        elif it.action == "pass" and has_ball:
            self.pass_ball(a, it.target or self.pick_pass_target(a, (0, 0)))
        elif it.action == "cross" and has_ball and a.cool <= 0:
            self.crossover(a)
        elif it.action == "steal" and a.cool <= 0 and b.state == "held" and b.holder.team != a.team:
            self.try_steal(a)
        elif it.action == "jump":
            a.jump = 0.4

    def make_chance(self, a, quality, dunk=False):
        d = dist(a.pos, S.HOOP)
        sh = a.p.stats["shooting"]
        if dunk:
            base = S.DUNK_BASE + a.eff("dunk") + (a.p.stats["speed"] - 50) / 400
        else:
            if d <= S.LAYUP_RANGE:
                base = 0.62 + a.eff("finish")
            elif d <= S.ARC_RADIUS:
                base = 0.46 - 0.10 * (d - S.LAYUP_RANGE) / (S.ARC_RADIUS - S.LAYUP_RANGE)
            else:
                base = 0.36 - 0.25 * max(0.0, d - S.ARC_RADIUS - 30) / 150 + a.eff("deep")
            base += (sh - 50) / 99 * 0.35
            base += quality * 0.16
        dd, dfd = self.nearest_opponent(a)
        if dfd and dd < 70:
            pen = (1 - dd / 70) * (0.12 + dfd.p.stats["defense"] / 99 * 0.2 + dfd.eff("contest"))
            if dunk:
                pen *= 0.4
            base -= pen
        return clamp(base, 0.02, 0.97)

    def take_shot(self, a, quality):
        d = dist(a.pos, S.HOOP)
        dunk = can_dunk(a.p) and d <= S.DUNK_RANGE
        pts = shot_points(a.pos)
        prob = self.make_chance(a, quality, dunk)
        for dfd in self.team(1 - a.team):
            dd = dist(dfd.pos, a.pos)
            if dd < S.BLOCK_RANGE and dfd.stun <= 0:
                ch = (S.BLOCK_BASE * dfd.p.stats["defense"] / 70
                      * (1.8 if dfd.jump > 0 else 1.0) * (1 - 0.5 * dd / S.BLOCK_RANGE))
                if dunk:
                    ch *= 0.4
                if pts == 2:
                    ch *= 0.6
                if self.rng.random() < ch:
                    self.say(f"BLOCKED by {dfd.p.name}!")
                    ux, uy = norm(a.x - S.HOOP[0], a.y - S.HOOP[1])
                    self.ball.set_loose(a.x, a.y, ux * 160 + self.rng.uniform(-60, 60),
                                        uy * 160 + self.rng.uniform(-60, 60), z=25)
                    return
        made = self.rng.random() < prob
        dur = 0.35 if dunk else 0.45 + d / 700
        self.ball.start_shot(a, S.HOOP, dur, made, pts, dunk)
        if dunk:
            self.say(f"{a.p.name} throws it down!" if made else "Dunk rattles out!")

    def pass_ball(self, a, target):
        a.hold_t = 0.0
        self.ball.start_pass(a, target, S.PASS_SPEED * (1 + a.eff("pass")))

    def crossover(self, a):
        a.cool = 1.3
        a.burst = 0.5
        dd, dfd = self.nearest_opponent(a)
        if dfd and dd < 50:
            ch = 0.25 + (a.p.stats["handles"] - dfd.p.stats["defense"]) / 200 + a.eff("cross")
            if self.rng.random() < clamp(ch, 0.05, 0.8):
                dfd.stun = 0.7
                self.say(f"{a.p.name} broke {dfd.p.name}'s ankles!")

    def try_steal(self, a):
        h = self.ball.holder
        if dist(a.pos, h.pos) > S.STEAL_RANGE:
            a.cool = 0.4
            return
        a.cool = 0.9
        ch = S.STEAL_BASE + (a.p.stats["defense"] - h.p.stats["handles"]) / 250 + a.eff("steal")
        if self.rng.random() < clamp(ch, 0.03, 0.6):
            self.ball.set_held(a)
            self.turnover(a.team)
            self.say(f"Stolen by {a.p.name}!")
        else:
            a.stun = 0.2

    # ---- ball ----------------------------------------------------------
    def _update_ball(self, dt):
        b = self.ball
        if b.state == "held":
            b.follow()
        elif b.state == "pass":
            b.update_pass(dt)
            for dfd in self.team(1 - b.passer.team):
                if id(dfd) in b.checked or dfd.stun > 0:
                    continue
                if dist((b.x, b.y), dfd.pos) < 16:
                    b.checked.add(id(dfd))
                    ch = (0.28 * dfd.p.stats["defense"] / 80 - b.passer.eff("pass") * 0.8
                          + dfd.eff("steal"))
                    if self.rng.random() < clamp(ch, 0.02, 0.7):
                        b.set_held(dfd)
                        self.turnover(dfd.team)
                        self.say(f"Picked off by {dfd.p.name}!")
                        return
            if dist((b.x, b.y), b.receiver.pos) < 16:
                b.set_held(b.receiver)
        elif b.state == "shot":
            if b.update_shot(dt):
                self._resolve_shot()
        elif b.state == "loose":
            b.update_loose(dt)
            if b.grab_delay <= 0 and b.z < 25:
                self._try_grab()

    def _resolve_shot(self):
        b = self.ball
        shooter = b.shooter
        if b.made:
            self.score[shooter.team] += b.points
            shooter.points += b.points
            self.say(f"{shooter.p.name} +{b.points}")
            b.set_dead(*S.HOOP)
            if self.score[shooter.team] >= self.game_to:
                self.phase = "over"
                self.winner = shooter.team
                return
            # make it take it
            self.offense = shooter.team
            self.phase = "scored"
            self.phase_t = 1.0
        else:
            ang = self.rng.uniform(0.15 * math.pi, 0.85 * math.pi)
            spd = self.rng.uniform(90, 220)
            b.set_loose(S.HOOP[0], S.HOOP[1] + 12, math.cos(ang) * spd, math.sin(ang) * spd, z=30)

    def _try_grab(self):
        b = self.ball
        cands = []
        for a in self.actors:
            if a.stun > 0:
                continue
            reach = S.GRAB_RADIUS + a.eff("reach") + (6 if a.jump > 0 else 0)
            if dist(a.pos, (b.x, b.y)) <= reach:
                w = a.p.stats["rebounding"] * (1 + a.eff("rebound"))
                cands.append((a, max(1.0, w)))
        if not cands:
            return
        total = sum(w for _, w in cands)
        r = self.rng.uniform(0, total)
        for a, w in cands:
            r -= w
            if r <= 0:
                break
        b.set_held(a)
        if a.team != self.offense:
            self.turnover(a.team)
            self.say(f"Board: {a.p.name}", 1.0)
        else:
            self.shot_clock = S.SHOT_CLOCK
            self.say(f"Offensive board: {a.p.name}", 1.0)
