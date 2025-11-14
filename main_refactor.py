import pygame
import json

# --- Константы ---
TILE_SIZE = 40
GRID_WIDTH = 32
GRID_HEIGHT = 18
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

# --- Классы игры ---

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
    def __init__(self, x, y, wall_texture="./reverse_tile.png", base_texture="./reverse_tile_on.png"):
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
        """Сбрасывает состояние клетки в изначальное"""
        self.is_transforming = False
        self.transform_timer = 0
        self.alpha = 255

    def update(self):
        if self.is_transforming:
            self.transform_timer += 1
            self.alpha = max(0, 255 - (self.transform_timer * self.fade_speed))

            if self.transform_timer >= self.transform_duration:
                self.is_transforming = False
                return Wall(self.rect.x, self.rect.y, self.wall_texture)
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
    def __init__(self, x, y, value=100):
        super().__init__(x, y)
        self.value = value
        self.is_collecting = False
        self.alpha = 255
        self.fade_speed = 15
        self.hitbox = self.rect.inflate(-20, -20)
        self.hitbox.center = self.rect.center

    def draw(self, surface, debug_mode=False):
        if self.alpha > 0:
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
    def __init__(self, x, y):
        super().__init__(x, y)
        self.is_active = False

        self.inactive_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.inactive_image.fill((100, 100, 255, 128))  # Синий для неактивного состояния

        self.active_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.active_image.fill((100, 255, 100, 200))  # Зелёный для активного состояния

    def draw(self, surface):
        if self.is_active:
            surface.blit(self.active_image, self.rect.topleft)
        else:
            surface.blit(self.inactive_image, self.rect.topleft)

    def debug_draw(self, surface):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        color = (100, 255, 100, 255) if self.is_active else (100, 100, 255, 128)
        s.fill(color)
        surface.blit(s, self.rect.topleft)

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False

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
        try:
            self.original_image = assets.get_image("hero", scale=(TILE_SIZE, TILE_SIZE))
            self.original_image = pygame.transform.smoothscale(self.original_image, (TILE_SIZE, TILE_SIZE))
        except pygame.error:
            self.original_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.original_image.fill((0, 200, 0))
            print("Используется стандартный квадрат.")

        self.current_tilt = 0.0
        self.target_tilt = 0.0
        self.tilt_timer = 0
        self.tilt_duration = 5
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        self.scale_timer = 0
        self.scale_duration = 5

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

        if direction == "left" or direction == "right":
            self.target_scale_x = 1.04
            self.target_scale_y = 0.9
        else:
            self.target_scale_x = 0.9
            self.target_scale_y = 1.04
        self.scale_timer = self.scale_duration

        if direction == "left":
            self.target_tilt = -15
        elif direction == "right":
            self.target_tilt = 15
        elif direction == "up":
            self.target_tilt = -15
        elif direction == "down":
            self.target_tilt = 15
        self.tilt_timer = self.tilt_duration

    def update(self):
        # Логика анимации
        lerp_factor = 0.7
        self.scale_x += (self.target_scale_x - self.scale_x) * lerp_factor
        self.scale_y += (self.target_scale_y - self.scale_y) * lerp_factor
        self.current_tilt += (self.target_tilt - self.current_tilt) * lerp_factor

        if not self.is_moving:
            self.target_scale_x, self.target_scale_y = 1.0, 1.0
            self.target_tilt = 0.0

        # Логика движения
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
        self.current_tilt = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0

    def draw(self, surface, debug_mode=False):
        rotated_image = pygame.transform.rotate(self.original_image, self.current_tilt)
        rotated_rect = rotated_image.get_rect(center=self.rect.center)
        scaled_width = int(rotated_rect.width * self.scale_x)
        scaled_height = int(rotated_rect.height * self.scale_y)
        if scaled_width > 0 and scaled_height > 0:
            scaled_image = pygame.transform.smoothscale(rotated_image, (scaled_width, scaled_height))
            scaled_rect = scaled_image.get_rect(center=self.rect.center)
            surface.blit(scaled_image, scaled_rect)
        else:
            surface.blit(self.original_image, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (0, 0, 255), self.hitbox, 1)
            pygame.draw.rect(surface, (0, 0, 255), self.rect, 1)

class Enemy:
    def __init__(self, x, y, move_type, speed=2, hitx=-5, hity=-5):
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

    def reset(self):
        self.x, self.y = float(self.start_pos[0]), float(self.start_pos[1])
        self.rect.topleft = self.start_pos
        self.hitbox.center = self.rect.center
        self.direction = 1

    def update(self, walls):
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
                self.direction *= -1
                break

    def draw(self, surface, debug_mode=False):
        pygame.draw.rect(surface, self.color, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (255, 255, 0), self.hitbox, 1)

