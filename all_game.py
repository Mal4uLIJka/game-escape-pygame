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
GREY = (100, 100, 100)
RED = (200, 0, 0)
HOVER_COLOR = (200, 200, 200)

def load_tile_image(path, size=(TILE_SIZE, TILE_SIZE)):
    """
    Загружает и масштабирует изображение, обрабатывая ошибки.
    """
    if not path:
        return None
    try:
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, size)
    except pygame.error:
        print(f"Текстура '{path}' не найдена.")
        return None

class Tile:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def draw(self, surface):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        surface.blit(s, self.rect.topleft)

    def debug_draw(self, surface, color=(255, 0, 0, 128)):
        """
        Универсальный метод для отрисовки отладочного прямоугольника.
        """
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill(color)
        surface.blit(s, self.rect.topleft)

class Wall(Tile):
    def __init__(self, x, y, texture=None):
        super().__init__(x, y)
        self.texture = texture
        self.image = load_tile_image(self.texture)
        self.was_reverse = False

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect.topleft)

    def debug_draw(self, surface):
        super().debug_draw(surface)

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

    def draw(self, surface):
        pass

    def debug_draw(self, surface):
        super().debug_draw(surface, color=(0, 255, 0, 128))


class Death(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)

    def draw(self, surface):
        pass

    def debug_draw(self, surface):
        super().debug_draw(surface, color=(0, 0, 255, 128))


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

        self.wall_image = load_tile_image(self.wall_texture)
        self.base_image = load_tile_image(self.base_texture)

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
        color = (0, 255, 255, 255) if self.is_transforming else (0, 255, 255, 128)
        super().debug_draw(surface, color=color)


