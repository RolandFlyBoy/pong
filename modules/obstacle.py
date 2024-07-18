import pygame
import random
import math


class Obstacle:
    def __init__(self, screen_width, screen_height, ball_radius):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ball_radius = ball_radius
        self.shape = random.choice(["hexagon", "triangle", "square"])
        self.generate()

    def generate(self):
        # Determine size
        min_size = self.ball_radius * 2
        max_size = self.ball_radius * 10
        size_factor = random.uniform(0, 1)
        self.size = min_size + (max_size - min_size) * size_factor

        # Determine position
        self.center = (
            random.randint(self.screen_width // 3, 2 * self.screen_width // 3),
            random.randint(self.screen_height // 3, 2 * self.screen_height // 3),
        )

        # Generate points based on shape
        if self.shape == "hexagon":
            self.points = [
                (
                    self.center[0] + self.size * math.cos(angle),
                    self.center[1] + self.size * math.sin(angle),
                )
                for angle in [i * math.pi / 3 for i in range(6)]
            ]
        elif self.shape == "triangle":
            self.points = [
                (self.center[0], self.center[1] - self.size),
                (
                    self.center[0] - self.size * math.sqrt(3) / 2,
                    self.center[1] + self.size / 2,
                ),
                (
                    self.center[0] + self.size * math.sqrt(3) / 2,
                    self.center[1] + self.size / 2,
                ),
            ]
        else:  # square
            half_size = self.size / math.sqrt(2)
            self.points = [
                (self.center[0] - half_size, self.center[1] - half_size),
                (self.center[0] + half_size, self.center[1] - half_size),
                (self.center[0] + half_size, self.center[1] + half_size),
                (self.center[0] - half_size, self.center[1] + half_size),
            ]

    def draw(self, screen, color):
        pygame.draw.polygon(screen, color, self.points)

    def check_collision(self, ball):
        # Check collision with each side of the obstacle
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]

            # Calculate the closest point on the line segment to the ball center
            line_vec = pygame.math.Vector2(p2[0] - p1[0], p2[1] - p1[1])
            ball_to_p1 = pygame.math.Vector2(ball.centerx - p1[0], ball.centery - p1[1])

            projection = ball_to_p1.dot(line_vec) / line_vec.length_squared()
            projection = max(0, min(1, projection))  # Clamp between 0 and 1

            closest_point = (
                p1[0] + projection * line_vec.x,
                p1[1] + projection * line_vec.y,
            )

            # Check if the ball is colliding with this side
            distance = pygame.math.Vector2(
                ball.centerx - closest_point[0], ball.centery - closest_point[1]
            ).length()
            if distance <= self.ball_radius:
                normal = pygame.math.Vector2(
                    ball.centerx - closest_point[0], ball.centery - closest_point[1]
                ).normalize()
                return normal, self.ball_radius - distance

        return None, 0

    def resolve_collision(self, ball, ball_dx, ball_dy):
        normal, overlap = self.check_collision(ball)
        if normal:
            velocity = pygame.math.Vector2(ball_dx, ball_dy)
            reflection = velocity.reflect(normal)

            # Move the ball out of the obstacle with a small extra buffer
            buffer = 1.01  # 1% extra to ensure it's clear of the obstacle
            ball.x += normal.x * overlap * buffer
            ball.y += normal.y * overlap * buffer

            # Adjust the reflection slightly to prevent sticking
            reflection_angle = math.atan2(reflection.y, reflection.x)
            reflection_angle += random.uniform(-0.1, 0.1)  # Add a small random angle
            speed = reflection.length()

            return speed * math.cos(reflection_angle), speed * math.sin(
                reflection_angle
            )
        return ball_dx, ball_dy
