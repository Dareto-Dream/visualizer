import math
import pygame
from visualizer_modules.scenes.base_scene import BaseScene
from visualizer_modules.audio_analyzer import AudioFeatures


class PulseCharacterSilhouetteScene(BaseScene):
    """
    Procedural walking silhouette character.
    Audio-reactive, lightweight, and stylized.
    """

    def __init__(self, size):
        super().__init__(size)

        # Movement state
        self.x = -100
        self.walk_phase = 0.0
        self.flash = 0.0

    def enter(self):
        self.x = -100
        self.walk_phase = 0.0
        self.flash = 0.0

    def update(self, dt, t, features: AudioFeatures, idx: int):
        self.t = t
        self.rms = features.rms[idx]
        self.bass = features.bass[idx]
        self.mid = features.mid[idx]
        self.onset = features.onset[idx]

        # Walking speed & phase
        walk_speed = 1.5 + self.bass * 2.5
        self.walk_phase += dt * walk_speed * 6.0

        # Horizontal motion
        self.x += walk_speed * dt * 60
        if self.x > self.width + 120:
            self.x = -120

        # Onset flash
        if self.onset > 0.6:
            self.flash = 1.0
        else:
            self.flash *= 0.88

    def draw(self, surface: pygame.Surface):
        surface.fill((5, 5, 10))

        # Base positioning
        base_y = int(self.height * 0.7)
        bob = math.sin(self.walk_phase * 2.0) * 8

        cx = int(self.x)
        cy = int(base_y + bob)

        # Body scaling
        scale_y = 1.0 + self.bass * 0.35
        scale_x = 1.0 - self.bass * 0.15

        body_w = int(110 * scale_x)
        body_h = int(210 * scale_y)

        body_rect = pygame.Rect(0, 0, body_w, body_h)
        body_rect.midbottom = (cx, cy)

        # Lean forward slightly while walking
        lean = math.sin(self.walk_phase) * 8
        body_rect.x += int(lean)

        # Glow / flash outline
        if self.flash > 0.01:
            glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(200 * self.flash)
            pygame.draw.rect(
                glow,
                (255, 0, 180, alpha),
                body_rect.inflate(30, 30),
                border_radius=40
            )
            surface.blit(glow, (0, 0))

        # Draw torso
        pygame.draw.rect(surface, (20, 20, 30), body_rect, border_radius=40)
        pygame.draw.rect(surface, (255, 255, 255), body_rect, 3, border_radius=40)

        # Head
        head_r = int(32 * (1.0 + self.rms * 0.25))
        head_center = (
            body_rect.centerx,
            body_rect.top - head_r + 6
        )

        pygame.draw.circle(surface, (20, 20, 30), head_center, head_r)
        pygame.draw.circle(surface, (255, 255, 255), head_center, head_r, 3)

        # === LEGS ===
        hip_y = body_rect.bottom - 10
        hip_offset = body_rect.width // 4
        leg_len = int(90 * scale_y)

        swing = math.sin(self.walk_phase) * (25 + self.bass * 20)

        # Left leg
        self._draw_leg(
            surface,
            (body_rect.centerx - hip_offset, hip_y),
            leg_len,
            swing
        )

        # Right leg (opposite phase)
        self._draw_leg(
            surface,
            (body_rect.centerx + hip_offset, hip_y),
            leg_len,
            -swing
        )

    def _draw_leg(self, surface, hip_pos, length, angle_deg):
        angle = math.radians(angle_deg)
        knee_len = length * 0.55
        foot_len = length * 0.45

        # Knee position
        knee_x = hip_pos[0] + math.sin(angle) * knee_len
        knee_y = hip_pos[1] + math.cos(angle) * knee_len

        # Foot position
        foot_x = knee_x + math.sin(angle) * foot_len
        foot_y = knee_y + math.cos(angle) * foot_len

        pygame.draw.line(
            surface,
            (255, 255, 255),
            hip_pos,
            (int(knee_x), int(knee_y)),
            4
        )
        pygame.draw.line(
            surface,
            (255, 255, 255),
            (int(knee_x), int(knee_y)),
            (int(foot_x), int(foot_y)),
            4
        )
