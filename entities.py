import pygame
import math

from settings import TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT
from animation import AnimationController


class Player:
    """
    Класс игрока. Отвечает за логику движения, анимацию
    и взаимодействие с миром.
    """

    def __init__(self, x, y, assets, base_speed=600):
        self.start_pos = (x, y)  # Начальная позиция (для респавна)
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hitbox = self.rect.copy()
        self.hitbox.inflate_ip(-15, -15)  # Уменьшенный хитбокс
        self.base_speed = base_speed
        self.speed = float(base_speed)
        self.direction = None  # Текущее направление (left, right, ...)
        self.is_moving = False  # Двигается ли сейчас?
        self.held_keys = set()  # Какие клавиши зажаты (для буферизации)
        self.next_direction = None  # Какое движение выполнить следующим
        self.reverse_tiles_underneath = []  # 'Reverse' тайлы, на которых стоит
        self.target_x = None  # Целевая координата X
        self.target_y = None  # Целевая координата Y
        self.anim_controller = AnimationController(squash_factor=0.04, tilt_factor=15)
        self.visible = True
        self.godmode = False  # Режим бессмертия

        try:
            self.original_image = assets.get_image("hero", scale=(TILE_SIZE, TILE_SIZE))
        except pygame.error:
            self.original_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.original_image.fill((0, 200, 0))
            print("Используется стандартный квадрат.")

    def start_move(self, direction, walls, transforming_tiles):
        """
        Начинает движение в указанном направлении до ближайшей стены.
        Это "пошаговое" (grid-based) движение.
        """
        if self.is_moving:
            return
        self.direction = direction

        # --- Сложная логика "броска луча" (Raycasting) ---
        # 1. Получаем текущую "сеточную" позицию
        current_grid_x = self.rect.x // TILE_SIZE
        current_grid_y = self.rect.y // TILE_SIZE

        # 2. Собираем "карту" всех препятствий
        obstacle_coords = {(w.rect.x // TILE_SIZE, w.rect.y // TILE_SIZE) for w in walls}
        transforming_coords = {(t.rect.x // TILE_SIZE, t.rect.y // TILE_SIZE) for t in transforming_tiles}
        obstacle_coords.update(transforming_coords)  # Добавляем ловушки-стены

        # 3. "Бросаем луч" (проверяем клетки) от игрока до края экрана
        target_grid_x, target_grid_y = current_grid_x, current_grid_y
        if direction == "left":
            # Идем влево от игрока (x-1) до края (-1)
            for x in range(current_grid_x - 1, -1, -1):
                if (x, current_grid_y) in obstacle_coords:
                    break  # Нашли стену, останавливаемся
                target_grid_x = x  # Клетка пустая, можно идти
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
        # --- Конец логики "броска луча" ---

        # Если не сдвинулись (уперлись в стену), выходим
        if target_grid_x == current_grid_x and target_grid_y == current_grid_y:
            return

        # 4. Запоминаем целевую *пиксельную* позицию
        self.target_x = float(target_grid_x * TILE_SIZE)
        self.target_y = float(target_grid_y * TILE_SIZE)
        self.is_moving = True

        # Запускаем анимации
        self.anim_controller.set_squash_stretch(direction)
        self.anim_controller.set_tilt(direction)

    def update(self, dt):
        """
        Обновляет позицию игрока (если он в движении) и анимации.
        """
        self.anim_controller.update(dt)  # Обновляем "сочность"

        if not self.is_moving:
            self.anim_controller.reset_animation()
            return  # Если не двигаемся, ничего не делаем

        # --- Логика движения к цели ---
        # `dt` (delta time) - время кадра.
        # Умножение на `dt` делает скорость независимой от FPS.
        move_distance = self.speed * dt

        if self.direction == "left":
            # Двигаемся влево, но не дальше, чем `target_x`
            self.x = max(self.target_x, self.x - move_distance)
        elif self.direction == "right":
            # Двигаемся вправо, но не дальше, чем `target_x`
            self.x = min(self.target_x, self.x + move_distance)
        elif self.direction == "up":
            self.y = max(self.target_y, self.y - move_distance)
        elif self.direction == "down":
            self.y = min(self.target_y, self.y + move_distance)

        self.rect.x = int(round(self.x))
        self.rect.y = int(round(self.y))
        self.hitbox.center = self.rect.center

        # --- Проверка достижения цели ---
        if self.rect.x == self.target_x and self.rect.y == self.target_y:
            # "Прилипаем" к точной позиции
            self.x = float(self.target_x)
            self.y = float(self.target_y)
            # Завершаем движение
            self.is_moving = False
            self.direction = None
            self.target_x = None
            self.target_y = None

    def reset(self):
        """Сбрасывает игрока в начальную позицию (при смерти/рестарте)."""
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
        """Рисует игрока."""
        if not self.visible:
            return

        # Используем контроллер анимаций для "сочной" отрисовки
        self.anim_controller.draw_animated(surface, self.original_image, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (0, 0, 255), self.hitbox, 1)
            pygame.draw.rect(surface, (0, 0, 255), self.rect, 1)


class Enemy:
    """
    Базовый класс для врагов. Двигается туда-сюда.
    """

    def __init__(self, x, y, move_type, assets, speed=240, hitx=-5, hity=-5):
        self.start_pos = (x, y)
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hitbox = self.rect.copy()
        self.hitbox.inflate_ip(hitx, hity)
        self.move_type = move_type  # 'horizontal' или 'vertical'
        self.speed = float(speed)
        self.direction = 1  # 1 = вправо/вниз, -1 = влево/вверх
        self.color = (255, 0, 0) if speed > 240 else (180, 50, 50)
        self.anim_controller = AnimationController(squash_factor=0.02, tilt_factor=5, anim_speed=1 + (speed / 240))

        self.is_paused = False  # Пауза при столкновении со стеной
        self.pause_timer = 0
        self.pause_duration = 30  # Длительность паузы в кадрах

        self.original_image = None
        # Загрузка текстуры в зависимости от скорости
        texture_name = ""
        if speed == 240:
            texture_name = "enemy_slow"
        elif speed == 480:
            texture_name = "enemy_fast"

        if texture_name and assets:
            self.original_image = assets.get_image(texture_name, scale=(TILE_SIZE, TILE_SIZE))

        if not self.original_image:
            self.original_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.original_image.fill(self.color)

    def reset(self):
        """Сброс в начальную позицию (при перезагрузке уровня)."""
        self.x, self.y = float(self.start_pos[0]), float(self.start_pos[1])
        self.rect.topleft = self.start_pos
        self.hitbox.center = self.rect.center
        self.direction = 1
        self.anim_controller.force_reset_animation()
        self.is_paused = False
        self.pause_timer = 0

    def update(self, walls, dt):
        """Обновляет позицию врага и обрабатывает столкновения."""

        # --- Логика паузы у стены ---
        if self.is_paused:
            self.pause_timer -= 1
            if self.pause_timer <= 0:
                self.is_paused = False
                self.direction *= -1  # Меняем направление
                self._on_direction_change()  # Хук для SuperEnemy

            self.anim_controller.reset_animation()
            self.anim_controller.update(dt)
            return  # Выходим, если на паузе
        # --- Конец логики паузы ---

        # Запускаем анимации движения
        move_direction = None
        if self.move_type == 'horizontal':
            move_direction = "right" if self.direction == 1 else "left"
        elif self.move_type == 'vertical':
            move_direction = "down" if self.direction == 1 else "up"
        if move_direction:
            self.anim_controller.set_squash_stretch(move_direction)
            self.anim_controller.set_tilt(move_direction)

        # Двигаем врага
        move_distance = self.speed * self.direction * dt
        if self.move_type == 'horizontal':
            self.x += move_distance
        elif self.move_type == 'vertical':
            self.y += move_distance

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.hitbox.center = self.rect.center

        # --- Логика столкновения со стенами ---
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                # Если столкнулись, "отталкиваемся" от стены
                if self.move_type == 'horizontal':
                    if self.direction == 1:  # Шли вправо
                        self.rect.right = wall.rect.left
                    else:  # Шли влево
                        self.rect.left = wall.rect.right
                    self.x = float(self.rect.x)
                elif self.move_type == 'vertical':
                    if self.direction == 1:  # Шли вниз
                        self.rect.bottom = wall.rect.top
                    else:  # Шли вверх
                        self.rect.top = wall.rect.bottom
                    self.y = float(self.rect.y)

                self.hitbox.center = self.rect.center
                self.is_paused = True  # Включаем паузу
                self.pause_timer = self.pause_duration
                break  # Выходим из цикла (хватит одной стены)

        self.anim_controller.update(dt)

    def draw(self, surface, debug_mode=False):
        """Рисует врага."""
        self.anim_controller.draw_animated(surface, self.original_image, self.rect)
        if debug_mode:
            pygame.draw.rect(surface, (255, 255, 0), self.hitbox, 1)

    def _on_direction_change(self):
        """Метод-заглушка. Будет переопределен в SuperEnemy."""
        pass


def is_line_of_sight_clear(start_pos, end_pos, walls):
    """
    Вспомогательная функция.
    Проверяет, есть ли стены на линии между двумя точками.
    """
    for wall in walls:
        # clipline - встроенная в pygame функция
        # Она проверяет, пересекает ли линия (start, end) прямоугольник (wall.rect)
        if wall.rect.clipline(start_pos, end_pos):
            return False  # Пересекает, линии 'не чистая'
    return True  # Ничто не пересекло, 'чистая'


class SuperEnemy(Enemy):
    """
    Улучшенный враг. Умеет "видеть" игрока в конусе обзора.
    """

    def __init__(self, x, y, move_type, assets, speed=240, hitx=-5, hity=-5):
        super().__init__(x, y, move_type, assets, speed, hitx, hity)
        # Направление взгляда (меняется при развороте)
        self.direction_look = 'right' if self.move_type == 'horizontal' else 'down'

        self.sight_length = 2.5 * TILE_SIZE  # Дальность (в пикселях)
        self.sight_angle = 10  # Угол (в градусах) в *каждую* сторону (общий 20)
        self.sight_color = (255, 0, 0, 70)  # Цвет конуса

        # Загрузка уникальной текстуры "супер" врага
        self.original_image = None
        texture_name = "enemy_super"
        if assets:
            self.original_image = assets.get_image(texture_name, scale=(TILE_SIZE, TILE_SIZE))
        if not self.original_image:
            self.original_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.original_image.fill(self.color)

    def _on_direction_change(self):
        """
        Переопределяем метод. Когда враг меняет направление движения,
        он также меняет направление взгляда.
        """
        if self.move_type == 'horizontal':
            self.direction_look = 'left' if self.direction == -1 else 'right'
        elif self.move_type == 'vertical':
            self.direction_look = 'up' if self.direction == -1 else 'down'

    def _cast_ray(self, start_pos, angle_rad, length, walls):
        """
        Внутренний метод. Бросает один луч из конуса обзора.
        Находит *ближайшую* стену на пути луча.
        """
        # 1. Считаем конечную точку луча (если бы не было стен)
        end_x = start_pos[0] + math.cos(angle_rad) * length
        end_y = start_pos[1] - math.sin(angle_rad) * length  # (Y-ось в pygame инвертирована)
        end_pos = (end_x, end_y)

        closest_end_pos = end_pos  # По умолчанию луч дошел до конца
        min_dist_sq = length * length  # Квадрат дист. (быстрее, чем корень)

        # 2. Проверяем *каждую* стену
        for wall in walls:
            clipped_line = wall.rect.clipline(start_pos, end_pos)
            if clipped_line:
                # Луч попал в стену!
                hit_point = clipped_line[0]  # Точка попадания
                # Считаем дист. до этой стены
                dist_sq = (hit_point[0] - start_pos[0]) ** 2 + (hit_point[1] - start_pos[1]) ** 2
                if dist_sq < min_dist_sq:
                    # Эта стена БЛИЖЕ, чем предыдущая
                    min_dist_sq = dist_sq
                    closest_end_pos = hit_point
        return closest_end_pos  # Возвращаем точку (либо конец луча, либо стену)

    def check_sight(self, player_rect, walls):
        """
        Проверяет, видит ли враг игрока.
        """
        player_pos = player_rect.center
        enemy_pos = self.rect.center

        # --- 1. Простая проверка дистанции ---
        vec_x = player_pos[0] - enemy_pos[0]
        vec_y = player_pos[1] - enemy_pos[1]
        dist_sq = vec_x ** 2 + vec_y ** 2  # Квадрат расстояния
        if dist_sq > self.sight_length ** 2:
            return False  # Игрок слишком далеко

        if dist_sq == 0: return True  # Игрок в той же точке

        # --- 2. Проверка угла (в конусе?) ---
        # Угол от врага к игроку (в радианах)
        angle_to_player_rad = math.atan2(-vec_y, vec_x)

        # Базовый угол, куда смотрит враг
        if self.direction_look == 'up':
            base_angle_rad = math.radians(90)
        elif self.direction_look == 'down':
            base_angle_rad = math.radians(-90)
        elif self.direction_look == 'left':
            base_angle_rad = math.radians(180)
        else:  # 'right'
            base_angle_rad = math.radians(0)

        # Считаем разницу углов
        angle_diff = (angle_to_player_rad - base_angle_rad)
        # Нормализуем угол (приводим к диапазону от -PI до +PI)
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        # Если угол > разрешенного, игрок вне конуса
        if abs(angle_diff) > math.radians(self.sight_angle):
            return False

        # --- 3. Проверка преград (есть ли стена?) ---
        # Если игрок близко и в конусе, проверяем линию видимости
        return is_line_of_sight_clear(enemy_pos, player_pos, walls)

    def draw_sight(self, surface, walls):
        """
        Рисует конус обзора (используется в game.py).
        """
        start_pos = self.rect.center

        # 1. Определяем базовый угол (куда смотрим)
        if self.direction_look == 'up':
            base_angle_rad = math.radians(90)
        elif self.direction_look == 'down':
            base_angle_rad = math.radians(-90)
        elif self.direction_look == 'left':
            base_angle_rad = math.radians(180)
        else:  # 'right'
            base_angle_rad = math.radians(0)

        # 2. Определяем левую и правую границы конуса
        angle_left_rad = base_angle_rad + math.radians(self.sight_angle)
        angle_right_rad = base_angle_rad - math.radians(self.sight_angle)

        # 3. Бросаем N лучей, чтобы построить полигон
        points = [start_pos]  # Начинаем с врага
        num_rays = 10  # (Больше лучей = красивее, но медленнее)
        for i in range(num_rays + 1):
            lerp_factor = i / num_rays  # (От 0.0 до 1.0)
            # Берем угол между правым и левым
            current_angle_rad = angle_right_rad + (angle_left_rad - angle_right_rad) * lerp_factor
            # Бросаем луч
            end_point = self._cast_ray(start_pos, current_angle_rad, self.sight_length, walls)
            points.append(end_point)
        points.append(start_pos)  # Замыкаем полигон

        # 4. Рисуем полигон на отдельной (прозрачной) поверхности
        if len(points) > 2:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, self.sight_color, points)
            surface.blit(s, (0, 0))