import pygame
from settings import TILE_SIZE


class AssetManager:
    """
    Хранит все загруженные ресурсы (картинки, звуки) в одном месте,
    чтобы не загружать их с диска каждый раз.
    Доступ к ресурсам происходит по имени (ключу).
    """

    def __init__(self):
        self.images = {}  # Словарь для { "имя_картинки": pygame.Surface }
        self.sounds = {}  # Словарь для { "имя_звука": pygame.mixer.Sound }

    def load_image(self, name, path):
        """
        Загружает картинку из файла `path` и сохраняет ее
        в `self.images` под ключом `name`.
        """
        try:
            image = pygame.image.load(path).convert_alpha()
            self.images[name] = image
        except pygame.error:
            print(f"Не удалось загрузить изображение: {path}")
            self.images[name] = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.images[name].fill((255, 0, 255))

    def get_image(self, name, scale=None):
        """
        Получает картинку по имени `name`.
        Если указан `scale` (размер, например (40, 40)),
        картинка будет отмасштабирована.
        """
        image = self.images.get(name)
        if image and scale:
            # smoothscale - качественное масштабирование
            return pygame.transform.smoothscale(image, scale)
        return image

    def load_sound(self, name, path):
        """
        Загружает звук из файла `path` и сохраняет его
        в `self.sounds` под ключом `name`.
        """
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except pygame.error:
            print(f"Не удалось загрузить звук: {path}")

    def get_sound(self, name):
        """Получает звук по имени `name`."""
        return self.sounds.get(name)


def load_tile_image(path, size=(TILE_SIZE, TILE_SIZE)):
    """
    Отдельная функция для загрузки ТЕКСТУР ТАЙЛОВ.
    Она не кэширует картинку в менеджере, а просто загружает,
    масштабирует до размера `size` и возвращает ее.

    Используется в классах тайлов (Wall, Coin и т.д.).
    """
    if not path:
        return None
    try:
        image = pygame.image.load(path).convert_alpha()
        # scale - обычное (быстрое) масштабирование
        return pygame.transform.scale(image, size)
    except pygame.error:
        print(f"Текстура '{path}' не найдена.")
        return None