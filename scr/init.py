"""
init.py
-------
Global constants shared across all game modules.
"""

# Window dimensions (pixels)
WIDTH: int = 500
HEIGHT: int = 800

# Horizontal padding to center sprites inside a lane
OFFSET: float = WIDTH / 10

# Size of every car/player sprite: (width, height)
CAR_SIZE: tuple = (WIDTH // 3 - OFFSET, (WIDTH // 3 - OFFSET) * 1.7)
