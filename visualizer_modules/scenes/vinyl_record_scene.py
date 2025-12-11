import pygame
import numpy as np
import math
from visualizer_modules.audio_analyzer import AudioFeatures
from visualizer_modules.scenes.base_scene import BaseScene


class VinylRecordScene(BaseScene):
    """
    Vinyl record visualization with spinning disc, reactive grooves,
    dust particles, and beat-synchronized effects.
    """
    
    def __init__(self, size):
        super().__init__(size)
        
        # Record properties
        self.record_radius = min(self.width, self.height) * 0.35
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.rotation = 0
        self.rpm = 33.33  # Standard vinyl speed
        self.angular_velocity = (self.rpm / 60) * 2 * math.pi
        
        # Label properties (center circle)
        self.label_radius = self.record_radius * 0.3
        
        # Groove properties
        self.num_grooves = 60
        self.groove_intensity = 0
        self.groove_wobble = 0
        
        # Beat reaction
        self.beat_scale = 1.0
        self.beat_flash = 0
        
        # Particles (dust on record)
        self.particles = []
        self.max_particles = 150
        self._init_particles()
        
        # Scratch effects
        self.scratches = []
        self.scratch_timer = 0
        
        # Glow effect
        self.glow_intensity = 0
        
    def _init_particles(self):
        """Initialize dust particles on the record."""
        for _ in range(self.max_particles):
            angle = np.random.uniform(0, 2 * math.pi)
            distance = np.random.uniform(self.label_radius, self.record_radius)
            self.particles.append({
                'angle': angle,
                'distance': distance,
                'size': np.random.uniform(1, 3),
                'speed': np.random.uniform(0.5, 1.5),
                'opacity': np.random.uniform(100, 255)
            })
    
    def enter(self):
        """Called when scene becomes active."""
        self.rotation = 0
        self.scratches = []
        
    def exit(self):
        """Called when scene is left."""
        pass
    
    def update(self, dt: float, t: float, features: AudioFeatures, idx: int):
        """Update scene state based on audio features."""
        # Get current audio features
        rms = features.rms[idx] if idx < len(features.rms) else 0
        treble = features.treble[idx] if idx < len(features.treble) else 0
        bass = features.bass[idx] if idx < len(features.bass) else 0
        onset = features.onset[idx] if idx < len(features.onset) else 0
        
        # Features are already normalized 0-1 from the analyzer
        rms_norm = rms
        treble_norm = treble
        bass_norm = bass
        
        # Update rotation (constant spin)
        self.rotation += self.angular_velocity * dt
        self.rotation = self.rotation % (2 * math.pi)
        
        # Groove intensity based on RMS
        self.groove_intensity = rms_norm * 15
        
        # Groove wobble based on treble (high frequencies)
        self.groove_wobble = treble_norm * 5
        
        # Beat detection (simple threshold on RMS change)
        if idx > 0 and idx < len(features.rms):
            rms_delta = features.rms[idx] - features.rms[idx - 1]
            if rms_delta > 0.05:
                self.beat_scale = 1.15
                self.beat_flash = 1.0
                
                # Add scratch on strong beats
                if rms_delta > 0.1:
                    self._add_scratch()
        
        # Decay beat effects
        self.beat_scale = max(1.0, self.beat_scale - dt * 2)
        self.beat_flash = max(0, self.beat_flash - dt * 3)
        
        # Update glow based on overall intensity
        self.glow_intensity = rms_norm * 0.8
        
        # Update particles
        for particle in self.particles:
            # Particles rotate with the record
            particle['angle'] += self.angular_velocity * dt * particle['speed']
            particle['angle'] = particle['angle'] % (2 * math.pi)
            
            # Particles pulse slightly with music
            particle['opacity'] = np.clip(
                150 + rms_norm * 105 + np.random.uniform(-20, 20),
                50, 255
            )
        
        # Update scratches
        self.scratch_timer -= dt
        self.scratches = [s for s in self.scratches if s['life'] > 0]
        for scratch in self.scratches:
            scratch['life'] -= dt * 0.5
            scratch['opacity'] = int(255 * scratch['life'])
    
    def _add_scratch(self):
        """Add a scratch effect on beat."""
        if len(self.scratches) < 5:
            angle = np.random.uniform(0, 2 * math.pi)
            self.scratches.append({
                'angle': angle,
                'start_radius': self.label_radius,
                'end_radius': self.record_radius,
                'life': 1.0,
                'opacity': 255
            })
    
    def draw(self, surface: pygame.Surface):
        """Draw the vinyl record scene."""
        # Clear background
        surface.fill((15, 10, 20))
        
        # Draw outer glow
        if self.glow_intensity > 0:
            self._draw_glow(surface)
        
        # Draw record shadow
        shadow_offset = 8
        pygame.draw.circle(
            surface,
            (5, 5, 5),
            (self.center_x + shadow_offset, self.center_y + shadow_offset),
            int(self.record_radius * self.beat_scale),
            0
        )
        
        # Draw main record
        record_radius = int(self.record_radius * self.beat_scale)
        pygame.draw.circle(
            surface,
            (25, 25, 25),
            (self.center_x, self.center_y),
            record_radius,
            0
        )
        
        # Draw grooves
        self._draw_grooves(surface, record_radius)
        
        # Draw scratches
        self._draw_scratches(surface)
        
        # Draw particles (dust)
        self._draw_particles(surface)
        
        # Draw center label
        self._draw_label(surface)
        
        # Draw center hole
        pygame.draw.circle(
            surface,
            (10, 10, 10),
            (self.center_x, self.center_y),
            int(self.label_radius * 0.15),
            0
        )
        
        # Beat flash overlay
        if self.beat_flash > 0:
            flash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_alpha = int(self.beat_flash * 30)
            pygame.draw.circle(
                flash_surface,
                (255, 255, 255, flash_alpha),
                (self.center_x, self.center_y),
                record_radius,
                0
            )
            surface.blit(flash_surface, (0, 0))
    
    def _draw_glow(self, surface):
        """Draw glow effect around record."""
        glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        glow_radius = int(self.record_radius * 1.2)
        glow_alpha = int(self.glow_intensity * 40)
        
        # Draw gradient glow
        for i in range(3):
            radius = glow_radius + i * 20
            alpha = max(0, glow_alpha - i * 15)
            pygame.draw.circle(
                glow_surface,
                (100, 50, 150, alpha),
                (self.center_x, self.center_y),
                radius,
                15
            )
        
        surface.blit(glow_surface, (0, 0))
    
    def _draw_grooves(self, surface, record_radius):
        """Draw reactive grooves on the record."""
        groove_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for i in range(self.num_grooves):
            # Calculate groove radius
            radius_ratio = (i / self.num_grooves)
            groove_radius = int(self.label_radius + (record_radius - self.label_radius) * radius_ratio)
            
            # Groove intensity creates thickness variation
            intensity_factor = 1 + math.sin(i * 0.5 + self.rotation * 5) * 0.3 * (self.groove_intensity / 15)
            
            # Wobble creates wave effect
            wobble_offset = math.sin(i * 0.3 + self.rotation * 3) * self.groove_wobble
            
            # Color varies with intensity
            brightness = 35 + int(self.groove_intensity * 2)
            color = (brightness, brightness, brightness, 180)
            
            # Draw groove circle with wobble
            pygame.draw.circle(
                groove_surface,
                color,
                (self.center_x + int(wobble_offset), self.center_y),
                groove_radius,
                max(1, int(intensity_factor))
            )
        
        surface.blit(groove_surface, (0, 0))
    
    def _draw_scratches(self, surface):
        """Draw scratch effects."""
        if not self.scratches:
            return
            
        scratch_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for scratch in self.scratches:
            # Draw radial scratch line
            start_x = self.center_x + math.cos(scratch['angle'] + self.rotation) * scratch['start_radius']
            start_y = self.center_y + math.sin(scratch['angle'] + self.rotation) * scratch['start_radius']
            end_x = self.center_x + math.cos(scratch['angle'] + self.rotation) * scratch['end_radius']
            end_y = self.center_y + math.sin(scratch['angle'] + self.rotation) * scratch['end_radius']
            
            # Ensure opacity is valid (0-255)
            opacity = max(0, min(255, int(scratch['opacity'])))
            
            pygame.draw.line(
                scratch_surface,
                (255, 200, 100, opacity),
                (int(start_x), int(start_y)),
                (int(end_x), int(end_y)),
                3
            )
        
        surface.blit(scratch_surface, (0, 0))
    
    def _draw_particles(self, surface):
        """Draw dust particles on the record."""
        particle_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for particle in self.particles:
            # Calculate particle position (rotates with record)
            x = self.center_x + math.cos(particle['angle'] + self.rotation) * particle['distance'] * self.beat_scale
            y = self.center_y + math.sin(particle['angle'] + self.rotation) * particle['distance'] * self.beat_scale
            
            # Draw particle with glow
            opacity = int(particle['opacity'])
            size = particle['size']
            
            # Outer glow
            pygame.draw.circle(
                particle_surface,
                (200, 200, 220, opacity // 3),
                (int(x), int(y)),
                int(size * 2),
                0
            )
            
            # Inner particle
            pygame.draw.circle(
                particle_surface,
                (255, 255, 255, opacity),
                (int(x), int(y)),
                int(size),
                0
            )
        
        surface.blit(particle_surface, (0, 0))
    
    def _draw_label(self, surface):
        """Draw center label."""
        label_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Label background
        pygame.draw.circle(
            label_surface,
            (180, 40, 40, 230),
            (self.center_x, self.center_y),
            int(self.label_radius * self.beat_scale),
            0
        )
        
        # Label ring
        pygame.draw.circle(
            label_surface,
            (220, 180, 60, 255),
            (self.center_x, self.center_y),
            int(self.label_radius * self.beat_scale),
            3
        )
        
        # Inner ring
        pygame.draw.circle(
            label_surface,
            (220, 180, 60, 200),
            (self.center_x, self.center_y),
            int(self.label_radius * 0.7 * self.beat_scale),
            2
        )
        
        # Text lines (spinning with record)
        num_lines = 8
        for i in range(num_lines):
            angle = self.rotation + (i * 2 * math.pi / num_lines)
            inner_r = self.label_radius * 0.5
            outer_r = self.label_radius * 0.65
            
            x1 = self.center_x + math.cos(angle) * inner_r
            y1 = self.center_y + math.sin(angle) * inner_r
            x2 = self.center_x + math.cos(angle) * outer_r
            y2 = self.center_y + math.sin(angle) * outer_r
            
            pygame.draw.line(
                label_surface,
                (100, 80, 20, 150),
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                2
            )
        
        surface.blit(label_surface, (0, 0))