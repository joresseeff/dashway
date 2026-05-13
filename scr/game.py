"""
game.py
-------
Core game loop: spawning, movement, collisions, power-ups, pause, and HUD.

Power-ups
---------
Three power-up types drop randomly alongside coins and cars:

* **Shield**      — absorbs one car collision (``P`` key to activate if held)
* **Slow Motion** — halves game speed for 4 seconds (automatic on pickup)
* **Multiplier**  — doubles coin value for 5 seconds (automatic on pickup)

The power-up queue is displayed as icons in the top-left corner of the HUD.
Pause is toggled with ESC and freezes all timers correctly.
"""

import time
import pygame
from random import randint, choice

from car import Car
from player import Player
from coin import Coin
from bomb import Bomb
from powerup import PowerUp, PowerUpType
from init import WIDTH, HEIGHT
from paths import resource
from paths import resource


class Game:
    """Manages a single play session from countdown to game-over.

    The session ends when ``self.close`` becomes True. The caller reads back
    ``bestScore``, ``coins``, ``numberBombs``, and ``session_duration``.

    Attributes:
        close (bool): True after the game-over animation finishes.
        score (int): Cars successfully avoided this session.
        bestScore (int): All-time best score.
        coins (int): Coins owned (persisted).
        numberBombs (int): Bombs remaining (persisted).
        session_duration (float): Seconds elapsed this session.
        pressed (dict): pygame key → bool mapping from main loop.
    """

    _BASE_SPEED      = 9
    _COUNTDOWN       = 3
    _OBJ_COOLDOWN    = 0.8
    _GAMEOVER_DELAY  = 1.5
    _SLOW_DURATION   = 4.0   # seconds slow-motion lasts
    _MULTI_DURATION  = 5.0   # seconds score multiplier lasts
    _POWERUP_CHANCE  = 8     # 1-in-N chance a spawn is a power-up

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
        self.screen     = screen
        self.pressed: dict = {}

        self._coin_sound  = coin_sound
        self._bomb_sound  = bomb_sound
        self._crash_sound = crash_sound

        # Session state
        self.score:           int   = 0
        self.bestScore:       int   = best_score
        self.coins:           int   = coins
        self.numberBombs:     int   = bombs
        self.speed:           int   = self._BASE_SPEED
        self.close:           bool  = False
        self.session_duration: float = 0.0

        # Object lists
        self._objects:  list = []
        self._bombs:    list = []
        self._powerups: list = []

        # Game-over
        self._game_over:      bool  = False
        self._game_over_time: float = 0.0
        self._crashed_car:    object = None

        # Pause
        self._paused:          bool  = False
        self._pause_start:     float = 0.0
        self._total_paused:    float = 0.0

        # Timers (real clock)
        self._obj_timer       = time.time()
        self._countdown_start = time.time()
        self._session_start   = time.time()

        # Power-up state
        self._shield_active: bool  = False
        self._slow_active:   bool  = False
        self._slow_end:      float = 0.0
        self._multi_active:  bool  = False
        self._multi_end:     float = 0.0
        self._held_powerups: list  = []   # queue of PowerUpType not yet used

        # One-shot key flags
        self._key_left_ready  = True
        self._key_right_ready = True
        self._key_space_ready = True
        self._key_p_ready     = True

        # Road scroll
        self._line_offset: int = 0

        # Assets
        self._boum_image  = pygame.image.load(resource("assets/boum.png"))
        bomb_img          = pygame.image.load(resource("assets/bomb.png"))
        self._bomb_icon   = pygame.transform.scale(bomb_img, (80, 80))
        self._coin_frames = self._slice_coin_sheet()
        self._car_surfaces = self._slice_car_sheet()

        # Fonts
        self._font           = pygame.font.Font(resource("munro.ttf"), 40)
        self._font_countdown = pygame.font.Font(resource("munro.ttf"), 100)
        self._font_pause     = pygame.font.Font(resource("munro.ttf"), 80)
        self._font_small     = pygame.font.Font(resource("munro.ttf"), 28)

        # Player
        self.player = Player(1, choice(self._car_surfaces))

        # Pre-populate bomb queue
        for _ in range(self.numberBombs):
            self._bombs.append(Bomb(self.player.x, self.player.y, self._bomb_icon))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self) -> None:
        """Advance the game by one frame."""
        if self._paused:
            self._draw_pause_overlay()
            return

        self._draw_road()

        in_countdown = time.time() < self._countdown_start + self._COUNTDOWN
        if in_countdown:
            self._draw_countdown()
        else:
            self._handle_input()
            self._spawn_objects()
            self._cull_objects()
            self._tick_powerups()

        self._increase_speed()
        self._draw_entities()
        self._check_collisions()
        self._draw_hud()

        # Update session duration only while playing
        if not self._game_over and not in_countdown:
            self.session_duration = time.time() - self._session_start - self._total_paused

    def toggle_pause(self) -> None:
        """Pause or resume the game, freezing all timers correctly."""
        if self._game_over:
            return
        if not self._paused:
            self._paused = True
            self._pause_start = time.time()
        else:
            paused_for = time.time() - self._pause_start
            self._total_paused  += paused_for
            # Shift all active timers forward so they don't fire immediately
            self._obj_timer       += paused_for
            self._countdown_start += paused_for
            if self._slow_active:
                self._slow_end += paused_for
            if self._multi_active:
                self._multi_end += paused_for
            if self._game_over:
                self._game_over_time += paused_for
            self._paused = False

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
            if self._key_space_ready and self._bombs and not self._bombs[0].active:
                self._bombs[0].launch()
                self.numberBombs -= 1
                self._key_space_ready = False
                pygame.mixer.Sound.play(self._bomb_sound)
        else:
            self._key_space_ready = True

        # P key — activate queued shield power-up
        if self.pressed.get(pygame.K_p):
            if self._key_p_ready and PowerUpType.SHIELD in self._held_powerups:
                self._held_powerups.remove(PowerUpType.SHIELD)
                self._shield_active = True
                self._key_p_ready = False
        else:
            self._key_p_ready = True

    # ------------------------------------------------------------------
    # Private — road and entities
    # ------------------------------------------------------------------

    def _draw_road(self) -> None:
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
        for pu in self._powerups:
            pu.update(self.screen, self.speed)

    def _draw_hud(self) -> None:
        """Render bomb count, score, coins, power-up icons, and timers."""
        # Bomb counter
        self.screen.blit(self._bomb_icon, (10, 10))
        self.screen.blit(
            self._font.render(str(self.numberBombs), True, "white"),
            (self._bomb_icon.get_width() + 20, 30),
        )

        # Score (top-right)
        label = "x2 " if self._multi_active else ""
        score_surf = self._font.render(f"{label}score : {self.score}", True,
                                       "gold" if self._multi_active else "white")
        self.screen.blit(score_surf, (WIDTH - score_surf.get_width() - 10, 10))

        # Coins
        coin_surf = self._font.render(f"coins : {self.coins}", True, "white")
        self.screen.blit(coin_surf, (WIDTH - coin_surf.get_width() - 10, 50))

        # Shield indicator
        if self._shield_active:
            shield_surf = self._font.render("🛡 SHIELD", True, "cyan")
            self.screen.blit(shield_surf, (WIDTH // 2 - shield_surf.get_width() // 2, 10))

        # Slow-motion timer bar
        if self._slow_active:
            remaining = max(0, self._slow_end - time.time())
            bar_w = int((remaining / self._SLOW_DURATION) * 120)
            pygame.draw.rect(self.screen, "white", pygame.Rect(10, 100, 120, 12), 2)
            pygame.draw.rect(self.screen, "deepskyblue", pygame.Rect(10, 100, bar_w, 12))
            self.screen.blit(self._font_small.render("SLOW", True, "deepskyblue"), (10, 114))

        # Multiplier timer bar
        if self._multi_active:
            remaining = max(0, self._multi_end - time.time())
            bar_w = int((remaining / self._MULTI_DURATION) * 120)
            pygame.draw.rect(self.screen, "white", pygame.Rect(10, 138, 120, 12), 2)
            pygame.draw.rect(self.screen, "gold", pygame.Rect(10, 138, bar_w, 12))
            self.screen.blit(self._font_small.render("x2", True, "gold"), (10, 152))

        # Queued power-ups (small icons, bottom-left)
        icon_labels = {"S": "cyan", "2x": "gold"}
        x_offset = 10
        for pu_type in self._held_powerups:
            label = "S" if pu_type == PowerUpType.SHIELD else "2x"
            color = icon_labels.get(label, "white")
            surf = self._font_small.render(f"[{label}]", True, color)
            self.screen.blit(surf, (x_offset, HEIGHT - 40))
            x_offset += surf.get_width() + 6

        # P-key hint if shield queued
        if PowerUpType.SHIELD in self._held_powerups:
            hint = self._font_small.render("P: activate shield", True, "cyan")
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

    def _draw_countdown(self) -> None:
        remaining = int((self._countdown_start + self._COUNTDOWN) - time.time()) + 1
        text = self._font_countdown.render(str(remaining), True, "black")
        self.screen.blit(
            text,
            (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2),
        )

    def _draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        pause_surf = self._font_pause.render("PAUSED", True, "white")
        self.screen.blit(
            pause_surf,
            (WIDTH // 2 - pause_surf.get_width() // 2, HEIGHT // 2 - 60),
        )
        hint = self._font_small.render("Press ESC to resume", True, "lightgray")
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 40))

    # ------------------------------------------------------------------
    # Private — spawning & culling
    # ------------------------------------------------------------------

    def _spawn_objects(self) -> None:
        if time.time() > self._obj_timer + self._OBJ_COOLDOWN:
            self._obj_timer = time.time()
            lane = randint(0, 2)
            roll = randint(1, self._POWERUP_CHANCE)
            if roll == 1:
                pu_type = choice(list(PowerUpType))
                self._powerups.append(PowerUp(pu_type, lane))
            elif roll == 2:
                self._objects.append(Coin(self._coin_frames, lane))
            else:
                self._objects.append(Car(choice(self._car_surfaces), lane))

    def _cull_objects(self) -> None:
        if self._objects and self._objects[0].y > HEIGHT + 200:
            if isinstance(self._objects[0], Car):
                self.score += 1
            self._objects.pop(0)

        if self._bombs and self._bombs[0].y < -50:
            self._bombs.pop(0)

        self._powerups = [p for p in self._powerups if p.y <= HEIGHT + 100]

    # ------------------------------------------------------------------
    # Private — power-up ticks
    # ------------------------------------------------------------------

    def _tick_powerups(self) -> None:
        now = time.time()
        if self._slow_active and now > self._slow_end:
            self._slow_active = False
            self.speed = self._BASE_SPEED + int((self.score ** 0.5) / 2)
        if self._multi_active and now > self._multi_end:
            self._multi_active = False

    def _apply_powerup(self, pu_type: "PowerUpType") -> None:
        now = time.time()
        if pu_type == PowerUpType.SHIELD:
            self._held_powerups.append(PowerUpType.SHIELD)
        elif pu_type == PowerUpType.SLOW:
            self._slow_active = True
            self._slow_end = now + self._SLOW_DURATION
            self.speed = max(3, self.speed // 2)
        elif pu_type == PowerUpType.MULTIPLIER:
            self._multi_active = True
            self._multi_end = now + self._MULTI_DURATION

    # ------------------------------------------------------------------
    # Private — collisions & game-over
    # ------------------------------------------------------------------

    def _check_collisions(self) -> None:
        hit_type, hit_obj = self.player.collide(self._objects)

        if hit_type == 1:   # coin
            self._objects.remove(hit_obj)
            gained = 2 if self._multi_active else 1
            self.coins += gained
            pygame.mixer.Sound.play(self._coin_sound)

        elif hit_type == 2:   # car
            if self._shield_active:
                # Shield absorbs the hit
                self._shield_active = False
                self._objects.remove(hit_obj)
            else:
                if not self._game_over:
                    self._game_over_time = time.time()
                    pygame.mixer.Sound.play(self._crash_sound)
                self._crashed_car = hit_obj
                self._trigger_game_over()

        # Power-up pickup
        for pu in list(self._powerups):
            if self.player.rect.colliderect(pu.get_rect()):
                self._apply_powerup(pu.type)
                self._powerups.remove(pu)

        # Bomb collision
        if self._bombs:
            b_type, b_obj = self._bombs[0].collide(self._objects)
            if b_type == 1:
                self._objects.remove(b_obj)
                self._bombs.pop(0)

    def _trigger_game_over(self) -> None:
        self._game_over = True
        self.speed = 0
        self._draw_boom()
        if self.score > self.bestScore:
            self.bestScore = self.score
        if time.time() > self._game_over_time + self._GAMEOVER_DELAY:
            self.close = True

    def _draw_boom(self) -> None:
        boum_w = self._boum_image.get_rect().w
        boum_h = self._boum_image.get_rect().h
        boom_y = (
            self.player.y - boum_h // 2
            if self.player.y > self._crashed_car.y
            else self.player.y + boum_h // 2
        )
        self.screen.blit(self._boum_image, (self.player.x * WIDTH // 3 - boum_w // 6, boom_y))

    # ------------------------------------------------------------------
    # Private — difficulty
    # ------------------------------------------------------------------

    def _increase_speed(self) -> None:
        if not self._slow_active:
            threshold = (self.speed - self._BASE_SPEED) ** 2 * 1.5
            if self.score >= threshold:
                self.speed += 1

    # ------------------------------------------------------------------
    # Private — sprite sheet slicing
    # ------------------------------------------------------------------

    def _slice_coin_sheet(self) -> list:
        sheet   = pygame.image.load(resource("assets/coin.png"))
        frame_w = sheet.get_width() // 13
        frames  = []
        for i in range(13):
            frame = pygame.Surface((frame_w, sheet.get_height()))
            frame.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, sheet.get_height()))
            frame.set_colorkey([0, 0, 0])
            frames.append(frame)
        return frames

    def _slice_car_sheet(self) -> list:
        sheet      = pygame.image.load(resource("assets/cars.png"))
        cols, rows = 3, 2
        w = sheet.get_width()  // cols
        h = sheet.get_height() // rows
        sprites = []
        for row in range(rows):
            for col in range(cols):
                surf = pygame.Surface((w - 20, h - 10))
                surf.blit(sheet, (0, 0), (col * w + 10, row * h + 5, w - 20, h - 10))
                surf.set_colorkey([0, 0, 0])
                sprites.append(surf)
        return sprites
