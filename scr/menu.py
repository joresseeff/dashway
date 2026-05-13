from paths import resource
"""
menu.py
-------
Generic menu screen: background image, labels, and clickable buttons.
"""

import pygame
from button import Button


class Menu:
    """A full-screen menu composed of a background, labels, and buttons.

    Labels are stored as ``(surface, position, id)`` tuples so they can be
    updated individually by id without rebuilding the whole menu.

    Attributes:
        screen (pygame.Surface): Main display surface.
        bg (pygame.Surface): Background image (must already match window size).
        buttons (list[Button]): All registered buttons.
        labels (list[tuple]): All registered labels as (surface, pos, id).
    """

    def __init__(self, screen: pygame.Surface, bg: pygame.Surface) -> None:
        """Initialise the menu.

        Args:
            screen: Main display surface.
            bg: Background image, pre-scaled to the window dimensions.
        """
        self.screen = screen
        self.bg = bg
        self.buttons: list[Button] = []
        self.labels: list[tuple] = []
        self._font = pygame.font.Font(resource("munro.ttf"), 50)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def update(self) -> None:
        """Draw background, all buttons, and all labels for one frame."""
        self.screen.blit(self.bg, (0, 0))
        for button in self.buttons:
            button.draw()
        for surface, pos, _ in self.labels:
            self.screen.blit(surface, pos)

    def add_button(
        self,
        id: int,
        x: int,
        y: int,
        w: int,
        h: int,
        image: pygame.Surface,
        text: str,
        size: int,
        color: str,
    ) -> None:
        """Register a new button on this menu.

        Args:
            id: Unique identifier (used in collide return value).
            x: Left edge position (pixels).
            y: Top edge position (pixels).
            w: Width (pixels).
            h: Height (pixels).
            image: Background image for the button.
            text: Label text.
            size: Font size in points.
            color: Label colour.
        """
        font = pygame.font.Font(resource("munro.ttf"), size)
        self.buttons.append(Button(id, x, y, w, h, image, self.screen, text, font, color))

    def add_label(
        self, x: int, y: int, text: str, size: int, color: str, id: int
    ) -> None:
        """Register a new static text label.

        Args:
            x: Left edge position (pixels).
            y: Top edge position (pixels).
            text: Text to display.
            size: Font size in points.
            color: Text colour.
            id: Unique identifier so the label can be updated later.
        """
        font = pygame.font.Font(resource("munro.ttf"), size)
        surface = font.render(text, True, color)
        self.labels.append((surface, (x, y), id))

    def update_label(
        self, x: int, y: int, text: str, size: int, color: str, id: int
    ) -> None:
        """Replace the label matching *id* with new content.

        Args:
            x: New left edge position (pixels).
            y: New top edge position (pixels).
            text: New text string.
            size: Font size in points.
            color: Text colour.
            id: Identifier of the label to update.
        """
        font = pygame.font.Font(resource("munro.ttf"), size)
        new_surface = font.render(text, True, color)
        self.labels = [
            (new_surface, (x, y), id) if lbl_id == id else (surf, pos, lbl_id)
            for surf, pos, lbl_id in self.labels
        ]

    def collide(self, x: int, y: int) -> tuple:
        """Check whether any button contains the point (x, y).

        Args:
            x: Mouse x position.
            y: Mouse y position.

        Returns:
            ``(True, button_id)`` if a button was hit, ``(False, 0)`` otherwise.
        """
        for button in self.buttons:
            if button.collide(x, y):
                return (True, button.id)
        return (False, 0)

    # ------------------------------------------------------------------
    # Backward-compatibility aliases (snake_case ↔ camelCase)
    # ------------------------------------------------------------------
    def addButton(self, id, x, y, w, h, image, text, size, color):
        self.add_button(id, x, y, w, h, image, text, size, color)

    def addLabel(self, x, y, text, size, color, id):
        self.add_label(x, y, text, size, color, id)

    def updateLabel(self, x, y, text, size, color, id):
        self.update_label(x, y, text, size, color, id)
