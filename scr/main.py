"""
main.py
-------
Entry point for Dashway.

Manages the application lifecycle: window creation, sound loading, menu
navigation, database save/load, and the top-level game loop.

Usage::

    cd scr
    python main.py
"""

import sys
import pygame

from game import Game
from menu import Menu
from database import Database
from init import WIDTH, HEIGHT


def _build_main_menu(screen, bg, btn_img, best_score):
    """Construct and return the main menu instance."""
    m = Menu(screen, bg)
    m.add_label(WIDTH // 2 - 150, HEIGHT // 12,          "DASHWAY",              100, "blue",  0)
    m.add_label(WIDTH // 2 - 175, int(HEIGHT / 6 * 1.5), f"Best: {best_score}",   70, "blue",  1)
    m.add_button(0, WIDTH // 2 - 100, int(HEIGHT / 3 * 1.5), 200, 70, btn_img, "PLAY",  50, "blue")
    m.add_button(1, WIDTH // 2 - 100, int(HEIGHT / 3 * 2),   200, 70, btn_img, "SHOP",  50, "blue")
    m.add_button(2, WIDTH // 2 - 100, int(HEIGHT / 3 * 2.5), 200, 70, btn_img, "SCORES", 50, "blue")
    m.add_button(3, WIDTH // 2 - 100, int(HEIGHT / 3 * 3),   200, 70, btn_img, "EXIT",  50, "blue")
    return m


def _build_shop_menu(screen, bg, btn_red, btn_gold, coins, bombs):
    """Construct and return the shop menu instance."""
    m = Menu(screen, bg)
    m.add_label(WIDTH // 2 - 80,  HEIGHT // 12,       "SHOP",             100, "white", 2)
    m.add_button(5, 50, HEIGHT // 3 - 50,      400, 150, btn_gold, "",               50, "black")
    m.add_label(80, HEIGHT // 3 - 40,          f"coins : {coins}",  50, "black", 3)
    m.add_label(80, HEIGHT // 3 + 20,          f"bombs : {bombs}",  50, "black", 4)
    m.add_button(6, 50, HEIGHT // 3 + 120,     400, 150, btn_red, "Bomb : 3 coins",  50, "black")
    m.add_button(7, 50, HEIGHT // 3 * 2 + 100, 400, 150, btn_red, "EXIT",            50, "black")
    return m


def _build_scores_menu(screen, bg, btn_img, db: Database):
    """Construct and return the leaderboard menu."""
    m = Menu(screen, bg)
    m.add_label(WIDTH // 2 - 130, HEIGHT // 12, "TOP SCORES", 80, "blue", 10)

    top = db.get_top_scores()
    if top:
        for entry in top:
            y = HEIGHT // 4 + entry["rank"] * 80
            text = f"#{entry['rank']}  {entry['score']} pts  {entry['date']}"
            m.add_label(40, y, text, 35, "blue", 10 + entry["rank"])
    else:
        m.add_label(WIDTH // 2 - 160, HEIGHT // 2, "No scores yet!", 50, "blue", 11)

    m.add_button(8, WIDTH // 2 - 100, HEIGHT - 120, 200, 70, btn_img, "BACK", 50, "blue")
    return m


def main() -> None:
    """Initialise pygame and run the main application loop."""
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DASHWAY")
    icon = pygame.image.load("../assets/lambo.png").convert()
    pygame.display.set_icon(icon)

    clock = pygame.time.Clock()
    FPS = 60

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    db = Database()
    coins, bombs = db.load_player()
    best_score = db.get_best_score()

    # ------------------------------------------------------------------ #
    # Sounds                                                               #
    # ------------------------------------------------------------------ #
    main_music  = pygame.mixer.Sound("../sounds/mainMusic.mp3")
    btn_sound   = pygame.mixer.Sound("../sounds/clickButton.mp3")
    coin_sound  = pygame.mixer.Sound("../sounds/carCollide.mp3")
    bomb_sound  = pygame.mixer.Sound("../sounds/launchBomb.mp3")
    crash_sound = pygame.mixer.Sound("../sounds/carCollide.mp3")
    pygame.mixer.Sound.play(main_music, loops=-1)

    # ------------------------------------------------------------------ #
    # Shared assets                                                        #
    # ------------------------------------------------------------------ #
    bg_main  = pygame.transform.scale(pygame.image.load("../assets/bgMenu.png"),  (WIDTH, HEIGHT))
    bg_shop  = pygame.transform.scale(pygame.image.load("../assets/shopBG.png"),  (WIDTH, HEIGHT))
    btn_green = pygame.image.load("../assets/greenButton.png")
    btn_red   = pygame.image.load("../assets/redButton.png")
    btn_gold  = pygame.image.load("../assets/goldButton.png")

    # ------------------------------------------------------------------ #
    # Menus                                                                #
    # ------------------------------------------------------------------ #
    main_menu   = _build_main_menu(screen, bg_main, btn_green, best_score)
    shop_menu   = _build_shop_menu(screen, bg_shop, btn_red, btn_gold, coins, bombs)
    scores_menu = _build_scores_menu(screen, bg_main, btn_green, db)

    # ------------------------------------------------------------------ #
    # Application loop                                                     #
    # ------------------------------------------------------------------ #
    window = "menu"
    reset_game = True
    mouse_was_down = False
    game = Game(screen, best_score, coins, bombs, coin_sound, bomb_sound, crash_sound)

    running = True
    while running:

        # ---- Recreate game session ----------------------------------- #
        if reset_game and window == "game":
            game = Game(screen, best_score, coins, bombs, coin_sound, bomb_sound, crash_sound)
            reset_game = False

        # ---- Draw active window ------------------------------------- #
        if window == "game":
            screen.fill((128, 129, 129))
            game.update()
            if game.close:
                # Persist results
                best_score = game.bestScore
                coins      = game.coins
                bombs      = game.numberBombs
                db.add_score(game.score, game.session_duration)
                db.save_player(coins, bombs)
                window = "menu"
                reset_game = True
                main_menu.update_label(
                    WIDTH // 2 - 175, int(HEIGHT / 6 * 1.5),
                    f"Best: {best_score}", 70, "blue", 1,
                )
                # Rebuild scores menu with updated data
                scores_menu = _build_scores_menu(screen, bg_main, btn_green, db)

        elif window == "menu":
            main_menu.update()
        elif window == "shop":
            shop_menu.update()
        elif window == "scores":
            scores_menu.update()

        # ---- Events ------------------------------------------------- #
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                db.save_player(coins, bombs)
                running = False

            if event.type == pygame.KEYDOWN:
                game.pressed[event.key] = True
                # Global pause toggle with ESC while in game
                if event.key == pygame.K_ESCAPE and window == "game":
                    game.toggle_pause()

            if event.type == pygame.KEYUP:
                game.pressed[event.key] = False

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
                            scores_menu = _build_scores_menu(screen, bg_main, btn_green, db)
                            window = "scores"
                        elif btn_id == 3:
                            db.save_player(coins, bombs)
                            running = False

                elif window == "shop":
                    hit, btn_id = shop_menu.collide(mx, my)
                    if hit:
                        if btn_id == 6:
                            pygame.mixer.Sound.play(btn_sound)
                            if coins >= 3:
                                coins -= 3
                                bombs += 1
                                shop_menu.update_label(80, HEIGHT // 3 - 40, f"coins : {coins}", 50, "black", 3)
                                shop_menu.update_label(80, HEIGHT // 3 + 20, f"bombs : {bombs}", 50, "black", 4)
                        elif btn_id == 7:
                            pygame.mixer.Sound.play(btn_sound)
                            window = "menu"

                elif window == "scores":
                    hit, btn_id = scores_menu.collide(mx, my)
                    if hit and btn_id == 8:
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
