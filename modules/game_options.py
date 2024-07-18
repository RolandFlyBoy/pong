import pygame
import json
import os

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE, BLACK, CYAN = (255, 255, 255), (0, 0, 0), (0, 255, 255)
FONT_SIZE = 14
INSTRUCTION_FONT_SIZE = 12

# Load fonts
font = pygame.font.Font("fonts/8-bit-wonder.ttf", FONT_SIZE)
instruction_font = pygame.font.Font("fonts/8-bit-wonder.ttf", INSTRUCTION_FONT_SIZE)


def draw_text(surface, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)


def load_settings():
    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "settings.db"
    )
    with open(settings_path, "r") as f:
        return json.load(f)


def save_settings(settings):
    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "settings.db"
    )
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)


def show_options_menu(screen):
    settings = load_settings()
    options = list(settings["GAME_SETTINGS"].keys())
    selected = 0

    while True:
        screen.fill(BLACK)

        # Draw instructions
        instructions = settings["LANGUAGE_COPY"]["OPTIONS_INSTRUCTIONS"]
        for i, instruction in enumerate(instructions):
            draw_text(
                screen, instruction, instruction_font, CYAN, WIDTH // 2, 30 + i * 20
            )

        # Draw options
        for i, option in enumerate(options):
            color = WHITE if i != selected else BLACK
            bg_color = BLACK if i != selected else WHITE
            value = settings["GAME_SETTINGS"][option]
            if isinstance(value, bool):
                value = "On" if value else "Off"
            text = f"{settings['LANGUAGE_COPY'][option + '_SETTING']}: {value}"

            pygame.draw.rect(
                screen, bg_color, (WIDTH // 4, 120 + i * 40, WIDTH // 2, 30)
            )
            draw_text(screen, text, font, color, WIDTH // 2, 135 + i * 40)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    option = options[selected]
                    value = settings["GAME_SETTINGS"][option]
                    if isinstance(value, bool):
                        settings["GAME_SETTINGS"][option] = not value
                    elif isinstance(value, int):
                        change = -1 if event.key == pygame.K_LEFT else 1
                        if option in ["WINNING_POINTS", "BALL_SPEED_TURNS"]:
                            settings["GAME_SETTINGS"][option] = max(
                                1, min(10, value + change)
                            )
                        elif option == "BALL_INCREMENT":
                            settings["GAME_SETTINGS"][option] = max(
                                1, min(20, value + change)
                            )
                        else:
                            settings["GAME_SETTINGS"][option] = max(
                                0, min(100, value + change)
                            )
                elif event.key == pygame.K_RETURN:
                    save_settings(settings)
                    return settings
                elif event.key == pygame.K_ESCAPE:
                    return None


def update_game_stats(stat_name, value):
    settings = load_settings()
    if value > settings["GAME_STATS"].get(stat_name, 0):
        settings["GAME_STATS"][stat_name] = value
        save_settings(settings)


if __name__ == "__main__":
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pong Options")
    show_options_menu(screen)
    pygame.quit()
