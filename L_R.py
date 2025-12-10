import time
import threading
from dataclasses import dataclass
from typing import List

import numpy as np
import pygame
import librosa
import sounddevice as sd


AUDIO_PATH = "powerdown.mp3"      # CHANGE THIS TO YOUR FILE
WINDOW_SIZE = (1280, 720)
FPS = 60


# ------------------- DATA STRUCTURES ------------------- #

@dataclass
class StereoFeatures:
    sr: int
    duration: float
    times: np.ndarray

    L_rms: np.ndarray
    L_bass: np.ndarray
    L_mid: np.ndarray
    L_treble: np.ndarray
    L_onset: np.ndarray

    R_rms: np.ndarray
    R_bass: np.ndarray
    R_mid: np.ndarray
    R_treble: np.ndarray
    R_onset: np.ndarray


# ------------------- AUDIO ANALYSIS ------------------- #

def analyze_audio(path: str) -> StereoFeatures:
    print("[analysis] loading audio…")

    # stereo audio
    y, sr = librosa.load(path, sr=None, mono=False)
    if y.ndim == 1:
        # fallback: duplicate mono to stereo
        y = np.stack([y, y], axis=0)

    left = y[0]
    right = y[1]

    duration = librosa.get_duration(y=left, sr=sr)

    hop = 512
    n_fft = 2048

    # STFT per channel
    S_L = np.abs(librosa.stft(left, n_fft=n_fft, hop_length=hop))
    S_R = np.abs(librosa.stft(right, n_fft=n_fft, hop_length=hop))

    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    frames = np.arange(S_L.shape[1])
    times = librosa.frames_to_time(frames, sr=sr, hop_length=hop)

    # -------- band extractor --------
    def get_band(S, fmin, fmax):
        idx = np.logical_and(freqs >= fmin, freqs <= fmax)
        if not np.any(idx):
            return np.zeros(S.shape[1])
        return S[idx, :].mean(axis=0)

    # ---- LEFT ----
    L_rms = librosa.feature.rms(S=S_L)[0]
    L_bass = get_band(S_L, 20, 150)
    L_mid = get_band(S_L, 150, 2000)
    L_treble = get_band(S_L, 2000, 8000)
    L_onset = librosa.onset.onset_strength(y=left, sr=sr, hop_length=hop)

    # ---- RIGHT ----
    R_rms = librosa.feature.rms(S=S_R)[0]
    R_bass = get_band(S_R, 20, 150)
    R_mid = get_band(S_R, 150, 2000)
    R_treble = get_band(S_R, 2000, 8000)
    R_onset = librosa.onset.onset_strength(y=right, sr=sr, hop_length=hop)

    # normalize helper
    def N(x):
        m = x.max()
        return x / m if m > 0 else x

    print("[analysis] done.")

    return StereoFeatures(
        sr=sr,
        duration=duration,
        times=times,

        L_rms=N(L_rms),
        L_bass=N(L_bass),
        L_mid=N(L_mid),
        L_treble=N(L_treble),
        L_onset=N(L_onset),

        R_rms=N(R_rms),
        R_bass=N(R_bass),
        R_mid=N(R_mid),
        R_treble=N(R_treble),
        R_onset=N(R_onset),
    )


# ------------------- AUDIO PLAYBACK ------------------- #

def play_audio(path: str):
    y, sr = librosa.load(path, sr=None, mono=False)
    if y.ndim == 1:
        y = np.stack([y, y], axis=0)
    y = y.T     # sounddevice expects shape: (samples, channels)
    sd.play(y, sr)
    sd.wait()


# ------------------- SCENE BASE CLASS ------------------- #

class BaseScene:
    def __init__(self, size):
        self.width, self.height = size

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self, dt, t, feat: StereoFeatures, idx: int):
        raise NotImplementedError

    def draw(self, surf):
        raise NotImplementedError


# ------------------- STRIPES SCENE ------------------- #