class Coin(Tile):
    def __init__(self, x, y, value=100, texture_path="./images/coin.png"):
        super().__init__(x, y)
        self.value = value
        self.is_collecting = False
        self.alpha = 255
        self.fade_speed = 15
        self.hitbox = self.rect.inflate(-20, -20)
        self.hitbox.center = self.rect.center

        self.image = load_tile_image(texture_path)

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
        self.image_off = load_tile_image(self.checkoff_path)
        self.image_on = load_tile_image(self.checkon_path)

    def draw(self, surface):
        if self.is_active:
            if self.image_on:  # Теперь эта проверка сработает
                surface.blit(self.image_on, self.rect.topleft)
        else:
            if self.image_off: # И эта тоже
                surface.blit(self.image_off, self.rect.topleft)

    def debug_draw(self, surface):
        color = (100, 255, 100, 255) if self.is_active else (100, 100, 255, 128)
        super().debug_draw(surface, color=color)

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
        self.anim_controller = AnimationController(squash_factor=0.02, tilt_factor=5, anim_speed=speed / 120)

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
                self.x, self.y = old_x, old_y
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
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
            "h": lambda x, y, assets: Enemy(x, y, 'horizontal', assets, speed=240),
            "v": lambda x, y, assets: Enemy(x, y, 'vertical', assets, speed=240),
            "f": lambda x, y, assets: Enemy(x, y, 'horizontal', assets, speed=480),
            "l": lambda x, y, assets: Enemy(x, y, 'vertical', assets, speed=480),
            "D": lambda x, y: Door(x, y),
            "s": lambda x, y: Slow(x, y, speed=2),
            "S": lambda x, y: Slow(x, y, speed=20),
            "X": lambda x, y: Death(x, y),
            "$": lambda x, y: Coin(x, y),
            "@": lambda x, y: Reverse(x, y),
            "H": lambda x, y, assets: SuperEnemy(x, y, 'horizontal', assets, speed=240),
            "V": lambda x, y, assets: SuperEnemy(x, y, 'vertical', assets, speed=240),
            "F": lambda x, y, assets: SuperEnemy(x, y, 'horizontal', assets, speed=480),
            "L": lambda x, y, assets: SuperEnemy(x, y, 'vertical', assets, speed=480),
            "C": lambda x, y: Checkpoint(x, y)
        }
        self.class_map = {
            Wall: [], Door: [], Slow: [], Death: [], Reverse: [], Coin: [], Enemy: [], Checkpoint: []
        }

    def _load_json(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def load_level(self, level_name, assets, is_menu_load=False):
        level_data = self.levels_data.get(level_name)
        if not level_data:
            raise ValueError(f"Уровень '{level_name}' не найден в JSON.")

        current_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        current_background.fill(pygame.Color('darkgrey'))
        try:
            background_image = pygame.image.load(level_data["background"]).convert()
            current_background = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error:
            print(f"Фон '{level_data['background']}' не найден. Используется серый цвет.")

        if is_menu_load:
            return current_background

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


class Button:
    def __init__(self, x, y, width, height, text, font, callback, subtext_font=None, subtext=None, disabled=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.subtext = subtext
        self.subtext_font = subtext_font
        self.disabled = disabled
        self.hovered = False

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered and not self.disabled:
            self.callback()
            return True
        return False

    def draw(self, surface):
        color = GREY if self.disabled else (HOVER_COLOR if self.hovered else WHITE)

        main_surf = self.font.render(self.text, True, color)
        main_rect = main_surf.get_rect(center=self.rect.center)

        main_surf_outline = self.font.render(self.text, True, BLACK)

        offset = 2
        surface.blit(main_surf_outline, (main_rect.x - offset, main_rect.y))
        surface.blit(main_surf_outline, (main_rect.x + offset, main_rect.y))
        surface.blit(main_surf_outline, (main_rect.x, main_rect.y - offset))
        surface.blit(main_surf_outline, (main_rect.x, main_rect.y + offset))
        surface.blit(main_surf, main_rect)

        if self.subtext:
            sub_color = GREY if self.disabled else WHITE
            sub_surf = self.subtext_font.render(self.subtext, True, sub_color)
            sub_rect = sub_surf.get_rect(centerx=self.rect.centerx, top=self.rect.bottom + 5)

            sub_surf_outline = self.subtext_font.render(self.subtext, True, BLACK)

            surface.blit(sub_surf_outline, (sub_rect.x - offset, sub_rect.y))
            surface.blit(sub_surf_outline, (sub_rect.x + offset, sub_rect.y))
            surface.blit(sub_surf_outline, (sub_rect.x, sub_rect.y - offset))
            surface.blit(sub_surf_outline, (sub_rect.x, sub_rect.y + offset))
            surface.blit(sub_surf, sub_rect)


class MenuManager:
    def __init__(self, game):
        self.game = game
        self.font_small = game.font_small
        self.font_medium = game.font_medium
        self.font_large = game.font_large
        self.overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.win_animation_timer = 0
        self.win_animation_duration = 120

        self.main_menu_buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 350, 200, 50, "Начать", self.font_medium, self.game.start_game),
            Button(SCREEN_WIDTH // 2 - 100, 420, 200, 50, "Выйти", self.font_medium, self.game.quit_game)
        ]

        self.death_menu_buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 350, 300, 50, "Продолжить с чекпоинта", self.font_medium,
                   self.game.continue_from_checkpoint, self.font_small, "(-100 Очков, +5c Времени)"),
            Button(SCREEN_WIDTH // 2 - 150, 440, 300, 50, "Начать с нуля", self.font_medium, self.game.start_game)
        ]

        self.win_menu_buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 400, 200, 50, "Начать с нуля", self.font_medium, self.game.start_game),
            Button(SCREEN_WIDTH // 2 - 100, 470, 200, 50, "Выйти", self.font_medium, self.game.quit_game)
        ]

    def handle_event(self, event, game_state):
        button_list = []
        if game_state == "main_menu":
            button_list = self.main_menu_buttons
        elif game_state == "death_screen":
            button_list = self.death_menu_buttons
        elif game_state == "win_screen":
            if self.win_animation_timer >= self.win_animation_duration:
                button_list = self.win_menu_buttons

        for button in button_list:
            button.handle_event(event)

    def update(self, mouse_pos, game_state):
        button_list = []
        if game_state == "main_menu":
            button_list = self.main_menu_buttons
        elif game_state == "death_screen":
            self.death_menu_buttons[0].disabled = self.game.active_checkpoint_pos is None
            button_list = self.death_menu_buttons
        elif game_state == "win_screen":
            if self.win_animation_timer < self.win_animation_duration:
                self.win_animation_timer += 1
                if self.win_animation_timer > 60:
                    self.game.player.visible = False
            else:
                button_list = self.win_menu_buttons

        for button in button_list:
            button.check_hover(mouse_pos)

    def draw(self, surface, game_state):
        if game_state == "main_menu":
            self.draw_main_menu(surface)
        elif game_state == "death_screen":
            self.draw_death_screen(surface)
        elif game_state == "win_screen":
            self.draw_win_screen(surface)

    def draw_main_menu(self, surface):
        surface.blit(self.game.main_menu_bg_dimmed, (0, 0))
        self.draw_text_with_outline(surface, "Игра-побег", self.font_large, WHITE, (SCREEN_WIDTH // 2, 200))
        for button in self.main_menu_buttons:
            button.draw(surface)

    def draw_death_screen(self, surface):
        self.game.in_game_draw()

        self.overlay_surface.fill((0, 0, 0, 180))
        surface.blit(self.overlay_surface, (0, 0))

        self.draw_text_with_outline(surface, "Вы умерли", self.font_large, RED, (SCREEN_WIDTH // 2, 200))

        self.draw_text_with_outline(surface, self.get_stats_text(), self.font_medium, WHITE, (SCREEN_WIDTH // 2, 280))

        for button in self.death_menu_buttons:
            button.draw(surface)

        self.draw_text_with_outline(surface, f"Очки: {self.game.score}  Время: {self.game.elapsed_time}c",
                                    self.font_small, WHITE,
                                    (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12), center_bottom=True)

    def draw_win_screen(self, surface):
        self.game.in_game_draw()

        alpha = min(200, int(200 * (self.win_animation_timer / self.win_animation_duration)))
        self.overlay_surface.fill((0, 0, 0, alpha))
        surface.blit(self.overlay_surface, (0, 0))

        if self.win_animation_timer >= self.win_animation_duration:
            self.draw_text_with_outline(surface, "Вы сбежали!", self.font_large, WHITE, (SCREEN_WIDTH // 2, 200))

            self.draw_text_with_outline(surface, self.get_stats_text(), self.font_medium, WHITE,
                                        (SCREEN_WIDTH // 2, 280))

            for button in self.win_menu_buttons:
                button.draw(surface)

        self.draw_text_with_outline(surface, f"Очки: {self.game.score}  Время: {self.game.elapsed_time}c",
                                    self.font_small, WHITE,
                                    (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12), center_bottom=True)

    def get_stats_text(self):
        score_str = f"Очки: {self.game.score} Время: {self.game.elapsed_time}c"
        return score_str

    def draw_text_with_outline(self, surface, text, font, color, center_pos, center_bottom=False):
        main_surf = font.render(text, True, color)
        outline_surf = font.render(text, True, BLACK)

        if center_bottom:
            main_rect = main_surf.get_rect(centerx=center_pos[0], bottom=center_pos[1])
        else:
            main_rect = main_surf.get_rect(center=center_pos)

        offset = 2
        surface.blit(outline_surf, (main_rect.x - offset, main_rect.y))
        surface.blit(outline_surf, (main_rect.x + offset, main_rect.y))
        surface.blit(outline_surf, (main_rect.x, main_rect.y - offset))
        surface.blit(outline_surf, (main_rect.x, main_rect.y + offset))

        surface.blit(main_surf, main_rect)


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)

        pygame.font.init()
        font_path = "./fonts/DigitalSemi-SerifPixel-Regular.otf"
        try:
            self.font_small = pygame.font.Font(font_path, 12)
            self.font_medium = pygame.font.Font(font_path, 34)
            self.font_large = pygame.font.Font(font_path, 64)
        except FileNotFoundError:
            print("UI Font not found, using default.")
            self.font_small = pygame.font.Font(None, 24)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_large = pygame.font.Font(None, 72)

        self.score = 0
        self.start_time = 0
        self.time_penalty = 0
        self.elapsed_time = 0
        self.clock = pygame.time.Clock()

        self.debug_start_level = 3

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Игра-побег")

        self.running = True
        self.debug_mode = False
        self.game_state = "main_menu"

        self.level_loader = LevelLoader('levels.json')
        self.level_names = list(self.level_loader.levels_data.keys())
        self.current_level_index = 0

        self.collected_coins_by_level = {}

        self.walls = []
        self.enemies = []
        self.doors = []
        self.player_spawn = None
        self.active_checkpoint_pos = None
        self.current_background = None
        self.main_menu_bg = None
        self.main_menu_bg_dimmed = None
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
        self.assets.load_sound("spawn", "./sounds/spawn.wav")
        self.assets.load_sound("finish", "./sounds/finish.wav")

        self.default_sound_volume = 0.4

        self.player = Player(40, 40, self.assets)
        self.menu_manager = MenuManager(self)

        self.preload_menu_background()

    def _play_sound(self, sound_name):
        sound = self.assets.get_sound(sound_name)
        if sound:
            sound.set_volume(self.default_sound_volume)
            channel = pygame.mixer.find_channel(True)
            if channel:
                channel.play(sound)

    def preload_menu_background(self):
        if self.level_names:
            level_name = self.level_names[0]
            self.main_menu_bg = self.level_loader.load_level(level_name, self.assets, is_menu_load=True)
            self.main_menu_bg_dimmed = self.main_menu_bg.copy()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.main_menu_bg_dimmed.blit(overlay, (0, 0))
        else:
            self.main_menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.main_menu_bg.fill(BLACK)
            self.main_menu_bg_dimmed = self.main_menu_bg.copy()

    def reset_game(self):
        self.score = 0
        self.start_time = pygame.time.get_ticks()
        self.time_penalty = 0
        self.elapsed_time = 0
        self.current_level_index = self.debug_start_level
        self.active_checkpoint_pos = None
        self.menu_manager.win_animation_timer = 0
        self.player.visible = True
        self.player.held_keys.clear()
        self.player.next_direction = None
        self.collected_coins_by_level = {}

    def start_game(self):
        self.reset_game()
        self.load_current_level()
        self.game_state = "in_game"
        self._play_sound("spawn")

    def quit_game(self):
        self.running = False

    def continue_from_checkpoint(self):
        self.score = max(0, self.score - 100)
        self.time_penalty += 5
        self.player.visible = True
        self.player.held_keys.clear()
        self.player.next_direction = None
        self.load_current_level()
        self.game_state = "in_game"

    def load_current_level(self):
        self.transforming_reverse_tiles.clear()

        if self.current_level_index < len(self.level_names):
            level_name = self.level_names[self.current_level_index]

            (self.walls, self.enemies, self.doors, self.player_spawn,
             self.current_background, self.death_tiles, self.slow_tiles,
             self.reverse_tiles, self.coins, self.checkpoint_tiles) = self.level_loader.load_level(level_name,
                                                                                                   self.assets)

            level_collected_coins = self.collected_coins_by_level.get(self.current_level_index, set())
            self.coins = [coin for coin in self.coins if coin.rect.topleft not in level_collected_coins]

            if self.player_spawn:
                self.player.start_pos = self.player_spawn

            if self.current_level_index > 0 and self.player_spawn:
                self.active_checkpoint_pos = self.player_spawn

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
            self.game_state = "win_screen"
            self._play_sound("finish")
            return False

    def run(self):
        while self.running:
            dt = self.clock.tick(120) / 1000.0
            mouse_pos = pygame.mouse.get_pos()

            self.events(mouse_pos)
            self.update(mouse_pos, dt)
            self.draw()

        pygame.quit()

    def events(self, mouse_pos):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.game_state == "in_game":
                self.in_game_events(event)
            else:
                self.menu_manager.handle_event(event, self.game_state)

    def update(self, mouse_pos, dt):
        if self.game_state == "in_game":
            self.in_game_update(mouse_pos, dt)
        else:
            self.menu_manager.update(mouse_pos, self.game_state)

    def draw(self):
        if self.game_state == "in_game":
            self.in_game_draw()
        else:
            self.menu_manager.draw(self.screen, self.game_state)

        if self.game_state == "in_game":
            self.menu_manager.draw_text_with_outline(self.screen, f"Очки: {self.score}  Время: {self.elapsed_time}c",
                                                     self.font_small, WHITE,
                                                     (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12), center_bottom=True)

        pygame.display.flip()

    def in_game_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_v:
                self.debug_mode = not self.debug_mode

            direction = None
            if event.key == pygame.K_LEFT:
                direction = "left"
            elif event.key == pygame.K_RIGHT:
                direction = "right"
            elif event.key == pygame.K_UP:
                direction = "up"
            elif event.key == pygame.K_DOWN:
                direction = "down"

            if direction:
                self.player.held_keys.add(event.key)
                if self.player.is_moving:
                    self.player.next_direction = direction
                else:
                    self.player.start_move(direction, self.walls, self.transforming_reverse_tiles)

        if event.type == pygame.KEYUP:
            if event.key in self.player.held_keys:
                self.player.held_keys.remove(event.key)

            direction = None
            if event.key == pygame.K_LEFT:
                direction = "left"
            elif event.key == pygame.K_RIGHT:
                direction = "right"
            elif event.key == pygame.K_UP:
                direction = "up"
            elif event.key == pygame.K_DOWN:
                direction = "down"

            if direction and self.player.next_direction == direction:
                self.player.next_direction = None

    def in_game_update(self, mouse_pos, dt):
        self.elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000 + self.time_penalty

        slow_tile_found = None
        for tile in self.slow_tiles:
            if self.player.hitbox.colliderect(tile.rect):
                slow_tile_found = tile
                break
        if slow_tile_found:
            self.player.speed = self.player.base_speed / slow_tile_found.speed
        else:
            self.player.speed = self.player.base_speed

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
                self._play_sound("reverse")
        for tile in completed_transformations:
            if tile in self.transforming_reverse_tiles: self.transforming_reverse_tiles.remove(tile)
            if tile in self.reverse_tiles: self.reverse_tiles.remove(tile)

        self.player.update(dt)

        if not self.player.is_moving:
            direction_to_move = None
            if self.player.next_direction:
                direction_to_move = self.player.next_direction
                self.player.next_direction = None
            else:
                if pygame.K_UP in self.player.held_keys:
                    direction_to_move = "up"
                elif pygame.K_DOWN in self.player.held_keys:
                    direction_to_move = "down"
                elif pygame.K_LEFT in self.player.held_keys:
                    direction_to_move = "left"
                elif pygame.K_RIGHT in self.player.held_keys:
                    direction_to_move = "right"

            if direction_to_move:
                self.player.start_move(direction_to_move, self.walls, self.transforming_reverse_tiles)

        for checkpoint in self.checkpoint_tiles:
            if self.player.hitbox.colliderect(checkpoint.rect) and not checkpoint.is_active:
                for cp in self.checkpoint_tiles:
                    cp.deactivate()
                checkpoint.activate()
                self.active_checkpoint_pos = checkpoint.rect.topleft
                self._play_sound("checkpoint")

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
            enemy.update(self.walls, dt)

        for door in self.doors:
            if self.player.hitbox.colliderect(door.rect):
                self._play_sound("next_level")
                self.current_level_index += 1
                self.active_checkpoint_pos = None
                if not self.load_current_level():
                    break

        if player_needs_reset:
            self._play_sound("death")
            self.game_state = "death_screen"

        for coin in self.coins:
            if self.player.hitbox.colliderect(coin.hitbox) and not coin.is_collecting:
                coin.is_collecting = True
                self.score += coin.value
                self.collected_coins_by_level.setdefault(self.current_level_index, set()).add(coin.rect.topleft)
                self._play_sound("coin")
            coin.update()
        self.coins = [coin for coin in self.coins if coin.alpha > 0]

    def in_game_draw(self):
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


if __name__ == '__main__':
    game = Game()
    game.run()