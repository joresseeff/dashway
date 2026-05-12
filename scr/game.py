"""
game.py
-------
Core game loop: spawning, movement, collisions, scoring, and rendering.
"""

import time
import pygame
from random import randint, choice

from car import Car
from player import Player
from coin import Coin
from bomb import Bomb
from init import WIDTH, HEIGHT


class Game:
    """Manages a single play session from countdown to game-over.

    The game session ends when ``self.close`` becomes True, at which point
    the caller (main.py) reads back ``bestScore``, ``coins``, and
    ``numberBombs`` before switching back to the menu.

    Attributes:
        close (bool): Set to True after the game-over animation finishes.
        score (int): Cars successfully avoided during this session.
        bestScore (int): All-time best score (updated on game-over).
        coins (int): Total coins owned (persisted across sessions).
        numberBombs (int): Bombs remaining (persisted across sessions).
        pressed (dict): Mapping of pygame key constants to pressed state.
    """

    # Speed formula: speed increases by 1 every time score exceeds (speed-9)²×1.5
    _BASE_SPEED = 9
    _COUNTDOWN   = 3      # seconds before input is accepted
    _OBJ_COOLDOWN = 0.8   # seconds between object spawns
    _GAMEOVER_DELAY = 1.5 # seconds the boom image is shown before closing

    def __init__(
        self,
        screen: pygame.Surface,
        best_score: int,
        coins: int,
        bombs: int,
        coin_sound: pygame.mixer.Sound,
        bomb_sound: pygame.mixer.Sound,
        crash_sound: pygame.mixer.Sound,
    ) -> None:
        """Initialise a new game session.

        Args:
            screen: Main display surface.
            best_score: Previous best score loaded from save data.
            coins: Coins available at session start.
            bombs: Bombs available at session start.
            coin_sound: Sound played when collecting a coin.
            bomb_sound: Sound played when launching a bomb.
            crash_sound: Sound played on car collision.
        """
        self.screen = screen
        self.pressed: dict = {}

        # Sounds
        self._coin_sound  = coin_sound
        self._bomb_sound  = bomb_sound
        self._crash_sound = crash_sound

        # Session state
        self.score: int = 0
        self.bestScore: int = best_score
        self.coins: int = coins
        self.numberBombs: int = bombs
        self.speed: int = self._BASE_SPEED
        self.close: bool = False

        # Object lists
        self._objects: list = []
        self._bombs:   list = []

        # Game-over state
        self._game_over: bool = False
        self._game_over_time: float = 0.0
        self._crashed_car: object = None

        # Timers
        self._obj_timer = time.time()
        self._countdown_start = time.time()

        # One-shot key flags (prevent key-hold from repeating actions)
        self._key_left_ready  = True
        self._key_right_ready = True
        self._key_space_ready = True

        # Lane-line scroll offset
        self._line_offset: int = 0

        # Assets
        self._boum_image = pygame.image.load("../assets/boum.png")
        bomb_img = pygame.image.load("../assets/bomb.png")
        self._bomb_icon = pygame.transform.scale(bomb_img, (80, 80))

        self._coin_frames  = self._slice_coin_sheet()
        self._car_surfaces = self._slice_car_sheet()

        # Fonts
        self._font = pygame.font.Font("../munro.ttf", 40)
        self._font_countdown = pygame.font.Font("../munro.ttf", 100)

        # Player
        self.player = Player(1, choice(self._car_surfaces))

        # Pre-populate bomb queue
        for _ in range(self.numberBombs):
            self._bombs.append(Bomb(self.player.x, self.player.y, self._bomb_icon))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self) -> None:
        """Advance the game by one frame. Must be called every tick."""
        self._draw_road()

        in_countdown = time.time() < self._countdown_start + self._COUNTDOWN
        if in_countdown:
            self._draw_countdown()
        else:
            self._handle_input()
            self._spawn_objects()
            self._cull_objects()

        self._increase_speed()
        self._draw_entities()
        self._check_collisions()
        self._draw_hud()

    # ------------------------------------------------------------------
    # Private — input
    # ------------------------------------------------------------------

    def _handle_input(self) -> None:
        if self._game_over:
            return

        if self.pressed.get(pygame.K_LEFT):
            if self._key_left_ready:
                self.player.left()
                for b in self._bombs:
                    b.left()
                self._key_left_ready = False
        else:
            self._key_left_ready = True

        if self.pressed.get(pygame.K_RIGHT):
            if self._key_right_ready:
                self.player.right()
                for b in self._bombs:
                    b.right()
                self._key_right_ready = False
        else:
            self._key_right_ready = True

        if self.pressed.get(pygame.K_SPACE):
            if (
                self._key_space_ready
                and self._bombs
                and not self._bombs[0].active
            ):
                self._bombs[0].launch()
                self.numberBombs -= 1
                self._key_space_ready = False
                pygame.mixer.Sound.play(self._bomb_sound)
        else:
            self._key_space_ready = True

    # ------------------------------------------------------------------
    # Private — road and entities
    # ------------------------------------------------------------------

    def _draw_road(self) -> None:
        """Draw the two dashed lane dividers with a scrolling effect."""
        for lane_x in (WIDTH // 3, (WIDTH // 3) * 2):
            pygame.draw.rect(self.screen, "white", pygame.Rect(lane_x - 5, 0, 10, HEIGHT))
            for y in range(-100 + self._line_offset, HEIGHT + self._line_offset, 80):
                pygame.draw.rect(
                    self.screen, (128, 129, 129), pygame.Rect(lane_x - 5, y, 10, 50)
                )
        self._line_offset = (self._line_offset + self.speed) % 80

    def _draw_entities(self) -> None:
        self.player.draw(self.screen)
        for obj in self._objects:
            obj.update(self.screen, self.speed)
        for bomb in self._bombs:
            bomb.update(self.screen)

    def _draw_hud(self) -> None:
        """Render bomb count, score, and coin count on screen."""
        # Bomb counter (top-left)
        self.screen.blit(self._bomb_icon, (10, 10))
        bomb_text = self._font.render(str(self.numberBombs), True, "white")
        self.screen.blit(bomb_text, (self._bomb_icon.get_width() + 20, 30))

        # Score (top-right)
        score_surf = self._font.render(f"score : {self.score}", True, "white")
        self.screen.blit(score_surf, (WIDTH - score_surf.get_width() - 10, 10))

        # Coins (below score)
        coin_surf = self._font.render(f"coins : {self.coins}", True, "white")
        self.screen.blit(coin_surf, (WIDTH - coin_surf.get_width() - 10, 50))

    def _draw_countdown(self) -> None:
        remaining = int((self._countdown_start + self._COUNTDOWN) - time.time()) + 1
        text = self._font_countdown.render(str(remaining), True, "black")
        self.screen.blit(
            text,
            (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2),
        )

    # ------------------------------------------------------------------
    # Private — spawning & culling
    # ------------------------------------------------------------------

    def _spawn_objects(self) -> None:
        """Spawn a coin (1-in-3 chance) or an enemy car at a random lane."""
        if time.time() > self._obj_timer + self._OBJ_COOLDOWN:
            self._obj_timer = time.time()
            lane = randint(0, 2)
            if randint(1, 3) == 1:
                self._objects.append(Coin(self._coin_frames, lane))
            else:
                self._objects.append(Car(choice(self._car_surfaces), lane))

    def _cull_objects(self) -> None:
        """Remove off-screen objects; award a point for each dodged Car."""
        if self._objects and self._objects[0].y > HEIGHT + 200:
            if isinstance(self._objects[0], Car):
                self.score += 1
            self._objects.pop(0)

        if self._bombs and self._bombs[0].y < -50:
            self._bombs.pop(0)

    # ------------------------------------------------------------------
    # Private — collision & game-over
    # ------------------------------------------------------------------

    def _check_collisions(self) -> None:
        hit_type, hit_obj = self.player.collide(self._objects)

        if hit_type == 1:          # coin collected
            self._objects.remove(hit_obj)
            self.coins += 1
            pygame.mixer.Sound.play(self._coin_sound)

        elif hit_type == 2:        # car collision → game over
            if not self._game_over:
                self._game_over_time = time.time()
                pygame.mixer.Sound.play(self._crash_sound)
            self._crashed_car = hit_obj
            self._trigger_game_over()

        # Bomb collision
        if self._bombs:
            b_type, b_obj = self._bombs[0].collide(self._objects)
            if b_type == 1:
                self._objects.remove(b_obj)
                self._bombs.pop(0)

    def _trigger_game_over(self) -> None:
        """Freeze the game, show boom image, then signal main loop to close."""
        self._game_over = True
        self.speed = 0
        self._draw_boom()
        if self.score > self.bestScore:
            self.bestScore = self.score
        if time.time() > self._game_over_time + self._GAMEOVER_DELAY:
            self.close = True

    def _draw_boom(self) -> None:
        """Blit the explosion image between player and colliding car."""
        boum_w = self._boum_image.get_rect().w
        boum_h = self._boum_image.get_rect().h
        if self.player.y > self._crashed_car.y:
            boom_y = self.player.y - boum_h // 2
        else:
            boom_y = self.player.y + boum_h // 2
        boom_x = (self.player.x * WIDTH // 3) - boum_w // 6
        self.screen.blit(self._boum_image, (boom_x, boom_y))

    # ------------------------------------------------------------------
    # Private — difficulty scaling
    # ------------------------------------------------------------------

    def _increase_speed(self) -> None:
        """Raise speed by 1 when score crosses the next threshold."""
        threshold = (self.speed - self._BASE_SPEED) ** 2 * 1.5
        if self.score >= threshold:
            self.speed += 1

    # ------------------------------------------------------------------
    # Private — sprite-sheet slicing
    # ------------------------------------------------------------------

    def _slice_coin_sheet(self) -> list:
        """Cut the coin animation strip into individual frames.

        Returns:
            List of 13 pygame.Surface frames.
        """
        sheet = pygame.image.load("../assets/coin.png")
        frame_w = sheet.get_width() // 13
        frames = []
        for i in range(13):
            frame = pygame.Surface((frame_w, sheet.get_height()))
            frame.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, sheet.get_height()))
            frame.set_colorkey([0, 0, 0])
            frames.append(frame)
        return frames

    def _slice_car_sheet(self) -> list:
        """Cut the car sprite sheet (3 columns × 2 rows) into 6 surfaces.

        Returns:
            List of up to 6 pygame.Surface car sprites.
        """
        sheet = pygame.image.load("../assets/cars.png")
        cols, rows = 3, 2
        w = sheet.get_width() // cols
        h = sheet.get_height() // rows
        sprites = []
        for row in range(rows):
            for col in range(cols):
                surf = pygame.Surface((w - 20, h - 10))
                surf.blit(sheet, (0, 0), (col * w + 10, row * h + 5, w - 20, h - 10))
                surf.set_colorkey([0, 0, 0])
                sprites.append(surf)
        return sprites
