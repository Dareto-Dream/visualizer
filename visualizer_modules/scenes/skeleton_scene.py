import numpy as np
import pygame
from visualizer_modules.scenes.base_scene import BaseScene
from visualizer_modules.audio_analyzer import AudioFeatures


class SkeletonXRayScene(BaseScene):
    """
    X-ray style skeleton visualization with hexagon grid background.
    Features detailed anatomical monitoring and digital timer display.
    """
    
    def __init__(self, size):
        super().__init__(size)
        self.font_large = None
        self.font_small = None
        self.font_digital = None
        
    def enter(self):
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 18, bold=True)
        self.font_digital = pygame.font.SysFont("Consolas", 64, bold=True)

    def update(self, dt, t, features: AudioFeatures, idx: int):
        self.rms = features.rms[idx]
        self.bass = features.bass[idx]
        self.mid = features.mid[idx]
        self.treble = features.treble[idx]
        self.onset = features.onset[idx]
        self.t = t

    def draw_hexagon(self, surface, center, radius, color, width=2):
        """Draw a hexagon."""
        points = []
        for i in range(6):
            angle = np.pi / 3 * i
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            points.append((int(x), int(y)))
        pygame.draw.polygon(surface, color, points, width)

    def draw_hexagon_grid(self, surface):
        """Draw honeycomb hexagon background."""
        hex_radius = 50
        hex_height = hex_radius * np.sqrt(3)
        hex_width = hex_radius * 1.5
        
        for row in range(-2, 16):
            for col in range(-2, 26):
                x = col * hex_width
                y = row * hex_height + (hex_height / 2 if col % 2 else 0)
                
                self.draw_hexagon(surface, (int(x), int(y)), hex_radius, (255, 255, 255), 3)
                
                if row % 3 == 0 and col % 3 == 0:
                    cross_size = 15
                    pygame.draw.line(surface, (255, 255, 255), 
                                   (int(x - cross_size), int(y)), 
                                   (int(x + cross_size), int(y)), 4)
                    pygame.draw.line(surface, (255, 255, 255), 
                                   (int(x), int(y - cross_size)), 
                                   (int(x), int(y + cross_size)), 4)

    def draw_skeleton(self, surface, center_x, center_y):
        """Draw blue skeleton figure with pink brain and cyan details."""
        scale = 1.0 + self.rms * 0.15
        
        skeleton_w = int(280 * scale)
        skeleton_h = int(380 * scale)
        
        body_color = (0, 100, 255)
        outline_color = (255, 255, 255)
        brain_color = (255, 100, 150)
        eye_color = (0, 0, 0)
        teeth_color = (0, 200, 255)
        pelvis_color = (0, 255, 255)
        
        body_rect = pygame.Rect(0, 0, skeleton_w, skeleton_h)
        body_rect.center = (int(center_x), int(center_y))
        
        pygame.draw.ellipse(surface, body_color, body_rect)
        pygame.draw.ellipse(surface, outline_color, body_rect, 4)
        
        head_y = body_rect.top + skeleton_h * 0.15
        head_radius = int(skeleton_w * 0.35)
        head_center = (int(center_x), int(head_y))
        
        brain_pulsing = 1.0 + self.treble * 0.3
        brain_w = int(head_radius * 1.4 * brain_pulsing)
        brain_h = int(head_radius * 0.8 * brain_pulsing)
        brain_rect = pygame.Rect(0, 0, brain_w, brain_h)
        brain_rect.center = head_center
        
        pygame.draw.ellipse(surface, brain_color, brain_rect)
        pygame.draw.ellipse(surface, outline_color, brain_rect, 3)
        
        num_swirls = 5
        for i in range(num_swirls):
            angle = (self.t * 2 + i * np.pi * 2 / num_swirls) % (np.pi * 2)
            radius = brain_w // 4
            sx = int(head_center[0] + np.cos(angle) * radius * 0.3)
            sy = int(head_center[1] + np.sin(angle) * radius * 0.3)
            pygame.draw.circle(surface, (200, 80, 120), (sx, sy), 8)
        
        eye_y = int(head_y + head_radius * 0.2)
        eye_spacing = head_radius // 2
        for eye_x in [center_x - eye_spacing, center_x + eye_spacing]:
            pygame.draw.circle(surface, eye_color, (int(eye_x), eye_y), 18)
            pygame.draw.circle(surface, outline_color, (int(eye_x), eye_y), 18, 2)
        
        teeth_y = int(head_y + head_radius * 0.6)
        teeth_w = head_radius
        teeth_h = 12
        for i in range(5):
            tooth_x = int(center_x - teeth_w // 2 + i * (teeth_w // 5))
            tooth_rect = pygame.Rect(tooth_x, teeth_y, teeth_w // 6, teeth_h)
            brightness = 1.0 if self.onset > 0.5 else 0.7
            color = tuple(int(c * brightness) for c in teeth_color)
            pygame.draw.rect(surface, color, tooth_rect, border_radius=2)
        
        ribcage_y = body_rect.top + skeleton_h * 0.4
        for i in range(6):
            rib_y = int(ribcage_y + i * 15)
            rib_w = int(skeleton_w * (0.6 - i * 0.05))
            rib_rect = pygame.Rect(0, 0, rib_w, 8)
            rib_rect.center = (int(center_x), rib_y)
            pygame.draw.ellipse(surface, eye_color, rib_rect)
            pygame.draw.ellipse(surface, outline_color, rib_rect, 2)
        
        pelvis_y = body_rect.bottom - skeleton_h * 0.25
        pelvis_pulse = 1.0 + self.bass * 0.5
        pelvis_r = int(30 * scale * pelvis_pulse)
        
        for ring in range(3):
            ring_r = pelvis_r + ring * 8
            pygame.draw.circle(surface, pelvis_color, (int(center_x), int(pelvis_y)), ring_r, 2)
        
        pygame.draw.circle(surface, pelvis_color, (int(center_x), int(pelvis_y)), pelvis_r)
        pygame.draw.circle(surface, outline_color, (int(center_x), int(pelvis_y)), pelvis_r, 3)
        
        arm_points_left = [
            (int(center_x - skeleton_w * 0.25), int(body_rect.top + skeleton_h * 0.35)),
            (int(center_x - skeleton_w * 0.5), int(body_rect.centery)),
            (int(center_x - skeleton_w * 0.6), int(body_rect.bottom - skeleton_h * 0.3))
        ]
        arm_points_right = [
            (int(center_x + skeleton_w * 0.25), int(body_rect.top + skeleton_h * 0.35)),
            (int(center_x + skeleton_w * 0.5), int(body_rect.centery)),
            (int(center_x + skeleton_w * 0.6), int(body_rect.bottom - skeleton_h * 0.3))
        ]
        
        pygame.draw.lines(surface, outline_color, False, arm_points_left, 5)
        pygame.draw.lines(surface, outline_color, False, arm_points_right, 5)

    def draw(self, surface: pygame.Surface):
        surface.fill((0, 0, 0))
        
        w, h = self.width, self.height
        
        self.draw_hexagon_grid(surface)
        
        skeleton_x = w * 0.28
        skeleton_y = h * 0.5
        self.draw_skeleton(surface, skeleton_x, skeleton_y)
        
        waveform_left_x = 10
        waveform_left_y = int(h * 0.65)
        waveform_width = 100
        waveform_height = 60
        
        points = []
        segments = 50
        for i in range(segments):
            px = waveform_left_x + (waveform_width * i / segments)
            wave = np.sin(self.t * 10 + i * 0.3) * 0.5
            wave += np.sin(self.t * 5 + i * 0.15) * 0.3
            py = waveform_left_y + wave * self.rms * waveform_height
            points.append((int(px), int(py)))
        
        if len(points) > 1:
            pygame.draw.lines(surface, (255, 255, 255), False, points, 2)
        
        panel_x = int(w * 0.55)
        panel_y = int(h * 0.08)
        panel_w = int(w * 0.4)
        panel_h = int(h * 0.85)
        
        code_box_rect = pygame.Rect(panel_x + 20, panel_y, 140, 80)
        pygame.draw.rect(surface, (20, 20, 20), code_box_rect)
        pygame.draw.rect(surface, (255, 255, 255), code_box_rect, 2)
        
        if self.font_small:
            code_lines = [
                "01001101",
                "11010110", 
                "00110101",
                "10101100"
            ]
            for i, line in enumerate(code_lines):
                code_text = self.font_small.render(line, True, (0, 255, 0))
                surface.blit(code_text, (code_box_rect.left + 10, code_box_rect.top + 10 + i * 18))
        
        bpm_x = code_box_rect.right + 40
        bpm_y = panel_y
        
        if self.font_large:
            bpm_label = self.font_large.render("BPM", True, (255, 255, 255))
            surface.blit(bpm_label, (bpm_x, bpm_y))
            
            bpm = 80 + int(120 * self.onset)
            bpm_value = self.font_large.render(str(bpm), True, (255, 255, 255))
            surface.blit(bpm_value, (bpm_x, bpm_y + 50))
            
            bar_w = 150
            bar_h = 20
            bar_rect = pygame.Rect(bpm_x, bpm_y + 100, bar_w, bar_h)
            pygame.draw.rect(surface, (50, 50, 50), bar_rect)
            pygame.draw.rect(surface, (255, 255, 255), bar_rect, 2)
            
            fill_w = int(bar_w * (bpm - 80) / 120)
            fill_rect = pygame.Rect(bpm_x, bpm_y + 100, fill_w, bar_h)
            pygame.draw.rect(surface, (255, 255, 255), fill_rect)
        
        brain_icon_rect = pygame.Rect(panel_x + 20, panel_y + 160, 100, 100)
        pygame.draw.ellipse(surface, (50, 100, 150), brain_icon_rect)
        pygame.draw.ellipse(surface, (255, 255, 255), brain_icon_rect, 3)
        
        mid_panel_y = panel_y + 300
        mid_panel_rect = pygame.Rect(panel_x + 20, mid_panel_y, panel_w - 40, 120)
        pygame.draw.rect(surface, (20, 20, 20), mid_panel_rect)
        pygame.draw.rect(surface, (255, 255, 255), mid_panel_rect, 3)
        
        waveform_points = []
        wave_segments = 60
        for i in range(wave_segments):
            px = mid_panel_rect.left + 10 + (mid_panel_rect.width - 20) * (i / wave_segments)
            wave_val = np.sin(self.t * 8 + i * 0.2) * self.mid
            py = mid_panel_rect.centery + wave_val * (mid_panel_rect.height / 2 - 10)
            waveform_points.append((int(px), int(py)))
        
        if len(waveform_points) > 1:
            pygame.draw.lines(surface, (255, 255, 255), False, waveform_points, 2)
        
        bars_y = mid_panel_y + 140
        num_bars = 6
        bar_width = 15
        bar_spacing = 25
        start_bar_x = panel_x + 50
        
        for i in range(num_bars):
            bar_x = start_bar_x + i * bar_spacing
            bar_val = [self.bass, self.mid, self.treble, self.rms, self.onset, self.bass][i]
            bar_h = int(40 * bar_val)
            bar_rect = pygame.Rect(bar_x, bars_y - bar_h, bar_width, bar_h)
            pygame.draw.rect(surface, (255, 255, 255), bar_rect)
        
        timer_y = int(h * 0.75)
        timer_w = int(panel_w - 40)
        timer_h = 100
        timer_rect = pygame.Rect(panel_x + 20, timer_y, timer_w, timer_h)
        pygame.draw.rect(surface, (0, 0, 0), timer_rect)
        pygame.draw.rect(surface, (255, 255, 255), timer_rect, 4)
        
        if self.font_digital:
            minutes = int(self.t // 60)
            seconds = int(self.t % 60)
            ms = int((self.t - int(self.t)) * 100)
            time_str = f"{minutes:02d}:{seconds:02d}:{ms:02d}"
            
            time_text = self.font_digital.render(time_str, True, (255, 255, 255))
            time_pos = time_text.get_rect(center=timer_rect.center)
            surface.blit(time_text, time_pos)
        
        plus_row_y = int(h * 0.92)
        plus_size = 20
        plus_spacing = 80
        start_plus_x = 40
        
        for i in range(8):
            plus_x = start_plus_x + i * plus_spacing
            pygame.draw.line(surface, (255, 255, 255), 
                           (plus_x - plus_size, plus_row_y), 
                           (plus_x + plus_size, plus_row_y), 4)
            pygame.draw.line(surface, (255, 255, 255), 
                           (plus_x, plus_row_y - plus_size), 
                           (plus_x, plus_row_y + plus_size), 4)
