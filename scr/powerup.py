"""
powerup.py
----------
Power-up sprite and type enum.

Three power-up types exist:

* ``SHIELD``     — absorbs one car collision (activated manually with P)
* ``SLOW``       — halves game speed for a few seconds (automatic on pickup)
* ``MULTIPLIER`` — doubles coin earnings for a few seconds (automatic on pickup)

Power-ups fall down the screen exactly like coins and disappear if not
collected before leaving the bottom edge.
"""

import pygame
from enum import Enum, auto
from init import WIDTH

from paths import resource
_FONT_PATH = resource("munro.ttf")


class PowerUpType(Enum):
    """Enumeration of all available power-up categories."""
    SHIELD     = auto()
    SLOW       = auto()
    MULTIPLIER = auto()


# Visual config per type: (label text, RGB colour)
_STYLE: dict[PowerUpType, tuple[str, tuple]] = {
    PowerUpType.SHIELD:     ("S",  (0,   200, 255)),
    PowerUpType.SLOW:       ("SL", (100, 149, 237)),
    PowerUpType.MULTIPLIER: ("x2", (255, 215,   0)),
}


class PowerUp:
    """A falling power-up token drawn as a coloured circle with a label.

    Attributes:
        type (PowerUpType): The kind of power-up this instance represents.
        x (int): Lane index (0, 1, or 2).
        y (float): Current vertical pixel position.
    """

    _RADIUS = 28  # circle radius in pixels

    def __init__(self, pu_type: PowerUpType, lane: int, y: int = -200) -> None:
        """Initialise a power-up token.

        Args:
            pu_type: Which power-up this represents.
            lane: Starting lane index.
            y: Initial vertical position; defaults to above the screen.
        """
        self.type  = pu_type
        self.x     = lane
        self.y     = float(y)
        self._label, self._color = _STYLE[pu_type]
        self._font = pygame.font.Font(_FONT_PATH, 30)
        self._center_x = self.x * WIDTH // 3 + WIDTH // 6

    def update(self, screen: pygame.Surface, speed: int) -> None:
        """Move downward and draw. Called once per frame.

        Args:
            screen: Main display surface.
            speed: Current global game speed.
        """
        self.y += speed
        self._center_x = self.x * WIDTH // 3 + WIDTH // 6
        self._draw(screen)

    def get_rect(self) -> pygame.Rect:
        """Return a square collision rect centred on the power-up.

        Returns:
            pygame.Rect for overlap tests with the player.
        """
        r = self._RADIUS
        return pygame.Rect(self._center_x - r, self.y - r, r * 2, r * 2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw(self, screen: pygame.Surface) -> None:
        cx = self._center_x
        cy = int(self.y)
        r  = self._RADIUS

        # Outer glow ring
        pygame.draw.circle(screen, "white",      (cx, cy), r + 3)
        pygame.draw.circle(screen, self._color,  (cx, cy), r)

        # Centred label
        label_surf = self._font.render(self._label, True, "white")
        screen.blit(
            label_surf,
            (cx - label_surf.get_width() // 2, cy - label_surf.get_height() // 2),
        )
