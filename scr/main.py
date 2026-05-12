"""
main.py
-------
Entry point for Dashway.

Manages the application lifecycle: window creation, sound loading, menu
navigation, save/load, and the top-level game loop.

Usage::

    cd scr
    python main.py
"""

import sys
import pygame

from game import Game
from menu import Menu
from init import WIDTH, HEIGHT


# ---------------------------------------------------------------------------
# Save file helpers
# ---------------------------------------------------------------------------

SAVE_PATH = "../save.txt"


def load_save() -> tuple[int, int, int]:
    """Load persisted game data from disk.

    Returns:
        Tuple of ``(best_score, coins, bombs)``. Returns ``(0, 0, 0)`` if the
        save file is missing or malformed.
    """
    try:
        with open(SAVE_PATH) as f:
            lines = f.readlines()
        return int(lines[0]), int(lines[1]), int(lines[2])
    except (FileNotFoundError, ValueError, IndexError):
        return 0, 0, 0


def write_save(best_score: int, coins: int, bombs: int) -> None:
    """Persist game data to disk.

    Args:
        best_score: All-time highest score.
        coins: Coins owned by the player.
        bombs: Bombs owned by the player.
    """
    with open(SAVE_PATH, "w") as f:
        f.write(f"{best_score}\n{coins}\n{bombs}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Initialise pygame and run the main application loop."""
    pygame.init()

    # Window
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DASHWAY")
    icon = pygame.image.load("../assets/lambo.png").convert()
    pygame.display.set_icon(icon)

    clock = pygame.time.Clock()
    FPS = 60

    # ------------------------------------------------------------------ #
    # Sounds                                                               #
    # ------------------------------------------------------------------ #
    main_music    = pygame.mixer.Sound("../sounds/mainMusic.mp3")
    btn_sound     = pygame.mixer.Sound("../sounds/clickButton.mp3")
    coin_sound    = pygame.mixer.Sound("../sounds/carCollide.mp3")   # reused as coin sfx
    bomb_sound    = pygame.mixer.Sound("../sounds/launchBomb.mp3")
    crash_sound   = pygame.mixer.Sound("../sounds/carCollide.mp3")

    pygame.mixer.Sound.play(main_music, loops=-1)

    # ------------------------------------------------------------------ #
    # Persistent state                                                     #
    # ------------------------------------------------------------------ #
    best_score, coins, bombs = load_save()

    # ------------------------------------------------------------------ #
    # Main menu                                                            #
    # ------------------------------------------------------------------ #
    bg_main = pygame.transform.scale(
        pygame.image.load("../assets/bgMenu.png"), (WIDTH, HEIGHT)
    )
    btn_img_green = pygame.image.load("../assets/greenButton.png")

    main_menu = Menu(screen, bg_main)
    main_menu.add_label(WIDTH // 2 - 150, HEIGHT // 12,          "DASHWAY",           100, "blue",  0)
    main_menu.add_label(WIDTH // 2 - 175, int(HEIGHT / 6 * 1.5), f"Best: {best_score}", 70, "blue",  1)
    main_menu.add_button(0, WIDTH // 2 - 100, int(HEIGHT / 3 * 1.5), 200, 70, btn_img_green, "PLAY",  50, "blue")
    main_menu.add_button(1, WIDTH // 2 - 100, int(HEIGHT / 3 * 2),   200, 70, btn_img_green, "SHOP",  50, "blue")
    main_menu.add_button(2, WIDTH // 2 - 100, int(HEIGHT / 3 * 2.5), 200, 70, btn_img_green, "EXIT",  50, "blue")

    # ------------------------------------------------------------------ #
    # Shop menu                                                            #
    # ------------------------------------------------------------------ #
    bg_shop = pygame.transform.scale(
        pygame.image.load("../assets/shopBG.png"), (WIDTH, HEIGHT)
    )
    btn_img_red  = pygame.image.load("../assets/redButton.png")
    btn_img_gold = pygame.image.load("../assets/goldButton.png")

    shop_menu = Menu(screen, bg_shop)
    shop_menu.add_label(WIDTH // 2 - 80,  HEIGHT // 12,          "SHOP",                100, "white", 2)
    shop_menu.add_button(5, 50, HEIGHT // 3 - 50,          400, 150, btn_img_gold, "",              50, "black")
    shop_menu.add_label(80,                HEIGHT // 3 - 40,      f"coins : {coins}",   50, "black", 3)
    shop_menu.add_label(80,                HEIGHT // 3 + 20,      f"bombs : {bombs}",   50, "black", 4)
    shop_menu.add_button(3, 50, HEIGHT // 3 + 120,         400, 150, btn_img_red,  "Bomb : 3 coins", 50, "black")
    shop_menu.add_button(4, 50, HEIGHT // 3 * 2 + 100,    400, 150, btn_img_red,  "EXIT",           50, "black")

    # ------------------------------------------------------------------ #
    # Application loop                                                     #
    # ------------------------------------------------------------------ #
    window = "menu"        # "menu" | "shop" | "game"
    reset_game = True
    mouse_was_down = False
    game = Game(screen, best_score, coins, bombs, coin_sound, bomb_sound, crash_sound)

    running = True
    while running:

        # ---- Recreate game session when switching to "game" ---------- #
        if reset_game and window == "game":
            game = Game(screen, best_score, coins, bombs, coin_sound, bomb_sound, crash_sound)
            reset_game = False

        # ---- Draw active window ------------------------------------- #
        if window == "game":
            screen.fill((128, 129, 129))
            game.update()
            if game.close:
                best_score, coins, bombs = game.bestScore, game.coins, game.numberBombs
                window = "menu"
                reset_game = True
                main_menu.update_label(
                    WIDTH // 2 - 175, int(HEIGHT / 6 * 1.5),
                    f"Best: {best_score}", 70, "blue", 1
                )

        elif window == "menu":
            main_menu.update()

        elif window == "shop":
            shop_menu.update()

        # ---- Events ------------------------------------------------- #
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False
                write_save(best_score, coins, bombs)

            if event.type == pygame.KEYDOWN:
                game.pressed[event.key] = True
            if event.type == pygame.KEYUP:
                game.pressed[event.key] = False

            # Single-click detection
            left_btn_down = pygame.mouse.get_pressed(3)[0]

            if left_btn_down and not mouse_was_down:
                mouse_was_down = True
                mx, my = pygame.mouse.get_pos()

                if window == "menu":
                    hit, btn_id = main_menu.collide(mx, my)
                    if hit:
                        pygame.mixer.Sound.play(btn_sound)
                        if btn_id == 0:
                            window = "game"
                        elif btn_id == 1:
                            window = "shop"
                            shop_menu.update_label(80, HEIGHT // 3 - 40, f"coins : {coins}", 50, "black", 3)
                            shop_menu.update_label(80, HEIGHT // 3 + 20, f"bombs : {bombs}", 50, "black", 4)
                        elif btn_id == 2:
                            running = False
                            write_save(best_score, coins, bombs)

                elif window == "shop":
                    hit, btn_id = shop_menu.collide(mx, my)
                    if hit:
                        if btn_id == 3:
                            pygame.mixer.Sound.play(btn_sound)
                            if coins >= 3:
                                coins  -= 3
                                bombs  += 1
                                shop_menu.update_label(80, HEIGHT // 3 - 40, f"coins : {coins}", 50, "black", 3)
                                shop_menu.update_label(80, HEIGHT // 3 + 20, f"bombs : {bombs}", 50, "black", 4)
                        elif btn_id == 4:
                            pygame.mixer.Sound.play(btn_sound)
                            window = "menu"

            elif not left_btn_down:
                mouse_was_down = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
