"""Every screen in the game: title, create player, hub, courts, wager, match, results,
crew, training, attribute shop, luck machine and mystery baller."""
import math
import random

import pygame

from . import luck
from . import settings as S
from .attributes import ATTR_ORDER, ATTRIBUTES, can_dunk, max_level
from .career import KING_TITLE, TIERS, Career, new_career, team_overall
from .court import draw_court
from .geometry import dist
from .match import Inputs, Match

CONFIRM = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BACK = (pygame.K_ESCAPE, pygame.K_BACKSPACE)
UP = (pygame.K_UP, pygame.K_w)
DOWN = (pygame.K_DOWN, pygame.K_s)
LEFT = (pygame.K_LEFT, pygame.K_a)
RIGHT = (pygame.K_RIGHT, pygame.K_d)
RARITY_COLORS = {"Bum": S.GREY, "Solid": S.WHITE, "Baller": S.BLUE, "Legend": S.GOLD}
SYMBOL_COLORS = {"BRICK": (170, 70, 50), "BALL": S.ORANGE, "SHOE": S.WHITE,
                 "CASH": S.GREEN, "CROWN": S.GOLD}


def text(surf, font, s, pos, color=S.WHITE, center=False, right=False):
    img = font.render(str(s), True, color)
    r = img.get_rect()
    if center:
        r.center = pos
    elif right:
        r.topright = pos
    else:
        r.topleft = pos
    surf.blit(img, r)
    return r


def panel(surf, rect, color=(20, 20, 26), alpha=220, border=S.GREY):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    s.fill((*color, alpha))
    surf.blit(s, rect.topleft)
    pygame.draw.rect(surf, border, rect, 2, border_radius=6)


