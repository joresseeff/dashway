"""
button.py
---------
Clickable UI button with a background image and centred label.
"""

import pygame


class Button:
    """A rectangular button rendered from a background image.

    Attributes:
        id (int): Unique identifier used by Menu to distinguish buttons.
        x (int): Left edge position in pixels.
        y (int): Top edge position in pixels.
        w (int): Width in pixels.
        h (int): Height in pixels.
    """

    def __init__(
        self,
        id: int,
        x: int,
        y: int,
        w: int,
        h: int,
        image: pygame.Surface,
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: str,
    ) -> None:
        """Initialise the button.

        Args:
            id: Unique identifier for this button.
            x: Left edge position (pixels).
            y: Top edge position (pixels).
            w: Width (pixels).
            h: Height (pixels).
            image: Background surface; will be scaled to (w, h).
            screen: Main display surface to draw onto.
            text: Label displayed at the centre of the button.
            font: Pygame font used to render the label.
            color: Label colour (name or hex string).
        """
        self.id = id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.screen = screen
        self.text = text
        self.font = font
        self.color = color
        self.image = pygame.transform.scale(image, (w, h))

    def draw(self) -> None:
        """Draw the background image and the centred text label."""
        self.screen.blit(self.image, (self.x, self.y))
        label = self.font.render(self.text, True, self.color)
        label_x = self.x + self.w // 2 - label.get_width() // 2
        label_y = self.y + self.h // 2 - label.get_height() // 2
        self.screen.blit(label, (label_x, label_y))

    def collide(self, x: int, y: int) -> bool:
        """Return True if the point (x, y) lies inside this button's rect.

        Args:
            x: Horizontal coordinate to test.
            y: Vertical coordinate to test.

        Returns:
            True if the point is inside the button, False otherwise.
        """
        return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h
