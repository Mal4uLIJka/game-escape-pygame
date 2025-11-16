import pygame
from settings import TILE_SIZE
from assets import load_tile_image

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