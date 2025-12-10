import numpy as np
import librosa
from dataclasses import dataclass


@dataclass
class AudioFeatures:
    sr: int
    duration: float
    times: np.ndarray
    rms: np.ndarray
    bass: np.ndarray
    mid: np.ndarray
    treble: np.ndarray
    onset: np.ndarray


def analyze_audio(path: str) -> AudioFeatures:
    """
    Analyze audio file and extract features for visualization.
    
    Args:
        path: Path to audio file
        
    Returns:
        AudioFeatures dataclass with all extracted features
    """
    print("[analysis] loading audio...")
    y, sr = librosa.load(path, sr=None, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    hop_length = 512
    n_fft = 2048
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop_length)

    rms = librosa.feature.rms(S=S)[0]

    def band_energy(fmin, fmax):
        idx = np.logical_and(freqs >= fmin, freqs < fmax)
        if not np.any(idx):
            return np.zeros(S.shape[1])
        band = S[idx, :]
        return band.mean(axis=0)

    bass = band_energy(20, 150)
    mid = band_energy(150, 2000)
    treble = band_energy(2000, 8000)
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

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
