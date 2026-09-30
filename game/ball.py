"""The ball: held, passed, shot, loose (rebound / block) or dead (after a make)."""
import math

from . import settings as S
from .geometry import clamp, dist


class Ball:
    def __init__(self):
        self.state = "held"
        self.holder = None
        self.x = self.y = self.z = 0.0
        self.vx = self.vy = 0.0
        # pass
        self.passer = self.receiver = None
        self.speed = 0.0
        self.checked = set()
        # shot
        self.shooter = None
        self.sx = self.sy = self.tx = self.ty = 0.0
        self.t = self.dur = 0.0
        self.made = False
        self.points = 0
        self.dunk = False
        self.peak = 0.0
        # loose
        self.grab_delay = 0.0

    def set_held(self, actor):
        self.state = "held"
        self.holder = actor
        self.passer = self.receiver = None
        self.z = 0.0
        self.follow()

    def follow(self):
        a = self.holder
        self.x = a.x + a.fx * 12
        self.y = a.y + a.fy * 12

    def start_pass(self, passer, receiver, speed):
        self.state = "pass"
        self.holder = None
        self.passer, self.receiver = passer, receiver
        self.speed = speed
        self.checked = set()
        self.z = 8.0

    def update_pass(self, dt):
        tx, ty = self.receiver.x, self.receiver.y
        d = dist((self.x, self.y), (tx, ty))
        step = self.speed * dt
        if d <= step:
            self.x, self.y = tx, ty
        else:
            self.x += (tx - self.x) / d * step
            self.y += (ty - self.y) / d * step

    def start_shot(self, shooter, target, dur, made, points, dunk):
        self.state = "shot"
        self.holder = None
        self.shooter = shooter
        self.sx, self.sy = shooter.x, shooter.y
        self.tx, self.ty = target
        self.t, self.dur = 0.0, dur
        self.made, self.points, self.dunk = made, points, dunk
        self.peak = 12.0 if dunk else 40.0 + dist((self.sx, self.sy), target) * 0.25

    def update_shot(self, dt):
        """Returns True when the ball reaches the rim."""
        self.t += dt
        f = min(1.0, self.t / self.dur)
        self.x = self.sx + (self.tx - self.sx) * f
        self.y = self.sy + (self.ty - self.sy) * f
        self.z = math.sin(math.pi * f) * self.peak + 20 * f
        return f >= 1.0

    def set_loose(self, x, y, vx, vy, z=20.0, delay=0.15):
        self.state = "loose"
        self.holder = None
        self.passer = self.receiver = None
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy = vx, vy
        self.grab_delay = delay

    def update_loose(self, dt):
        self.grab_delay = max(0.0, self.grab_delay - dt)
        self.x += self.vx * dt
        self.y += self.vy * dt
        drag = max(0.0, 1.0 - 1.6 * dt)
        self.vx *= drag
        self.vy *= drag
        self.z = max(0.0, self.z - 60 * dt)
        pad = 8
        if not S.COURT_LEFT + pad <= self.x <= S.COURT_RIGHT - pad:
            self.vx = -self.vx
        if not S.COURT_TOP + pad <= self.y <= S.COURT_BOTTOM - pad:
            self.vy = -self.vy
        self.x = clamp(self.x, S.COURT_LEFT + pad, S.COURT_RIGHT - pad)
        self.y = clamp(self.y, S.COURT_TOP + pad, S.COURT_BOTTOM - pad)

    def set_dead(self, x, y):
        self.state = "dead"
        self.holder = None
        self.x, self.y, self.z = x, y, 0.0
