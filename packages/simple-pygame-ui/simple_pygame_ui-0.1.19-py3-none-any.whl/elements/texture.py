import pygame

import draw_context
from better_math import Vector2i
from pygame_scene import PyGameUIHandler


class Texture(PyGameUIHandler):
    def __init__(self, texture_path, rect : pygame.Rect, uv : tuple[int,int,int,int] = (0,0,-1,-1),texture_size : Vector2i = Vector2i(128,128)):
        self.texture_path = texture_path
        self.rect = rect
        self.uv = uv
        self.texture_size = texture_size
        super().__init__()
    def get_rect(self) -> pygame.Rect:
        return self.rect

    def draw(self, surface, offset: Vector2i = Vector2i(0, 0)):
        context = draw_context.DrawContext(surface)
        context.texture(self.texture_path,Vector2i(self.get_rect().x,self.get_rect().y),self.uv,Vector2i(self.get_rect().w,self.get_rect().h),self.texture_size)

class StagedTexture(PyGameUIHandler):
    def __init__(self,texture_paths : list[str],rect : pygame.Rect,uv : tuple[int,int,int,int] = (0,0,-1,-1),texture_size : Vector2i = Vector2i(128,128)):
        self.texture_paths = texture_paths
        self.rect = rect
        self.uv = uv
        self.texture_size = texture_size
        self.stage = 0
        super().__init__()
    def get_rect(self) -> pygame.Rect:
        return self.rect
    def draw(self, surface, offset: Vector2i = Vector2i(0, 0)):
        context = draw_context.DrawContext(surface)
        for stage in range(self.stage):
            context.texture(self.texture_paths[stage], Vector2i(self.get_rect().x, self.get_rect().y), self.uv,
                            Vector2i(self.get_rect().w, self.get_rect().h), self.texture_size)

