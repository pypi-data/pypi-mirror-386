import pygame

from draw_context import DrawContext
import pygame_scene
from better_math import Vector2i


class Button(pygame_scene.PyGameUIHandler):
    def __init__(self, text, center, size, font, on_click, color=(60, 120, 255), hover_color=(40, 90, 210),
                 text_color=(240, 240, 240), on_click_values = ()):
        super().__init__()
        self.collision_rect = pygame.Rect(center[0], center[1], size[0], size[1])
        self.text = text
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.font = font
        self.on_click = on_click
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.pressed = False
        self.on_click_values = on_click_values
        if not (font is None):
            self.text_surf = self.font.render(self.text, True, self.text_color)
            self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        else:
            self.text_surf = None


    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.get_rect().collidepoint(event.pos)
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.hovered:
                self.on_click(*self.on_click_values)
                return True
            self.pressed = False
        return False

    def get_rect(self) -> pygame.Rect:
        return self.rect.move(self.parent.get_rect().x, self.parent.get_rect().y)

    def draw(self, surface,offset : Vector2i = Vector2i(0, 0)):
        col = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, col, self.rect.move(offset.x,offset.y), border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), self.rect.move(offset.x,offset.y), 2, border_radius=10)
        self.text_rect.center = self.rect.center
        surface.blit(self.text_surf, self.text_rect.move(offset.x,offset.y))


class ToggleButton(Button):
    toggled = False

    def _do_nothing(self, new_value):
        pass

    def __init__(self, text, center, size, font, on_changed=_do_nothing, color=(60, 120, 255), hover_color=(40, 90, 210),
                 text_color=(240, 240, 240),  on_click_values = ()):
        def toggle():
            self.toggled = not self.toggled
            on_changed(self.toggled)

        self.on_changed = on_changed
        super().__init__(text, center, size, font, toggle,color,hover_color,text_color,on_click_values=on_click_values)

    def get_rect(self) -> pygame.Rect:
        button_rect = self.rect.move(60, (self.rect.y // 2) + 7)
        button_rect.w = 40
        button_rect.h = 20
        return button_rect.move(self.parent.get_rect().x, self.parent.get_rect().y)

    def draw(self, surface,offset : Vector2i = Vector2i(0, 0)):
        col = self.hover_color if self.hovered else self.color
        button_rect = self.rect.move(60, (self.rect.y // 2) + 7)
        button_rect.w = 40
        button_rect.h = 20
        pygame.draw.rect(surface, (60, 60, 60), button_rect.move(offset.x,offset.y), border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), button_rect.move(offset.x,offset.y), 2, border_radius=10)
        toggle_pos = -20
        if self.toggled:
            toggle_pos = 20
        circle_pos = (button_rect.center[0] + toggle_pos + offset.x, button_rect.center[1] + offset.y)
        pygame.draw.circle(surface, col, circle_pos, 12)
        pygame.draw.circle(surface, (0, 0, 0), circle_pos, 12, 2)
        self.text_rect.center = (button_rect.center[0] - (self.font.size(self.text)[0] // 2), button_rect.center[1])

        surface.blit(self.text_surf, self.text_rect.move(-(self.text_rect.w // 2) - 20, 0))
        pygame_scene.PyGameUIHandler.draw(self, surface)

class TextureButton(Button):
    def __init__(self, texture_path, center, size, on_click,texture_size=Vector2i(32,32), on_click_values=()):
        self.texture_path = texture_path
        self.texture_size = texture_size
        super().__init__("", center, size, None, on_click, on_click_values=on_click_values)

    def draw(self, surface, offset: Vector2i = Vector2i(0, 0)):
        draw_context = DrawContext(surface,offset)
        draw_context.texture(self.texture_path, Vector2i(self.rect.x, self.rect.y), size=Vector2i(self.get_rect().w, self.get_rect().h),texture_size=self.texture_size)