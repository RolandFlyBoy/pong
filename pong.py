import pygame
import random
import math
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
FONT_SIZES = {"main": 16, "score": 18, "stats": 14, "instruction": 12}
PADDLE_SHRINK_RATE = INITIAL_PADDLE_HEIGHT / 60  # Halve in 30 seconds
COLLISION_COOLDOWN = 100  # milliseconds

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(SETTINGS["LANGUAGE_COPY"]["MENU_TITLE"])
fonts = {
    key: pygame.font.Font("fonts/8-bit-wonder.ttf", size)
    for key, size in FONT_SIZES.items()
}

strike_sounds = [pygame.mixer.Sound(f"media/strike_{i}.wav") for i in range(1, 4)]
intro_music = pygame.mixer.Sound("media/intro_music.mp3")

try:
    trophy_image = pygame.image.load("media/trophy.jpg")
    trophy_image = pygame.transform.scale(trophy_image, (30, 30))
except pygame.error:
    trophy_image = pygame.Surface((30, 30))
    trophy_image.fill((255, 215, 0))

gif = Image.open("media/splash.gif")
gif_frames = [
    pygame.image.fromstring(
        frame.convert("RGBA").tobytes(), frame.size, "RGBA"
    ).convert_alpha()
    for frame in ImageSequence.Iterator(gif)
]
new_width = 300
aspect_ratio = gif.width / gif.height
gif_frames = [
    pygame.transform.scale(frame, (new_width, int(new_width / aspect_ratio)))
    for frame in gif_frames
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


def draw_text(text, font_key, color, x, y):
    surface = fonts[font_key].render(text, True, color)
    screen.blit(surface, surface.get_rect(center=(x, y)))


def reset_game_state():
    global ball_dx, ball_dy, strike_count, current_ball_speed, player_score, computer_score, longest_rally, game_start_time, last_collision_time
    ball.center = (WIDTH // 2, HEIGHT // 2)
    ball_dx = ball_dy = 0
    strike_count = current_ball_speed = 0
    player_score = computer_score = longest_rally = 0
    player_paddle.height = computer_paddle.height = INITIAL_PADDLE_HEIGHT
    player_paddle.centery = computer_paddle.centery = HEIGHT // 2
    game_start_time = pygame.time.get_ticks()
    last_collision_time = 0
    if SETTINGS["GAME_SETTINGS"]["OBSTACLE"]:
        global obstacle
        obstacle = Obstacle(WIDTH, HEIGHT, BALL_RADIUS)


def start_ball_movement():
    global ball_dx, ball_dy, rally_start_time
    ball_dx = random.choice([-1, 1]) * 5
    ball_dy = random.choice([-1, 1]) * 5
    rally_start_time = pygame.time.get_ticks()


def move_computer_paddle():
    move = calculate_computer_move(
        ball.centery,
        computer_paddle.centery,
        computer_paddle.height,
        HEIGHT,
        SETTINGS["GAME_SETTINGS"]["COMPUTER_SPEED"],
        SETTINGS["GAME_SETTINGS"]["COMPUTER_RANDOMNESS"],
    )
    computer_paddle.y += move * (SETTINGS["GAME_SETTINGS"]["COMPUTER_SPEED"] / 10)
    computer_paddle.clamp_ip(screen.get_rect())


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
    waiting = True
    gif_frame_index = gif_last_update = 0
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
            end_message = (
                SETTINGS["LANGUAGE_COPY"]["COMPUTER_WIN"]
                if computer_score >= SETTINGS["GAME_SETTINGS"]["WINNING_POINTS"]
                else SETTINGS["LANGUAGE_COPY"]["PLAYER_WIN"]
            )
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


running = True
clock = pygame.time.Clock()
game_started = ball_moving = False
reset_game_state()

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
                - int(PADDLE_SHRINK_RATE * (current_time - game_start_time) // 1000),
                INITIAL_PADDLE_HEIGHT // 2,
            )

        if SETTINGS["GAME_SETTINGS"]["OBSTACLE"]:
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
            rally_duration = (current_time - rally_start_time) // 1000
            longest_rally = max(longest_rally, rally_duration)

            ball.x += ball_dx
            ball.y += ball_dy

            if SETTINGS["GAME_SETTINGS"]["OBSTACLE"]:
                collision = obstacle.check_collision(ball)
                if collision[0]:
                    if current_time - last_collision_time > COLLISION_COOLDOWN:
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
                    if ball.colliderect(player_paddle):
                        ball.right = player_paddle.left
                    else:
                        ball.left = computer_paddle.right
                    ball_dx = -ball_dx
                    strike_count += 1
                    random.choice(strike_sounds).play()
                    update_ball_speed()
                    last_collision_time = current_time

            if ball.left <= 0 or ball.right >= WIDTH:
                if ball.left <= 0:
                    player_score += 1
                else:
                    computer_score += 1
                ball_moving = False
                ball.center = (WIDTH // 2, HEIGHT // 2)
                rally_start_time = current_time

            if (
                player_score >= SETTINGS["GAME_SETTINGS"]["WINNING_POINTS"]
                or computer_score >= SETTINGS["GAME_SETTINGS"]["WINNING_POINTS"]
            ):
                if longest_rally > SETTINGS["GAME_STATS"]["LONGEST_RALLY"]:
                    SETTINGS["GAME_STATS"]["LONGEST_RALLY"] = longest_rally
                    game_options.save_settings(SETTINGS)
                game_started = False

            move_computer_paddle()
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
        if keys[pygame.K_UP] and player_paddle.top > 0:
            player_paddle.y -= 5
        if keys[pygame.K_DOWN] and player_paddle.bottom < HEIGHT:
            player_paddle.y += 5

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    reset_game_state()
                    ball_moving = False
                elif not ball_moving:
                    start_ball_movement()
                    ball_moving = True

        pygame.display.flip()
        clock.tick(60)

pygame.quit()
