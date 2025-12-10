import numpy as np
import pygame
from visualizer_modules.scenes.base_scene import BaseScene
from visualizer_modules.audio_analyzer import AudioFeatures


class GraffitiRapperScene(BaseScene):
    """
    Urban graffiti style scene with animated rapper character.
    Features spray paint effects, barcode, arrow controls, and technical overlays.
    """
    
    def __init__(self, size):
        super().__init__(size)
        self.font_large = None
        self.font_small = None
        self.spray_particles = []
        
    def enter(self):
        self.font_large = pygame.font.SysFont("Impact", 48, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 24, bold=True)

    def update(self, dt, t, features: AudioFeatures, idx: int):
        self.rms = features.rms[idx]
        self.bass = features.bass[idx]
        self.mid = features.mid[idx]
        self.treble = features.treble[idx]
        self.onset = features.onset[idx]
        self.t = t
        
        if self.onset > 0.7:
            for _ in range(5):
                self.spray_particles.append({
                    'x': np.random.randint(200, 800),
                    'y': np.random.randint(200, 500),
                    'vx': np.random.uniform(-2, 2),
                    'vy': np.random.uniform(-3, 1),
                    'life': 1.0,
                    'size': np.random.randint(3, 8)
                })
        
        for particle in self.spray_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= dt * 2
            if particle['life'] <= 0:
                self.spray_particles.remove(particle)

    def draw_spray_background(self, surface):
        """Draw spray paint texture background."""
        w, h = self.width, self.height
        
        orange_base = (220, 120, 40)
        brown_accent = (150, 80, 40)
        
        num_sprays = 15
        for i in range(num_sprays):
            x = int(w * (0.3 + 0.6 * np.random.random()))
            y = int(h * (0.2 + 0.6 * np.random.random()))
            size = int(60 + 80 * np.random.random())
            
            for layer in range(3, 0, -1):
                alpha = 30 + layer * 20
                spray_surface = pygame.Surface((w, h), pygame.SRCALPHA)
                color = orange_base if i % 2 else brown_accent
                color_alpha = color + (alpha,)
                pygame.draw.circle(spray_surface, color_alpha, (x, y), size * layer // 3)
                surface.blit(spray_surface, (0, 0))
        
        diagonal_spacing = 40
        for i in range(-h, w, diagonal_spacing):
            start = (i, 0)
            end = (i + h, h)
            pygame.draw.line(surface, (180, 90, 30), start, end, 3)

    def draw_rapper_character(self, surface, center_x, center_y):
        """Draw animated rapper character in graffiti style."""
        bounce = np.sin(self.t * 8) * (10 + self.bass * 20)
        char_y = center_y - int(bounce)
        
        scale = 1.0 + self.onset * 0.15
        
        head_w = int(140 * scale)
        head_h = int(100 * scale)
        head_rect = pygame.Rect(0, 0, head_w, head_h)
        head_rect.center = (int(center_x), int(char_y - 80))
        
        pygame.draw.ellipse(surface, (255, 140, 60), head_rect)
        pygame.draw.ellipse(surface, (0, 0, 0), head_rect, 4)
        
        hair_points = [
            (head_rect.left, head_rect.top + 20),
            (head_rect.left - 30, head_rect.top - 20),
            (head_rect.centerx - 20, head_rect.top - 30),
            (head_rect.centerx + 20, head_rect.top - 35),
            (head_rect.right + 30, head_rect.top - 10),
            (head_rect.right, head_rect.top + 20)
        ]
        pygame.draw.polygon(surface, (255, 100, 30), hair_points)
        pygame.draw.polygon(surface, (0, 0, 0), hair_points, 4)
        
        eye_y = head_rect.centery - 10
        eye_spacing = 35
        for eye_x in [center_x - eye_spacing, center_x + eye_spacing]:
            pygame.draw.line(surface, (0, 0, 0), 
                           (int(eye_x - 15), int(eye_y)), 
                           (int(eye_x + 15), int(eye_y)), 5)
        
        mouth_y = head_rect.centery + 20
        mouth_points = [
            (int(center_x - 25), int(mouth_y)),
            (int(center_x - 15), int(mouth_y + 10)),
            (int(center_x + 15), int(mouth_y + 10)),
            (int(center_x + 25), int(mouth_y))
        ]
        pygame.draw.lines(surface, (0, 0, 0), False, mouth_points, 4)
        
        torso_w = int(120 * scale)
        torso_h = int(140 * scale)
        torso_rect = pygame.Rect(0, 0, torso_w, torso_h)
        torso_rect.center = (int(center_x), int(char_y + 40))
        
        pygame.draw.rect(surface, (255, 255, 255), torso_rect, border_radius=15)
        pygame.draw.rect(surface, (0, 0, 0), torso_rect, 4, border_radius=15)
        
        arm_angle_left = np.sin(self.t * 8) * 30
        arm_angle_right = np.sin(self.t * 8 + np.pi) * 30
        
        arm_length = 70
        left_shoulder = (torso_rect.left, torso_rect.top + 20)
        left_elbow = (
            int(left_shoulder[0] - arm_length * 0.7 * np.cos(np.radians(arm_angle_left))),
            int(left_shoulder[1] + arm_length * 0.5 + arm_length * 0.5 * np.sin(np.radians(arm_angle_left)))
        )
        left_hand = (
            int(left_elbow[0] - arm_length * 0.5),
            int(left_elbow[1] + arm_length * 0.3)
        )
        
        pygame.draw.line(surface, (255, 140, 60), left_shoulder, left_elbow, 12)
        pygame.draw.line(surface, (255, 140, 60), left_elbow, left_hand, 10)
        pygame.draw.line(surface, (0, 0, 0), left_shoulder, left_elbow, 3)
        pygame.draw.line(surface, (0, 0, 0), left_elbow, left_hand, 3)
        
        right_shoulder = (torso_rect.right, torso_rect.top + 20)
        right_elbow = (
            int(right_shoulder[0] + arm_length * 0.7 * np.cos(np.radians(arm_angle_right))),
            int(right_shoulder[1] + arm_length * 0.5 + arm_length * 0.5 * np.sin(np.radians(arm_angle_right)))
        )
        right_hand = (
            int(right_elbow[0] + arm_length * 0.5),
            int(right_elbow[1] + arm_length * 0.3)
        )
        
        pygame.draw.line(surface, (255, 140, 60), right_shoulder, right_elbow, 12)
        pygame.draw.line(surface, (255, 140, 60), right_elbow, right_hand, 10)
        pygame.draw.line(surface, (0, 0, 0), right_shoulder, right_elbow, 3)
        pygame.draw.line(surface, (0, 0, 0), right_elbow, right_hand, 3)
        
        pygame.draw.circle(surface, (0, 255, 200), 
                         (int(center_x - 20), torso_rect.centery), 
                         int(12 * (1 + self.bass * 0.3)))
        pygame.draw.circle(surface, (0, 0, 0), 
                         (int(center_x - 20), torso_rect.centery), 
                         int(12 * (1 + self.bass * 0.3)), 2)
        
        leg_spacing = 40
        leg_length = 80
        for leg_offset in [-leg_spacing, leg_spacing]:
            hip = (int(center_x + leg_offset), torso_rect.bottom)
            knee = (int(center_x + leg_offset), torso_rect.bottom + leg_length // 2)
            foot = (int(center_x + leg_offset + 15), torso_rect.bottom + leg_length)
            
            pygame.draw.line(surface, (255, 140, 60), hip, knee, 12)
            pygame.draw.line(surface, (255, 140, 60), knee, foot, 10)
            pygame.draw.line(surface, (0, 0, 0), hip, knee, 3)
            pygame.draw.line(surface, (0, 0, 0), knee, foot, 3)
            
            shoe_rect = pygame.Rect(foot[0] - 10, foot[1] - 5, 35, 15)
            pygame.draw.ellipse(surface, (50, 50, 50), shoe_rect)
            pygame.draw.ellipse(surface, (0, 0, 0), shoe_rect, 2)

    def draw(self, surface: pygame.Surface):
        surface.fill((200, 100, 30))
        
        w, h = self.width, self.height
        
        self.draw_spray_background(surface)
        
        for particle in self.spray_particles:
            alpha = int(255 * particle['life'])
            if alpha > 0:
                spray_surf = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                color = (255, 255, 255, alpha)
                pygame.draw.circle(spray_surf, color, (particle['size'], particle['size']), particle['size'])
                surface.blit(spray_surf, (int(particle['x']), int(particle['y'])))
        
        left_panel_w = 120
        left_panel_rect = pygame.Rect(10, 10, left_panel_w, h - 20)
        pygame.draw.rect(surface, (0, 0, 0), left_panel_rect)
        pygame.draw.rect(surface, (255, 140, 60), left_panel_rect, 4)
        
        if self.font_large:
            ng_text = self.font_large.render("NG", True, (255, 140, 60))
            ng_rect = ng_text.get_rect(center=(left_panel_rect.centerx, 100))
            
            glow_surf = pygame.Surface((ng_text.get_width() + 10, ng_text.get_height() + 10), pygame.SRCALPHA)
            glow_text = self.font_large.render("NG", True, (255, 140, 60, 100))
            glow_surf.blit(glow_text, (5, 5))
            surface.blit(glow_surf, (ng_rect.x - 5, ng_rect.y - 5))
            
            surface.blit(ng_text, ng_rect)
        
        icon_y = 200
        icon_size = 60
        icon_rect = pygame.Rect(left_panel_rect.centerx - icon_size // 2, icon_y, icon_size, icon_size)
        pygame.draw.rect(surface, (255, 140, 60), icon_rect, border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), icon_rect, 3, border_radius=10)
        
        barcode_y = h - 200
        barcode_w = left_panel_w - 20
        barcode_h = 80
        barcode_rect = pygame.Rect(left_panel_rect.centerx - barcode_w // 2, barcode_y, barcode_w, barcode_h)
        pygame.draw.rect(surface, (255, 255, 255), barcode_rect)
        
        num_bars = 30
        for i in range(num_bars):
            bar_w = barcode_w // num_bars
            if np.random.random() > 0.5:
                bar_x = barcode_rect.left + i * bar_w
                pygame.draw.rect(surface, (0, 0, 0), (bar_x, barcode_rect.top, bar_w // 2, barcode_h))
        
        if self.font_small:
            barcode_num = self.font_small.render("5 58008 10520 6", True, (0, 0, 0))
            surface.blit(barcode_num, (barcode_rect.left, barcode_rect.bottom + 5))
        
        char_x = w * 0.55
        char_y = h * 0.55
        self.draw_rapper_character(surface, char_x, char_y)
        
        top_right_x = int(w * 0.75)
        top_right_y = 40
        
        gun_diagram_w = 220
        gun_diagram_h = 120
        gun_rect = pygame.Rect(top_right_x, top_right_y, gun_diagram_w, gun_diagram_h)
        
        diagram_surf = pygame.Surface((gun_diagram_w, gun_diagram_h), pygame.SRCALPHA)
        diagram_surf.fill((255, 255, 255, 80))
        
        pygame.draw.line(diagram_surf, (255, 255, 255), (20, 60), (180, 60), 4)
        pygame.draw.rect(diagram_surf, (255, 255, 255), (150, 40, 40, 40), 2)
        pygame.draw.circle(diagram_surf, (255, 255, 255), (30, 60), 15, 2)
        
        for i in range(5):
            y = 15 + i * 20
            pygame.draw.line(diagram_surf, (255, 255, 255), (10, y), (200, y), 1)
            if self.font_small:
                label = pygame.font.SysFont("Arial", 10).render(str(i + 1), True, (255, 255, 255))
                diagram_surf.blit(label, (5, y - 5))
        
        surface.blit(diagram_surf, gun_rect)
        pygame.draw.rect(surface, (255, 255, 255), gun_rect, 2)
        
        circles_x = w - 150
        circles_y = 60
        circle_radius = 35
        circle_spacing = 90
        
        for i in range(4):
            cy = circles_y + i * circle_spacing
            pygame.draw.circle(surface, (255, 255, 255), (circles_x, cy), circle_radius, 4)
            pygame.draw.line(surface, (255, 255, 255), 
                           (circles_x - circle_radius + 10, cy - circle_radius + 10),
                           (circles_x + circle_radius - 10, cy + circle_radius - 10), 4)
        
        arrow_y = h - 80
        arrow_size = 40
        arrow_spacing = 80
        start_arrow_x = int(w * 0.3)
        
        arrows = ["◄", "▼", "◄", "▲"]
        
        for i, arrow in enumerate(arrows):
            arrow_x = start_arrow_x + i * arrow_spacing
            
            color = (255, 140, 60) if self.onset > 0.6 and i == int(self.t * 2) % 4 else (100, 60, 30)
            
            arrow_rect = pygame.Rect(arrow_x - arrow_size // 2, arrow_y - arrow_size // 2, arrow_size, arrow_size)
            pygame.draw.rect(surface, (0, 0, 0), arrow_rect, border_radius=5)
            pygame.draw.rect(surface, color, arrow_rect, 4, border_radius=5)
            
            if self.font_large:
                arrow_text = self.font_large.render(arrow, True, color)
                arrow_text_rect = arrow_text.get_rect(center=(arrow_x, arrow_y))
                surface.blit(arrow_text, arrow_text_rect)