class Screen:
    def __init__(self, app):
        self.app = app

    @property
    def career(self):
        return self.app.career

    def f(self, size):
        return self.app.font(size)

    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, s):
        pass

    def header(self, s, subtitle=""):
        c = self.career
        s.fill((18, 20, 26))
        pygame.draw.rect(s, (30, 32, 42), (0, 0, S.WIDTH, 70))
        text(s, self.f(40), c.me.name, (24, 10), S.GOLD)
        title_color = S.GOLD if c.champion else S.WHITE
        text(s, self.f(24), f"{c.title}  |  OVR {c.me.overall()}  |  {c.me.attr_label()}",
             (24, 44), title_color)
        text(s, self.f(34), f"${c.cash}", (S.WIDTH - 24, 10), S.GREEN, right=True)
        text(s, self.f(24), f"Fame {c.fame}", (S.WIDTH - 24, 44), S.GOLD, right=True)
        if subtitle:
            text(s, self.f(48), subtitle, (S.WIDTH // 2, 110), S.WHITE, center=True)

    def footer(self, s, hint):
        text(s, self.f(22), hint, (S.WIDTH // 2, S.HEIGHT - 22), S.GREY, center=True)


class Menu:
    """Up/down + enter list. Items are (label, callback); label may be a function."""

    def __init__(self, items):
        self.items = items
        self.i = 0

    def handle(self, e):
        if e.type != pygame.KEYDOWN or not self.items:
            return
        if e.key in UP:
            self.i = (self.i - 1) % len(self.items)
        elif e.key in DOWN:
            self.i = (self.i + 1) % len(self.items)
        elif e.key in CONFIRM:
            self.items[self.i][1]()

    def draw(self, s, font, x, y, gap=46):
        for idx, (label, _) in enumerate(self.items):
            lbl = label() if callable(label) else label
            sel = idx == self.i
            text(s, font, ("> " if sel else "  ") + lbl, (x, y + idx * gap),
                 S.GOLD if sel else S.WHITE, center=True)


# ---------------------------------------------------------------- title / create
class TitleScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        items = [("New Career", lambda: app.switch(CreateScreen(app)))]
        if app.save_path.exists():
            items.insert(0, ("Continue", self.cont))
        items.append(("Quit", app.quit))
        self.menu = Menu(items)
        self.t = 0.0

    def cont(self):
        self.app.career = Career.load(self.app.save_path)
        self.app.switch(HubScreen(self.app))

    def handle(self, e):
        self.menu.handle(e)

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        draw_court(s, 0)
        panel(s, pygame.Rect(200, 150, 600, 400))
        text(s, self.f(84), "STREETBALL", (500, 220), S.ORANGE, center=True)
        text(s, self.f(84), "KINGDOM", (500, 285), S.GOLD, center=True)
        text(s, self.f(26), "Start as a nobody. Leave as the King of the Courts.",
             (500, 340), S.WHITE, center=True)
        self.menu.draw(s, self.f(40), 500, 400)
        self.footer(s, "Arrows / W S to move   Enter to pick")


class CreateScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.name = ""
        self.ai = 0

    def handle(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key == pygame.K_ESCAPE:
            self.app.switch(TitleScreen(self.app))
        elif e.key == pygame.K_LEFT:
            self.ai = (self.ai - 1) % len(ATTR_ORDER)
        elif e.key == pygame.K_RIGHT:
            self.ai = (self.ai + 1) % len(ATTR_ORDER)
        elif e.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            name = self.name.strip() or "Rookie"
            self.app.career = new_career(name, ATTR_ORDER[self.ai])
            self.app.save()
            self.app.switch(HubScreen(self.app))
        elif e.unicode and e.unicode.isprintable() and len(self.name) < 14:
            self.name += e.unicode

    def draw(self, s):
        s.fill((18, 20, 26))
        text(s, self.f(56), "Create Your Baller", (500, 80), S.GOLD, center=True)
        text(s, self.f(28), "Name (type it):", (500, 160), S.GREY, center=True)
        box = pygame.Rect(300, 185, 400, 50)
        pygame.draw.rect(s, (40, 42, 52), box, border_radius=6)
        text(s, self.f(40), self.name + "_", box.center, S.WHITE, center=True)
        text(s, self.f(28), "Main attribute (Left / Right):", (500, 290), S.GREY, center=True)
        a = ATTRIBUTES[ATTR_ORDER[self.ai]]
        text(s, self.f(48), f"<  {a['name']}  >", (500, 340), S.ORANGE, center=True)
        text(s, self.f(26), a["desc"], (500, 385), S.WHITE, center=True)
        text(s, self.f(24), "Your Main gets the full effect and goes to level 5. You start at level 1.",
             (500, 440), S.GREY, center=True)
        text(s, self.f(24), "At Local fame you can add a Secondary: 50% effect, max level 3.",
             (500, 470), S.GREY, center=True)
        text(s, self.f(24), "You start with 40 in every stat, $100, and two scrubs for a crew.",
             (500, 520), S.GREY, center=True)
        self.footer(s, "Enter to start your career   Esc to go back")


# ---------------------------------------------------------------- hub
class HubScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        a = app
        self.menu = Menu([
            ("Hit the Courts", lambda: a.switch(CourtScreen(a))),
            ("Crew", lambda: a.switch(CrewScreen(a))),
            ("Train Stats", lambda: a.switch(TrainScreen(a))),
            ("Attribute Shop", lambda: a.switch(AttrScreen(a))),
            ("Luck Machine", lambda: a.switch(SlotScreen(a))),
            ("Mystery Baller", lambda: a.switch(MysteryScreen(a))),
            ("Save & Quit to Title", self.quit),
        ])

    def quit(self):
        self.app.save()
        self.app.switch(TitleScreen(self.app))

    def handle(self, e):
        self.menu.handle(e)

    def draw(self, s):
        self.header(s)
        c = self.career
        self.menu.draw(s, self.f(38), 330, 150, 52)
        box = pygame.Rect(560, 120, 400, 420)
        panel(s, box)
        text(s, self.f(30), "THE ROAD TO THE THRONE", (box.centerx, box.top + 24), S.GOLD, center=True)
        for i, t in enumerate(TIERS):
            y = box.top + 60 + i * 62
            done = i < c.tier or (i == len(TIERS) - 1 and c.champion)
            here = i == c.tier and not c.champion
            col = S.GREEN if done else (S.WHITE if here else S.GREY)
            mark = "DONE" if done else ("YOU ARE HERE" if here else "LOCKED")
            text(s, self.f(28), t["court"], (box.left + 20, y), col)
            text(s, self.f(20), mark, (box.right - 20, y + 4), col, right=True)
            if here:
                need = t["boss_fame"]
                status = "Boss is open!" if c.fame >= need else f"Boss needs {need} fame"
                text(s, self.f(20), f"Boss: {t['crews'][2]} - {status}", (box.left + 20, y + 26), S.GREY)
        if c.champion:
            text(s, self.f(30), f"You are the {KING_TITLE}!", (box.centerx, box.bottom - 30), S.GOLD, center=True)
        self.footer(s, "Arrows to move   Enter to pick   (progress autosaves)")


# ---------------------------------------------------------------- courts / wager
class CourtScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.ci = self.career.tier
        self.sel = 0
        self.msg = ""

    def crews(self):
        return self.career.crews_for(self.ci)

    def handle(self, e):
        if e.type != pygame.KEYDOWN:
            return
        c = self.career
        if e.key in BACK:
            self.app.switch(HubScreen(self.app))
        elif e.key in LEFT:
            self.ci = max(0, self.ci - 1)
        elif e.key in RIGHT:
            self.ci = min(c.tier, self.ci + 1)
        elif e.key in UP:
            self.sel = (self.sel - 1) % 3
        elif e.key in DOWN:
            self.sel = (self.sel + 1) % 3
        elif e.key in CONFIRM:
            crew = self.crews()[self.sel]
            if crew["boss"] and not c.boss_unlocked(self.ci):
                self.msg = f"Earn {TIERS[self.ci]['boss_fame']} fame to challenge the boss."
                return
            self.app.switch(WagerScreen(self.app, self.ci, crew))

    def draw(self, s):
        c = self.career
        draw_court(s, self.ci)
        panel(s, pygame.Rect(120, 90, 760, 500))
        arrows = ("<  " if self.ci > 0 else "   ") + TIERS[self.ci]["court"] + ("  >" if self.ci < c.tier else "   ")
        text(s, self.f(52), arrows, (500, 130), S.GOLD, center=True)
        text(s, self.f(24), f"Your lineup OVR {team_overall(c.lineup())}", (500, 172), S.GREY, center=True)
        for i, crew in enumerate(self.crews()):
            y = 210 + i * 110
            sel = i == self.sel
            box = pygame.Rect(160, y, 680, 96)
            pygame.draw.rect(s, (60, 60, 75) if sel else (35, 35, 44), box, border_radius=8)
            if sel:
                pygame.draw.rect(s, S.GOLD, box, 2, border_radius=8)
            locked = crew["boss"] and not c.boss_unlocked(self.ci)
            name = ("BOSS: " if crew["boss"] else "") + crew["name"]
            text(s, self.f(34), name, (box.left + 16, y + 10), S.RED if crew["boss"] else S.WHITE)
            text(s, self.f(30), f"OVR {crew['ovr']}", (box.right - 16, y + 12), S.WHITE, right=True)
            tag = "LOCKED" if locked else ("BEATEN" if crew["beaten"] else "")
            text(s, self.f(22), tag, (box.right - 16, y + 44), S.GREY if locked else S.GREEN, right=True)
            roster = ",  ".join(f"{p.name} ({p.overall()})" for p in crew["players"])
            text(s, self.f(22), roster, (box.left + 16, y + 48), S.GREY)
        if self.msg:
            text(s, self.f(26), self.msg, (500, 560), S.RED, center=True)
        self.footer(s, "Left/Right change court   Up/Down pick crew   Enter to play   Esc back")


class WagerScreen(Screen):
    def __init__(self, app, ci, crew):
        super().__init__(app)
        self.ci, self.crew = ci, crew
        cash = self.career.cash
        self.bets = [0] + [b for b in [25, 50, 100, 250, 500, 1000] if b <= cash]
        if cash > 0 and cash not in self.bets:
            self.bets.append(cash)
        self.i = 0
        self.mult = luck.wager_multiplier(team_overall(self.career.lineup()), crew["ovr"])

    def handle(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key in BACK:
            self.app.switch(CourtScreen(self.app))
        elif e.key in LEFT:
            self.i = max(0, self.i - 1)
        elif e.key in RIGHT:
            self.i = min(len(self.bets) - 1, self.i + 1)
        elif e.key in CONFIRM:
            bet = self.bets[self.i]
            if luck.place_bet(self.career, bet):
                self.app.save()
                self.app.switch(MatchScreen(self.app, self.ci, self.crew, bet, self.mult))

    def draw(self, s):
        self.header(s, "Side Bet?")
        c = self.career
        mine = team_overall(c.lineup())
        text(s, self.f(34), f"Your crew OVR {mine}   vs   {self.crew['name']} OVR {self.crew['ovr']}",
             (500, 190), S.WHITE, center=True)
        text(s, self.f(26), f"Bet on yourself. Win and you get {self.mult}x your bet back. Lose and it's gone.",
             (500, 240), S.GREY, center=True)
        bet = self.bets[self.i]
        label = "No bet" if bet == 0 else ("ALL IN  $%d" % bet if bet == c.cash and bet not in (25, 50, 100, 250, 500, 1000) else f"${bet}")
        text(s, self.f(64), f"<  {label}  >", (500, 330), S.GOLD if bet else S.WHITE, center=True)
        if bet:
            text(s, self.f(30), f"Win pays ${round(bet * self.mult)}", (500, 400), S.GREEN, center=True)
        text(s, self.f(26), "Lineup: " + ", ".join(p.name for p in c.lineup()), (500, 470), S.GREY, center=True)
        self.footer(s, "Left/Right change bet   Enter to tip off   Esc back")


# ---------------------------------------------------------------- match
class MatchScreen(Screen):
    def __init__(self, app, ci, crew, bet=0, mult=1.0, rng=None):
        super().__init__(app)
        self.ci, self.crew, self.bet, self.mult = ci, crew, bet, mult
        self.match = Match(self.career.lineup(), crew["players"], rng=rng or random.Random())
        self.edges = Inputs()
        self.paused = False
        self.done_t = 0.0

    def handle(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key in (pygame.K_ESCAPE, pygame.K_p):
            self.paused = not self.paused
        elif self.paused and e.key == pygame.K_f:
            self.finish(forfeit=True)
        elif e.key == pygame.K_SPACE:
            self.edges.shoot_pressed = True
        elif e.key == pygame.K_j:
            self.edges.pass_pressed = True
        elif e.key == pygame.K_k:
            self.edges.move_pressed = True
        elif e.key == pygame.K_q:
            self.edges.switch_pressed = True

    def finish(self, forfeit=False):
        self.app.switch(ResultScreen(self.app, self.ci, self.crew, self.match, self.bet, self.mult, forfeit))

    def update(self, dt):
        if self.paused:
            return
        keys = pygame.key.get_pressed()
        mx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        my = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        inp = self.edges
        inp.move = (float(mx), float(my))
        inp.shoot_down = bool(keys[pygame.K_SPACE])
        self.match.update(min(dt, 1 / 30), inp)
        self.edges = Inputs()
        if self.match.phase == "over":
            self.done_t += dt
            if self.done_t > 1.8:
                self.finish()

    def draw(self, s):
        m = self.match
        draw_court(s, self.ci)
        b = m.ball
        # shadows first
        for a in m.actors:
            pygame.draw.circle(s, (22, 22, 26), (int(a.x) + 3, int(a.y) + 4), S.PLAYER_RADIUS)
        if b.z > 1:
            pygame.draw.circle(s, (20, 20, 20), (int(b.x), int(b.y)), 5)
        for a in m.actors:
            self.draw_actor(s, a)
        bx, by = int(b.x), int(b.y - b.z * 0.6)
        pygame.draw.circle(s, S.ORANGE, (bx, by), 7)
        pygame.draw.circle(s, (60, 30, 10), (bx, by), 7, 1)
        pygame.draw.line(s, (60, 30, 10), (bx - 6, by), (bx + 6, by), 1)
        self.draw_meter(s)
        self.draw_hud(s)
        if self.paused:
            panel(s, pygame.Rect(300, 250, 400, 180))
            text(s, self.f(52), "PAUSED", (500, 295), S.WHITE, center=True)
            text(s, self.f(26), "Esc to resume   F to forfeit (counts as a loss)", (500, 360), S.GREY, center=True)

    def draw_actor(self, s, a):
        m = self.match
        col = S.TEAM_COLORS[a.team]
        pos = (int(a.x), int(a.y))
        if a.stun > 0:
            col = tuple(c // 2 for c in col)
        pygame.draw.circle(s, col, pos, S.PLAYER_RADIUS)
        is_main = a.team == 0 and a.slot == 0
        pygame.draw.circle(s, S.GOLD if is_main else S.BLACK, pos, S.PLAYER_RADIUS, 3 if is_main else 1)
        text(s, self.f(20), a.p.number, pos, S.WHITE, center=True)
        # facing tick
        pygame.draw.line(s, S.WHITE, pos, (pos[0] + int(a.fx * 18), pos[1] + int(a.fy * 18)), 2)
        if a is m.controlled:
            pulse = 3 + int(2 * math.sin(m.elapsed * 8))
            pygame.draw.circle(s, S.WHITE, pos, S.PLAYER_RADIUS + 4 + pulse, 2)
            pygame.draw.polygon(s, S.GOLD, [(pos[0] - 7, pos[1] - 32), (pos[0] + 7, pos[1] - 32), (pos[0], pos[1] - 22)])
            text(s, self.f(20), a.p.name, (pos[0], pos[1] + 26), S.WHITE, center=True)
        if a.stun > 0:
            text(s, self.f(20), "@#!", (pos[0], pos[1] - 26), S.GOLD, center=True)

    def draw_meter(self, s):
        m = self.match
        a = m.controlled
        x, y, h = int(a.x) + 24, int(a.y) - 30, 60
        if m.meter is None:
            return
        pygame.draw.rect(s, S.DARK, (x, y, 10, h))
        w = m.meter_window(a)
        lo, hi = S.METER_SWEET - w, S.METER_SWEET + w
        pygame.draw.rect(s, S.GREEN, (x, y + h - int(hi * h), 10, int((hi - lo) * h)))
        fill = int(min(1.0, m.meter) * h)
        pygame.draw.rect(s, S.WHITE, (x + 2, y + h - fill, 6, fill))
        pygame.draw.rect(s, S.WHITE, (x, y, 10, h), 1)

    def draw_hud(self, s):
        m = self.match
        pygame.draw.rect(s, (15, 15, 20), (0, 0, S.WIDTH, 44))
        text(s, self.f(34), f"YOU  {m.score[0]}", (340, 22), S.TEAM_COLORS[0], right=False, center=True)
        text(s, self.f(24), f"first to {m.game_to}", (500, 22), S.GREY, center=True)
        text(s, self.f(34), f"{m.score[1]}  {self.crew['name'].upper()}", (680, 22), S.TEAM_COLORS[1], center=True)
        text(s, self.f(22), f"{TIERS[self.ci]['court']}", (16, 14), S.GREY)
        text(s, self.f(26), f"Shot {max(0, int(m.shot_clock + 0.99))}", (S.WIDTH - 16, 12), S.WHITE, right=True)
        if m.needs_clear:
            who = "YOU" if m.offense == 0 else "THEY"
            text(s, self.f(28), f"{who} MUST CLEAR IT PAST THE ARC", (500, 60), S.GOLD, center=True)
        for i, (msg, _) in enumerate(reversed(m.messages)):
            text(s, self.f(32 if i == 0 else 24), msg, (500, 600 - i * 28), S.WHITE, center=True)
        if m.phase == "check":
            text(s, self.f(40), "CHECK BALL", (500, 380), S.WHITE, center=True)
        if m.phase == "over":
            won = m.winner == 0
            text(s, self.f(72), "YOU WIN!" if won else "YOU LOSE", (500, 330), S.GREEN if won else S.RED, center=True)
        a = m.controlled
        dunk = " | SPACE near rim = DUNK" if can_dunk(a.p) else ""
        text(s, self.f(20), "WASD move | SPACE hold+release shoot" + dunk + " | J pass | K crossover/steal | Q switch | Esc pause",
             (500, S.HEIGHT - 16), S.WHITE, center=True)


class ResultScreen(Screen):
    def __init__(self, app, ci, crew, match, bet, mult, forfeit=False):
        super().__init__(app)
        c = self.career
        self.crew, self.match, self.bet = crew, match, bet
        self.won = (not forfeit) and match.winner == 0
        self.forfeit = forfeit
        margin = match.score[0] - match.score[1]
        self.r = c.apply_result(ci, crew["id"], crew["boss"], self.won, max(0, margin), bet, mult)
        self.my_pts = match.main_guy.points
        self.msg = ""
        items = []
        if self.won:
            for p in crew["players"]:
                items.append((lambda p=p: f"Recruit {p.name}  OVR {p.overall()}  ${c.recruit_cost(p)}",
                              lambda p=p: self.recruit(p)))
        items.append(("Back to the Hub", lambda: app.switch(HubScreen(app))))
        self.menu = Menu(items)
        app.save()

    def recruit(self, p):
        c = self.career
        if len(c.crew) >= S.CREW_MAX:
            self.msg = "Crew is full. Release someone first."
        elif c.recruit(p):
            self.msg = f"{p.name} joined your crew!"
            self.menu.items = [it for it in self.menu.items if it[0]() != f"Recruit {p.name}  OVR {p.overall()}  ${c.recruit_cost(p)}"]
            self.menu.i = 0
            self.app.save()
        else:
            self.msg = f"Not enough cash (${c.recruit_cost(p)})."

    def handle(self, e):
        self.menu.handle(e)

    def draw(self, s):
        self.header(s)
        m = self.match
        title = "FORFEIT" if self.forfeit else ("VICTORY" if self.won else "DEFEAT")
        text(s, self.f(72), title, (500, 120), S.GREEN if self.won else S.RED, center=True)
        text(s, self.f(36), f"{m.score[0]} - {m.score[1]}  vs  {self.crew['name']}", (500, 175), S.WHITE, center=True)
        text(s, self.f(28), f"You scored {self.my_pts}", (500, 212), S.GREY, center=True)
        lines = [f"+{self.r['fame']} fame", f"+${self.r['cash']}"]
        if self.bet:
            lines.append(f"Bet paid ${self.r['bet_win']}!" if self.won else f"Lost your ${self.bet} bet")
        text(s, self.f(32), "     ".join(lines), (500, 255), S.GOLD, center=True)
        if self.r["tier_up"]:
            text(s, self.f(36), f"FAME UP! You're now {self.career.title}. {TIERS[self.career.tier]['court']} unlocked!",
                 (500, 300), S.GOLD, center=True)
        if self.r["crowned"]:
            text(s, self.f(40), f"YOU ARE THE {KING_TITLE.upper()}!", (500, 300), S.GOLD, center=True)
        if self.won:
            text(s, self.f(26), "Recruit one of them? (crew max %d)" % S.CREW_MAX, (500, 345), S.GREY, center=True)
        self.menu.draw(s, self.f(30), 500, 385, 40)
        if self.msg:
            text(s, self.f(26), self.msg, (500, 600), S.WHITE, center=True)
        self.footer(s, "Up/Down + Enter")


# ---------------------------------------------------------------- crew / training / attributes
def stat_line(p):
    return "  ".join(f"{S.STAT_LABELS[k][:3].upper()} {p.stats[k]}" for k in S.STAT_NAMES)


class CrewScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.i = 0
        self.msg = ""

    def handle(self, e):
        if e.type != pygame.KEYDOWN:
            return
        c = self.career
        if e.key in BACK:
            self.app.switch(HubScreen(self.app))
        elif e.key in UP:
            self.i = (self.i - 1) % len(c.crew)
        elif e.key in DOWN:
            self.i = (self.i + 1) % len(c.crew)
        elif e.key in CONFIRM:
            c.toggle_starter(self.i)
            self.app.save()
        elif e.key == pygame.K_x:
            name = c.crew[self.i].name
            if c.release(self.i):
                self.msg = f"Released {name}."
                self.i = min(self.i, len(c.crew) - 1)
                self.app.save()
            else:
                self.msg = "You need at least 2 in your crew."

    def draw(self, s):
        self.header(s, "Your Crew")
        c = self.career
        y = 150
        me = c.me
        text(s, self.f(26), f"YOU  #{me.number} {me.name}  OVR {me.overall()}", (80, y), S.GOLD)
        text(s, self.f(22), stat_line(me) + "   " + me.attr_label(), (80, y + 26), S.GREY)
        for i, p in enumerate(c.crew):
            y = 220 + i * 62
            sel = i == self.i
            box = pygame.Rect(60, y - 6, 880, 56)
            if sel:
                pygame.draw.rect(s, (55, 55, 70), box, border_radius=6)
            tag = "  [STARTER]" if i in c.starters else ""
            text(s, self.f(26), f"#{p.number} {p.name}  OVR {p.overall()}{tag}", (80, y), S.GREEN if tag else S.WHITE)
            text(s, self.f(22), stat_line(p) + "   " + p.attr_label(), (80, y + 26), S.GREY)
        if self.msg:
            text(s, self.f(24), self.msg, (500, 620), S.WHITE, center=True)
        self.footer(s, "Up/Down pick   Enter = make starter   X = release   Esc back")


class TrainScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.msg = ""
        self.menu = Menu([(self.label(k), lambda k=k: self.buy(k)) for k in S.STAT_NAMES])

    def label(self, k):
        def f():
            v = self.career.me.stats[k]
            if v >= S.STAT_MAX:
                return f"{S.STAT_LABELS[k]}  {v}  (MAX)"
            return f"{S.STAT_LABELS[k]}  {v} -> {min(S.STAT_MAX, v + S.STAT_STEP)}   ${self.career.stat_cost(v)}"
        return f

    def buy(self, k):
        if self.career.buy_stat(k):
            self.msg = f"{S.STAT_LABELS[k]} up!"
            self.app.save()
        else:
            self.msg = "Not enough cash."

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE,):
            self.app.switch(HubScreen(self.app))
        else:
            self.menu.handle(e)

    def draw(self, s):
        self.header(s, "Train Your Game")
        self.menu.draw(s, self.f(36), 500, 190, 56)
        text(s, self.f(24), "Shooting = makes   Speed = movement   Handles = crossovers & protecting the ball",
             (500, 490), S.GREY, center=True)
        text(s, self.f(24), "Defense = contests, steals, blocks   Rebounding = winning loose balls",
             (500, 520), S.GREY, center=True)
        if self.msg:
            text(s, self.f(28), self.msg, (500, 570), S.WHITE, center=True)
        self.footer(s, "Enter to buy   Esc back")


class AttrScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.row = 0
        me = self.career.me
        self.sec_i = 0 if me.sec_attr is None else ATTR_ORDER.index(me.sec_attr)
        if me.sec_attr is None and ATTR_ORDER[self.sec_i] == me.main_attr:
            self.sec_i = 1
        self.msg = ""

    def handle(self, e):
        if e.type != pygame.KEYDOWN:
            return
        me = self.career.me
        if e.key in BACK:
            self.app.switch(HubScreen(self.app))
        elif e.key in UP or e.key in DOWN:
            self.row = 1 - self.row
        elif (e.key in LEFT or e.key in RIGHT) and self.row == 1 and me.sec_lvl == 0:
            step = -1 if e.key in LEFT else 1
            self.sec_i = (self.sec_i + step) % len(ATTR_ORDER)
            if ATTR_ORDER[self.sec_i] == me.main_attr:
                self.sec_i = (self.sec_i + step) % len(ATTR_ORDER)
        elif e.key in CONFIRM:
            if self.row == 0:
                ok, self.msg = self.career.buy_attr("main")
            else:
                ok, self.msg = self.career.buy_attr("sec", ATTR_ORDER[self.sec_i])
            if ok:
                self.app.save()

    def draw(self, s):
        self.header(s, "Attribute Shop")
        c = self.career
        me = c.me
        rows = []
        cost = c.attr_cost("main")
        rows.append((f"MAIN: {ATTRIBUTES[me.main_attr]['name']}   Lv {me.main_lvl}/{max_level('main')}",
                     "MAXED" if cost is None or me.main_lvl >= max_level("main") else f"Next level ${cost}",
                     "Full effect"))
        if not c.secondary_unlocked():
            rows.append(("SECONDARY: locked", "Reach Local fame", f"{int(S.SECONDARY_PCT * 100)}% effect"))
        else:
            key = me.sec_attr or ATTR_ORDER[self.sec_i]
            name = ATTRIBUTES[key]["name"]
            pick = f"<  {name}  >" if me.sec_lvl == 0 else name
            cost = c.attr_cost("sec")
            rows.append((f"SECONDARY: {pick}   Lv {me.sec_lvl}/{max_level('sec')}",
                         "MAXED" if cost is None or me.sec_lvl >= max_level("sec") else f"Next level ${cost}",
                         f"{int(S.SECONDARY_PCT * 100)}% effect"))
        for i, (a, b, note) in enumerate(rows):
            box = pygame.Rect(120, 160 + i * 90, 760, 74)
            pygame.draw.rect(s, (60, 60, 75) if i == self.row else (35, 35, 44), box, border_radius=8)
            if i == self.row:
                pygame.draw.rect(s, S.GOLD, box, 2, border_radius=8)
            text(s, self.f(32), a, (box.left + 16, box.top + 10), S.WHITE)
            text(s, self.f(24), note, (box.left + 16, box.top + 44), S.GREY)
            text(s, self.f(28), b, (box.right - 16, box.top + 24), S.GREEN, right=True)
        y = 360
        for key in ATTR_ORDER:
            a = ATTRIBUTES[key]
            text(s, self.f(24), a["name"], (120, y), S.ORANGE)
            text(s, self.f(22), a["desc"], (290, y + 2), S.GREY)
            y += 32
        if self.msg:
            text(s, self.f(28), self.msg, (500, 620), S.WHITE, center=True)
        self.footer(s, "Up/Down pick slot   Left/Right choose Secondary   Enter buy   Esc back")


# ---------------------------------------------------------------- luck
class SlotScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.bi = 1
        self.spin_t = 0.0
        self.result = None
        self.reels = ["BALL", "CROWN", "CASH"]
        self.msg = "Pick a bet and press SPACE to spin."
        self.rng = random.Random()

    def handle(self, e):
        if e.type != pygame.KEYDOWN or self.spin_t > 0:
            return
        if e.key in BACK:
            self.app.switch(HubScreen(self.app))
        elif e.key in LEFT:
            self.bi = max(0, self.bi - 1)
        elif e.key in RIGHT:
            self.bi = min(len(luck.BET_OPTIONS) - 1, self.bi + 1)
        elif e.key in CONFIRM:
            bet = luck.BET_OPTIONS[self.bi]
            res = luck.play_slots(self.career, bet, self.rng)
            if res is None:
                self.msg = "Not enough cash for that bet."
                return
            self.result = (bet, *res)
            self.spin_t = 1.2
            self.app.save()

    def update(self, dt):
        if self.spin_t > 0:
            self.spin_t -= dt
            if self.spin_t <= 0:
                bet, reels, win = self.result
                self.reels = reels
                if win > bet:
                    self.msg = f"WINNER! +${win}"
                elif win == bet:
                    self.msg = "Push. You got your bet back."
                else:
                    self.msg = "Brick. Better luck next time."
            else:
                self.reels = [self.rng.choice(luck.SYMBOLS) for _ in range(3)]

    def draw(self, s):
        self.header(s, "Luck Machine")
        for i, sym in enumerate(self.reels):
            box = pygame.Rect(260 + i * 170, 170, 150, 150)
            pygame.draw.rect(s, (40, 40, 50), box, border_radius=12)
            pygame.draw.rect(s, S.GOLD, box, 3, border_radius=12)
            text(s, self.f(36), sym, box.center, SYMBOL_COLORS[sym], center=True)
        bet = luck.BET_OPTIONS[self.bi]
        text(s, self.f(48), f"<  Bet ${bet}  >", (500, 370), S.WHITE, center=True)
        col = S.GREEN if self.msg.startswith("WINNER") else S.WHITE
        text(s, self.f(32), self.msg, (500, 425), col, center=True)
        pays = ["3 CROWNS = 20x", "Any 3 of a kind = 5x", "2 CASH or 2 CROWNS = 2x", "Any other pair = bet back",
                "The machine usually wins. Don't bet what you need!"]
        for i, p in enumerate(pays):
            text(s, self.f(24), p, (500, 480 + i * 26), S.GREY, center=True)
        self.footer(s, "Left/Right bet   Space spin   Esc back")


class MysteryScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.rng = random.Random()
        self.reveal = None
        self.msg = ""

    def handle(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key in BACK:
            self.app.switch(HubScreen(self.app))
        elif e.key in CONFIRM:
            c = self.career
            if len(c.crew) >= S.CREW_MAX:
                self.msg = "Crew is full. Release someone in the Crew screen."
                return
            res = luck.roll_mystery(c, self.rng)
            if res is None:
                self.msg = f"Need ${luck.mystery_cost(c.tier)}."
                return
            self.reveal = res
            self.msg = ""
            self.app.save()

    def draw(self, s):
        self.header(s, "Mystery Baller")
        c = self.career
        cost = luck.mystery_cost(c.tier)
        text(s, self.f(30), f"Pay ${cost} for a random baller. Could be a Legend... could be a Bum.",
             (500, 170), S.WHITE, center=True)
        for i, (name, pct, off) in enumerate(luck.RARITIES):
            text(s, self.f(28), f"{name}: {pct}%", (500, 215 + i * 30), RARITY_COLORS[name], center=True)
        crew_best = max(p.overall() for p in c.crew)
        text(s, self.f(22), f"Your best crew member is OVR {crew_best}. Crew {len(c.crew)}/{S.CREW_MAX}",
             (500, 345), S.GREY, center=True)
        if self.reveal:
            rarity, p = self.reveal
            box = pygame.Rect(250, 380, 500, 180)
            pygame.draw.rect(s, (40, 40, 50), box, border_radius=12)
            pygame.draw.rect(s, RARITY_COLORS[rarity], box, 4, border_radius=12)
            text(s, self.f(44), rarity.upper(), (500, 410), RARITY_COLORS[rarity], center=True)
            text(s, self.f(34), f"#{p.number} {p.name}  OVR {p.overall()}", (500, 455), S.WHITE, center=True)
            text(s, self.f(22), stat_line(p), (500, 495), S.GREY, center=True)
            text(s, self.f(22), p.attr_label(), (500, 525), S.GREY, center=True)
        if self.msg:
            text(s, self.f(26), self.msg, (500, 600), S.RED, center=True)
        self.footer(s, "Enter to roll   Esc back")
