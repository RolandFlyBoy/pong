import random


def calculate_computer_move(
    ball_y, paddle_y, paddle_height, court_height, speed, randomness
):
    """
    Calculate the computer paddle's movement direction based on the current game state and AI settings.

    :param ball_y: Y-position of the ball
    :param paddle_y: Y-position of the computer paddle
    :param paddle_height: Height of the paddle
    :param court_height: Height of the game court
    :param speed: AI speed setting (0-100)
    :param randomness: AI randomness setting (0-100)
    :return: Movement direction (-1 for up, 1 for down, 0 for no movement)
    """

    # Calculate the center of the paddle
    paddle_center = paddle_y + paddle_height / 2

    # Add randomness to the target
    random_factor = (random.random() - 0.5) * randomness / 50  # -1 to 1 range
    target_y = ball_y + random_factor * paddle_height

    # Determine direction to move
    if target_y < paddle_center - 2:
        return -1  # Move up
    elif target_y > paddle_center + 2:
        return 1  # Move down
    else:
        return 0  # Don't move

    # Note: We're not using the speed parameter here. It will be used in the main game loop.


# You can add additional helper functions or constants here if needed in the future
