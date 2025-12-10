import numpy as np
import pygame
from visualizer_modules.scenes.base_scene import BaseScene
from visualizer_modules.audio_analyzer import AudioFeatures


class BrainHUDScene(BaseScene):
    """
    Futuristic brain/body monitor HUD scene.
    Features glowing character visualization and technical panels.
    """
    
    def __init__(self, size):
        super().__init__(size)
        self.font = None
        
    def enter(self):
        self.font = pygame.font.SysFont("Consolas", 28, bold=True)

    def update(self, dt, t, features: AudioFeatures, idx: int):
        self.rms = features.rms[idx]
        self.bass = features.bass[idx]
        self.mid = features.mid[idx]
        self.treble = features.treble[idx]
        self.onset = features.onset[idx]
        self.t = t

    def draw(self, surface: pygame.Surface):
        surface.fill((0, 0, 0))
        
        w, h = self.width, self.height
        
        # Background grid
        grid_spacing = 40
        for x in range(0, w, grid_spacing):
            pygame.draw.line(surface, (30, 30, 30), (x, 0), (x, h), 1)
        for y in range(0, h, grid_spacing):
            pygame.draw.line(surface, (30, 30, 30), (0, y), (w, y), 1)
        
        # Central character visualization
        center_x = w * 0.25
        center_y = h * 0.5
        scale = 1.0 + 0.2 * self.rms
        
        # Glow effect
        glow_color = (255, 0, 180)
        for i in range(5, 0, -1):
            alpha = 40 * (i / 5)
            glow_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            
            body_w = int(140 * scale * (1 + i * 0.05))
            body_h = int(200 * scale * (1 + i * 0.05))
            body_rect = pygame.Rect(0, 0, body_w, body_h)
            body_rect.center = (int(center_x), int(center_y))
            
            color_with_alpha = glow_color + (int(alpha),)
            pygame.draw.rect(glow_surface, color_with_alpha, body_rect, border_radius=30)
            surface.blit(glow_surface, (0, 0))
        
        # Main body
        body_w = int(140 * scale)
        body_h = int(200 * scale)
        body_rect = pygame.Rect(0, 0, body_w, body_h)
        body_rect.center = (int(center_x), int(center_y))
        
        pygame.draw.rect(surface, (0, 80, 180), body_rect, border_radius=30)
        pygame.draw.rect(surface, (255, 255, 255), body_rect, 3, border_radius=30)
        
        # Brain (treble responsive)
        brain_r = int(35 * scale * (1.0 + self.treble * 0.5))
        brain_center = (int(center_x), int(center_y - body_h * 0.35))
        
        for i in range(3, 0, -1):
            glow_r = brain_r + i * 8
            alpha = 60 * (i / 3)
            glow_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 0, 180, int(alpha)), brain_center, glow_r)
            surface.blit(glow_surface, (0, 0))
        
        pygame.draw.circle(surface, (255, 0, 180), brain_center, brain_r)
        pygame.draw.circle(surface, (255, 255, 255), brain_center, brain_r, 3)
        
        pulse_r = brain_r - 10
        pulse_alpha = int(100 + 155 * self.treble)
        pulse_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(pulse_surface, (255, 100, 255, pulse_alpha), brain_center, pulse_r)
        surface.blit(pulse_surface, (0, 0))
        
        # Speaker (bass responsive)
        speaker_r = int(25 * scale * (1.0 + self.bass * 0.8))
        speaker_center = (int(center_x), int(center_y + body_h * 0.25))
        
        for ring in range(3):
            ring_r = speaker_r + ring * 12
            pygame.draw.circle(surface, (0, 255, 255), speaker_center, ring_r, 2)
        
        pygame.draw.circle(surface, (0, 200, 255), speaker_center, speaker_r)
        pygame.draw.circle(surface, (255, 255, 255), speaker_center, speaker_r, 3)
        
        # Right panel HUD
        panel_x = int(w * 0.55)
        panel_y = int(h * 0.1)
        panel_w = int(w * 0.38)
        panel_h = int(h * 0.8)
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (10, 10, 30), panel_rect)
        pygame.draw.rect(surface, (255, 255, 255), panel_rect, 3)
        
        # BPM and status
        if self.font:
            bpm = 80 + int(140 * self.onset)
            bpm_text = self.font.render(f"BPM: {bpm}", True, (0, 255, 255))
            surface.blit(bpm_text, (panel_x + 20, panel_y + 20))
            
            status_text = self.font.render("STATUS: ACTIVE", True, (0, 255, 100))
            surface.blit(status_text, (panel_x + 20, panel_y + 60))
        
        # Waveform display
        wave_rect = pygame.Rect(panel_x + 20, panel_y + 120, panel_w - 40, 100)
        pygame.draw.rect(surface, (0, 0, 0), wave_rect)
        pygame.draw.rect(surface, (0, 255, 255), wave_rect, 2)
        
        points = []
        segments = 80
        for i in range(segments):
            px = wave_rect.left + wave_rect.width * (i / (segments - 1))
            
            freq1 = 3 + self.bass * 5
            freq2 = 7 + self.treble * 10
            wave = np.sin(self.t * freq1 + i * 0.3) * 0.3
            wave += np.sin(self.t * freq2 + i * 0.1) * 0.2
            
            amp = self.rms * 0.6 + self.onset * 0.4
            py = wave_rect.centery + wave * amp * (wave_rect.height / 2 - 10)
            points.append((int(px), int(py)))
        
        if len(points) > 1:
            pygame.draw.lines(surface, (0, 255, 255), False, points, 3)
        
        # Frequency spectrum
        spectrum_rect = pygame.Rect(panel_x + 20, panel_y + 250, panel_w - 40, 150)
        pygame.draw.rect(surface, (0, 0, 0), spectrum_rect)
        pygame.draw.rect(surface, (255, 0, 180), spectrum_rect, 2)
        
        if self.font:
            spec_label = self.font.render("FREQUENCY SPECTRUM", True, (255, 0, 180))
            surface.blit(spec_label, (spectrum_rect.left + 5, spectrum_rect.top + 5))
        
        num_bars = 20
        bar_w = (spectrum_rect.width - 40) // num_bars
        for i in range(num_bars):
            ratio = i / num_bars
            if ratio < 0.3:
                val = self.bass
                color = (255, 0, 100)
            elif ratio < 0.7:
                val = self.mid
                color = (255, 100, 180)
            else:
                val = self.treble
                color = (255, 150, 255)
            
            bar_h = int((spectrum_rect.height - 50) * val * (0.5 + np.random.random() * 0.5))
            bar_x = spectrum_rect.left + 20 + i * bar_w
            bar_y = spectrum_rect.bottom - bar_h - 10
            
            pygame.draw.rect(surface, color, (bar_x, bar_y, bar_w - 2, bar_h))
        
        # Timer
        timer_rect = pygame.Rect(panel_x + 20, panel_y + panel_h - 80, panel_w - 40, 60)
        pygame.draw.rect(surface, (0, 0, 0), timer_rect)
        pygame.draw.rect(surface, (255, 255, 255), timer_rect, 2)
        
        if self.font:
            minutes = int(self.t // 60)
            seconds = int(self.t % 60)
            ms = int((self.t - int(self.t)) * 100)
            timer_text = self.font.render(f"{minutes:02d}:{seconds:02d}.{ms:02d}", True, (0, 255, 100))
            timer_pos = timer_text.get_rect(center=timer_rect.center)
            surface.blit(timer_text, timer_pos)
