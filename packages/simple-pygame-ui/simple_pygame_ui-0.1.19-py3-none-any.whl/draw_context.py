import pygame

import math
from better_math import Vector2i

_rendered_texture_cache : dict[tuple[tuple[int, int, int, int],Vector2i,Vector2i,tuple[int,int,int]], pygame.Surface] = {}
_texture_cache: dict[str, pygame.Surface] = {}

class DrawContext:
    def __init__(self, screen: pygame.Surface, position_offset: Vector2i = Vector2i(0, 0)):
        self.screen = screen
        self.position_offset = position_offset
        # persistente Caches (einmalig anlegen!)
        self._img_cache: dict[str, pygame.Surface] = {}
        self._scaled_cache: dict[tuple, pygame.Surface] = {}
        self._colored_cache: dict[tuple, pygame.Surface] = {}
        self._pattern_cache: dict[tuple, pygame.Surface] = {}
        self._final_cache: dict[tuple, pygame.Surface] = {}

        # optional: verhindert, dass Caches unendlich wachsen
        self._max_cache_items = 256

    def _load_texture(self, path: str) -> pygame.Surface:
        global _texture_cache
        if path not in _texture_cache:
            _texture_cache[path] = pygame.image.load(path).convert_alpha()
        return _texture_cache[path]

    # ---------- Hilfsfunktionen (alle verwenden persistente Caches) ----------
    def _enforce_cache_limit(self, cache: dict):
        if len(cache) > self._max_cache_items:
            # simple FIFO: pop das erste Element
            cache.pop(next(iter(cache)))

    def _load_texture(self, texture_path: str) -> pygame.Surface:
        surf = self._img_cache.get(texture_path)
        if surf is None:
            surf = pygame.image.load(texture_path).convert_alpha()
            # in Displayformat konvertieren (gleiche Pixelformate -> schnellere Blits)
            if surf.get_bitsize() != self.screen.get_bitsize():
                surf = surf.convert_alpha(self.screen)
            self._img_cache[texture_path] = surf
            self._enforce_cache_limit(self._img_cache)
        return surf

    def _get_scaled(self, img: pygame.Surface, tw: int, th: int) -> pygame.Surface:
        if img.get_width() == tw and img.get_height() == th:
            return img
        key = (id(img), tw, th, self.screen.get_bitsize())
        surf = self._scaled_cache.get(key)
        if surf is None:
            # Nearest Neighbor (schnell). Für hohe Qualität: smoothscale (langsamer).
            surf = pygame.transform.scale(img, (tw, th))
            # sicherstellen, dass das Format passt
            if surf.get_bitsize() != self.screen.get_bitsize():
                surf = surf.convert_alpha(self.screen)
            self._scaled_cache[key] = surf
            self._enforce_cache_limit(self._scaled_cache)
        return surf

    def _get_colored(self, tile: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
        if color == (255, 255, 255):
            return tile
        key = (id(tile), color)
        surf = self._colored_cache.get(key)
        if surf is None:
            surf = tile.copy()
            # 1x premul, dann weiterverwenden
            surf.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._colored_cache[key] = surf
            self._enforce_cache_limit(self._colored_cache)
        return surf

    def _get_tiled_pattern(
            self,
            tile: pygame.Surface,
            uv: tuple[int, int, int, int],
            tile_w: int,
            tile_h: int
    ) -> pygame.Surface:
        u0, v0, uW, vH = uv
        key = (id(tile), u0 % tile_w, v0 % tile_h, uW, vH)
        surf = self._pattern_cache.get(key)
        if surf is None:
            # so klein wie möglich anlegen (uW x vH) und dann per Batch blitten
            surf = pygame.Surface((uW, vH), flags=pygame.SRCALPHA)
            # Start so wählen, dass die erste sichtbare Kachel *links/oben* außerhalb beginnt
            offset_x = (-u0) % tile_w
            offset_y = (-v0) % tile_h
            start_x = offset_x - tile_w
            start_y = offset_y - tile_h

            tiles_x = (uW // tile_w) + 3
            tiles_y = (vH // tile_h) + 3

            # Zielpositionen sammeln -> ein blits()-Batch
            dests = []
            x = start_x
            for _ in range(tiles_x):
                y = start_y
                for _ in range(tiles_y):
                    dests.append((x, y))
                    y += tile_h
                x += tile_w

            surf.blits([(tile, d) for d in dests])
            # im Displayformat halten
            if surf.get_bitsize() != self.screen.get_bitsize():
                surf = surf.convert_alpha(self.screen)

            self._pattern_cache[key] = surf
            self._enforce_cache_limit(self._pattern_cache)
        return surf

    # ---------------------------- deine API ----------------------------------
    def texture(
            self,
            texture_path: str,
            pos: Vector2i,
            uv: tuple[int, int, int, int] = (0, 0, -1, -1),
            size: Vector2i = Vector2i(32, 32),
            texture_size: Vector2i = Vector2i(16, 16),
            color: tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        """
        Sehr schnelle Version:
        - ALLE Zwischenresultate persistent gecacht (img, scaled, colored, tiled, final)
        - Fast-Paths für Vollbild/Einzeltile
        - Keine Surface-Erzeugung/Skalierung pro Frame, wenn Parameter gleich bleiben
        - Immer Display-Pixelformat, um Blits zu beschleunigen
        """
        position = (int(pos.x + self.position_offset.x), int(pos.y + self.position_offset.y))

        img = self._load_texture(texture_path)

        tw, th = int(texture_size.x), int(texture_size.y)
        if tw <= 0 or th <= 0:
            return

        u0, v0, uW, vH = uv
        if uW == -1: uW = tw
        if vH == -1: vH = th
        if uW <= 0 or vH <= 0:
            return

        # --- Fast-Path: "Ganzes Bild Vollbild anzeigen" -----------------------
        screen_w, screen_h = self.screen.get_size()
        if (uW == img.get_width() and vH == img.get_height() and u0 == 0 and v0 == 0
                and size.x == screen_w and size.y == screen_h and tw == img.get_width() and th == img.get_height()):
            # Nur 1x Vollbild-Scaling cachen, danach pro Frame nur blit
            key_final = ("FULL", id(img), screen_w, screen_h, color)
            final = self._final_cache.get(key_final)
            if final is None:
                base = img
                if color != (255, 255, 255):
                    base = self._get_colored(img, color)
                final = pygame.transform.scale(base, (screen_w, screen_h))
                if final.get_bitsize() != self.screen.get_bitsize():
                    final = final.convert_alpha(self.screen)
                self._final_cache[key_final] = final
                self._enforce_cache_limit(self._final_cache)
            self.screen.blit(final, (0, 0))
            return

        # 1) auf (tw, th) skalieren (cached)
        base_tile = self._get_scaled(img, tw, th)

        # 2) farb-multiplizieren (cached)
        tile = self._get_colored(base_tile, color)

        # Fast-Path: genau ein Tile ohne Offset
        if (uW == tw and vH == th) and (u0 % tw == 0) and (v0 % th == 0):
            # Final-Scaling cachen
            key_final = ("ONE", id(tile), int(size.x), int(size.y))
            render_surface = self._final_cache.get(key_final)
            if render_surface is None:
                if size.x != uW or size.y != vH:
                    render_surface = pygame.transform.scale(tile, (int(size.x), int(size.y)))
                    if render_surface.get_bitsize() != self.screen.get_bitsize():
                        render_surface = render_surface.convert_alpha(self.screen)
                else:
                    render_surface = tile
                self._final_cache[key_final] = render_surface
                self._enforce_cache_limit(self._final_cache)

            self.screen.blit(render_surface, position)
            return

        # 3) Musterfläche (uW x vH) (cached)
        pattern_surface = self._get_tiled_pattern(tile, (u0, v0, uW, vH), tw, th)

        # 4) Final auf Zielgröße (cached)
        key_final = ("PAT", id(pattern_surface), int(size.x), int(size.y))
        render_surface = self._final_cache.get(key_final)
        if render_surface is None:
            if size.x != uW or size.y != vH:
                render_surface = pygame.transform.scale(pattern_surface, (int(size.x), int(size.y)))
                if render_surface.get_bitsize() != self.screen.get_bitsize():
                    render_surface = render_surface.convert_alpha(self.screen)
            else:
                render_surface = pattern_surface
            self._final_cache[key_final] = render_surface
            self._enforce_cache_limit(self._final_cache)

        # 5) Zeichnen
        self.screen.blit(render_surface, position)


    def text(self, text: str, font: str, pos: Vector2i, size: int, color=(0, 0, 0)):
        """Zeichnet Text ab (pos.x, pos.y) mit pygame.font.SysFont(font, size)."""
        target = self.screen  # erwartet: pygame.Surface vorhanden
        fnt = pygame.font.SysFont(font, size)  # pygame.font ist bereits initialisiert

        x, y = int(pos.x), int(pos.y)
        lines = text.split("\n")
        line_h = fnt.get_linesize()

        for line in lines:
            if line == "":
                y += line_h
                continue
            surf = fnt.render(line, True, color)

            target.blit(surf, (x, y))
            y += line_h

