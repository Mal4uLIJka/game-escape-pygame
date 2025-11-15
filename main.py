import pygame
import json
import random
import math

TILE_SIZE = 40
GRID_WIDTH = 32
GRID_HEIGHT = 18
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Tile:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def draw(self, surface):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        surface.blit(s, self.rect.topleft)


class Wall(Tile):
    def __init__(self, x, y, texture=None):
        super().__init__(x, y)
        self.texture = texture
        self.image = None
        self.was_reverse = False
        if self.texture:
            try:
                self.image = pygame.image.load(self.texture).convert_alpha()
                self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
            except pygame.error:
                print(f"Текстура '{self.texture}' не найдена.")

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect.topleft)

    def debug_draw(self, surface):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill((255, 0, 0, 128))
        surface.blit(s, self.rect.topleft)


class Door(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.s.fill((255, 255, 0, 128))

    def draw(self, surface):
        surface.blit(self.s, self.rect.topleft)


class Slow(Tile):
    def __init__(self, x, y, speed=2):
        super().__init__(x, y)
        self.speed = speed
        self.s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.s.fill((0, 255, 0, 128))

    def draw(self, surface):
        pass

    def debug_draw(self, surface):
        surface.blit(self.s, self.rect.topleft)


class Death(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.s.fill((0, 0, 255, 128))

    def draw(self, surface):
        pass

    def debug_draw(self, surface):
        surface.blit(self.s, self.rect.topleft)


class Reverse(Tile):
    def __init__(self, x, y, wall_texture="./images/reverse_tile.png", base_texture="./images/reverse_tile_on.png"):
        super().__init__(x, y)
        self.wall_texture = wall_texture
        self.base_texture = base_texture
        self.is_transforming = False
        self.transform_timer = 0
        self.transform_duration = 20
        self.alpha = 255
        self.fade_speed = 255 // self.transform_duration

        self.wall_image, self.base_image = None, None

        try:
            self.wall_image = pygame.image.load(self.wall_texture).convert_alpha()
            self.wall_image = pygame.transform.scale(self.wall_image, (TILE_SIZE, TILE_SIZE))
        except pygame.error:
            pass
        try:
            self.base_image = pygame.image.load(self.base_texture).convert_alpha()
            self.base_image = pygame.transform.scale(self.base_image, (TILE_SIZE, TILE_SIZE))
        except pygame.error:
            pass

    def start_transformation(self):
        self.is_transforming = True
        self.transform_timer = 0
        self.alpha = 255

    def reset(self):
        self.is_transforming = False
        self.transform_timer = 0
        self.alpha = 255

    def update(self):
        if self.is_transforming:
            self.transform_timer += 1
            self.alpha = max(0, 255 - (self.transform_timer * self.fade_speed))

            if self.transform_timer >= self.transform_duration:
                self.is_transforming = False
                new_wall = Wall(self.rect.x, self.rect.y, self.wall_texture)
                new_wall.was_reverse = True
                return new_wall
        return None

    def draw(self, surface):
        if self.is_transforming:
            if self.wall_image:
                wall_surface = self.wall_image.copy()
                wall_alpha = 255 - self.alpha
                wall_surface.fill((255, 255, 255, wall_alpha), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(wall_surface, self.rect.topleft)
            if self.base_image:
                base_surface = self.base_image.copy()
                base_surface.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(base_surface, self.rect.topleft)
        else:
            if self.base_image:
                surface.blit(self.base_image, self.rect.topleft)

    def debug_draw(self, surface):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        if self.is_transforming:
            s.fill((0, 255, 255, 255))
        else:
            s.fill((0, 255, 255, 128))
        surface.blit(s, self.rect.topleft)


class Coin(Tile):
    def __init__(self, x, y, value=100, texture_path="./images/coin.png"):
        super().__init__(x, y)
        self.value = value
        self.is_collecting = False
        self.alpha = 255
        self.fade_speed = 15
        self.hitbox = self.rect.inflate(-20, -20)
        self.hitbox.center = self.rect.center

        self.image = None
        try:
            self.image = pygame.image.load(texture_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        except pygame.error:
            print(f"Текстура монеты '{texture_path}' не найдена.")

    def draw(self, surface, debug_mode=False):
        if self.alpha > 0:
            if self.image:
                temp_image = self.image.copy()
                temp_image.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(temp_image, self.rect.topleft)
            else:
                s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                s.fill((255, 255, 0, self.alpha))
                surface.blit(s, self.rect.topleft)
        if debug_mode:
            pygame.draw.rect(surface, (0, 0, 255), self.hitbox, 1)

    def update(self):
        if self.is_collecting:
            self.alpha = max(0, self.alpha - self.fade_speed)
            self.hitbox.center = self.rect.center


class Checkpoint(Tile):
    def __init__(self, x, y, checkoff="./images/checkpoint_off.png", checkon="./images/checkpoint_on.png"):
        super().__init__(x, y)
        self.checkoff_path = checkoff
        self.checkon_path = checkon
        self.is_active = False

        self.image_off = None
        self.image_on = None

        try:
            self.image_off = pygame.image.load(self.checkoff_path).convert_alpha()
            self.image_off = pygame.transform.scale(self.image_off, (TILE_SIZE, TILE_SIZE))
        except pygame.error:
            print(f"Текстура 'checkoff' '{self.checkoff_path}' не найдена.")

        try:
            self.image_on = pygame.image.load(self.checkon_path).convert_alpha()
            self.image_on = pygame.transform.scale(self.image_on, (TILE_SIZE, TILE_SIZE))
        except pygame.error:
            print(f"Текстура 'checkon' '{self.checkon_path}' не найдена.")

    def draw(self, surface):
        if self.is_active:
            if self.image_on:
                surface.blit(self.image_on, self.rect.topleft)
        else:
            if self.image_off:
                surface.blit(self.image_off, self.rect.topleft)

    def debug_draw(self, surface):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        color = (100, 255, 100, 255) if self.is_active else (100, 100, 255, 128)
        s.fill(color)
        surface.blit(s, self.rect.topleft)

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False


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
        self.wobble_speed = 0.1 * (self.anim_speed/2)
        self.is_moving = False

    def update(self):
        lerp_factor = 0.7
        self.scale_x += (self.target_scale_x - self.scale_x) * lerp_factor
        self.scale_y += (self.target_scale_y - self.scale_y) * lerp_factor

        if self.is_moving:
            self.wobble_timer += self.wobble_speed
            self.current_tilt = self.target_tilt * math.sin(self.wobble_timer)
        else:
            self.wobble_timer = 0.0
            self.current_tilt += (0.0 - self.current_tilt) * 0.2

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


class Player:
    def __init__(self, x, y, assets, base_speed=5):
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
        self.pressed_keys = set()
        self.reverse_tiles_underneath = []
        self.target_x = None
        self.target_y = None
        self.anim_controller = AnimationController(squash_factor=0.04, tilt_factor=15)

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

    def update(self):
        self.anim_controller.update()

        if not self.is_moving:
            self.anim_controller.reset_animation()

        if not self.is_moving:
            return
        if self.direction == "left":
            self.x = max(self.target_x, self.x - self.speed)
        elif self.direction == "right":
            self.x = min(self.target_x, self.x + self.speed)
        elif self.direction == "up":
            self.y = max(self.target_y, self.y - self.speed)
        elif self.direction == "down":
            self.y = min(self.target_y, self.y + self.speed)
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

    def draw(self, surface, debug_mode=False):
        self.anim_controller.draw_animated(surface, self.original_image, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (0, 0, 255), self.hitbox, 1)
            pygame.draw.rect(surface, (0, 0, 255), self.rect, 1)


class Enemy:
    def __init__(self, x, y, move_type, assets, speed=2, hitx=-5, hity=-5):
        self.start_pos = (x, y)
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hitbox = self.rect.copy()
        self.hitbox.inflate_ip(hitx, hity)
        self.move_type = move_type
        self.speed = float(speed)
        self.direction = 1
        self.color = (255, 0, 0) if speed > 2 else (180, 50, 50)
        self.anim_controller = AnimationController(squash_factor=0.02, tilt_factor=5, anim_speed=speed)

        self.is_paused = False
        self.pause_timer = 0
        self.pause_duration = 30

        self.original_image = None
        texture_name = ""
        if speed == 2:
            texture_name = "enemy_slow"
        elif speed == 4:
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

    def update(self, walls):
        if self.is_paused:
            self.pause_timer -= 1
            if self.pause_timer <= 0:
                self.is_paused = False
                self.direction *= -1

            self.anim_controller.reset_animation()
            self.anim_controller.update()
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
        if self.move_type == 'horizontal':
            self.x += self.speed * self.direction
        elif self.move_type == 'vertical':
            self.y += self.speed * self.direction
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.hitbox.center = self.rect.center

        for wall in walls:
            if self.rect.colliderect(wall.rect):
                self.x, self.y = old_x, old_y
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                self.hitbox.center = self.rect.center
                self.is_paused = True
                self.pause_timer = self.pause_duration
                break

        self.anim_controller.update()

    def draw(self, surface, debug_mode=False):
        self.anim_controller.draw_animated(surface, self.original_image, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (255, 255, 0), self.hitbox, 1)


def is_line_of_sight_clear(start_pos, end_pos, walls):
    for wall in walls:
        if wall.rect.clipline(start_pos, end_pos):
            return False
    return True


class SuperEnemy(Enemy):
    def __init__(self, x, y, move_type, assets, speed=2, hitx=-5, hity=-5):
        super().__init__(x, y, move_type, assets, speed, hitx, hity)
        self.color = (139, 0, 0)
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

    def update(self, walls):
        if self.is_paused:
            self.pause_timer -= 1
            if self.pause_timer <= 0:
                self.is_paused = False
                self.direction *= -1
                if self.move_type == 'horizontal':
                    self.direction_look = 'left' if self.direction == -1 else 'right'
                elif self.move_type == 'vertical':
                    self.direction_look = 'up' if self.direction == -1 else 'down'

            self.anim_controller.reset_animation()
            self.anim_controller.update()
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
        if self.move_type == 'horizontal':
            self.x += self.speed * self.direction
        elif self.move_type == 'vertical':
            self.y += self.speed * self.direction
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.hitbox.center = self.rect.center

        for wall in walls:
            if self.rect.colliderect(wall.rect):
                self.x, self.y = old_x, old_y
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                self.hitbox.center = self.rect.center
                self.is_paused = True
                self.pause_timer = self.pause_duration
                break

        self.anim_controller.update()

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


class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}

    def load_image(self, name, path):
        try:
            image = pygame.image.load(path).convert_alpha()
            self.images[name] = image
        except pygame.error:
            print(f"Не удалось загрузить изображение: {path}")
            self.images[name] = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.images[name].fill((255, 0, 255))

    def get_image(self, name, scale=None):
        image = self.images.get(name)
        if image and scale:
            return pygame.transform.smoothscale(image, scale)
        return image

    def load_sound(self, name, path):
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except pygame.error:
            print(f"Не удалось загрузить звук: {path}")

    def get_sound(self, name):
        return self.sounds.get(name)


class LevelLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.levels_data = self._load_json()

        self.tile_map = {
            "#": lambda x, y: Wall(x, y),
            " ": None,
            "P": "player",
            "h": lambda x, y, assets: Enemy(x, y, 'horizontal', assets, speed=2),
            "v": lambda x, y, assets: Enemy(x, y, 'vertical', assets, speed=2),
            "f": lambda x, y, assets: Enemy(x, y, 'horizontal', assets, speed=4),
            "l": lambda x, y, assets: Enemy(x, y, 'vertical', assets, speed=4),
            "D": lambda x, y: Door(x, y),
            "s": lambda x, y: Slow(x, y),
            "S": lambda x, y: Slow(x, y, 20),
            "X": lambda x, y: Death(x, y),
            "$": lambda x, y: Coin(x, y),
            "@": lambda x, y: Reverse(x, y),
            "H": lambda x, y, assets: SuperEnemy(x, y, 'horizontal', assets, speed=2),
            "V": lambda x, y, assets: SuperEnemy(x, y, 'vertical', assets, speed=2),
            "F": lambda x, y, assets: SuperEnemy(x, y, 'horizontal', assets, speed=4),
            "L": lambda x, y, assets: SuperEnemy(x, y, 'vertical', assets, speed=4),
            "C": lambda x, y: Checkpoint(x, y)
        }
        self.class_map = {
            Wall: [], Door: [], Slow: [], Death: [], Reverse: [], Coin: [], Enemy: [], Checkpoint: []
        }

    def _load_json(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def load_level(self, level_name, assets):
        level_data = self.levels_data.get(level_name)
        if not level_data:
            raise ValueError(f"Уровень '{level_name}' не найден в JSON.")
        for obj_list in self.class_map.values():
            obj_list.clear()
        player_spawn = None
        level_matrix = level_data["matrix"]
        for y, row in enumerate(level_matrix):
            for x, cell in enumerate(row):
                pos_x, pos_y = x * TILE_SIZE, y * TILE_SIZE
                tile_type = self.tile_map.get(cell)
                if tile_type is None:
                    continue
                elif tile_type == "player":
                    player_spawn = (pos_x, pos_y)
                else:
                    obj = None
                    if cell in ["h", "v", "f", "l", "H", "V", "F", "L"]:
                        obj = tile_type(pos_x, pos_y, assets)
                    else:
                        obj = tile_type(pos_x, pos_y)

                    for cls, obj_list in self.class_map.items():
                        if isinstance(obj, cls):
                            obj_list.append(obj)
                            break

        current_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        current_background.fill(pygame.Color('darkgrey'))

        try:
            background_image = pygame.image.load(level_data["background"]).convert()
            current_background = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error:
            print(f"Фон '{level_data['background']}' не найден. Используется серый цвет.")

        return (
            self.class_map[Wall],
            self.class_map[Enemy],
            self.class_map[Door],
            player_spawn,
            current_background,
            self.class_map[Death],
            self.class_map[Slow],
            self.class_map[Reverse],
            self.class_map[Coin],
            self.class_map[Checkpoint]
        )


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)

        pygame.font.init()
        try:
            self.ui_font = pygame.font.Font("./fonts/DigitalSemi-SerifPixel-Regular.otf", 12)
        except FileNotFoundError:
            print("UI Font not found, using default.")
            self.ui_font = pygame.font.Font(None, 12)

        self.score = 0
        self.time = pygame.time.get_ticks()
        self.clock = pygame.time.Clock()
        self.elapsed_time = 0

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Побег из 2 общежития")

        self.running = True
        self.debug_mode = False

        self.level_loader = LevelLoader('levels.json')
        self.level_names = list(self.level_loader.levels_data.keys())
        self.current_level_index = 3

        self.walls = []
        self.enemies = []
        self.doors = []
        self.player_spawn = None
        self.active_checkpoint_pos = None
        self.current_background = None
        self.death_tiles = []
        self.slow_tiles = []
        self.reverse_tiles = []
        self.coins = []
        self.checkpoint_tiles = []
        self.transforming_reverse_tiles = []

        self.assets = AssetManager()
        self.assets.load_image("hero", "./images/hero.png")
        self.assets.load_image("enemy_slow", "./images/enemy.png")
        self.assets.load_image("enemy_fast", "./images/angry_enemy.png")
        self.assets.load_image("enemy_super", "./images/super_angry_enemy.png")

        self.assets.load_sound("checkpoint", "./sounds/checkpoint.wav")
        self.assets.load_sound("death", "./sounds/hitHurt.wav")
        self.assets.load_sound("coin", "./sounds/pickupCoin.wav")
        self.assets.load_sound("next_level", "./sounds/nextLevel.wav")
        self.assets.load_sound("reverse", "./sounds/click.wav")

        self.player = Player(40, 40, self.assets)

    def load_current_level(self):
        self.transforming_reverse_tiles.clear()

        if self.current_level_index < len(self.level_names):
            level_name = self.level_names[self.current_level_index]

            (self.walls, self.enemies, self.doors, self.player_spawn,
             self.current_background, self.death_tiles, self.slow_tiles,
             self.reverse_tiles, self.coins, self.checkpoint_tiles) = self.level_loader.load_level(level_name,
                                                                                                   self.assets)

            if self.player_spawn:
                self.player.start_pos = self.player_spawn

            self.player.reset()

            if self.active_checkpoint_pos:
                self.player.start_pos = self.active_checkpoint_pos
                self.player.reset()
                for cp in self.checkpoint_tiles:
                    if cp.rect.topleft == self.active_checkpoint_pos:
                        cp.activate()
                        break

            return True
        else:
            print("Поздравляю! Вы прошли все уровни!")
            return False

    def run(self):
        if not self.load_current_level():
            return

        self.active_checkpoint_pos = None

        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(120)

        pygame.quit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v:
                    self.debug_mode = not self.debug_mode
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                    self.player.pressed_keys.add(event.key)
            if event.type == pygame.KEYUP:
                if event.key in self.player.pressed_keys:
                    self.player.pressed_keys.remove(event.key)

    def update(self):
        self.elapsed_time = (pygame.time.get_ticks() - self.time) // 1000

        if not self.player.is_moving:
            direction_to_move = None
            if pygame.K_UP in self.player.pressed_keys:
                direction_to_move = "up"
            elif pygame.K_DOWN in self.player.pressed_keys:
                direction_to_move = "down"
            elif pygame.K_LEFT in self.player.pressed_keys:
                direction_to_move = "left"
            elif pygame.K_RIGHT in self.player.pressed_keys:
                direction_to_move = "right"
            if direction_to_move:
                self.player.start_move(direction_to_move, self.walls, self.transforming_reverse_tiles)

        current_reverse_tiles = []
        for path in self.reverse_tiles:
            if self.player.rect.colliderect(path.rect):
                current_reverse_tiles.append(path)

        for tile in self.player.reverse_tiles_underneath:
            if tile not in current_reverse_tiles and not tile.is_transforming:
                tile.start_transformation()
                self.transforming_reverse_tiles.append(tile)
        self.player.reverse_tiles_underneath = current_reverse_tiles

        completed_transformations = []
        for tile in self.transforming_reverse_tiles:
            new_wall = tile.update()
            if new_wall:
                self.walls.append(new_wall)
                completed_transformations.append(tile)
                sound = self.assets.get_sound("reverse")
                if sound:
                    sound.set_volume(0.4)
                    channel = pygame.mixer.find_channel(True)
                    channel.play(sound)
        for tile in completed_transformations:
            if tile in self.transforming_reverse_tiles: self.transforming_reverse_tiles.remove(tile)
            if tile in self.reverse_tiles: self.reverse_tiles.remove(tile)

        self.player.update()

        for checkpoint in self.checkpoint_tiles:
            if self.player.hitbox.colliderect(checkpoint.rect) and not checkpoint.is_active:
                for cp in self.checkpoint_tiles:
                    cp.deactivate()
                checkpoint.activate()
                self.active_checkpoint_pos = checkpoint.rect.topleft
                sound = self.assets.get_sound("checkpoint")
                if sound:
                    sound.set_volume(0.4)
                    channel = pygame.mixer.find_channel(True)
                    channel.play(sound)

        player_needs_reset = False
        for enemy in self.enemies:
            if isinstance(enemy, SuperEnemy):
                if enemy.check_sight(self.player.rect, self.walls):
                    player_needs_reset = True
                    break
            if self.player.hitbox.colliderect(enemy.hitbox):
                player_needs_reset = True
                break
        if not player_needs_reset:
            for tile in self.death_tiles:
                if self.player.hitbox.colliderect(tile.rect):
                    player_needs_reset = True
                    break

        for enemy in self.enemies:
            enemy.update(self.walls)

        slow_tile_found = None
        for tile in self.slow_tiles:
            if self.player.hitbox.colliderect(tile.rect):
                slow_tile_found = tile
                break
        if slow_tile_found:
            self.player.speed = self.player.base_speed / slow_tile_found.speed
        else:
            self.player.speed = self.player.base_speed

        for door in self.doors:
            if self.player.hitbox.colliderect(door.rect):
                sound = self.assets.get_sound("next_level")
                if sound:
                    sound.set_volume(0.4)
                    channel = pygame.mixer.find_channel(True)
                    channel.play(sound)
                self.current_level_index += 1
                self.active_checkpoint_pos = None
                running = self.load_current_level()
                if not running:
                    break

        if player_needs_reset:
            sound = self.assets.get_sound("death")
            if sound:
                sound.set_volume(0.4)
                channel = pygame.mixer.find_channel(True)
                channel.play(sound)

            saved_checkpoint_pos = self.active_checkpoint_pos

            self.load_current_level()

            if saved_checkpoint_pos:
                self.player.start_pos = saved_checkpoint_pos
                self.active_checkpoint_pos = saved_checkpoint_pos
                self.player.reset()

                for cp in self.checkpoint_tiles:
                    if cp.rect.topleft == saved_checkpoint_pos:
                        cp.activate()
                        break

        for coin in self.coins:
            if self.player.hitbox.colliderect(coin.hitbox) and not coin.is_collecting:
                coin.is_collecting = True
                self.score += coin.value
                sound = self.assets.get_sound("coin")
                if sound:
                    sound.set_volume(0.4)
                    channel = pygame.mixer.find_channel(True)
                    channel.play(sound)
            coin.update()
        self.coins = [coin for coin in self.coins if coin.alpha > 0]

    def draw(self):
        if self.current_background:
            self.screen.blit(self.current_background, (0, 0))

        for tile in self.walls + self.reverse_tiles + self.transforming_reverse_tiles + self.coins + self.checkpoint_tiles:
            tile.draw(self.screen)

        for enemy in self.enemies:
            if isinstance(enemy, SuperEnemy):
                enemy.draw_sight(self.screen, self.walls)
            enemy.draw(self.screen)

        self.player.draw(self.screen)

        if self.debug_mode:
            for tile in self.walls + self.slow_tiles + self.death_tiles + self.reverse_tiles + self.transforming_reverse_tiles + self.checkpoint_tiles:
                tile.debug_draw(self.screen)

            for enemy in self.enemies:
                enemy.draw(self.screen, True)

            self.player.draw(self.screen, True)

            for coin in self.coins:
                coin.draw(self.screen, True)

        score_str = f"Очки:{self.score} Время:{self.elapsed_time}"
        score_surf_main = self.ui_font.render(score_str, True, WHITE)
        score_rect = score_surf_main.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 12)
        score_surf_outline = self.ui_font.render(score_str, True, BLACK)

        offset = 2

        self.screen.blit(score_surf_outline, (score_rect.x - offset, score_rect.y))
        self.screen.blit(score_surf_outline, (score_rect.x + offset, score_rect.y))
        self.screen.blit(score_surf_outline, (score_rect.x, score_rect.y - offset))
        self.screen.blit(score_surf_outline, (score_rect.x, score_rect.y + offset))

        self.screen.blit(score_surf_main, score_rect)

        pygame.display.flip()


if __name__ == '__main__':
    game = Game()
    game.run()