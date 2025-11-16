import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, GREY, RED, HOVER_COLOR)

class Button:
    def __init__(self, x, y, width, height, text, font, callback, subtext_font=None, subtext=None, disabled=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.subtext = subtext
        self.subtext_font = subtext_font
        self.disabled = disabled
        self.hovered = False

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered and not self.disabled:
            self.callback()
            return True
        return False

    def draw(self, surface):
        color = GREY if self.disabled else (HOVER_COLOR if self.hovered else WHITE)

        main_surf = self.font.render(self.text, True, color)
        main_rect = main_surf.get_rect(center=self.rect.center)

        main_surf_outline = self.font.render(self.text, True, BLACK)

        offset = 2
        surface.blit(main_surf_outline, (main_rect.x - offset, main_rect.y))
        surface.blit(main_surf_outline, (main_rect.x + offset, main_rect.y))
        surface.blit(main_surf_outline, (main_rect.x, main_rect.y - offset))
        surface.blit(main_surf_outline, (main_rect.x, main_rect.y + offset))
        surface.blit(main_surf, main_rect)

        if self.subtext:
            sub_color = GREY if self.disabled else WHITE
            sub_surf = self.subtext_font.render(self.subtext, True, sub_color)
            sub_rect = sub_surf.get_rect(centerx=self.rect.centerx, top=self.rect.bottom + 5)

            sub_surf_outline = self.subtext_font.render(self.subtext, True, BLACK)

            surface.blit(sub_surf_outline, (sub_rect.x - offset, sub_rect.y))
            surface.blit(sub_surf_outline, (sub_rect.x + offset, sub_rect.y))
            surface.blit(sub_surf_outline, (sub_rect.x, sub_rect.y - offset))
            surface.blit(sub_surf_outline, (sub_rect.x, sub_rect.y + offset))
            surface.blit(sub_surf, sub_rect)

class MenuManager:
    def __init__(self, game):
        self.game = game
        self.font_small = game.font_small
        self.font_medium = game.font_medium
        self.font_large = game.font_large
        self.overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.win_animation_timer = 0
        self.win_animation_duration = 120

        self.main_menu_buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 350, 200, 50, "Начать", self.font_medium, self.game.start_game),
            Button(SCREEN_WIDTH // 2 - 100, 420, 200, 50, "Выйти", self.font_medium, self.game.quit_game)
        ]

        self.death_menu_buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 350, 300, 50, "Продолжить с чекпоинта", self.font_medium,
                   self.game.continue_from_checkpoint, self.font_small, "(-100 Очков, +5c Времени)"),
            Button(SCREEN_WIDTH // 2 - 150, 440, 300, 50, "Начать с нуля", self.font_medium, self.game.start_game)
        ]

        self.win_menu_buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 400, 200, 50, "Начать с нуля", self.font_medium, self.game.start_game),
            Button(SCREEN_WIDTH // 2 - 100, 470, 200, 50, "Выйти", self.font_medium, self.game.quit_game)
        ]

    def handle_event(self, event, game_state):
        button_list = []
        if game_state == "main_menu":
            button_list = self.main_menu_buttons
        elif game_state == "death_screen":
            button_list = self.death_menu_buttons
        elif game_state == "win_screen":
            if self.win_animation_timer >= self.win_animation_duration:
                button_list = self.win_menu_buttons

        for button in button_list:
            button.handle_event(event)

    def update(self, mouse_pos, game_state):
        button_list = []
        if game_state == "main_menu":
            button_list = self.main_menu_buttons
        elif game_state == "death_screen":
            is_first_level = self.game.current_level_index == 0
            no_checkpoint = self.game.active_checkpoint_pos is None
            self.death_menu_buttons[0].disabled = is_first_level and no_checkpoint
            button_list = self.death_menu_buttons
        elif game_state == "win_screen":
            if self.win_animation_timer < self.win_animation_duration:
                self.win_animation_timer += 1
                if self.win_animation_timer > 60:
                    self.game.player.visible = False
            else:
                button_list = self.win_menu_buttons

        for button in button_list:
            button.check_hover(mouse_pos)

    def draw(self, surface, game_state):
        if game_state == "main_menu":
            self.draw_main_menu(surface)
        elif game_state == "death_screen":
            self.draw_death_screen(surface)
        elif game_state == "win_screen":
            self.draw_win_screen(surface)

    def draw_main_menu(self, surface):
        surface.blit(self.game.main_menu_bg_dimmed, (0, 0))
        self.draw_text_with_outline(surface, "Игра-побег", self.font_large, WHITE, (SCREEN_WIDTH // 2, 200))
        for button in self.main_menu_buttons:
            button.draw(surface)

    def draw_death_screen(self, surface):
        self.game.in_game_draw()

        self.overlay_surface.fill((0, 0, 0, 180))
        surface.blit(self.overlay_surface, (0, 0))

        self.draw_text_with_outline(surface, "Вы умерли", self.font_large, RED, (SCREEN_WIDTH // 2, 200))

        self.draw_text_with_outline(surface, self.get_stats_text(), self.font_medium, WHITE, (SCREEN_WIDTH // 2, 280))

        for button in self.death_menu_buttons:
            button.draw(surface)

        self.draw_text_with_outline(surface, f"Очки: {self.game.score}  Время: {self.game.elapsed_time}c",
                                    self.font_small, WHITE,
                                    (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12), center_bottom=True)

    def draw_win_screen(self, surface):
        self.game.in_game_draw()

        alpha = min(200, int(200 * (self.win_animation_timer / self.win_animation_duration)))
        self.overlay_surface.fill((0, 0, 0, alpha))
        surface.blit(self.overlay_surface, (0, 0))

        if self.win_animation_timer >= self.win_animation_duration:
            self.draw_text_with_outline(surface, "Вы сбежали!", self.font_large, WHITE, (SCREEN_WIDTH // 2, 200))

            self.draw_text_with_outline(surface, self.get_stats_text(), self.font_medium, WHITE,
                                        (SCREEN_WIDTH // 2, 280))

            for button in self.win_menu_buttons:
                button.draw(surface)

        self.draw_text_with_outline(surface, f"Очки: {self.game.score}  Время: {self.game.elapsed_time}c",
                                    self.font_small, WHITE,
                                    (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12), center_bottom=True)

    def get_stats_text(self):
        score_str = f"Очки: {self.game.score} Время: {self.game.elapsed_time}c"
        return score_str

    def draw_text_with_outline(self, surface, text, font, color, center_pos, center_bottom=False):
        main_surf = font.render(text, True, color)
        outline_surf = font.render(text, True, BLACK)

        if center_bottom:
            main_rect = main_surf.get_rect(centerx=center_pos[0], bottom=center_pos[1])
        else:
            main_rect = main_surf.get_rect(center=center_pos)

        offset = 2
        surface.blit(outline_surf, (main_rect.x - offset, main_rect.y))
        surface.blit(outline_surf, (main_rect.x + offset, main_rect.y))
        surface.blit(outline_surf, (main_rect.x, main_rect.y - offset))
        surface.blit(outline_surf, (main_rect.x, main_rect.y + offset))

        surface.blit(main_surf, main_rect)