import pygame
import random
from modules.computer_ai import calculate_computer_move
from modules import game_options
from modules.obstacle import Obstacle
from PIL import Image, ImageSequence

pygame.init()
pygame.mixer.init()

SETTINGS = game_options.load_settings()
WIDTH, HEIGHT = 800, 600
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
BALL_RADIUS, PADDLE_WIDTH, INITIAL_PADDLE_HEIGHT = 10, 10, 100
PADDLE_SHRINK_RATE = INITIAL_PADDLE_HEIGHT / 60
COLLISION_COOLDOWN = 100

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(SETTINGS["LANGUAGE_COPY"]["MENU_TITLE"])
fonts = {
    k: pygame.font.Font("fonts/8-bit-wonder.ttf", v)
    for k, v in {"main": 16, "score": 18, "stats": 14, "instruction": 12}.items()
}

strike_sounds = [pygame.mixer.Sound(f"media/strike_{i}.wav") for i in range(1, 4)]
intro_music = pygame.mixer.Sound("media/intro_music.mp3")

trophy_image = (
    pygame.transform.scale(pygame.image.load("media/trophy.jpg"), (30, 30))
    if pygame.image.get_extended()
    else pygame.Surface((30, 30)).fill((255, 215, 0))
)

gif = Image.open("media/splash.gif")
new_width, aspect_ratio = 300, gif.width / gif.height
gif_frames = [
    pygame.transform.scale(
        pygame.image.fromstring(
            frame.convert("RGBA").tobytes(), frame.size, "RGBA"
        ).convert_alpha(),
        (new_width, int(new_width / aspect_ratio)),
    )
    for frame in ImageSequence.Iterator(gif)
]

