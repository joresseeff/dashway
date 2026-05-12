"""
bomb.py
-------
Player-launched projectile that destroys the first enemy car it hits.
"""

import pygame
from car import Car
from init import WIDTH, OFFSET


class Bomb:
    """A bomb that travels upward from the player's position.

    The bomb sits on top of the player sprite and follows lane changes until
    it is launched. Once launched (``active`` is True) it travels upward at
    a fixed speed and destroys the first Car it overlaps.

    Attributes:
        x (int): Lane index (0 = left, 1 = centre, 2 = right).
        y (float): Current vertical pixel position.
        active (bool): Whether the bomb is currently in flight.
        speed (int): Upward speed in pixels per frame.
    """

    _SPEED = 10  # pixels per frame when launched

    def __init__(self, lane: int, y: float, image: pygame.Surface) -> None:
        """Initialise a bomb at the player's position.

        Args:
            lane: Starting lane index (mirrors player lane).
            y: Initial vertical position (mirrors player y).
            image: Sprite surface (will be scaled to fit a lane width).
        """
        self.x: int = lane
        self.y: float = y
        self.active: bool = False
        self.speed: int = self._SPEED
        self._center: tuple = (self.x * WIDTH // 3 + WIDTH // 6, self.y)
        self.image = pygame.transform.scale(image, (WIDTH // 6, WIDTH // 6))

    def update(self, screen: pygame.Surface) -> None:
        """Move and draw the bomb if it has been launched.

        Args:
            screen: Main display surface.
        """
        if self.active:
            self._move()
            self._draw(screen)

    def launch(self) -> None:
        """Activate the bomb so it starts flying upward."""
        self.active = True

    def collide(self, objects: list) -> tuple:
        """Check whether the bomb overlaps any Car in *objects*.

        Only runs when the bomb is active (in flight).

        Args:
            objects: List of active game objects.

        Returns:
            ``(1, car)`` on first hit, ``(0, 0)`` if no collision.
        """
        if not self.active:
            return (0, 0)
        bomb_rect = self._get_rect()
        for obj in objects:
            if isinstance(obj, Car) and bomb_rect.colliderect(obj.get_rect()):
                return (1, obj)
        return (0, 0)

    def left(self) -> None:
        """Follow the player one lane to the left (only before launch)."""
        if self.x > 0 and not self.active:
            self.x -= 1
            self._update_center()

    def right(self) -> None:
        """Follow the player one lane to the right (only before launch)."""
        if self.x < 2 and not self.active:
            self.x += 1
            self._update_center()

    # ------------------------------------------------------------------
    # Backward-compatibility alias
    # ------------------------------------------------------------------
    def activeLunch(self) -> None:
        """Alias kept for compatibility with legacy main.py calls."""
        self.launch()

    @property
    def lunch(self) -> bool:
        """Legacy attribute name alias for ``active``."""
        return self.active

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw(self, screen: pygame.Surface) -> None:
        self._update_center()
        cx, cy = self._center
        screen.blit(self.image, (cx - WIDTH // 12, cy))

    def _move(self) -> None:
        self.y -= self.speed

    def _update_center(self) -> None:
        self._center = (self.x * WIDTH // 3 + WIDTH // 6, self.y)

    def _get_rect(self) -> pygame.Rect:
        cx, cy = self._center
        size = WIDTH // 3 - 2 * OFFSET
        return pygame.Rect((cx - OFFSET // 2, cy - OFFSET // 4), (size, size))