class StripesScene(BaseScene):
    def update(self, dt, t, F: StereoFeatures, i):
        self.L_bass = F.L_bass[i]
        self.R_bass = F.R_bass[i]
        self.L_mid = F.L_mid[i]
        self.R_mid = F.R_mid[i]
        self.L_treble = F.L_treble[i]
        self.R_treble = F.R_treble[i]
        self.L_on = F.L_onset[i]
        self.R_on = F.R_onset[i]
        self.L_rms = F.L_rms[i]
        self.R_rms = F.R_rms[i]
        self.rms = max(self.L_rms, self.R_rms)

    def draw(self, s):
        s.fill((20, 0, 20))
        w, h = self.width, self.height

        # Left stripes
        left_val = (self.L_bass + self.L_mid + self.L_treble) / 3
        lw = w // 2
        lh = int(h * left_val)
        pygame.draw.rect(s, (255, 80, 150), (0, h - lh, lw, lh))

        # Right stripes
        right_val = (self.R_bass + self.R_mid + self.R_treble) / 3
        rh = int(h * right_val)
        pygame.draw.rect(s, (80, 150, 255), (lw, h - rh, lw, rh))

        # Center panning shift
        pan = (self.L_rms - self.R_rms) * 120
        cx = w // 2 + int(pan)
        pygame.draw.circle(s, (255, 255, 255), (cx, h // 2), 18)


# ------------------- BRAIN HUD SCENE ------------------- #

class BrainHUDScene(BaseScene):
    def update(self, dt, t, F: StereoFeatures, i):
        self.t = t
        self.rms = max(F.L_rms[i], F.R_rms[i])
        self.bass = (F.L_bass[i] + F.R_bass[i]) / 2
        self.treb = (F.L_treble[i] + F.R_treble[i]) / 2
        self.onset = max(F.L_onset[i], F.R_onset[i])

    def draw(self, s):
        s.fill((0, 0, 0))
        w, h = self.width, self.height

        size = 160 + int(self.bass * 80)
        cx, cy = w//2, h//2

        pygame.draw.circle(s, (0, 100, 255), (cx, cy), size)
        pygame.draw.circle(s, (255, 255, 255), (cx, cy), size, 5)

        brain_r = 40 + int(self.treb * 40)
        pygame.draw.circle(s, (255, 40, 180), (cx, cy - size // 2), brain_r)

        if self.onset > 0.7:
            pygame.draw.rect(s, (255, 255, 255), (0, 0, w, 10))


# ------------------- SCENE MANAGER ------------------- #

@dataclass
class SceneEntry:
    start: float
    end: float
    scene: BaseScene


class SceneManager:
    def __init__(self, entries: List[SceneEntry]):
        self.entries = entries
        self.current = None

    def get_scene(self, t):
        for e in self.entries:
            if e.start <= t < e.end:
                if self.current != e.scene:
                    if self.current:
                        self.current.exit()
                    self.current = e.scene
                    self.current.enter()
                return self.current
        return self.current


# ------------------- MAIN LOOP ------------------- #

def main():
    F = analyze_audio(AUDIO_PATH)

    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()

    stripes = StripesScene(WINDOW_SIZE)
    brain = BrainHUDScene(WINDOW_SIZE)

    timeline = [
        SceneEntry(0, F.duration * 0.5, stripes),
        SceneEntry(F.duration * 0.5, F.duration, brain),
    ]
    manager = SceneManager(timeline)

    audio_thread = threading.Thread(target=play_audio, args=(AUDIO_PATH,), daemon=True)
    audio_thread.start()

    start = time.time()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        t = time.time() - start

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        if t > F.duration:
            running = False

        idx = np.searchsorted(F.times, t)
        idx = np.clip(idx, 0, len(F.times) - 1)

        scene = manager.get_scene(t)
        scene.update(dt, t, F, idx)
        scene.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
