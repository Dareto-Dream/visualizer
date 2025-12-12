import random
import pygame
import numpy as np
from visualizer_modules.scenes.base_scene import BaseScene
from visualizer_modules.audio_analyzer import AudioFeatures


class BeatSlicerScene(BaseScene):
    """
    Abstract panel slicing scene.
    Panels react sharply to onset and spectral flux.
    """

    def __init__(self, size):
        super().__init__(size)
        self.panels = []
        self.num_panels = 12
        self.panel_offsets = [0.0] * self.num_panels
        self.panel_velocities = [0.0] * self.num_panels

    def enter(self):
        panel_w = self.width // self.num_panels
        self.panels = []
        for i in range(self.num_panels):
            rect = pygame.Rect(
                i * panel_w,
                0,
                panel_w + 1,
                self.height
            )
            self.panels.append(rect)

    def update(self, dt, t, features: AudioFeatures, idx: int):
        self.rms = features.rms[idx]
        self.onset = features.onset[idx]
        self.flux = features.spectral_flux[idx]

        # Trigger sharp slice on onset
        if self.onset > 0.65:
            for i in range(self.num_panels):
                direction = -1 if i % 2 == 0 else 1
                self.panel_velocities[i] += direction * (8 + 40 * self.onset)

        # Apply motion + damping
        for i in range(self.num_panels):
            jitter = (random.random() - 0.5) * self.flux * 6
            self.panel_velocities[i] += jitter
            self.panel_offsets[i] += self.panel_velocities[i] * dt * 60
            self.panel_velocities[i] *= 0.88

    def draw(self, surface: pygame.Surface):
        surface.fill((0, 0, 0))

        base_color = (255, 40, 120)
        glow_color = (255, 80, 180)

        for i, rect in enumerate(self.panels):
            offset_x = int(self.panel_offsets[i])
            draw_rect = rect.move(offset_x, 0)

            # Glow pass
            glow = pygame.Surface((draw_rect.width + 20, draw_rect.height), pygame.SRCALPHA)
            alpha = int(80 + 120 * self.rms)
            pygame.draw.rect(
                glow,
                glow_color + (alpha,),
                glow.get_rect(),
                border_radius=10
            )
            surface.blit(glow, (draw_rect.x - 10, 0))

            # Main panel
            pygame.draw.rect(surface, base_color, draw_rect)
            pygame.draw.rect(surface, (255, 255, 255), draw_rect, 2)
