import pygame
from settings import TILE_SIZE

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