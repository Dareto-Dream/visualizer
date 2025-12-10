import time
import threading
from dataclasses import dataclass
from typing import List, Dict

import numpy as np
import pygame
import librosa
import sounddevice as sd


AUDIO_PATH = "powerdown.mp3"  # <-- change this to your audio file
WINDOW_SIZE = (1280, 720)
FPS = 60


# ---------------------- Audio Analysis ---------------------- #

@dataclass
class AudioFeatures:
    sr: int
    duration: float
    times: np.ndarray         # shape: (T,)
    rms: np.ndarray           # (T,)
    bass: np.ndarray          # (T,)
    mid: np.ndarray           # (T,)
    treble: np.ndarray        # (T,)
    onset: np.ndarray         # (T,)


def analyze_audio(path: str) -> AudioFeatures:
    print("[analysis] loading audio…")
    y, sr = librosa.load(path, sr=None, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # STFT
    hop_length = 512
    n_fft = 2048
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))  # (freq, time)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop_length)

    # RMS
    rms = librosa.feature.rms(S=S)[0]

    # Frequency bands
    def band_energy(fmin, fmax):
        idx = np.logical_and(freqs >= fmin, freqs < fmax)
        if not np.any(idx):
            return np.zeros(S.shape[1])
        band = S[idx, :]
        return band.mean(axis=0)

    bass = band_energy(20, 150)
    mid = band_energy(150, 2000)
    treble = band_energy(2000, 8000)

    # Onset strength
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    # Normalize to 0–1
    def norm(x):
        m = np.max(x)
        return x / m if m > 0 else x

    rms = norm(rms)
    bass = norm(bass)
    mid = norm(mid)
    treble = norm(treble)
    onset = norm(onset)

    print("[analysis] done.")
    return AudioFeatures(
        sr=sr,
        duration=duration,
        times=times,
        rms=rms,
        bass=bass,
        mid=mid,
        treble=treble,
        onset=onset
    )


# ---------------------- Audio Playback ---------------------- #

def play_audio_blocking(path: str):
    """Plays audio using sounddevice; run in a thread so pygame loop can run."""
    y, sr = librosa.load(path, sr=None, mono=True)
    sd.play(y, sr)
    sd.wait()


# ---------------------- Scene System ------------------------ #

class BaseScene:
    def __init__(self, size):
        self.width, self.height = size

    def enter(self):
        """Called when scene becomes active."""
        pass

    def exit(self):
        """Called when scene is left."""
        pass

    def update(self, dt: float, t: float, features: AudioFeatures, idx: int):
        """dt: frame delta, t: song time, idx: feature frame index."""
        raise NotImplementedError

    def draw(self, surface: pygame.Surface):
        raise NotImplementedError


