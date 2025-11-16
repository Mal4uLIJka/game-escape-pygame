import pygame
import random
import math

class AnimationController:
    def __init__(self, squash_factor=0.04, tilt_factor=15, anim_speed=2):
        self.current_tilt = 0.0
        self.target_tilt = 0.0
        self.tilt_duration = 5
        self.tilt_timer = 0

        self.scale_x = 1.0
        self.scale_y = 1.0
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        self.scale_duration = 5
        self.scale_timer = 0

        self.squash_factor = squash_factor
        self.tilt_factor = tilt_factor
        self.anim_speed = anim_speed

        self.wobble_timer = 0.0
        self.is_moving = False

    def update(self, dt):
        lerp_strength = 20
        self.scale_x += (self.target_scale_x - self.scale_x) * lerp_strength * dt
        self.scale_y += (self.target_scale_y - self.scale_y) * lerp_strength * dt

        if self.is_moving:
            wobble_speed_per_second = 6 * self.anim_speed
            self.wobble_timer += wobble_speed_per_second * dt
            self.current_tilt = self.target_tilt * math.sin(self.wobble_timer)
        else:
            self.wobble_timer = 0.0
            self.current_tilt += (0.0 - self.current_tilt) * 10 * dt

    def set_squash_stretch(self, direction):
        squash = self.squash_factor * random.uniform(0.9, 1.1)
        if direction == "left" or direction == "right":
            self.target_scale_x = 1.0 + squash
            self.target_scale_y = 1.0 - squash
        elif direction == "up" or direction == "down":
            self.target_scale_x = 1.0 - squash
            self.target_scale_y = 1.0 + squash
        self.scale_timer = self.scale_duration

    def set_tilt(self, direction):
        self.is_moving = True
        tilt = self.tilt_factor * random.uniform(0.9, 1.1)
        if direction == "left":
            self.target_tilt = -tilt
        elif direction == "right":
            self.target_tilt = tilt
        elif direction == "up":
            self.target_tilt = -tilt
        elif direction == "down":
            self.target_tilt = tilt
        self.tilt_timer = self.tilt_duration

    def reset_animation(self):
        self.is_moving = False
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        self.target_tilt = 0.0

    def force_reset_animation(self):
        self.is_moving = False
        self.current_tilt = 0.0
        self.target_tilt = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0

    def draw_animated(self, surface, original_image, rect):
        if not original_image:
            return

        scaled_width = int(rect.width * self.scale_x)
        scaled_height = int(rect.height * self.scale_y)

        if scaled_width <= 0 or scaled_height <= 0:
            if original_image:
                surface.blit(original_image, rect)
            return

        scaled_image = pygame.transform.smoothscale(original_image, (scaled_width, scaled_height))

        rotated_image = pygame.transform.rotate(scaled_image, self.current_tilt)

        rotated_rect = rotated_image.get_rect(center=rect.center)

        surface.blit(rotated_image, rotated_rect)
