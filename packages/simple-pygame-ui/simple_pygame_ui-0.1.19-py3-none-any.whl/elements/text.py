import pygame

import draw_context
import pygame_scene
from draw_context import DrawContext
from better_math import Vector2i
from pygame_scene import PyGameUIHandler


class Text(PyGameUIHandler):
    def __init__(self, text: str,font, rect: pygame.Rect):
        self.text = text
        self.rect = rect
        self.font = font
        centerx = rect.centerx
        rect.w = pygame.font.SysFont(font,rect.h).size(text)[0]
        rect.centerx = centerx

        super().__init__()

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def draw(self, surface, offset: Vector2i = Vector2i(0, 0)):
        context = DrawContext(surface)
        context.text(self.text,self.font,Vector2i(self.get_rect().x,self.get_rect().y),self.get_rect().h)
        super().draw(surface,offset)

class TextEdit(PyGameUIHandler):
    def __init__(self, text: str, placeholder: str, font, rect: pygame.Rect, can_write = None, is_password : bool = False):
        self.text = text
        self.placeholder = placeholder
        self.font = font
        self.rect = rect
        self.can_write = can_write
        self.is_password = is_password
        super().__init__()

    hovered = False
    animation_tick = 0
    def get_rect(self) -> pygame.Rect:
        return self.rect
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.get_rect().collidepoint(event.pos[0],event.pos[1]):
                self.hovered = True
                return True
            else:
                self.hovered = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                if pygame_scene.focused_ui_handler is not None:
                    pygame_scene.focused_ui_handler.no_longer_focused()
                pygame.key.set_repeat(300, 30)
                pygame_scene.focused_ui_handler = self
                return True
        elif event.type == pygame.TEXTINPUT and self.is_focused():
            if self.can_write is not None:
                if not self.can_write(self.text + event.text):
                    return True
            self.text += event.text
            return True
        elif event.type == pygame.KEYDOWN and self.is_focused():
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
        return False
    def no_longer_focused(self):
        print("No Longer Focused")
        pygame.key.set_repeat(0)
    def draw(self, surface, offset: Vector2i = Vector2i(0, 0)):
        bg_texture = (170,170,170)
        if self.hovered:
            bg_texture = (190,190,190)
        pygame.draw.rect(surface,bg_texture,self.get_rect(),border_radius=10)
        pygame.draw.rect(surface,(70,70,70),self.get_rect(),width=2,border_radius=10)
        context = draw_context.DrawContext(surface,offset)
        text = self.text
        if self.is_password:
            text = "•" * len(self.text)
        if self.is_focused():
            if (self.animation_tick % 50) < 25:
                text += "|"
            self.animation_tick += 1
        else:
            self.animation_tick = 0
        if text == "" and not self.is_focused():
            context.text(self.placeholder,self.font,Vector2i(self.get_rect().x + 5, self.get_rect().center[1] - 8),16,(120,120,120))
        else:
            context.text(text,self.font, Vector2i(self.get_rect().x + 5, self.get_rect().center[1] - 8), 16,
                         (0,0,0))

class UnderlinedTextEdit(TextEdit):
    def __init__(self, text: str, line_amount: int, font, pos : Vector2i, can_write = None, centered : bool = False, skip : list[int] = []):
        self.line_amount = line_amount
        self.can_write_underlined = can_write
        self.skip = skip
        def check_for_lenght(new_text):
            print(len(new_text) > line_amount and not (can_write is not None and can_write(new_text)))
            if len(new_text) > line_amount and not (can_write is not None and can_write(new_text)):
                return False,
            return True
        rect = pygame.Rect(pos.x,pos.y,50 * line_amount - 10,40)
        if centered:
            rect.centerx = pos.x
        super().__init__(text, "", font, rect,check_for_lenght)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.text.endswith(" "):
                    self.text = self.text[:-1]
        val = super().handle_event(event)
        if event.type == pygame.TEXTINPUT:
            if len(self.text) in self.skip:
                self.text += " "
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.text.endswith(" "):
                    self.text = self.text[:-1]
        return val

    def draw(self, surface, offset: Vector2i = Vector2i(0, 0)):
        x = 0
        context = draw_context.DrawContext(surface,offset)
        for line in range(self.line_amount):
            if line in self.skip:
                x += 50
                continue
            pygame.draw.rect(surface,(0,0,0),(x + self.get_rect().x,self.get_rect().y + self.get_rect().height,40,6))
            if len(self.text) > line:
                context.text(self.text[line],self.font,Vector2i(x + self.get_rect().x + (20 - pygame.font.SysFont(self.font,40).size(self.text[line])[0] // 2),self.get_rect().y),40)
            x += 50