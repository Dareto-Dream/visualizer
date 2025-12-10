import numpy as np
import pygame
from visualizer_modules.scenes.base_scene import BaseScene
from visualizer_modules.audio_analyzer import AudioFeatures


class EnhancedStripesScene(BaseScene):
    """
    Vertical frequency bars with animated cars and dancing figures.
    Inspired by Friday Night Funkin' aesthetics.
    """
    
    def __init__(self, size):
        super().__init__(size)
        self.waveform_history = [[] for _ in range(8)]
        self.history_length = 60
        self.font_large = None
        self.font_small = None
        
    def enter(self):
        self.font_large = pygame.font.SysFont("Impact", 32, bold=True)
        self.font_small = pygame.font.SysFont("Impact", 20, bold=True)

    def update(self, dt, t, features: AudioFeatures, idx: int):
        self.rms = features.rms[idx]
        self.bass = features.bass[idx]
        self.mid = features.mid[idx]
        self.treble = features.treble[idx]
        self.onset = features.onset[idx]
        self.t = t
        
        if len(self.waveform_history[0]) >= self.history_length:
            for h in self.waveform_history:
                h.pop(0)
        
        self.waveform_history[0].append(self.bass)
        self.waveform_history[1].append(self.bass)
        self.waveform_history[2].append(self.mid)
        self.waveform_history[3].append(self.mid)
        self.waveform_history[4].append(self.mid)
        self.waveform_history[5].append(self.treble)
        self.waveform_history[6].append(self.treble)
        self.waveform_history[7].append(self.rms)

    def draw_halftone_pattern(self, surface, rect, color, intensity):
        """Draw halftone dot pattern for retro aesthetic."""
        dot_size = 4
        spacing = 6
        for y in range(rect.top, rect.bottom, spacing):
            for x in range(rect.left, rect.right, spacing):
                size = int(dot_size * intensity)
                if size > 1:
                    pygame.draw.circle(surface, color, (x, y), size // 2)

    def draw(self, surface: pygame.Surface):
        surface.fill((0, 0, 0))
        
        w, h = self.width, self.height
        
        # Draw frequency bars
        num_bars = 8
        bar_width = 100
        total_width = num_bars * bar_width + (num_bars - 1) * 20
        start_x = (w - total_width) // 2
        
        labels = ["VOCAL BF", "VOCAL BF", "VOCAL MOMMY", "VOCAL MOMMY", "BASS", "DRUMS", "SYNTH", ""]
        colors = [
            (255, 100, 180),
            (255, 120, 200),
            (255, 80, 160),
            (255, 100, 180),
            (255, 60, 140),
            (255, 140, 200),
            (255, 100, 180),
            (255, 120, 200)
        ]
        
        for i in range(num_bars):
            x = start_x + i * (bar_width + 20)
            
            history = self.waveform_history[i]
            if len(history) > 0:
                current_val = history[-1]
            else:
                current_val = 0
            
            bar_height = int(h * 0.5 * (0.3 + current_val * 0.7))
            bar_y = h - bar_height - 200
            
            bar_rect = pygame.Rect(x, bar_y, bar_width, bar_height)
            
            # Gradient fill
            gradient_steps = 20
            for step in range(gradient_steps):
                step_h = bar_height // gradient_steps
                step_y = bar_y + step * step_h
                intensity = 1.0 - (step / gradient_steps) * 0.6
                color = tuple(int(c * intensity) for c in colors[i])
                step_rect = pygame.Rect(x, step_y, bar_width, step_h)
                pygame.draw.rect(surface, color, step_rect)
            
            # Halftone overlay
            halftone_intensity = 0.4 + current_val * 0.6
            self.draw_halftone_pattern(surface, bar_rect, (255, 255, 255), halftone_intensity * 0.3)
            
            pygame.draw.rect(surface, (255, 255, 255), bar_rect, 2)
            
            # Draw horizontal waveform inside bar
            if len(history) > 2:
                points = []
                waveform_segments = min(len(history), 40)
                waveform_margin = 10
                
                for j in range(waveform_segments):
                    progress = j / (waveform_segments - 1)
                    px = x + waveform_margin + (bar_width - 2 * waveform_margin) * progress
                    
                    hist_idx = int(j * (len(history) - 1) / (waveform_segments - 1))
                    val = history[hist_idx]
                    
                    py = bar_y + bar_height // 2 + int((val - 0.5) * bar_height * 0.6)
                    points.append((int(px), int(py)))
                
                if len(points) > 1:
                    pygame.draw.lines(surface, (255, 255, 255), False, points, 2)
            
            # Labels
            if labels[i] and self.font_small:
                label_text = self.font_small.render(labels[i], True, (255, 255, 255))
                label_rect = label_text.get_rect()
                
                label_surface = pygame.Surface((label_rect.height, label_rect.width), pygame.SRCALPHA)
                label_surface.fill((0, 0, 0, 0))
                label_surface.blit(label_text, (0, 0))
                rotated = pygame.transform.rotate(label_surface, 90)
                
                label_x = x + bar_width // 2 - rotated.get_width() // 2
                label_y = bar_y + bar_height // 2 - rotated.get_height() // 2
                surface.blit(rotated, (label_x, label_y))
                
                num_label = self.font_large.render(f"0{i+1}", True, (255, 60, 140))
                num_x = x + bar_width // 2 - num_label.get_width() // 2
                num_y = bar_y + bar_height + 10
                surface.blit(num_label, (num_x, num_y))
        
        # Draw TWO cars moving RIGHT to LEFT
        vehicle_width = 400
        vehicle_height = 80
        vehicle_y = h - 150
        
        speed = 150 + 200 * self.rms
        offset = (self.t * speed) % (w + vehicle_width * 2.5)
        
        car_positions = [
            w - offset,
            w - offset + vehicle_width * 1.8
        ]
        
        for car_idx, vehicle_x in enumerate(car_positions):
            if vehicle_x < -vehicle_width or vehicle_x > w + 50:
                continue
            
            body_rect = pygame.Rect(int(vehicle_x), vehicle_y, vehicle_width, vehicle_height)
            pygame.draw.rect(surface, (0, 0, 0), body_rect)
            pygame.draw.rect(surface, (255, 255, 255), body_rect, 3)
            
            # Windshield
            windshield_width = 100
            windshield_height = 50
            windshield_x = int(vehicle_x + vehicle_width - 120)
            windshield_y = vehicle_y - 15
            windshield_points = [
                (windshield_x, windshield_y + windshield_height),
                (windshield_x + 20, windshield_y),
                (windshield_x + windshield_width, windshield_y),
                (windshield_x + windshield_width, windshield_y + windshield_height)
            ]
            pygame.draw.polygon(surface, (255, 100, 180), windshield_points)
            pygame.draw.polygon(surface, (255, 255, 255), windshield_points, 2)
            
            # Windows
            window_rects = [
                pygame.Rect(int(vehicle_x + 50), vehicle_y + 15, 60, 50),
                pygame.Rect(int(vehicle_x + 130), vehicle_y + 15, 60, 50),
                pygame.Rect(int(vehicle_x + 210), vehicle_y + 15, 60, 50),
            ]
            for rect in window_rects:
                pygame.draw.rect(surface, (255, 140, 200), rect)
                pygame.draw.rect(surface, (255, 255, 255), rect, 2)
            
            # Driver
            driver_x = int(windshield_x + 40)
            driver_y = int(windshield_y + 25)
            pygame.draw.circle(surface, (0, 0, 0), (driver_x, driver_y), 10)
            pygame.draw.circle(surface, (255, 255, 255), (driver_x, driver_y), 10, 2)
            
            # Passengers
            for rect in window_rects:
                passenger_x = int(rect.centerx)
                passenger_y = int(rect.centery - 5)
                pygame.draw.circle(surface, (0, 0, 0), (passenger_x, passenger_y), 8)
                pygame.draw.circle(surface, (255, 255, 255), (passenger_x, passenger_y), 8, 2)
            
            # Wheels
            wheel_positions = [
                (int(vehicle_x + 70), vehicle_y + vehicle_height),
                (int(vehicle_x + vehicle_width - 70), vehicle_y + vehicle_height)
            ]
            wheel_radius = 35
            for wx, wy in wheel_positions:
                wx_int = int(wx)
                wy_int = int(wy)
                pygame.draw.circle(surface, (0, 0, 0), (wx_int, wy_int), wheel_radius)
                pygame.draw.circle(surface, (255, 255, 255), (wx_int, wy_int), wheel_radius, 3)
                pygame.draw.circle(surface, (255, 100, 180), (wx_int, wy_int), wheel_radius - 10)
                pygame.draw.circle(surface, (255, 255, 255), (wx_int, wy_int), wheel_radius - 10, 2)
                
                rotation = (self.t * 500) % 360
                for spoke in range(4):
                    angle = rotation + spoke * 90
                    rad = np.radians(angle)
                    end_x = wx_int + np.cos(rad) * (wheel_radius - 15)
                    end_y = wy_int + np.sin(rad) * (wheel_radius - 15)
                    pygame.draw.line(surface, (255, 255, 255), (wx_int, wy_int), (int(end_x), int(end_y)), 2)
            
            # Dancers on roof
            roof_y = vehicle_y - 10
            num_dancers = 3
            dancer_spacing = 80
            start_dancer_x = vehicle_x + vehicle_width // 2 - (num_dancers * dancer_spacing) // 2
            
            for i in range(num_dancers):
                dx = int(start_dancer_x + i * dancer_spacing)
                dy = roof_y
                
                phase = self.t * 8 + i * 2 + car_idx * 3
                bounce = np.sin(phase) * (15 + self.onset * 25)
                dy -= int(bounce)
                
                arm_angle = np.sin(phase) * 30
                leg_angle = np.sin(phase + np.pi) * 20
                
                self._draw_stick_figure(surface, dx, dy, arm_angle, leg_angle)
        
        # Road
        road_y = h - 40
        pygame.draw.rect(surface, (100, 0, 50), (0, road_y, w, 40))
        
        dash_width = 60
        dash_spacing = 40
        dash_offset = int((self.t * 200) % (dash_width + dash_spacing))
        for x in range(-dash_width, w, dash_width + dash_spacing):
            dash_x = x - dash_offset
            pygame.draw.rect(surface, (255, 100, 180), (dash_x, road_y + 15, dash_width, 10))
        
        # Now playing text
        if self.font_large:
            text = "NOW PLAYING: HIGH-RETRO VISION"
            text_surface = self.font_large.render(text, True, (255, 60, 140))
            text_outline = self.font_large.render(text, True, (0, 0, 0))
            
            text_x = 20
            text_y = h - 30
            
            for offset_x, offset_y in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                surface.blit(text_outline, (text_x + offset_x, text_y + offset_y))
            surface.blit(text_surface, (text_x, text_y))

    @staticmethod
    def _draw_stick_figure(surface, x, y, arm_angle, leg_angle):
        """Draw an animated stick figure dancer."""
        color = (255, 255, 255)
        
        # Head
        pygame.draw.circle(surface, color, (x, y), 12)
        pygame.draw.circle(surface, (0, 0, 0), (x, y), 10)
        
        # Body
        body_length = 35
        pygame.draw.line(surface, color, (x, y + 12), (x, y + 12 + body_length), 4)
        
        # Arms
        arm_length = 25
        arm_y = y + 20
        left_arm_x = x - np.cos(np.radians(arm_angle)) * arm_length
        left_arm_y = arm_y + np.sin(np.radians(arm_angle)) * arm_length
        right_arm_x = x + np.cos(np.radians(arm_angle)) * arm_length
        right_arm_y = arm_y - np.sin(np.radians(arm_angle)) * arm_length
        
        pygame.draw.line(surface, color, (x, arm_y), (int(left_arm_x), int(left_arm_y)), 4)
        pygame.draw.line(surface, color, (x, arm_y), (int(right_arm_x), int(right_arm_y)), 4)
        
        # Legs
        leg_length = 30
        hip_y = y + 12 + body_length
        left_leg_x = x - 10 - np.sin(np.radians(leg_angle)) * 5
        left_leg_y = hip_y + leg_length
        right_leg_x = x + 10 + np.sin(np.radians(leg_angle)) * 5
        right_leg_y = hip_y + leg_length
        
        pygame.draw.line(surface, color, (x - 5, hip_y), (int(left_leg_x), int(left_leg_y)), 4)
        pygame.draw.line(surface, color, (x + 5, hip_y), (int(right_leg_x), int(right_leg_y)), 4)
