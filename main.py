"""Streetball Kingdom: a top-down 3v3 streetball career game. Run: python main.py"""
from pathlib import Path

import pygame

from game import settings as S
from game.screens import TitleScreen

SAVE_PATH = Path(__file__).resolve().parent / "saves" / "career.json"


class App:
    def __init__(self, screen, save_path=SAVE_PATH):
        self.screen = screen
        self.save_path = Path(save_path)
        self.career = None
        self.running = True
        self._fonts = {}
        self.current = TitleScreen(self)

    def font(self, size):
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def switch(self, screen):
        self.current = screen

    def save(self):
        if self.career:
            self.career.save(self.save_path)

    def quit(self):
        self.save()
        self.running = False

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(S.FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.quit()
                else:
                    self.current.handle(e)
            self.current.update(dt)
            self.current.draw(self.screen)
            pygame.display.flip()


def main():
    pygame.init()
    pygame.display.set_caption(S.TITLE)
    screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
    App(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()