ball = pygame.Rect(WIDTH // 2, HEIGHT // 2, BALL_RADIUS * 2, BALL_RADIUS * 2)
player_paddle = pygame.Rect(
    WIDTH - 20,
    HEIGHT // 2 - INITIAL_PADDLE_HEIGHT // 2,
    PADDLE_WIDTH,
    INITIAL_PADDLE_HEIGHT,
)
computer_paddle = pygame.Rect(
    10, HEIGHT // 2 - INITIAL_PADDLE_HEIGHT // 2, PADDLE_WIDTH, INITIAL_PADDLE_HEIGHT
)
obstacle = None

running = game_started = ball_moving = False
player_score = computer_score = longest_rally = ball_dx = ball_dy = strike_count = (
    current_ball_speed
) = game_start_time = last_collision_time = rally_start_time = 0


def draw_text(text, font_key, color, x, y):
    screen.blit(
        fonts[font_key].render(text, True, color),
        fonts[font_key].render(text, True, color).get_rect(center=(x, y)),
    )


def reset_game_state():
    global ball_dx, ball_dy, strike_count, current_ball_speed, player_score, computer_score, longest_rally, game_start_time, last_collision_time, obstacle
    ball.center = (WIDTH // 2, HEIGHT // 2)
    ball_dx = ball_dy = strike_count = current_ball_speed = player_score = (
        computer_score
    ) = longest_rally = 0
    player_paddle.height = computer_paddle.height = INITIAL_PADDLE_HEIGHT
    player_paddle.centery = computer_paddle.centery = HEIGHT // 2
    game_start_time = pygame.time.get_ticks()
    last_collision_time = 0
    obstacle = (
        Obstacle(WIDTH, HEIGHT, BALL_RADIUS)
        if SETTINGS["GAME_SETTINGS"]["OBSTACLE"]
        else None
    )


def start_ball_movement():
    global ball_dx, ball_dy, rally_start_time
    ball_dx, ball_dy = random.choice([-1, 1]) * 5, random.choice([-1, 1]) * 5
    rally_start_time = pygame.time.get_ticks()


def update_ball_speed():
    global ball_dx, ball_dy, current_ball_speed
    if strike_count % SETTINGS["GAME_SETTINGS"]["BALL_SPEED_TURNS"] == 0:
        speed_multiplier = 1 + min(
            SETTINGS["GAME_SETTINGS"]["BALL_SPEED"] / 50,
            (strike_count // SETTINGS["GAME_SETTINGS"]["BALL_SPEED_TURNS"])
            * (SETTINGS["GAME_SETTINGS"]["BALL_INCREMENT"] / 100),
        )
        ball_dx = abs(ball_dx) / ball_dx * 5 * speed_multiplier
        ball_dy = abs(ball_dy) / ball_dy * 5 * speed_multiplier
        current_ball_speed = (abs(ball_dx) + abs(ball_dy)) / 2


def show_menu(is_game_over=False, new_record=False):
    if SETTINGS["GAME_SETTINGS"]["MUSIC_ENABLED"]:
        intro_music.play(-1)
    waiting, gif_frame_index, gif_last_update = True, 0, 0
    while waiting:
        current_time = pygame.time.get_ticks()
        screen.fill(BLACK)
        if current_time - gif_last_update > 100:
            gif_frame_index = (gif_frame_index + 1) % len(gif_frames)
            gif_last_update = current_time
        screen.blit(
            gif_frames[gif_frame_index],
            ((WIDTH - gif_frames[gif_frame_index].get_width()) // 2, 50),
        )

        vertical_start = 50 + gif_frames[0].get_height() + 50
        if is_game_over:
            end_message = SETTINGS["LANGUAGE_COPY"][
                (
                    "COMPUTER_WIN"
                    if computer_score >= SETTINGS["GAME_SETTINGS"]["WINNING_POINTS"]
                    else "PLAYER_WIN"
                )
            ]
            draw_text(end_message, "main", WHITE, WIDTH // 2, vertical_start)
            vertical_start += 40
            if new_record:
                congrats_text = SETTINGS["LANGUAGE_COPY"]["LONGEST_RALLY_CONGRATS"]
                text_width, _ = fonts["main"].size(congrats_text)
                screen.blit(
                    trophy_image,
                    (WIDTH // 2 - text_width // 2 - 40, vertical_start - 15),
                )
                draw_text(congrats_text, "main", WHITE, WIDTH // 2, vertical_start)
                vertical_start += 40

        draw_text(
            SETTINGS["LANGUAGE_COPY"]["START_GAME"],
            "main",
            WHITE,
            WIDTH // 2,
            vertical_start,
        )
        draw_text(
            SETTINGS["LANGUAGE_COPY"]["OPTIONS_MENU"],
            "main",
            WHITE,
            WIDTH // 2,
            vertical_start + 40,
        )
        draw_text(
            SETTINGS["LANGUAGE_COPY"]["QUIT_GAME"],
            "main",
            WHITE,
            WIDTH // 2,
            vertical_start + 80,
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_q
            ):
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_o:
                    intro_music.stop()
                    new_settings = game_options.show_options_menu(screen)
                    if new_settings:
                        SETTINGS.update(new_settings)
                    if SETTINGS["GAME_SETTINGS"]["MUSIC_ENABLED"]:
                        intro_music.play(-1)
                else:
                    waiting = False
                    intro_music.stop()
    return True


def run_game():
    global running, game_started, ball_moving, player_score, computer_score, longest_rally
    global ball_dx, ball_dy, strike_count, current_ball_speed, game_start_time, last_collision_time, rally_start_time

    clock = pygame.time.Clock()

    while running:
        if not game_started:
            game_started = show_menu(
                player_score > 0 or computer_score > 0,
                longest_rally > SETTINGS["GAME_STATS"]["LONGEST_RALLY"],
            )
            if not game_started:
                running = False
            else:
                reset_game_state()
                ball_moving = False
        else:
            screen.fill(BLACK)
            current_time = pygame.time.get_ticks()

            if SETTINGS["GAME_SETTINGS"]["PADDLE_EROSION"]:
                player_paddle.height = max(
                    INITIAL_PADDLE_HEIGHT
                    - int(
                        PADDLE_SHRINK_RATE * (current_time - game_start_time) // 1000
                    ),
                    INITIAL_PADDLE_HEIGHT // 2,
                )

            if obstacle:
                obstacle.draw(screen, WHITE)

            pygame.draw.rect(screen, WHITE, player_paddle)
            pygame.draw.rect(screen, WHITE, computer_paddle)
            pygame.draw.ellipse(screen, WHITE, ball)

            draw_text(
                f"{SETTINGS['LANGUAGE_COPY']['PLAYER_SCORE']}: {player_score}  {SETTINGS['LANGUAGE_COPY']['COMPUTER_SCORE']}: {computer_score}",
                "score",
                WHITE,
                WIDTH // 2,
                20,
            )
            draw_text(
                f"{SETTINGS['LANGUAGE_COPY']['BALL_SPEED']}: {current_ball_speed:.1f}  {SETTINGS['LANGUAGE_COPY']['STRIKES']}: {strike_count}",
                "stats",
                WHITE,
                WIDTH // 2,
                50,
            )

            if ball_moving:
                longest_rally = max(
                    longest_rally, (current_time - rally_start_time) // 1000
                )
                ball.x += ball_dx
                ball.y += ball_dy

                if obstacle:
                    collision = obstacle.check_collision(ball)
                    if (
                        collision[0]
                        and current_time - last_collision_time > COLLISION_COOLDOWN
                    ):
                        ball_dx, ball_dy = obstacle.resolve_collision(
                            ball, ball_dx, ball_dy
                        )
                        random.choice(strike_sounds).play()
                        last_collision_time = current_time

                if ball.top <= 0 or ball.bottom >= HEIGHT:
                    ball.clamp_ip(screen.get_rect())
                    ball_dy = -ball_dy

                if ball.colliderect(player_paddle) or ball.colliderect(computer_paddle):
                    if current_time - last_collision_time > COLLISION_COOLDOWN:
                        ball.right, ball.left = (
                            player_paddle.left,
                            computer_paddle.right,
                        )[ball.colliderect(computer_paddle)]
                        ball_dx = -ball_dx
                        strike_count += 1
                        random.choice(strike_sounds).play()
                        update_ball_speed()
                        last_collision_time = current_time

                if ball.left <= 0 or ball.right >= WIDTH:
                    player_score, computer_score = (
                        (player_score + 1, computer_score)
                        if ball.left <= 0
                        else (player_score, computer_score + 1)
                    )
                    ball_moving, ball.center, rally_start_time = (
                        False,
                        (WIDTH // 2, HEIGHT // 2),
                        current_time,
                    )

                if (
                    player_score >= SETTINGS["GAME_SETTINGS"]["WINNING_POINTS"]
                    or computer_score >= SETTINGS["GAME_SETTINGS"]["WINNING_POINTS"]
                ):
                    if longest_rally > SETTINGS["GAME_STATS"]["LONGEST_RALLY"]:
                        SETTINGS["GAME_STATS"]["LONGEST_RALLY"] = longest_rally
                        game_options.save_settings(SETTINGS)
                    game_started = False

                computer_paddle.y += calculate_computer_move(
                    ball.centery,
                    computer_paddle.centery,
                    computer_paddle.height,
                    HEIGHT,
                    SETTINGS["GAME_SETTINGS"]["COMPUTER_SPEED"],
                    SETTINGS["GAME_SETTINGS"]["COMPUTER_RANDOMNESS"],
                ) * (SETTINGS["GAME_SETTINGS"]["COMPUTER_SPEED"] / 10)
                computer_paddle.clamp_ip(screen.get_rect())
            else:
                draw_text(
                    SETTINGS["LANGUAGE_COPY"]["SERVE_BALL"],
                    "instruction",
                    WHITE,
                    WIDTH // 2,
                    HEIGHT - 50,
                )
                draw_text(
                    f"{SETTINGS['LANGUAGE_COPY']['QUIT_GAME']}, {SETTINGS['LANGUAGE_COPY']['RESTART_GAME']}",
                    "instruction",
                    WHITE,
                    WIDTH // 2,
                    HEIGHT - 20,
                )

            keys = pygame.key.get_pressed()
            player_paddle.y += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 5
            player_paddle.clamp_ip(screen.get_rect())

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_q
                ):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        reset_game_state()
                        ball_moving = False
                    elif not ball_moving:
                        start_ball_movement()
                        ball_moving = True

            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    reset_game_state()
    run_game()
    pygame.quit()