class StripesScene(BaseScene):
    """
    Vertical stripes + moving 'cars' reacting to band energies.
    Inspired by the first reference screen.
    """

    def update(self, dt, t, features: AudioFeatures, idx: int):
        self.rms = features.rms[idx]
        self.bass = features.bass[idx]
        self.mid = features.mid[idx]
        self.treble = features.treble[idx]
        self.onset = features.onset[idx]

    def draw(self, surface: pygame.Surface):
        surface.fill((15, 0, 25))

        w, h = self.width, self.height
        stripe_count = 5
        stripe_w = w // (stripe_count + 2)
        margin_x = (w - stripe_count * stripe_w) // 2

        # Background stripes
        for i in range(stripe_count):
            x = margin_x + i * stripe_w
            # brightness per band
            if i == 0:
                v = self.bass
                color = (255, 80, 150)
            elif i == 1:
                v = self.mid
                color = (255, 120, 180)
            elif i == 2:
                v = self.treble
                color = (255, 200, 255)
            else:
                v = self.rms
                color = (255, 100, 200)

            # stripe height modulation
            height = int(h * (0.3 + 0.6 * v))
            rect = pygame.Rect(x, h - height, stripe_w - 10, height)
            pygame.draw.rect(surface, color, rect)

            # fake waveform line inside stripe
            line_y_center = h - height // 2
            points = []
            segments = 32
            for k in range(segments):
                px = x + 5 + (stripe_w - 20) * (k / (segments - 1))
                noise = np.sin((k * 0.7) + time.time() * 8) * 15 * v
                py = line_y_center + noise
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(surface, (0, 0, 0), False, points, 2)

        # Two "cars"
        base_y = int(h * 0.72)
        car_len = int(w * 0.26)
        car_h = int(h * 0.12)

        speed = 60 + 180 * self.rms
        offset = (time.time() * speed) % (w + car_len)

        for i in range(2):
            x = int((w + car_len) - offset - i * (car_len * 0.8))
            car_rect = pygame.Rect(x, base_y, car_len, car_h)
            pygame.draw.rect(surface, (0, 0, 0), car_rect, border_radius=10)
            pygame.draw.rect(surface, (255, 80, 160), car_rect, 4, border_radius=10)

            # wheels
            wheel_r = car_h // 4
            for k in range(2):
                cx = x + int(car_len * (0.25 + 0.45 * k))
                cy = base_y + car_h + wheel_r - 4
                pygame.draw.circle(surface, (0, 0, 0), (cx, cy), wheel_r)
                pygame.draw.circle(surface, (255, 255, 255), (cx, cy), wheel_r - 4, 2)

        # Jumping stick figures on top reacting to onset
        jump_amp = 20 + self.onset * 80
        for i in range(4):
            fx = w * 0.2 + i * 80
            fy = base_y - 40 - (np.sin(time.time() * 8 + i) * jump_amp)
            self._draw_stick(surface, int(fx), int(fy))

    @staticmethod
    def _draw_stick(surface, x, y):
        color = (255, 255, 255)
        # head
        pygame.draw.circle(surface, color, (x, y), 14, 2)
        # body
        pygame.draw.line(surface, color, (x, y + 14), (x, y + 40), 3)
        # arms
        pygame.draw.line(surface, color, (x - 16, y + 24), (x + 16, y + 24), 3)
        # legs
        pygame.draw.line(surface, color, (x, y + 40), (x - 10, y + 60), 3)
        pygame.draw.line(surface, color, (x, y + 40), (x + 10, y + 60), 3)


