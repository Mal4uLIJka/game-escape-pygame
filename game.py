import pygame

from settings import *
from assets import AssetManager
from level_loader import LevelLoader
from entities import Player, SuperEnemy
from ui import MenuManager

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

        self.debug_start_level = 0

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Игра-побег")
        pygame.display.set_icon(pygame.image.load("images/super_angry_enemy.png"))

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
            self.elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000 + self.time_penalty

            self.in_game_update(dt)
        else:
            self.menu_manager.update(mouse_pos, self.game_state)

    def draw(self):
        if self.game_state == "in_game":
            self.in_game_draw()
        else:
            self.menu_manager.draw(self.screen, self.game_state)

        if self.game_state == "in_game":
            self.menu_manager.draw_text_with_outline(self.screen, f"Очки: {self.score}  Время: {self.elapsed_time}c" + (" Godmode: True" if self.player.godmode else ""),
                                                     self.font_small, WHITE,
                                                     (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12), center_bottom=True)

        pygame.display.flip()

    def in_game_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                self.player.godmode = not self.player.godmode

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

    def in_game_update(self, dt):
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

        if self.player.godmode:
            player_needs_reset = False

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
