

import pygame

import scene_handler
from better_math import Vector2i
from preview_scene import PreviewScene
from pygame_scene import PyGameScene

clock = pygame.time.Clock()

def setup(default_scene : PyGameScene,window_name="PyGameUI Window"):
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption(window_name)
    screen = pygame.display.set_mode((scene_handler.camera_size.x,scene_handler.camera_size.y),pygame.RESIZABLE)
    running = True
    scene_handler.current_scene = default_scene
    default_scene.update()
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                scene_handler.camera_size = Vector2i(event.w,event.h)
                scene_handler.current_scene.update()
        if running:
            running = scene_handler.current_scene.render(screen,events)

        if not running:
            scene_handler.current_scene.close()
        pygame.display.update()
        scene_handler.delta = clock.tick(scene_handler.FPS)


if __name__ == "__main__":
    setup(PreviewScene())