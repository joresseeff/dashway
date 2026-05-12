"""
player.py
---------
The player-controlled car sprite.
"""

import pygame
from coin import Coin
from init import CAR_SIZE, HEIGHT, WIDTH, OFFSET


class Player:
    """Player-controlled car that moves between the three lanes.

    The road is divided into three equal lanes (index 0, 1, 2).
    The car's pixel x-position is derived from the lane index so that
    the sprite is always centred inside its lane.

    Attributes:
        x (int): Current lane index (0 = left, 1 = centre, 2 = right).
        y (float): Vertical pixel position (fixed during gameplay).
        rect (pygame.Rect): Collision rectangle updated on every move.
        image (pygame.Surface): Scaled car sprite.
    """

    def __init__(self, lane: int, image: pygame.Surface) -> None:
        """Initialise the player car.

        Args:
            lane: Starting lane index (0, 1, or 2).
            image: Sprite surface; will be scaled to CAR_SIZE.
        """
        self.x: int = lane
        self.y: float = HEIGHT / 1.5
        self.rect = pygame.Rect((self.x * WIDTH // 3 + OFFSET // 2, self.y), CAR_SIZE)
        self.image = pygame.transform.scale(image, (self.rect[2], self.rect[3]))

    def draw(self, screen: pygame.Surface) -> None:
        """Blit the player sprite onto *screen* at its current position.

        Args:
            screen: Main display surface.
        """
        screen.blit(self.image, (self.x * WIDTH // 3 + OFFSET // 2, self.y))

    def left(self) -> None:
        """Move one lane to the left, if not already in the leftmost lane."""
        if self.x > 0:
            self.x -= 1
            self._update_rect()

    def right(self) -> None:
        """Move one lane to the right, if not already in the rightmost lane."""
        if self.x < 2:
            self.x += 1
            self._update_rect()

    def collide(self, objects: list) -> tuple:
        """Detect and classify a collision between the player and any object.

        Args:
            objects: List of active game objects (Car or Coin instances).

        Returns:
            ``(1, obj)`` if *obj* is a Coin, ``(2, obj)`` if *obj* is a Car,
            ``(0, 0)`` when there is no collision.
        """
        for obj in objects:
            if self.rect.colliderect(obj.get_rect()):
                return (1, obj) if isinstance(obj, Coin) else (2, obj)
        return (0, 0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_rect(self) -> None:
        """Recalculate the collision rect after a lane change."""
        self.rect = pygame.Rect(
            (self.x * WIDTH // 3 + OFFSET // 2, self.y), CAR_SIZE
        )
