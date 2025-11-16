import pygame
import math

from settings import TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT
from animation import AnimationController

class Player:
    def __init__(self, x, y, assets, base_speed=600):
        self.start_pos = (x, y)
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hitbox = self.rect.copy()
        self.hitbox.inflate_ip(-15, -15)
        self.base_speed = base_speed
        self.speed = float(base_speed)
        self.direction = None
        self.is_moving = False
        self.held_keys = set()
        self.next_direction = None
        self.reverse_tiles_underneath = []
        self.target_x = None
        self.target_y = None
        self.anim_controller = AnimationController(squash_factor=0.04, tilt_factor=15)
        self.visible = True

        try:
            self.original_image = assets.get_image("hero", scale=(TILE_SIZE, TILE_SIZE))
        except pygame.error:
            self.original_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.original_image.fill((0, 200, 0))
            print("Используется стандартный квадрат.")

    def start_move(self, direction, walls, transforming_tiles):
        if self.is_moving:
            return
        self.direction = direction
        current_grid_x = self.rect.x // TILE_SIZE
        current_grid_y = self.rect.y // TILE_SIZE
        obstacle_coords = {(w.rect.x // TILE_SIZE, w.rect.y // TILE_SIZE) for w in walls}
        transforming_coords = {(t.rect.x // TILE_SIZE, t.rect.y // TILE_SIZE) for t in transforming_tiles}
        obstacle_coords.update(transforming_coords)
        target_grid_x, target_grid_y = current_grid_x, current_grid_y
        if direction == "left":
            for x in range(current_grid_x - 1, -1, -1):
                if (x, current_grid_y) in obstacle_coords:
                    break
                target_grid_x = x
        elif direction == "right":
            for x in range(current_grid_x + 1, GRID_WIDTH):
                if (x, current_grid_y) in obstacle_coords:
                    break
                target_grid_x = x
        elif direction == "up":
            for y in range(current_grid_y - 1, -1, -1):
                if (current_grid_x, y) in obstacle_coords:
                    break
                target_grid_y = y
        elif direction == "down":
            for y in range(current_grid_y + 1, GRID_HEIGHT):
                if (current_grid_x, y) in obstacle_coords:
                    break
                target_grid_y = y
        if target_grid_x == current_grid_x and target_grid_y == current_grid_y:
            return
        self.target_x = float(target_grid_x * TILE_SIZE)
        self.target_y = float(target_grid_y * TILE_SIZE)
        self.is_moving = True

        self.anim_controller.set_squash_stretch(direction)
        self.anim_controller.set_tilt(direction)

    def update(self, dt):
        self.anim_controller.update(dt)

        if not self.is_moving:
            self.anim_controller.reset_animation()

        if not self.is_moving:
            return

        move_distance = self.speed * dt

        if self.direction == "left":
            self.x = max(self.target_x, self.x - move_distance)
        elif self.direction == "right":
            self.x = min(self.target_x, self.x + move_distance)
        elif self.direction == "up":
            self.y = max(self.target_y, self.y - move_distance)
        elif self.direction == "down":
            self.y = min(self.target_y, self.y + move_distance)

        self.rect.x = int(round(self.x))
        self.rect.y = int(round(self.y))
        self.hitbox.center = self.rect.center

        if self.rect.x == self.target_x and self.rect.y == self.target_y:
            self.x = float(self.target_x)
            self.y = float(self.target_y)
            self.is_moving = False
            self.direction = None
            self.target_x = None
            self.target_y = None

    def reset(self):
        self.x, self.y = float(self.start_pos[0]), float(self.start_pos[1])
        self.rect.topleft = self.start_pos
        self.hitbox.center = self.rect.center
        self.is_moving = False
        self.direction = None
        self.target_x = None
        self.target_y = None
        self.anim_controller.force_reset_animation()
        self.visible = True
        self.held_keys.clear()
        self.next_direction = None

    def draw(self, surface, debug_mode=False):
        if not self.visible:
            return

        self.anim_controller.draw_animated(surface, self.original_image, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (0, 0, 255), self.hitbox, 1)
            pygame.draw.rect(surface, (0, 0, 255), self.rect, 1)

class Enemy:
    def __init__(self, x, y, move_type, assets, speed=240, hitx=-5, hity=-5):
        self.start_pos = (x, y)
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hitbox = self.rect.copy()
        self.hitbox.inflate_ip(hitx, hity)
        self.move_type = move_type
        self.speed = float(speed)
        self.direction = 1
        self.color = (255, 0, 0) if speed > 240 else (180, 50, 50)
        self.anim_controller = AnimationController(squash_factor=0.02, tilt_factor=5, anim_speed=1 + (speed / 240))

        self.is_paused = False
        self.pause_timer = 0
        self.pause_duration = 30

        self.original_image = None
        texture_name = ""
        if speed == 240:
            texture_name = "enemy_slow"
        elif speed == 480:
            texture_name = "enemy_fast"

        if texture_name and assets:
            try:
                self.original_image = assets.get_image(texture_name, scale=(TILE_SIZE, TILE_SIZE))
            except pygame.error:
                pass

        if not self.original_image:
            self.original_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.original_image.fill(self.color)

    def reset(self):
        self.x, self.y = float(self.start_pos[0]), float(self.start_pos[1])
        self.rect.topleft = self.start_pos
        self.hitbox.center = self.rect.center
        self.direction = 1
        self.anim_controller.force_reset_animation()
        self.is_paused = False
        self.pause_timer = 0

    def update(self, walls, dt):
        if self.is_paused:
            self.pause_timer -= 1
            if self.pause_timer <= 0:
                self.is_paused = False
                self.direction *= -1
                self._on_direction_change()

            self.anim_controller.reset_animation()
            self.anim_controller.update(dt)
            return

        move_direction = None
        if self.move_type == 'horizontal':
            move_direction = "right" if self.direction == 1 else "left"
        elif self.move_type == 'vertical':
            move_direction = "down" if self.direction == 1 else "up"

        if move_direction:
            self.anim_controller.set_squash_stretch(move_direction)
            self.anim_controller.set_tilt(move_direction)

        old_x, old_y = self.x, self.y
        move_distance = self.speed * self.direction * dt

        if self.move_type == 'horizontal':
            self.x += move_distance
        elif self.move_type == 'vertical':
            self.y += move_distance

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.hitbox.center = self.rect.center

        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.move_type == 'horizontal':
                    if self.direction == 1:
                        self.rect.right = wall.rect.left
                    else:
                        self.rect.left = wall.rect.right
                    self.x = float(self.rect.x)
                elif self.move_type == 'vertical':
                    if self.direction == 1:
                        self.rect.bottom = wall.rect.top
                    else:
                        self.rect.top = wall.rect.bottom
                    self.y = float(self.rect.y)

                self.hitbox.center = self.rect.center
                self.is_paused = True
                self.pause_timer = self.pause_duration
                break

        self.anim_controller.update(dt)

    def draw(self, surface, debug_mode=False):
        self.anim_controller.draw_animated(surface, self.original_image, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (255, 255, 0), self.hitbox, 1)

    def _on_direction_change(self):
        pass

def is_line_of_sight_clear(start_pos, end_pos, walls):
    for wall in walls:
        if wall.rect.clipline(start_pos, end_pos):
            return False
    return True

class SuperEnemy(Enemy):
    def __init__(self, x, y, move_type, assets, speed=240, hitx=-5, hity=-5):
        super().__init__(x, y, move_type, assets, speed, hitx, hity)
        self.direction_look = 'right' if self.move_type == 'horizontal' else 'down'

        self.sight_length = 2.5 * TILE_SIZE
        self.sight_angle = 10
        self.sight_color = (255, 0, 0, 70)

        self.original_image = None
        texture_name = "enemy_super"

        if assets:
            try:
                self.original_image = assets.get_image(texture_name, scale=(TILE_SIZE, TILE_SIZE))
            except pygame.error:
                pass

        if not self.original_image:
            self.original_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.original_image.fill(self.color)

    def _on_direction_change(self):
        if self.move_type == 'horizontal':
            self.direction_look = 'left' if self.direction == -1 else 'right'
        elif self.move_type == 'vertical':
            self.direction_look = 'up' if self.direction == -1 else 'down'

    def _cast_ray(self, start_pos, angle_rad, length, walls):
        end_x = start_pos[0] + math.cos(angle_rad) * length
        end_y = start_pos[1] - math.sin(angle_rad) * length
        end_pos = (end_x, end_y)

        closest_end_pos = end_pos
        min_dist_sq = length * length

        for wall in walls:
            clipped_line = wall.rect.clipline(start_pos, end_pos)
            if clipped_line:
                hit_point = clipped_line[0]
                dist_sq = (hit_point[0] - start_pos[0]) ** 2 + (hit_point[1] - start_pos[1]) ** 2
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_end_pos = hit_point
        return closest_end_pos

    def check_sight(self, player_rect, walls):
        player_pos = player_rect.center
        enemy_pos = self.rect.center

        vec_x = player_pos[0] - enemy_pos[0]
        vec_y = player_pos[1] - enemy_pos[1]

        dist_sq = vec_x ** 2 + vec_y ** 2
        if dist_sq > self.sight_length ** 2:
            return False

        if dist_sq == 0:
            return True

        angle_to_player_rad = math.atan2(-vec_y, vec_x)

        if self.direction_look == 'up':
            base_angle_rad = math.radians(90)
        elif self.direction_look == 'down':
            base_angle_rad = math.radians(-90)
        elif self.direction_look == 'left':
            base_angle_rad = math.radians(180)
        else:
            base_angle_rad = math.radians(0)

        angle_diff = (angle_to_player_rad - base_angle_rad)
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) > math.radians(self.sight_angle):
            return False

        return is_line_of_sight_clear(enemy_pos, player_pos, walls)

    def draw_sight(self, surface, walls):
        start_pos = self.rect.center

        if self.direction_look == 'up':
            base_angle_rad = math.radians(90)
        elif self.direction_look == 'down':
            base_angle_rad = math.radians(-90)
        elif self.direction_look == 'left':
            base_angle_rad = math.radians(180)
        else:
            base_angle_rad = math.radians(0)

        angle_left_rad = base_angle_rad + math.radians(self.sight_angle)
        angle_right_rad = base_angle_rad - math.radians(self.sight_angle)

        points = [start_pos]
        num_rays = 10
        for i in range(num_rays + 1):
            lerp_factor = i / num_rays
            current_angle_rad = angle_right_rad + (angle_left_rad - angle_right_rad) * lerp_factor
            end_point = self._cast_ray(start_pos, current_angle_rad, self.sight_length, walls)
            points.append(end_point)
        points.append(start_pos)

        if len(points) > 2:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, self.sight_color, points)
            surface.blit(s, (0, 0))
