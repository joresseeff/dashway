"""
tests/test_button.py
--------------------
Unit tests for the Button class.
Pygame is initialised in headless mode (SDL_VIDEODRIVER=dummy).
"""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scr"))

import pygame
import pytest
from button import Button


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def make_button(x=50, y=50, w=200, h=60):
    screen = pygame.display.set_mode((500, 800))
    image = pygame.Surface((w, h))
    font = pygame.font.SysFont(None, 30)
    return Button(0, x, y, w, h, image, screen, "PLAY", font, "white")


class TestButtonCollide:
    def test_centre_hit(self):
        btn = make_button(50, 50, 200, 60)
        assert btn.collide(150, 80) is True

    def test_top_left_corner_hit(self):
        btn = make_button(50, 50, 200, 60)
        assert btn.collide(50, 50) is True

    def test_bottom_right_corner_hit(self):
        btn = make_button(50, 50, 200, 60)
        assert btn.collide(250, 110) is True

    def test_miss_left(self):
        btn = make_button(50, 50, 200, 60)
        assert btn.collide(49, 80) is False

    def test_miss_right(self):
        btn = make_button(50, 50, 200, 60)
        assert btn.collide(251, 80) is False

    def test_miss_above(self):
        btn = make_button(50, 50, 200, 60)
        assert btn.collide(150, 49) is False

    def test_miss_below(self):
        btn = make_button(50, 50, 200, 60)
        assert btn.collide(150, 111) is False
