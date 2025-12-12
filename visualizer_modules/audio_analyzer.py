import numpy as np
import librosa
from dataclasses import dataclass


@dataclass
class AudioFeatures:
    # Original features - unchanged
    sr: int
    duration: float
    times: np.ndarray
    rms: np.ndarray
    bass: np.ndarray
    mid: np.ndarray
    treble: np.ndarray
    onset: np.ndarray
    
    # Spectral features
    spectral_centroid: np.ndarray
    spectral_rolloff: np.ndarray
    spectral_flatness: np.ndarray
    spectral_bandwidth: np.ndarray
    spectral_contrast: np.ndarray
    
    # Rhythm & Tempo
    tempo: float
    beat_frames: np.ndarray
    beat_times: np.ndarray
    tempogram: np.ndarray
    
    # Harmonic features
    harmonic: np.ndarray
    percussive: np.ndarray
    chroma: np.ndarray
    tonnetz: np.ndarray
    
    # Dynamic features
    zero_crossing_rate: np.ndarray
    
    # Additional frequency bands
    sub_bass: np.ndarray      # 20-60 Hz
    low_mid: np.ndarray       # 250-500 Hz
    high_mid: np.ndarray      # 2000-4000 Hz
    presence: np.ndarray      # 4000-6000 Hz
    brilliance: np.ndarray    # 6000+ Hz
    
    # Advanced features
    mfcc: np.ndarray          # 13 coefficients
    mfcc_delta: np.ndarray    # Delta (velocity)
    mfcc_delta2: np.ndarray   # Delta-delta (acceleration)
    
    # Energy and loudness
    loudness: np.ndarray
    
    # Novelty/complexity
    novelty: np.ndarray
    spectral_flux: np.ndarray


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

    # === ORIGINAL FEATURES (unchanged) ===
    print("[analysis] extracting original features...")
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

    # Normalize original features
    rms = norm(rms)
    bass = norm(bass)
    mid = norm(mid)
    treble = norm(treble)
    onset = norm(onset)

    # === NEW SPECTRAL FEATURES ===
    print("[analysis] extracting spectral features...")
    spectral_centroid = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(S=S, sr=sr)[0]
    spectral_flatness = librosa.feature.spectral_flatness(S=S)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]
    spectral_contrast = librosa.feature.spectral_contrast(S=S, sr=sr)
    
    # Normalize spectral features
    spectral_centroid = norm(spectral_centroid)
    spectral_rolloff = norm(spectral_rolloff)
    spectral_flatness = norm(spectral_flatness)
    spectral_bandwidth = norm(spectral_bandwidth)
    spectral_contrast = norm(spectral_contrast.mean(axis=0))

    # === RHYTHM & TEMPO ===
    print("[analysis] extracting tempo and beats...")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
    tempogram = librosa.feature.tempogram(y=y, sr=sr, hop_length=hop_length)
    tempogram = norm(tempogram.mean(axis=0))

    # === HARMONIC & PERCUSSIVE ===
    print("[analysis] separating harmonic and percussive components...")
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    
    # Get energy of harmonic and percussive components
    S_harmonic = np.abs(librosa.stft(y_harmonic, n_fft=n_fft, hop_length=hop_length))
    S_percussive = np.abs(librosa.stft(y_percussive, n_fft=n_fft, hop_length=hop_length))
    
    harmonic = librosa.feature.rms(S=S_harmonic)[0]
    percussive = librosa.feature.rms(S=S_percussive)[0]
    
    harmonic = norm(harmonic)
    percussive = norm(percussive)
    
    # Chroma features (pitch class)
    chroma = librosa.feature.chroma_stft(S=S, sr=sr)
    chroma = norm(chroma.mean(axis=0))
    
    # Tonnetz (harmonic network)
    tonnetz = librosa.feature.tonnetz(y=y_harmonic, sr=sr)
    tonnetz = norm(tonnetz.mean(axis=0))

    # === DYNAMIC FEATURES ===
    print("[analysis] extracting dynamic features...")
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]
    zero_crossing_rate = norm(zero_crossing_rate)

    # === ADDITIONAL FREQUENCY BANDS ===
    print("[analysis] extracting detailed frequency bands...")
    sub_bass = band_energy(20, 60)
    low_mid = band_energy(250, 500)
    high_mid = band_energy(2000, 4000)
    presence = band_energy(4000, 6000)
    brilliance = band_energy(6000, sr/2)  # Up to Nyquist frequency
    
    sub_bass = norm(sub_bass)
    low_mid = norm(low_mid)
    high_mid = norm(high_mid)
    presence = norm(presence)
    brilliance = norm(brilliance)

    # === ADVANCED FEATURES ===
    print("[analysis] extracting MFCCs and advanced features...")
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
    mfcc_delta = librosa.feature.delta(mfcc)
    mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
    
    # Average across coefficients for simpler visualization
    mfcc = norm(mfcc.mean(axis=0))
    mfcc_delta = norm(mfcc_delta.mean(axis=0))
    mfcc_delta2 = norm(mfcc_delta2.mean(axis=0))

    # === ENERGY & LOUDNESS ===
    print("[analysis] calculating loudness...")
    # Perceptual loudness using A-weighting approximation
    loudness = librosa.feature.rms(S=S)[0]
    loudness = norm(loudness)

    # === NOVELTY & COMPLEXITY ===
    print("[analysis] calculating novelty and spectral flux...")
    # Novelty - how much the audio is changing
    novelty = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    novelty = norm(novelty)
    
    # Spectral flux - rate of change in the power spectrum
    spectral_flux = np.zeros(S.shape[1])
    for i in range(1, S.shape[1]):
        spectral_flux[i] = np.sum(np.abs(S[:, i] - S[:, i-1]))
    spectral_flux = norm(spectral_flux)

    print("[analysis] done.")
    return AudioFeatures(
        # Original features
        sr=sr,
        duration=duration,
        times=times,
        rms=rms,
        bass=bass,
        mid=mid,
        treble=treble,
        onset=onset,
        
        # Spectral features
        spectral_centroid=spectral_centroid,
        spectral_rolloff=spectral_rolloff,
        spectral_flatness=spectral_flatness,
        spectral_bandwidth=spectral_bandwidth,
        spectral_contrast=spectral_contrast,
        
        # Rhythm & Tempo
        tempo=tempo,
        beat_frames=beat_frames,
        beat_times=beat_times,
        tempogram=tempogram,
        
        # Harmonic features
        harmonic=harmonic,
        percussive=percussive,
        chroma=chroma,
        tonnetz=tonnetz,
        
        # Dynamic features
        zero_crossing_rate=zero_crossing_rate,
        
        # Additional frequency bands
        sub_bass=sub_bass,
        low_mid=low_mid,
        high_mid=high_mid,
        presence=presence,
        brilliance=brilliance,
        
        # Advanced features
        mfcc=mfcc,
        mfcc_delta=mfcc_delta,
        mfcc_delta2=mfcc_delta2,
        
        # Energy and loudness
        loudness=loudness,
        
        # Novelty/complexity
        novelty=novelty,
        spectral_flux=spectral_flux
    )