def is_line_of_sight_clear(start_pos, end_pos, walls):
    for wall in walls:
        if wall.rect.clipline(start_pos, end_pos):
            return False
    return True

class SuperEnemy(Enemy):
    def __init__(self, x, y, move_type, speed=2, hitx=-5, hity=-5):
        super().__init__(x, y, move_type, speed, hitx, hity)
        self.color = (139, 0, 0)
        self.direction_look = 'right' if self.move_type == 'horizontal' else 'down'

    def update(self, walls):
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
                self.direction *= -1
                if self.move_type == 'horizontal':
                    self.direction_look = 'left' if self.direction == -1 else 'right'
                elif self.move_type == 'vertical':
                    self.direction_look = 'up' if self.direction == -1 else 'down'
                break

    def check_sight(self, player_rect, walls):
        enemy_pos = self.rect.center
        player_pos = player_rect.center
        sight_length = 2.5 * TILE_SIZE
        is_in_sight = False
        if self.direction_look == 'up' and enemy_pos[1] > player_pos[1] and abs(
                enemy_pos[0] - player_pos[0]) < TILE_SIZE and abs(enemy_pos[1] - player_pos[1]) <= sight_length:
            is_in_sight = True
        elif self.direction_look == 'down' and enemy_pos[1] < player_pos[1] and abs(
                enemy_pos[0] - player_pos[0]) < TILE_SIZE and abs(enemy_pos[1] - player_pos[1]) <= sight_length:
            is_in_sight = True
        elif self.direction_look == 'left' and enemy_pos[0] > player_pos[0] and abs(
                enemy_pos[1] - player_pos[1]) < TILE_SIZE and abs(enemy_pos[0] - player_pos[0]) <= sight_length:
            is_in_sight = True
        elif self.direction_look == 'right' and enemy_pos[0] < player_pos[0] and abs(
                enemy_pos[1] - player_pos[1]) < TILE_SIZE and abs(enemy_pos[0] - player_pos[0]) <= sight_length:
            is_in_sight = True
        if is_in_sight:
            return is_line_of_sight_clear(enemy_pos, player_pos, walls)
        return False

    def draw_sight(self, surface):
        sight_length = 2 * TILE_SIZE
        line_color = (255, 0, 0)
        start_pos = self.rect.center
        end_pos = start_pos
        if self.direction_look == 'up':
            end_pos = (self.rect.centerx, self.rect.centery - sight_length)
        elif self.direction_look == 'down':
            end_pos = (self.rect.centerx, self.rect.centery + sight_length)
        elif self.direction_look == 'left':
            end_pos = (self.rect.centerx - sight_length, self.rect.centery)
        elif self.direction_look == 'right':
            end_pos = (self.rect.centerx + sight_length, self.rect.centery)
        pygame.draw.line(surface, line_color, start_pos, end_pos, 3)

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
            return pygame.transform.scale(image, scale)
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
            "h": lambda x, y: Enemy(x, y, 'horizontal', speed=2),
            "v": lambda x, y: Enemy(x, y, 'vertical', speed=2),
            "f": lambda x, y: Enemy(x, y, 'horizontal', speed=4),
            "l": lambda x, y: Enemy(x, y, 'vertical', speed=4),
            "D": lambda x, y: Door(x, y),
            "s": lambda x, y: Slow(x, y),
            "S": lambda x, y: Slow(x, y, 20),
            "X": lambda x, y: Death(x, y),
            "$": lambda x, y: Coin(x, y),
            "@": lambda x, y: Reverse(x, y),
            "H": lambda x, y: SuperEnemy(x, y, 'horizontal', speed=2),
            "V": lambda x, y: SuperEnemy(x, y, 'vertical', speed=2),
            "F": lambda x, y: SuperEnemy(x, y, 'horizontal', speed=4),
            "L": lambda x, y: SuperEnemy(x, y, 'vertical', speed=4),
            "C": lambda x, y: Checkpoint(x, y)
        }
        self.class_map = {
            Wall: [], Door: [], Slow: [], Death: [], Reverse: [], Coin: [], Enemy: [], Checkpoint: []
        }

    def _load_json(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def load_level(self, level_name):
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

# --- Запуск игры ---

class Game:
    def __init__(self):
        pygame.init()

        pygame.font.init()
        self.font = pygame.font.Font(None, 36)

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
        self.current_level_index = 0

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
        self.assets.load_image("hero", "hero.png")

        self.player = Player(40, 40, self.assets)

    def load_current_level(self):
        """Загрузка уровня."""
        self.transforming_reverse_tiles.clear()
        self.active_checkpoint_pos = None

        for tile in self.reverse_tiles:
            tile.reset()
        for tile in self.transforming_reverse_tiles:
            tile.reset()

        if self.current_level_index < len(self.level_names):
            level_name = self.level_names[self.current_level_index]

            (self.walls, self.enemies, self.doors, self.player_spawn,
             self.current_background, self.death_tiles, self.slow_tiles,
             self.reverse_tiles, self.coins, self.checkpoint_tiles) = self.level_loader.load_level(level_name)

            if self.player_spawn:
                self.player.start_pos = self.player_spawn
            self.player.reset()
            return True
        else:
            print("Поздравляю! Вы прошли все уровни!")
            return False

    def run(self):
        """Главный игровой цикл."""
        if not self.load_current_level():
            return

        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(120)

        pygame.quit()

    def events(self):
        """Обработка пользовательского ввода."""

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
        """Обновление состояния всех игровых объектов."""
        self.elapsed_time = (pygame.time.get_ticks() - self.time) // 1000

        # --- Reverse Tile ---
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
        for tile in completed_transformations:
            if tile in self.transforming_reverse_tiles: self.transforming_reverse_tiles.remove(tile)
            if tile in self.reverse_tiles: self.reverse_tiles.remove(tile)
        # --------------------

        self.player.update()

        # --- Постановка точки возрождения ---
        for checkpoint in self.checkpoint_tiles:
            if self.player.hitbox.colliderect(checkpoint.rect) and not checkpoint.is_active:
                for cp in self.checkpoint_tiles:
                    cp.deactivate()
                checkpoint.activate()
                self.active_checkpoint_pos = checkpoint.rect.topleft
        #-------------------------------------

        # --- Логика врагов ---
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
        # --- Логика врагов ---

        # --- Slow Tile ---
        slow_tile_found = None
        for tile in self.slow_tiles:
            if self.player.hitbox.colliderect(tile.rect):
                slow_tile_found = tile
                break
        if slow_tile_found:
            self.player.speed = self.player.base_speed / slow_tile_found.speed
        else:
            self.player.speed = self.player.base_speed

        # --- Slow Tile ---

        # --- Door Tile ---
        for door in self.doors:
            if self.player.hitbox.colliderect(door.rect):
                self.current_level_index += 1
                running = self.load_current_level()
                if not running:
                    break
        # --- Door Tile ---

        # --- Логика возрождения ---
        if player_needs_reset:
            if self.active_checkpoint_pos:
                self.player.start_pos = self.active_checkpoint_pos
            elif self.player_spawn:
                self.player.start_pos = self.player_spawn

            self.player.reset()
            for enemy in self.enemies:
                enemy.reset()

            # Сброс Reverse клеток в изначальное состояние
            for reverse_tile in self.reverse_tiles:
                reverse_tile.reset()
            for transforming_tile in self.transforming_reverse_tiles:
                transforming_tile.reset()

            # Удаляем стены, которые были созданы из Reverse клеток
            self.walls = [wall for wall in self.walls if not hasattr(wall, 'was_reverse')]
        # --- Логика возрождения ---

        # --- Логика монет ---
        for coin in self.coins:
            if self.player.hitbox.colliderect(coin.hitbox) and not coin.is_collecting:
                coin.is_collecting = True
                self.score += coin.value
            coin.update()
        self.coins = [coin for coin in self.coins if coin.alpha > 0]
        # --- Логика монет ---

    def draw(self):
        """Отрисовка всего на экране."""

        if self.current_background:
            self.screen.blit(self.current_background, (0, 0))

        for tile in self.walls + self.reverse_tiles + self.transforming_reverse_tiles + self.coins + self.checkpoint_tiles:
            tile.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.player.draw(self.screen)

        if self.debug_mode:
            for tile in self.walls + self.slow_tiles + self.death_tiles + self.reverse_tiles + self.transforming_reverse_tiles + self.checkpoint_tiles:
                tile.debug_draw(self.screen)

            for enemy in self.enemies:
                if isinstance(enemy, SuperEnemy):
                    enemy.draw_sight(self.screen)

                enemy.draw(self.screen, True)

            self.player.draw(self.screen, True)

            for coin in self.coins:
                coin.draw(self.screen, True)

        timer_text = self.font.render(f"Время: {self.elapsed_time}", True, (255, 255, 255))
        score_text = self.font.render(f"Очки: {self.score}", True, (255, 255, 255))
        self.screen.blit(timer_text, (10, 10))
        self.screen.blit(score_text, (10, 50))

        pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
