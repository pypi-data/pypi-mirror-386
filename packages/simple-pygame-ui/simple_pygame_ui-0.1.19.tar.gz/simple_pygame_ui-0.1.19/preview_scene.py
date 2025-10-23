import pygame

import scene_handler
from better_math import Vector2i
from elements.py_button import Button, ToggleButton
from pygame_scene import PyGameScene
from elements.text import Text, TextEdit, UnderlinedTextEdit
from elements.texture import Texture, StagedTexture


class PreviewScene(PyGameScene):
    def update(self):
        super().update()
        # Adding a Text Object
        self.drawables.append(Text("This is a Text","arial",pygame.Rect(scene_handler.camera_size.x // 2,60,0,40)))


        # Specifying the Size and Position of a Button
        button_rect = pygame.Rect(0,120,250,50)
        button_rect.centerx = scene_handler.camera_size.x // 2


        # Adding a Button Object
        self.drawables.append(Button("This is a Button",(scene_handler.camera_size.x // 2, 130),(250,40),pygame.font.SysFont("arial",16),lambda: print("You Clicked A Button")))


        # Adding a Toggle Button Object, DISCLAIMER: This is buggy and doesn't work as Supposed.
        self.drawables.append(ToggleButton("Test",(scene_handler.camera_size.x // 2, 130),(0,0),pygame.font.SysFont("arial",16),lambda new_value: print("You Toggled A Button"),text_color=(0,0,0)))


        # Adding a Input Field
        self.drawables.append(TextEdit(
            "", # Here Goes the Text that is Shown
            "Enter Text:", # Here Goes a Placeholder, a Gray text that's shown until your write text of focus
            "arial", # The Name of the Font you want to use
            pygame.Rect(scene_handler.camera_size.x // 2 - 125,200,250,40), # The Position and Size on the Screen
            is_password=True
        ))


        # Adding a Underlined Input Field, this is handy if you want to make smthn like Hangman
        self.drawables.append(UnderlinedTextEdit(
            "", # The Text Shown on the Lines
            6, # The Amount of Lines Shown
            "arial", # The Name of the Font you want to use
            Vector2i(scene_handler.camera_size.x // 2,260), # The Position and Size on the Screen
            centered=True, # If the object is supposed to be Centered
            skip=[2] # The Indexes of Lines to be Skipped
        ))


        # Adding a texture, this is for Rendering simple Textures, it's not supposed to be used as GameObjects as it is supposed to only be changed in the update method
        self.drawables.append(Texture("textures/test.png",pygame.Rect(0,0,128,128),texture_size=Vector2i(16,16)))

        # Adding a Staged Texture, in My Case in the Render Method i am Changing the stage every 90 Frames/1.5 seconds on 60 FPS
        self.staged_texture = StagedTexture(["textures/hangman_0.png","textures/hangman_1.png","textures/hangman_2.png","textures/hangman_3.png","textures/hangman_4.png","textures/hangman_5.png","textures/hangman_6.png","textures/hangman_7.png","textures/hangman_8.png"],pygame.Rect(0,128,512,512),texture_size=Vector2i(128,128))
        self.drawables.append(self.staged_texture)


    frame_amount = 0


    def render(self, screen, events) -> bool:
        pygame.draw.rect(screen,(255,255,255),(0,0,scene_handler.camera_size.x,scene_handler.camera_size.y))
        self.frame_amount += 1
        self.staged_texture.stage = (self.frame_amount // 90) % 10
        super().render(screen,events)
        return True