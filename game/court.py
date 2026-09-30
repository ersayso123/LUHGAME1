"""Drawing the outdoor court from above. Each fame tier has its own look."""
import math

import pygame

from . import settings as S

THEMES = [
    # Rusty Rim Park: cracked grey asphalt, patchy grass
    {"asphalt": (78, 80, 86), "surround": (62, 105, 58), "line": (225, 225, 215),
     "paint": (150, 80, 50), "fence": (120, 120, 120)},
    # Southside Blacktop: fresh blacktop, sidewalk
    {"asphalt": (44, 46, 52), "surround": (120, 118, 110), "line": (240, 240, 240),
     "paint": (50, 90, 160), "fence": (90, 90, 95)},
    # Pier Courts: sea-blue court, boardwalk
    {"asphalt": (56, 86, 110), "surround": (150, 118, 80), "line": (245, 245, 235),
     "paint": (30, 140, 150), "fence": (200, 200, 190)},
    # Downtown Cage: dark court, brick
    {"asphalt": (38, 38, 44), "surround": (112, 56, 44), "line": (230, 230, 230),
     "paint": (190, 50, 50), "fence": (70, 70, 75)},
    # The Throne: royal purple and gold
    {"asphalt": (58, 36, 82), "surround": (40, 30, 18), "line": (245, 205, 90),
     "paint": (110, 60, 150), "fence": (200, 160, 60)},
]


def court_rect():
    return pygame.Rect(S.COURT_LEFT, S.COURT_TOP,
                       S.COURT_RIGHT - S.COURT_LEFT, S.COURT_BOTTOM - S.COURT_TOP)


def draw_court(surf, tier):
    th = THEMES[min(tier, len(THEMES) - 1)]
    surf.fill(th["surround"])
    rect = court_rect()
    hx, hy = int(S.HOOP[0]), int(S.HOOP[1])
    r = int(S.ARC_RADIUS)

    # chain-link fence around the court
    fence = rect.inflate(56, 56)
    pygame.draw.rect(surf, th["fence"], fence, 3)
    for x in range(fence.left, fence.right + 1, 80):
        pygame.draw.circle(surf, th["fence"], (x, fence.top), 5)
        pygame.draw.circle(surf, th["fence"], (x, fence.bottom), 5)

    pygame.draw.rect(surf, th["asphalt"], rect)
    if tier == 0:  # cracks for the starter court
        crack = tuple(max(0, c - 18) for c in th["asphalt"])
        for pts in ([(180, 520), (230, 540), (260, 600)], [(760, 470), (800, 430), (850, 450)],
                    [(600, 580), (640, 560), (700, 600)]):
            pygame.draw.lines(surf, crack, False, pts, 2)

    line = th["line"]
    # paint and free throw circle
    paint = pygame.Rect(hx - S.PAINT_HALF_WIDTH, S.COURT_TOP, S.PAINT_HALF_WIDTH * 2, S.PAINT_DEPTH)
    pygame.draw.rect(surf, th["paint"], paint)
    pygame.draw.rect(surf, line, paint, 3)
    pygame.draw.circle(surf, line, (hx, S.COURT_TOP + S.PAINT_DEPTH), 60, 3)
    # 2-point arc and corner lines
    pygame.draw.arc(surf, line, pygame.Rect(hx - r, hy - r, 2 * r, 2 * r), math.pi, 2 * math.pi, 3)
    pygame.draw.line(surf, line, (hx - r, S.COURT_TOP), (hx - r, hy), 3)
    pygame.draw.line(surf, line, (hx + r - 1, S.COURT_TOP), (hx + r - 1, hy), 3)
    pygame.draw.rect(surf, line, rect, 3)
    # check-ball mark
    pygame.draw.circle(surf, line, (int(S.CHECK_SPOT[0]), int(S.CHECK_SPOT[1])), 6, 2)
    # backboard, rim, net
    pygame.draw.line(surf, (235, 235, 235), (hx - 32, hy - 22), (hx + 32, hy - 22), 5)
    pygame.draw.line(surf, (180, 180, 180), (hx, hy - 22), (hx, hy - 10), 3)
    pygame.draw.circle(surf, (230, 230, 230), (hx, hy), 7, 1)
    pygame.draw.circle(surf, S.ORANGE, (hx, hy), 11, 3)
