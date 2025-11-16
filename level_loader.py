import pygame
import json

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

from tiles import Wall, Door, Slow, Death, Reverse, Coin, Checkpoint
from entities import Enemy, SuperEnemy


class LevelLoader:
    """
    Отвечает за загрузку и парсинг (разбор) данных уровня из JSON-файла.

    Этот класс читает файл `levels.json`, хранит его содержимое
    и умеет по имени уровня ("level_1", "level_2" и т.д.) создавать
    все необходимые игровые объекты (стены, враги, игрок)
    и фон.
    """

    def __init__(self, file_path):
        """
        Инициализирует загрузчик.

        Параметры:
            file_path (str): Путь к JSON-файлу с данными всех уровней.
        """
        self.file_path = file_path
        self.levels_data = self._load_json()

        # Используем lambda-функции, чтобы отложить создание объекта
        # до момента, когда у нас будут координаты (x, y).
        self.tile_map = {
            "#": lambda x, y: Wall(x, y),
            " ": None,
            "P": "player",  # 'player' - особый маркер, не класс
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

        # 'class_map' используется для быстрой сортировки созданных объектов
        # по их типам. Вместо 10 отдельных списков, мы используем один
        # словарь, где ключ - это класс, а значение - список объектов.
        self.class_map = {
            Wall: [], Door: [], Slow: [], Death: [], Reverse: [], Coin: [], Enemy: [], Checkpoint: []
        }

    def _load_json(self):
        """
        Внутренний метод. Загружает JSON-файл с диска.
        """
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def load_level(self, level_name, assets, is_menu_load=False):
        """
        Главный метод. Загружает и парсит конкретный уровень по его имени.

        Он читает матрицу ("matrix") уровня, создает все объекты
        и возвращает их, отсортированными по спискам.

        Параметры:
            level_name (str): Имя уровня (ключ в JSON-файле).
            assets (AssetManager): Ссылка на менеджер ассетов
                                   (нужен для врагов).
            is_menu_load (bool): Флаг для главного меню.
                                 Если True, загружается *только* фон.

        Возвращает:
            tuple: Кортеж со списками объектов и другими данными уровня.
            ИЛИ
            pygame.Surface: Если is_menu_load=True, возвращает только фон.
        """
        level_data = self.levels_data.get(level_name)
        if not level_data:
            raise ValueError(f"Уровень '{level_name}' не найден в JSON.")

        # --- 1. Загрузка фона ---
        current_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        current_background.fill(pygame.Color('darkgrey'))  # Фон по умолчанию
        try:
            background_image = pygame.image.load(level_data["background"]).convert()
            current_background = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error:
            print(f"Фон '{level_data['background']}' не найден. Используется серый цвет.")

        # Если это загрузка для меню, то объекты нам не нужны.
        if is_menu_load:
            return current_background

        # --- 2. Очистка списков от предыдущего уровня ---
        for obj_list in self.class_map.values():
            obj_list.clear()
        player_spawn = None

        # --- 3. Парсинг матрицы уровня ---
        level_matrix = level_data["matrix"]
        for y, row in enumerate(level_matrix):  # y - номер строки
            for x, cell in enumerate(row):  # x - номер столбца, cell - символ
                pos_x, pos_y = x * TILE_SIZE, y * TILE_SIZE

                tile_type = self.tile_map.get(cell)

                if tile_type is None:
                    continue  # Это пустая клетка " "

                elif tile_type == "player":
                    player_spawn = (pos_x, pos_y)

                else:
                    # Создаем объект
                    obj = None
                    if cell in ["h", "v", "f", "l", "H", "V", "F", "L"]:
                        # Врагам нужны ассеты
                        obj = tile_type(pos_x, pos_y, assets)
                    else:
                        # Обычным тайлам - нет
                        obj = tile_type(pos_x, pos_y)

                        # Сортируем созданный объект в 'class_map'
                    for cls, obj_list in self.class_map.items():
                        if isinstance(obj, cls):
                            obj_list.append(obj)
                            break

        # --- 4. Возврат всех данных ---
        # Возвращаем кортеж со всеми списками и данными
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