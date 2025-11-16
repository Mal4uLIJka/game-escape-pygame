import pygame
from settings import TILE_SIZE
from assets import load_tile_image


class Tile:
    """
    Базовый класс для всех "плиток" на уровне.
    Это "кирпичик", от которого наследуются все остальные:
    стены, двери, монеты и т.д.

    Он просто хранит свое положение и размер (rect).
    """

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def draw(self, surface):
        """По умолчанию тайл невидимый."""
        pass

    def debug_draw(self, surface, color=(255, 0, 0, 128)):
        """
        Рисует полупрозрачный квадрат.
        Используется только в режиме отладки (V),
        чтобы видеть невидимые тайлы (смерть, замедление).
        """
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill(color)
        surface.blit(s, self.rect.topleft)


class Wall(Tile):
    """Стена. Твердый объект, блокирующий движение."""

    def __init__(self, x, y, texture=None):
        super().__init__(x, y)
        self.texture = texture
        self.image = load_tile_image(self.texture)
        self.was_reverse = False  # Флаг, чтобы знать, была ли эта стена раньше 'Reverse' тайлом

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect.topleft)

    def debug_draw(self, surface):
        super().debug_draw(surface)


class Door(Tile):
    """Дверь. Переход на следующий уровень."""

    def __init__(self, x, y):
        super().__init__(x, y)
        # Рисуем полупрозрачный желтый квадрат
        self.s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.s.fill((255, 255, 0, 128))

    def draw(self, surface):
        surface.blit(self.s, self.rect.topleft)


class Slow(Tile):
    """Зона замедления. Невидимый тайл, который замедляет игрока."""

    def __init__(self, x, y, speed=2):
        super().__init__(x, y)
        self.speed = speed  # Во сколько раз замедлить

    def draw(self, surface):
        """Невидимый в обычной игре."""
        pass

    def debug_draw(self, surface):
        # В режиме отладки - зеленый
        super().debug_draw(surface, color=(0, 255, 0, 128))


class Death(Tile):
    """Зона смерти. Невидимый тайл, который убивает игрока."""

    def __init__(self, x, y):
        super().__init__(x, y)

    def draw(self, surface):
        """Невидимый в обычной игре."""
        pass

    def debug_draw(self, surface):
        # В режиме отладки - синий
        super().debug_draw(surface, color=(0, 0, 255, 128))


class Reverse(Tile):
    """
    "Обратный" тайл (ловушка).
    Игрок может по нему ходить. Но как только он с него уходит,
    тайл начинает превращаться в стену.
    """

    def __init__(self, x, y, wall_texture="./images/reverse_tile.png", base_texture="./images/reverse_tile_on.png"):
        super().__init__(x, y)
        self.wall_texture = wall_texture  # Текстура, когда он станет стеной
        self.base_texture = base_texture  # Текстура, пока он "включен"
        self.is_transforming = False  # Флаг: идет ли процесс превращения?
        self.transform_timer = 0  # Таймер анимации
        self.transform_duration = 20  # Сколько кадров длится превращение
        self.alpha = 255  # Прозрачность для анимации
        self.fade_speed = 255 // self.transform_duration

        self.wall_image = load_tile_image(self.wall_texture)
        self.base_image = load_tile_image(self.base_texture)

    def start_transformation(self):
        """Запускает процесс превращения в стену."""
        self.is_transforming = True
        self.transform_timer = 0
        self.alpha = 255

    def reset(self):
        """Сброс состояния (не используется в коде, но полезно)."""
        self.is_transforming = False
        self.transform_timer = 0
        self.alpha = 255

    def update(self):
        """
        Вызывается каждый кадр.
        Если идет трансформация, обновляет таймер и прозрачность.
        Когда таймер доходит до конца, "возвращает" новый объект Стены.
        """
        if self.is_transforming:
            self.transform_timer += 1
            self.alpha = max(0, 255 - (self.transform_timer * self.fade_speed))

            if self.transform_timer >= self.transform_duration:
                # Превращение завершено!
                self.is_transforming = False
                # Создаем и возвращаем новый объект Стены на этом же месте
                new_wall = Wall(self.rect.x, self.rect.y, self.wall_texture)
                new_wall.was_reverse = True  # Помечаем, что это бывший 'Reverse'
                return new_wall
        return None  # Если трансформация не закончена, ничего не возвращаем

    def draw(self, surface):
        """Рисует тайл в зависимости от его состояния."""
        if self.is_transforming:
            # Анимация "перекрестного затухания"
            # 1. Рисуем "стену", которая плавно появляется
            if self.wall_image:
                wall_surface = self.wall_image.copy()
                wall_alpha = 255 - self.alpha  # Прозрачность от 0 до 255
                wall_surface.fill((255, 255, 255, wall_alpha), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(wall_surface, self.rect.topleft)
            # 2. Рисуем "базу", которая плавно исчезает
            if self.base_image:
                base_surface = self.base_image.copy()
                base_surface.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(base_surface, self.rect.topleft)
        else:
            # Если не трансформируется, просто рисуем "базу"
            if self.base_image:
                surface.blit(self.base_image, self.rect.topleft)

    def debug_draw(self, surface):
        color = (0, 255, 255, 255) if self.is_transforming else (0, 255, 255, 128)
        super().debug_draw(surface, color=color)


class Coin(Tile):
    """Монетка. Собираемый предмет, дающий очки."""

    def __init__(self, x, y, value=100, texture_path="./images/coin.png"):
        super().__init__(x, y)
        self.value = value  # Сколько очков дает
        self.is_collecting = False  # Флаг: началась ли анимация сбора?
        self.alpha = 255  # Прозрачность для анимации
        self.fade_speed = 15  # Скорость исчезания

        # Хитбокс меньше, чем тайл, чтобы было удобнее собирать
        self.hitbox = self.rect.inflate(-20, -20)
        self.hitbox.center = self.rect.center

        self.image = load_tile_image(texture_path)

    def draw(self, surface, debug_mode=False):
        if self.alpha > 0:
            if self.image:
                # Рисуем картинку с учетом текущей прозрачности
                temp_image = self.image.copy()
                temp_image.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(temp_image, self.rect.topleft)

        if debug_mode:
            pygame.draw.rect(surface, (0, 0, 255), self.hitbox, 1)

    def update(self):
        """Если монетку 'собирают', она плавно исчезает."""
        if self.is_collecting:
            self.alpha = max(0, self.alpha - self.fade_speed)
            self.hitbox.center = self.rect.center


class Checkpoint(Tile):
    """Чекпоинт. Сохраняет место возрождения игрока."""

    def __init__(self, x, y, checkoff="./images/checkpoint_off.png", checkon="./images/checkpoint_on.png"):
        super().__init__(x, y)
        self.checkoff_path = checkoff  # Текстура выключенного
        self.checkon_path = checkon  # Текстура включенного
        self.is_active = False  # Активен ли этот чекпоинт?

        self.image_off = load_tile_image(self.checkoff_path)
        self.image_on = load_tile_image(self.checkon_path)

    def draw(self, surface):
        """Рисует нужную текстуру в зависимости от состояния."""
        if self.is_active:
            if self.image_on:
                surface.blit(self.image_on, self.rect.topleft)
        else:
            if self.image_off:
                surface.blit(self.image_off, self.rect.topleft)

    def debug_draw(self, surface):
        color = (100, 255, 100, 255) if self.is_active else (100, 100, 255, 128)
        super().debug_draw(surface, color=color)

    def activate(self):
        """Включает чекпоинт."""
        self.is_active = True

    def deactivate(self):
        """Выключает чекпоинт."""
        self.is_active = False