class BrainHUDScene(BaseScene):
    """
    Simple 'brain monitor' HUD inspired by the second reference.
    """

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

        # Hex grid-ish background (just vertical stripes with plus signs)
        stripe_w = 80
        for i in range(w // stripe_w + 2):
            x = i * stripe_w
            pygame.draw.line(surface, (40, 40, 40), (x, 0), (x, h), 2)
            for y in range(0, h, 64):
                pygame.draw.line(surface, (80, 80, 80), (x - 10, y), (x + 10, y), 2)

        # Left: stylized skeleton character (just a silhouette)
        center_x = w * 0.3
        center_y = h * 0.55
        scale = 1.0 + 0.3 * self.rms

        body_color = (0, 120, 255)
        outline = (255, 255, 255)

        # body
        body_rect = pygame.Rect(0, 0, 160 * scale, 220 * scale)
        body_rect.center = (center_x, center_y)
        pygame.draw.rect(surface, body_color, body_rect, border_radius=40)
        pygame.draw.rect(surface, outline, body_rect, 3, border_radius=40)

        # brain circle (treble driven)
        brain_r = int(40 * scale * (0.8 + self.treble * 0.8))
        brain_center = (int(center_x), int(center_y - body_rect.height * 0.4))
        pygame.draw.circle(surface, (255, 60, 160), brain_center, brain_r)
        pygame.draw.circle(surface, outline, brain_center, brain_r, 3)

        # teeth (onset flicker)
        teeth_w = int(60 * scale)
        teeth_h = int(20 * scale)
        teeth_rect = pygame.Rect(0, 0, teeth_w, teeth_h)
        teeth_rect.center = (center_x, center_y - body_rect.height * 0.05)
        teeth_color = (0, 255, 255) if self.onset > 0.6 else (0, 150, 200)
        pygame.draw.rect(surface, teeth_color, teeth_rect, border_radius=4)

        # Pelvis "speaker" pulsing with bass
        bass_r = int(20 * scale * (0.8 + self.bass * 1.2))
        speaker_center = (int(center_x), int(center_y + body_rect.height * 0.2))
        pygame.draw.circle(surface, (0, 255, 255), speaker_center, bass_r)
        pygame.draw.circle(surface, outline, speaker_center, bass_r, 3)

        # Right HUD panels
        panel_x = int(w * 0.6)
        panel_y = int(h * 0.15)
        panel_w = int(w * 0.32)
        panel_h = int(h * 0.7)

        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (10, 10, 10), panel_rect)
        pygame.draw.rect(surface, outline, panel_rect, 3)

        # BPM display (fake from onset intensity)
        bpm = 80 + int(160 * self.onset)
        font = pygame.font.SysFont("Consolas", 32)
        label = font.render(f"BPM {bpm}", True, (255, 255, 255))
        surface.blit(label, (panel_x + 20, panel_y + 10))

        # Waveform strip (rms)
        wave_rect = pygame.Rect(panel_x + 20, panel_y + 80, panel_w - 40, 80)
        pygame.draw.rect(surface, (20, 20, 20), wave_rect)
        pygame.draw.rect(surface, outline, wave_rect, 2)

        points = []
        segments = 64
        for i in range(segments):
            px = wave_rect.left + (wave_rect.width) * (i / (segments - 1))
            noise = np.sin(self.t * 8 + i * 0.7) * 0.5
            amp = self.rms * 0.7 + self.onset * 0.3
            py = wave_rect.centery + noise * amp * (wave_rect.height / 2 - 5)
            points.append((px, py))
        if len(points) > 1:
            pygame.draw.lines(surface, (0, 200, 255), False, points, 2)

        # Simple 'timer' at bottom
        timer_rect = pygame.Rect(panel_x + 20, panel_y + panel_h - 90, panel_w - 40, 60)
        pygame.draw.rect(surface, (0, 0, 0), timer_rect)
        pygame.draw.rect(surface, outline, timer_rect, 2)

        minutes = int(self.t // 60)
        seconds = int(self.t % 60)
        ms = int((self.t - int(self.t)) * 100)
        timer_label = font.render(f"{minutes:02d}:{seconds:02d}.{ms:02d}", True, (255, 255, 255))
        timer_pos = timer_label.get_rect(center=timer_rect.center)
        surface.blit(timer_label, timer_pos)


# ---------------------- Timeline --------------------------- #

@dataclass
class SceneEntry:
    start: float     # seconds
    end: float       # seconds
    scene: BaseScene


class SceneManager:
    def __init__(self, scenes: List[SceneEntry]):
        self.scenes = scenes
        self.current = None

    def get_scene_for_time(self, t: float) -> BaseScene:
        for entry in self.scenes:
            if entry.start <= t < entry.end:
                if self.current is not entry.scene:
                    if self.current:
                        self.current.exit()
                    self.current = entry.scene
                    self.current.enter()
                return entry.scene
        return self.current


# ---------------------- Main --------------------------- #

def main():
    features = analyze_audio(AUDIO_PATH)

    pygame.init()
    pygame.display.set_caption("FNF-style Advanced Song Visualizer")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()

    # Prepare scenes and timeline
    stripes = StripesScene(WINDOW_SIZE)
    brain = BrainHUDScene(WINDOW_SIZE)

    scenes = [
        SceneEntry(0.0, features.duration * 0.4, stripes),
        SceneEntry(features.duration * 0.4, features.duration, brain),
    ]
    manager = SceneManager(scenes)

    # Start audio playback in a background thread
    audio_thread = threading.Thread(target=play_audio_blocking, args=(AUDIO_PATH,), daemon=True)
    audio_thread.start()
    start_time = time.time()

    running = True
    last_t = start_time
    while running:
        dt = time.time() - last_t
        last_t = time.time()
        t = last_t - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if t > features.duration:
            running = False

        # Find closest feature index for current time
        idx = np.searchsorted(features.times, t)
        idx = int(np.clip(idx, 0, len(features.times) - 1))

        scene = manager.get_scene_for_time(t)
        if scene is None:
            scene = scenes[0].scene

        scene.update(dt, t, features, idx)
        scene.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
