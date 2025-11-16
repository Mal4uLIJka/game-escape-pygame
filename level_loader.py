import pygame
import json

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

from tiles import Wall, Door, Slow, Death, Reverse, Coin, Checkpoint
from entities import Enemy, SuperEnemy

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