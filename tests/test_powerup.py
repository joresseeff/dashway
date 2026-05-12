"""
tests/test_powerup.py
---------------------
Unit tests for the PowerUp class and PowerUpType enum.
"""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scr"))

import pygame
import pytest
from powerup import PowerUp, PowerUpType


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


class TestPowerUpRect:
    def test_rect_is_centered_on_lane(self):
        pu = PowerUp(PowerUpType.SHIELD, lane=1, y=400)
        rect = pu.get_rect()
        from init import WIDTH
        expected_cx = 1 * WIDTH // 3 + WIDTH // 6
        assert abs((rect.x + rect.w // 2) - expected_cx) <= 2

    def test_all_types_instantiate(self):
        for pu_type in PowerUpType:
            pu = PowerUp(pu_type, lane=0)
            assert pu.type == pu_type

    def test_falls_downward(self):
        screen = pygame.display.set_mode((500, 800))
        pu = PowerUp(PowerUpType.SLOW, lane=0, y=100)
        y_before = pu.y
        pu.update(screen, speed=9)
        assert pu.y > y_before
