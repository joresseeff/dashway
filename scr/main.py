"""
main.py
-------
Point d'entrée de Dashway.
"""

import sys
import pygame

from game import Game
from menu import Menu
from database import Database
from init import WIDTH, HEIGHT
from paths import resource


SAVE_PATH = resource("save.txt")


def load_save() -> tuple:
    try:
        with open(SAVE_PATH) as f:
            lines = f.readlines()
        return int(lines[0]), int(lines[1]), int(lines[2])
    except (FileNotFoundError, ValueError, IndexError):
        return 0, 0, 0


def write_save(best_score: int, coins: int, bombs: int) -> None:
    with open(SAVE_PATH, "w") as f:
        f.write(f"{best_score}\n{coins}\n{bombs}")


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DASHWAY")
    icon = pygame.image.load(resource("assets/lambo.png")).convert()
    pygame.display.set_icon(icon)

    clock = pygame.time.Clock()
    FPS = 60

    db = Database()
    coins, bombs = db.load_player()
    best_score = db.get_best_score()

    main_music  = pygame.mixer.Sound(resource("sounds/mainMusic.mp3"))
    btn_sound   = pygame.mixer.Sound(resource("sounds/clickButton.mp3"))
    coin_sound  = pygame.mixer.Sound(resource("sounds/carCollide.mp3"))
    bomb_sound  = pygame.mixer.Sound(resource("sounds/launchBomb.mp3"))
    crash_sound = pygame.mixer.Sound(resource("sounds/carCollide.mp3"))
    pygame.mixer.Sound.play(main_music, loops=-1)

    bg_main = pygame.transform.scale(
        pygame.image.load(resource("assets/bgMenu.png")), (WIDTH, HEIGHT))
    bg_shop   = pygame.transform.scale(pygame.image.load(resource("assets/shopBG.png")), (WIDTH, HEIGHT))
    btn_green = pygame.image.load(resource("assets/greenButton.png"))
    btn_red   = pygame.image.load(resource("assets/redButton.png"))
    btn_gold  = pygame.image.load(resource("assets/goldButton.png"))

    def build_main_menu():
        m = Menu(screen, bg_main)
        m.add_label(WIDTH // 2 - 150, HEIGHT // 12,          "DASHWAY",              100, "blue",  0)
        m.add_label(WIDTH // 2 - 175, int(HEIGHT / 6 * 1.5), f"Best: {best_score}",   70, "blue",  1)
        m.add_button(0, WIDTH // 2 - 100, int(HEIGHT / 3 * 1.5), 200, 70, btn_green, "PLAY",   50, "blue")
        m.add_button(1, WIDTH // 2 - 100, int(HEIGHT / 3 * 2),   200, 70, btn_green, "SHOP",   50, "blue")
        m.add_button(2, WIDTH // 2 - 100, int(HEIGHT / 3 * 2.5), 200, 70, btn_green, "SCORES", 50, "blue")
        m.add_button(3, WIDTH // 2 - 100, int(HEIGHT / 3 * 3),   200, 70, btn_green, "EXIT",   50, "blue")
        return m

    def build_shop_menu():
        m = Menu(screen, bg_shop)
        m.add_label(WIDTH // 2 - 80, HEIGHT // 12,       "SHOP",            100, "white", 2)
        m.add_button(5, 50, HEIGHT // 3 - 50,      400, 150, btn_gold, "",              50, "black")
        m.add_label(80, HEIGHT // 3 - 40,          f"coins : {coins}",  50, "black", 3)
        m.add_label(80, HEIGHT // 3 + 20,          f"bombs : {bombs}",  50, "black", 4)
        m.add_button(6, 50, HEIGHT // 3 + 120,     400, 150, btn_red, "Bomb : 3 coins", 50, "black")
        m.add_button(7, 50, HEIGHT // 3 * 2 + 100, 400, 150, btn_red, "EXIT",           50, "black")
        return m

    def build_scores_menu():
        m = Menu(screen, bg_main)
        m.add_label(WIDTH // 2 - 130, HEIGHT // 12, "TOP SCORES", 80, "blue", 10)
        top = db.get_top_scores()
        if top:
            for entry in top:
                y = HEIGHT // 4 + entry["rank"] * 80
                label = f"#{entry['rank']}  {entry['score']} pts  {entry['date']}"
                m.add_label(40, y, label, 35, "blue", 10 + entry["rank"])
        else:
            m.add_label(WIDTH // 2 - 160, HEIGHT // 2, "Aucun score !", 50, "blue", 11)
        m.add_button(8, WIDTH // 2 - 100, HEIGHT - 120, 200, 70, btn_green, "RETOUR", 50, "blue")
        return m

    main_menu   = build_main_menu()
    shop_menu   = build_shop_menu()
    scores_menu = build_scores_menu()

    window = "menu"
    reset_game = True
    mouse_was_down = False
    game = Game(screen, best_score, coins, bombs, coin_sound, bomb_sound, crash_sound)

    running = True
    while running:
        if reset_game and window == "game":
            game = Game(screen, best_score, coins, bombs, coin_sound, bomb_sound, crash_sound)
            reset_game = False

        if window == "game":
            screen.fill((128, 129, 129))
            game.update()
            if game.close:
                best_score = game.bestScore
                coins      = game.coins
                bombs      = game.numberBombs
                db.add_score(game.score, game.session_duration)
                db.save_player(coins, bombs)
                window = "menu"
                reset_game = True
                main_menu = build_main_menu()
                scores_menu = build_scores_menu()
        elif window == "menu":
            main_menu.update()
        elif window == "shop":
            shop_menu.update()
        elif window == "scores":
            scores_menu.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                db.save_player(coins, bombs)
                running = False

            if event.type == pygame.KEYDOWN:
                game.pressed[event.key] = True
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
                            shop_menu = build_shop_menu()
                            window = "shop"
                        elif btn_id == 2:
                            scores_menu = build_scores_menu()
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
                                shop_menu = build_shop_menu()
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
