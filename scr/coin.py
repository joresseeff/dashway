"""
coin.py
-------
Collectable coin sprite with a frame-by-frame spin animation.
"""

import pygame
from random import randint
from init import WIDTH, OFFSET


class Coin:
    """A spinning coin that falls down a lane and can be collected.

    Animation is driven by a sprite sheet already split into individual
    frames before the Coin is constructed. Each frame is randomly advanced
    at ~50 % probability per tick to produce a natural-looking spin speed.

    Attributes:
        x (int): Lane index (0 = left, 1 = centre, 2 = right).
        y (float): Current vertical pixel position.
        images (list[pygame.Surface]): Animation frames.
        current_frame (int): Index of the frame currently displayed.
    """

    def __init__(self, images: list, lane: int, y: int = -200) -> None:
        """Initialise a coin.

        Args:
            images: Pre-cropped animation frames from the sprite sheet.
            lane: Starting lane index.
            y: Initial vertical position; defaults to above the screen.
        """
        self.x: int = lane
        self.y: float = y
        self.images = images
        self.current_frame: int = 0
        self._rect_center: tuple = (self.x * WIDTH // 3 + WIDTH // 6, self.y)
        self._update_image()

    def update(self, screen: pygame.Surface, speed: int) -> None:
        """Advance animation, move downward, and draw. Called once per frame.

        Args:
            screen: Main display surface.
            speed: Current global game speed.
        """
        self._fall(speed)
        self._draw(screen)
        self._animate()

    def get_rect(self) -> pygame.Rect:
        """Return the collision rectangle (slightly inset from the sprite).

        Returns:
            pygame.Rect used for overlap tests with the player.
        """
        cx, cy = self._rect_center
        return pygame.Rect(
            (cx - OFFSET // 2, cy - OFFSET // 2),
            (WIDTH // 3 - OFFSET, WIDTH // 3 - OFFSET),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw(self, screen: pygame.Surface) -> None:
        self._rect_center = (self.x * WIDTH // 3 + WIDTH // 6, self.y)
        cx, cy = self._rect_center
        screen.blit(self.image, (cx - WIDTH // 12, cy))

    def _fall(self, speed: int) -> None:
        self.y += speed

    def _animate(self) -> None:
        """Advance to the next frame with ~50 % probability each tick."""
        if randint(0, 1):
            self.current_frame = (self.current_frame + 1) % len(self.images)
            self._update_image()

    def _update_image(self) -> None:
        self.image = pygame.transform.scale(
            self.images[self.current_frame], (WIDTH // 6, WIDTH // 6)
        )
