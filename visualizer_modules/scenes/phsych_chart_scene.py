import pygame
from visualizer_modules.audio_analyzer import AudioFeatures
from visualizer_modules.scenes.base_scene import BaseScene


class PsychEngineChartScene(BaseScene):
    """
    Friday Night Funkin' / Psych Engine–style chart visualizer.
    Notes scroll upward and are hit at the top.
    """

    def __init__(self, size, chart_data=None):
        super().__init__(size)

        # Chart data
        self.chart_data = chart_data
        self.bpm = chart_data.bpm if chart_data else 174
        self.scroll_speed = chart_data.scroll_speed if chart_data else 3.1

        # Visual settings
        self.note_width = 80
        self.note_height = 20
        self.lane_spacing = 100
        self.receptor_y = 120
        self.scroll_speed_pixels = 900

        # Timing (IMPORTANT)
        self.beat_duration = 60.0 / self.bpm
        self.audio_offset = 0.08  # seconds (tune this)

        # Colors (Left, Down, Up, Right)
        self.lane_colors = [
            (194, 75, 153),
            (0, 255, 255),
            (18, 250, 5),
            (249, 57, 63),
        ]

        # Beat state
        self.current_beat = 0.0
        self.beat_time = 0.0
        self.beat_pulse = 0.0

        # Notes
        self.active_notes = []
        self.hit_notes = set()
        self.hit_flashes = [0.0, 0.0, 0.0, 0.0]

        # Background
        self.bg_color = (20, 20, 35)

        # Positions
        self.receptor_positions = self._calculate_receptor_positions()

        # Fonts (cached)
        self.info_font = pygame.font.Font(None, 36)
        self.arrow_font = pygame.font.Font(None, int(self.note_width * 0.8))

    def _calculate_receptor_positions(self):
        total_width = 3 * self.lane_spacing
        start_x = (self.width - total_width) // 2
        return [start_x + i * self.lane_spacing for i in range(4)]

    def enter(self):
        self.current_beat = 0.0
        self.beat_time = 0.0
        self.beat_pulse = 0.0
        self.hit_notes.clear()

    def exit(self):
        pass

    def update(self, dt: float, t: float, features: AudioFeatures, idx: int):
        # Audio-aligned time
        visual_time = t - self.audio_offset

        # Beat timing
        self.current_beat = visual_time / self.beat_duration
        self.beat_time = (visual_time % self.beat_duration) / self.beat_duration

        # Beat pulse
        if self.beat_time < 0.1:
            self.beat_pulse = 1.0 - (self.beat_time / 0.1)
        else:
            self.beat_pulse = max(0.0, self.beat_pulse - dt * 5.0)

        # Notes
        if self.chart_data:
            self.active_notes = self.chart_data.get_notes_in_range(
                visual_time - 0.5,
                visual_time + 2.0,
                player_only=True
            )

            hit_window = 0.1
            for note in self.active_notes:
                nid = id(note)
                if nid in self.hit_notes:
                    continue

                if abs(note.time - visual_time) <= hit_window:
                    self.hit_notes.add(nid)
                    self.hit_flashes[note.lane] = 1.0

        # Flash decay
        for i in range(4):
            self.hit_flashes[i] = max(0.0, self.hit_flashes[i] - dt * 4.0)

    def draw(self, surface: pygame.Surface):
        surface.fill(self.bg_color)

        self._draw_grid(surface)
        self._draw_lanes(surface)

        if self.chart_data:
            self._draw_notes(surface)

        self._draw_receptors(surface)
        self._draw_hit_effects(surface)
        self._draw_info(surface)

    def _draw_grid(self, surface):
        for i in range(-5, 20):
            beat_offset = i - self.beat_time
            y = self.receptor_y + (
                beat_offset * self.beat_duration * self.scroll_speed_pixels
            )

            if 0 <= y <= self.height:
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
        half_w = self.note_width // 2
        for i, x in enumerate(self.receptor_positions):
            lane_rect = pygame.Rect(x - half_w, 0, self.note_width, self.height)
            color = tuple(int(c * 0.15) for c in self.lane_colors[i])
            pygame.draw.rect(surface, color, lane_rect)

            pygame.draw.line(
                surface,
                (50, 50, 65),
                (x - half_w, 0),
                (x - half_w, self.height),
                1
            )

    def _draw_notes(self, surface):
        visual_time = (self.current_beat * self.beat_duration)
        half_w = self.note_width // 2
        half_h = self.note_height // 2

        for note in self.active_notes:
            lane = note.lane
            x = self.receptor_positions[lane]

            time_until_hit = note.time - visual_time
            y = self.receptor_y + (time_until_hit * self.scroll_speed_pixels)

            if y < -50 or y > self.height + 50:
                continue

            nid = id(note)
            base_color = self.lane_colors[lane]

            if nid in self.hit_notes:
                color = tuple(int(c * 0.3) for c in base_color)
            elif abs(time_until_hit) < 0.1:
                color = tuple(min(255, int(c * 1.3)) for c in base_color)
            else:
                color = base_color

            note_rect = pygame.Rect(
                x - half_w,
                int(y - half_h),
                self.note_width,
                self.note_height
            )

            pygame.draw.rect(surface, color, note_rect, border_radius=5)
            pygame.draw.rect(surface, (255, 255, 255), note_rect, 2, border_radius=5)

            # Sustain tail (downward)
            if note.sustain > 0:
                sustain_h = int(note.sustain * self.scroll_speed_pixels)
                sustain_rect = pygame.Rect(
                    x - self.note_width // 4,
                    int(y),
                    self.note_width // 2,
                    sustain_h
                )

                pygame.draw.rect(surface, color, sustain_rect, border_radius=3)

    def _draw_receptors(self, surface):
        arrows = ['←', '↓', '↑', '→']

        for i, x in enumerate(self.receptor_positions):
            scale = 1.0 + (self.beat_pulse * 0.15)
            size = int(self.note_width * scale)
            y = self.receptor_y

            rect = pygame.Rect(x - size // 2, y - size // 2, size, size)

            if self.hit_flashes[i] > 0:
                mul = 1.0 + self.hit_flashes[i]
                color = tuple(min(255, int(c * mul)) for c in self.lane_colors[i])
            else:
                color = tuple(int(c * 0.6) for c in self.lane_colors[i])

            pygame.draw.rect(surface, color, rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), rect, 3, border_radius=8)

            arrow = self.arrow_font.render(arrows[i], True, (255, 255, 255))
            surface.blit(arrow, arrow.get_rect(center=(x, y)))

    def _draw_hit_effects(self, surface):
        for i, flash in enumerate(self.hit_flashes):
            if flash <= 0:
                continue

            radius = int(self.note_width * (1 - flash) * 1.5)
            alpha = int(flash * 200)

            if radius <= 0:
                continue

            circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                circle,
                (*self.lane_colors[i], alpha),
                (radius, radius),
                radius,
                5
            )

            x = self.receptor_positions[i] - radius
            y = self.receptor_y - radius
            surface.blit(circle, (x, y))

    def _draw_info(self, surface):
        bpm_text = self.info_font.render(f"BPM: {self.bpm}", True, (200, 200, 200))
        surface.blit(bpm_text, (20, 20))

        if self.chart_data:
            notes_text = self.info_font.render(
                f"Notes: {len(self.chart_data.player_notes)}",
                True,
                (200, 200, 200)
            )
            surface.blit(notes_text, (20, 60))

            active_text = self.info_font.render(
                f"Active: {len(self.active_notes)}",
                True,
                (150, 150, 150)
            )
            surface.blit(active_text, (20, 100))
