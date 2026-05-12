"""
tests/test_player.py
--------------------
Unit tests for the Player class (movement and boundary clamping).
"""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scr"))

import pygame
import pytest
from player import Player


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def make_player(lane=1):
    image = pygame.Surface((80, 130))
    return Player(lane, image)


class TestPlayerMovement:
    def test_starts_in_centre_lane(self):
        p = make_player(1)
        assert p.x == 1

    def test_move_left(self):
        p = make_player(1)
        p.left()
        assert p.x == 0

    def test_move_right(self):
        p = make_player(1)
        p.right()
        assert p.x == 2

    def test_cannot_go_left_of_lane_0(self):
        p = make_player(0)
        p.left()
        assert p.x == 0

    def test_cannot_go_right_of_lane_2(self):
        p = make_player(2)
        p.right()
        assert p.x == 2

    def test_rect_updates_after_move(self):
        p = make_player(1)
        rect_before = p.rect.x
        p.left()
        assert p.rect.x != rect_before
