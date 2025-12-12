import pygame
import numpy as np
import math
from visualizer_modules.audio_analyzer import AudioFeatures
from visualizer_modules.scenes.base_scene import BaseScene


class PsychEngineChartScene(BaseScene):
    """
    Friday Night Funkin' / Psych Engine chart visualizer.
    Shows falling notes in 4 lanes with receptors at the bottom.
    """
    
    def __init__(self, size, chart_data=None):
        """
        Initialize the chart scene.
        
        Args:
            size: Tuple of (width, height)
            chart_data: ChartData object from ChartLoader (optional)
        """
        super().__init__(size)
        
        # Chart data
        self.chart_data = chart_data
        self.bpm = chart_data.bpm if chart_data else 174
        self.scroll_speed = chart_data.scroll_speed if chart_data else 3.1
        
        # Visual settings
        self.note_width = 80
        self.note_height = 20
        self.lane_spacing = 100
        self.receptor_y = self.height - 150
        self.scroll_speed_pixels = 900  # Pixels per second
        
        # Colors for each lane (DFJK / Left Down Up Right)
        self.lane_colors = [
            (194, 75, 153),   # Purple (Left)
            (0, 255, 255),    # Cyan (Down)
            (18, 250, 5),     # Green (Up)
            (249, 57, 63)     # Red (Right)
        ]
        
        # Beat tracking
        self.current_beat = 0
        self.beat_time = 0
        self.beat_pulse = 0
        
        # Active notes (visible on screen)
        self.active_notes = []
        
        # Hit effects
        self.hit_flashes = [0, 0, 0, 0]
        self.hit_notes = set()  # Track which notes have been hit
        
        # Background
        self.bg_color = (20, 20, 35)
        
        # Receptor positions
        self.receptor_positions = self._calculate_receptor_positions()
        
    def _calculate_receptor_positions(self):
        """Calculate X positions for the 4 receptors."""
        total_width = 3 * self.lane_spacing
        start_x = (self.width - total_width) // 2
        return [start_x + i * self.lane_spacing for i in range(4)]
    
    def enter(self):
        """Called when scene becomes active."""
        self.current_beat = 0
        self.beat_time = 0
        self.hit_notes.clear()
    
    def exit(self):
        """Called when scene is left."""
        pass
    
    def update(self, dt: float, t: float, features: AudioFeatures, idx: int):
        """Update scene state based on time and audio features."""
        # Get current audio features
        rms = features.rms[idx] if idx < len(features.rms) else 0
        bass = features.bass[idx] if idx < len(features.bass) else 0
        onset = features.onset[idx] if idx < len(features.onset) else 0
        
        # Calculate current beat
        beat_duration = 60.0 / self.bpm
        self.current_beat = t / beat_duration
        self.beat_time = (t % beat_duration) / beat_duration
        
        # Beat pulse effect (zooms receptors on beat)
        if self.beat_time < 0.1:
            self.beat_pulse = 1.0 - (self.beat_time / 0.1)
        else:
            self.beat_pulse = max(0, self.beat_pulse - dt * 5)
        
        # Update active notes if we have chart data
        if self.chart_data:
            lookahead_time = 2.0  # Show notes 2 seconds ahead
            self.active_notes = self.chart_data.get_notes_in_range(
                t - 0.5,
                t + lookahead_time,
                player_only=True
            )
            
            # Check for "hits" (when notes pass the receptor)
            hit_threshold = 0.1  # 100ms hit window
            for note in self.active_notes:
                note_id = id(note)
                if note_id not in self.hit_notes and abs(note.time - t) < hit_threshold:
                    self.hit_notes.add(note_id)
                    self.hit_flashes[note.lane] = 1.0
        
        # Decay hit flashes
        for i in range(4):
            self.hit_flashes[i] = max(0, self.hit_flashes[i] - dt * 4)
    
    def draw(self, surface: pygame.Surface):
        """Draw the FNF-style chart visualization."""
        # Clear background
        surface.fill(self.bg_color)
        
        # Draw grid lines (beat lines)
        self._draw_grid(surface)
        
        # Draw lanes
        self._draw_lanes(surface)
        
        # Draw notes
        if self.chart_data:
            self._draw_notes(surface)
        
        # Draw receptors
        self._draw_receptors(surface)
        
        # Draw hit effects
        self._draw_hit_effects(surface)
        
        # Draw info text
        self._draw_info(surface)
    
    def _draw_grid(self, surface):
        """Draw background grid lines for beats."""
        beat_duration = 60.0 / self.bpm
        
        # Draw horizontal lines for each beat
        for i in range(-5, 20):
            beat_offset = i - self.beat_time
            y = self.receptor_y - (beat_offset * beat_duration * self.scroll_speed_pixels)
            
            if 0 <= y <= self.height:
                # Emphasize measure lines (every 4 beats)
                if i % 4 == 0:
                    color = (60, 60, 80)
                    thickness = 2
                else:
                    color = (40, 40, 55)
                    thickness = 1
                
                pygame.draw.line(
                    surface,
                    color,
                    (0, int(y)),
                    (self.width, int(y)),
                    thickness
                )
    
    def _draw_lanes(self, surface):
        """Draw the 4 lanes with subtle shading."""
        for i in range(4):
            x = self.receptor_positions[i]
            
            # Draw lane background
            lane_rect = pygame.Rect(
                x - self.note_width // 2,
                0,
                self.note_width,
                self.height
            )
            
            # Subtle lane color
            color = tuple(int(c * 0.15) for c in self.lane_colors[i])
            pygame.draw.rect(surface, color, lane_rect)
            
            # Lane borders
            pygame.draw.line(
                surface,
                (50, 50, 65),
                (x - self.note_width // 2, 0),
                (x - self.note_width // 2, self.height),
                1
            )
    
    def _draw_notes(self, surface):
        """Draw falling notes."""
        current_time = self.current_beat * (60.0 / self.bpm)
        
        for note in self.active_notes:
            lane = note.lane
            x = self.receptor_positions[lane]
            
            # Calculate Y position based on time until hit
            time_until_hit = note.time - current_time
            y = self.receptor_y - (time_until_hit * self.scroll_speed_pixels)
            
            # Skip if off screen
            if y < -50 or y > self.height + 50:
                continue
            
            # Check if note has been hit
            note_hit = id(note) in self.hit_notes
            
            # Note color (brighter if about to hit)
            if note_hit:
                # Faded after hit
                color = tuple(int(c * 0.3) for c in self.lane_colors[lane])
            elif abs(time_until_hit) < 0.1:
                # Bright when in hit window
                color = tuple(min(255, int(c * 1.3)) for c in self.lane_colors[lane])
            else:
                color = self.lane_colors[lane]
            
            # Draw note head
            note_rect = pygame.Rect(
                x - self.note_width // 2,
                int(y - self.note_height // 2),
                self.note_width,
                self.note_height
            )
            
            pygame.draw.rect(surface, color, note_rect, border_radius=5)
            pygame.draw.rect(surface, (255, 255, 255), note_rect, 2, border_radius=5)
            
            # Draw sustain tail if present
            if note.sustain > 0:
                sustain_height = note.sustain * self.scroll_speed_pixels
                sustain_rect = pygame.Rect(
                    x - self.note_width // 4,
                    int(y),
                    self.note_width // 2,
                    int(sustain_height)
                )
                
                # Sustain color (semi-transparent)
                sustain_surface = pygame.Surface(
                    (sustain_rect.width, sustain_rect.height),
                    pygame.SRCALPHA
                )
                sustain_color = (*color, 150)
                pygame.draw.rect(
                    sustain_surface,
                    sustain_color,
                    sustain_surface.get_rect(),
                    border_radius=3
                )
                surface.blit(sustain_surface, sustain_rect)
    
    def _draw_receptors(self, surface):
        """Draw receptor arrows at the bottom."""
        # Arrow directions: Left, Down, Up, Right
        arrows = ['←', '↓', '↑', '→']
        
        for i in range(4):
            x = self.receptor_positions[i]
            y = self.receptor_y
            
            # Pulse effect on beat
            scale = 1.0 + (self.beat_pulse * 0.15)
            size = int(self.note_width * scale)
            
            # Receptor background
            receptor_rect = pygame.Rect(
                x - size // 2,
                y - size // 2,
                size,
                size
            )
            
            # Color (brighter on hit flash)
            if self.hit_flashes[i] > 0:
                color = tuple(min(255, int(c * (1 + self.hit_flashes[i]))) for c in self.lane_colors[i])
            else:
                color = tuple(int(c * 0.6) for c in self.lane_colors[i])
            
            pygame.draw.rect(surface, color, receptor_rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), receptor_rect, 3, border_radius=8)
            
            # Draw arrow
            font = pygame.font.Font(None, int(size * 0.8))
            arrow_text = font.render(arrows[i], True, (255, 255, 255))
            arrow_rect = arrow_text.get_rect(center=(x, y))
            surface.blit(arrow_text, arrow_rect)
    
    def _draw_hit_effects(self, surface):
        """Draw hit splash effects."""
        for i in range(4):
            if self.hit_flashes[i] > 0:
                x = self.receptor_positions[i]
                y = self.receptor_y
                
                # Expanding circle effect
                radius = int(self.note_width * (1 - self.hit_flashes[i]) * 1.5)
                alpha = int(self.hit_flashes[i] * 255)
                
                splash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                color = (*self.lane_colors[i], alpha)
                pygame.draw.circle(
                    splash_surface,
                    color,
                    (x, y),
                    radius,
                    5
                )
                surface.blit(splash_surface, (0, 0))
    
    def _draw_info(self, surface):
        """Draw info text (BPM, notes, etc.)."""
        font = pygame.font.Font(None, 36)
        
        # BPM display
        bpm_text = font.render(f"BPM: {self.bpm}", True, (200, 200, 200))
        surface.blit(bpm_text, (20, 20))
        
        if self.chart_data:
            # Note count
            total_notes = len(self.chart_data.player_notes)
            notes_text = font.render(f"Notes: {total_notes}", True, (200, 200, 200))
            surface.blit(notes_text, (20, 60))
            
            # Active notes count
            active_text = font.render(f"Active: {len(self.active_notes)}", True, (150, 150, 150))
            surface.blit(active_text, (20, 100))