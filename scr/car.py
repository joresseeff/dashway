"""
car.py
------
Enemy car sprite that falls from the top of the screen.
"""

import pygame
from random import randint
from init import WIDTH, OFFSET, CAR_SIZE


class Car:
    """An enemy car that falls down one of the three lanes.

    Each car is assigned a random acceleration tier (1, 2, or 3) so that
    different cars move at different speeds relative to the global game speed.

    Attributes:
        x (int): Lane index (0 = left, 1 = centre, 2 = right).
        y (float): Current vertical pixel position.
        acceleration (int): Speed multiplier (1, 2, or 3).
        rect (pygame.Rect): Collision rectangle.
        image (pygame.Surface): Scaled and flipped sprite.
    """

    # Acceleration thresholds — rolled on [1, 20]
    _ACC_SLOW = 12    # < 12  → tier 1
    _ACC_MED  = 20    # < 20  → tier 2
                      # == 20 → tier 3

    def __init__(self, image: pygame.Surface, lane: int, y: int = -200) -> None:
        """Initialise an enemy car.

        Args:
            image: Sprite surface (will be scaled and rotated 180°).
            lane: Starting lane index.
            y: Initial vertical position; defaults to above the screen.
        """
        self.x: int = lane
        self.y: float = y
        self.rect = pygame.Rect((self.x * WIDTH // 3 + OFFSET // 2, self.y), CAR_SIZE)

        self.image = pygame.transform.rotate(
            pygame.transform.scale(image, (int(self.rect.w), int(self.rect.h))),
            180,
        )

        roll = randint(1, 20)
        if roll < self._ACC_SLOW:
            self.acceleration = 1
        elif roll < self._ACC_MED:
            self.acceleration = 2
        else:
            self.acceleration = 3

    def update(self, screen: pygame.Surface, speed: int) -> None:
        """Move the car downward and draw it. Called once per frame.

        Args:
            screen: Main display surface.
            speed: Current global game speed.
        """
        self._fall(speed)
        self._draw(screen)

    def get_rect(self) -> pygame.Rect:
        """Return the current collision rectangle.

        Returns:
            Up-to-date pygame.Rect for collision detection.
        """
        return self.rect

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw(self, screen: pygame.Surface) -> None:
        self.rect = pygame.Rect(
            (self.x * WIDTH // 3 + OFFSET // 2, self.y), CAR_SIZE
        )
        screen.blit(self.image, (self.x * WIDTH // 3 + OFFSET // 2, self.y))

    def _fall(self, speed: int) -> None:
        self.y += speed * self.acceleration
