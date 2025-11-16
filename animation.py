import pygame
import random
import math


class AnimationController:
    """
    Управляет процедурной анимацией объекта (игрока, врага).

    Создает эффекты "сжатия/растяжения" (squash & stretch) и
    "наклона/качания" (tilt & wobble) при движении.

    Идея в том, что мы не меняем параметры (масштаб, угол) напрямую,
    а задаем *целевые* (target) значения. А метод `update`
    плавно "догоняет" текущие значения до целевых.
    Это создает плавную, органическую анимацию.
    """

    def __init__(self, squash_factor=0.04, tilt_factor=15, anim_speed=2):
        # --- Параметры для Наклона (Tilt) ---
        self.current_tilt = 0.0  # Текущий угол наклона в градусах
        self.target_tilt = 0.0  # Целевой угол (база для качания)

        # --- Параметры для Масштаба (Squash/Stretch) ---
        self.scale_x = 1.0  # Текущий масштаб по X (1.0 = 100%)
        self.scale_y = 1.0  # Текущий масштаб по Y
        self.target_scale_x = 1.0  # Целевой масштаб по X
        self.target_scale_y = 1.0  # Целевой масштаб по Y

        # --- Конфигурация анимации ---
        self.squash_factor = squash_factor  # Насколько сильно сжиматься (0.04 = 4%)
        self.tilt_factor = tilt_factor  # Насколько сильно наклоняться (15 градусов)
        self.anim_speed = anim_speed  # Общая скорость анимаций

        # --- Состояние для "Качания" (Wobble) ---
        self.wobble_timer = 0.0  # Внутренний таймер для синусоиды
        self.is_moving = False  # Двигается ли объект сейчас?

    def update(self, dt):
        """
        Главный метод, обновляет всю анимацию. Вызывается каждый кадр.
        dt (delta time) - время, прошедшее с прошлого кадра.
        """

        # 1. Плавное "приближение" к целевому масштабу (Лерп / Lerp)
        #    Это создает эффект "пружинки" при сжатии/растяжении.
        #    (target - current) * strength * dt
        lerp_strength = 20  # Насколько "резко" происходит анимация
        self.scale_x += (self.target_scale_x - self.scale_x) * lerp_strength * dt
        self.scale_y += (self.target_scale_y - self.scale_y) * lerp_strength * dt

        # 2. Обновление "Качания" (Wobble)
        if self.is_moving:
            # Если мы двигаемся, таймер "качания" тикает
            wobble_speed_per_second = 6 * self.anim_speed
            self.wobble_timer += wobble_speed_per_second * dt

            self.current_tilt = self.target_tilt * math.sin(self.wobble_timer)
        else:
            self.wobble_timer = 0.0
            self.current_tilt += (0.0 - self.current_tilt) * 10 * dt

    def set_squash_stretch(self, direction):
        """
        Задает *целевой* масштаб при начале движения.
        Добавляет немного случайности, чтобы не выглядело одинаково.
        """
        squash = self.squash_factor * random.uniform(0.9, 1.1)

        if direction == "left" or direction == "right":
            # Движемся по горизонтали:
            # Сжимаемся по Y (ниже), растягиваемся по X (шире)
            self.target_scale_x = 1.0 + squash
            self.target_scale_y = 1.0 - squash
        elif direction == "up" or direction == "down":
            # Движемся по вертикали:
            # Сжимаемся по X (уже), растягиваемся по Y (выше)
            self.target_scale_x = 1.0 - squash
            self.target_scale_y = 1.0 + squash

    def set_tilt(self, direction):
        """
        Задает *целевой* (базовый) наклон при начале движения.
        """
        self.is_moving = True
        tilt = self.tilt_factor * random.uniform(0.9, 1.1)

        # Наклоняемся "по ходу движения"
        if direction == "left":
            self.target_tilt = -tilt
        elif direction == "right":
            self.target_tilt = tilt
        elif direction == "up":
            self.target_tilt = -tilt
        elif direction == "down":
            self.target_tilt = tilt

    def reset_animation(self):
        """
        "Мягкий" сброс анимации (когда движение закончилось).
        Плавно возвращает объект в состояние покоя (масштаб 1.0, наклон 0).
        """
        self.is_moving = False
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        self.target_tilt = 0.0

    def force_reset_animation(self):
        """
        "Жесткий" сброс. Мгновенно ставит объект в
        состояние покоя. Используется при респавне/смерти.
        """
        self.is_moving = False
        self.current_tilt = 0.0
        self.target_tilt = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0

    def draw_animated(self, surface, original_image, rect):
        """
        Главный метод отрисовки.
        Применяет все трансформации и рисует на экране.
        """
        if not original_image:
            return

        # 1. Рассчитываем новый размер на основе текущего масштаба
        scaled_width = int(rect.width * self.scale_x)
        scaled_height = int(rect.height * self.scale_y)

        # Защита от ошибки, если масштаб стал 0 или отрицательным
        if scaled_width <= 0 or scaled_height <= 0:
            if original_image:
                surface.blit(original_image, rect)
            return

        # 2. Создаем новую картинку (Surface) с этим размером
        scaled_image = pygame.transform.smoothscale(original_image, (scaled_width, scaled_height))

        # 3. Вращаем *уже смасштабированную* картинку
        rotated_image = pygame.transform.rotate(scaled_image, self.current_tilt)

        # 4. ВАЖНЫЙ ШАГ:
        #    При вращении у картинки меняется размер.
        #    Мы должны получить новый 'rect' для повернутой картинки,
        #    но с тем же *центром*, что и у оригинального 'rect'.
        #    Это гарантирует, что объект вращается "на месте".
        rotated_rect = rotated_image.get_rect(center=rect.center)

        # 5. Рисуем повернутую и смасштабированную картинку
        surface.blit(rotated_image, rotated_rect)