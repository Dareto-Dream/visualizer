import numpy as np
import librosa
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache


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
    Ultra-fast parallel implementation.
    
    Args:
        path: Path to audio file
        
    Returns:
        AudioFeatures dataclass with all extracted features
    """
    print("[analysis] loading audio...")
    y, sr = librosa.load(path, sr=22050, mono=True)  # Downsample to 22kHz for speed
    duration = librosa.get_duration(y=y, sr=sr)

    hop_length = 512
    n_fft = 2048
    
    # === COMPUTE STFT ONCE ===
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop_length)

    # Pre-compute ALL frequency band indices at once
    freq_bands = {
        'bass': (20, 150),
        'mid': (150, 2000),
        'treble': (2000, 8000),
        'sub_bass': (20, 60),
        'low_mid': (250, 500),
        'high_mid': (2000, 4000),
        'presence': (4000, 6000),
        'brilliance': (6000, sr/2)
    }
    
    band_indices = {name: np.logical_and(freqs >= fmin, freqs < fmax) 
                   for name, (fmin, fmax) in freq_bands.items()}

    # Ultra-fast normalization
    def norm(x):
        m = np.max(x)
        return x / m if m > 1e-10 else x

    # === PARALLEL FEATURE EXTRACTION ===
    print("[analysis] extracting features in parallel...")
    
    # Group 1: Basic energy features (computed from S directly)
    def extract_basic_features():
        rms = norm(librosa.feature.rms(S=S)[0])
        
        # Vectorized band energy extraction
        bands = {}
        for name, idx in band_indices.items():
            if np.any(idx):
                bands[name] = norm(S[idx, :].mean(axis=0))
            else:
                bands[name] = np.zeros(S.shape[1])
        
        return rms, bands
    
    # Group 2: Spectral features
    def extract_spectral_features():
        return {
            'centroid': norm(librosa.feature.spectral_centroid(S=S, sr=sr)[0]),
            'rolloff': norm(librosa.feature.spectral_rolloff(S=S, sr=sr)[0]),
            'flatness': norm(librosa.feature.spectral_flatness(S=S)[0]),
            'bandwidth': norm(librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]),
            'contrast': norm(librosa.feature.spectral_contrast(S=S, sr=sr).mean(axis=0)),
            'chroma': norm(librosa.feature.chroma_stft(S=S, sr=sr).mean(axis=0))
        }
    
    # Group 3: Onset and tempo
    def extract_rhythm_features():
        onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=hop_length)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
        tempogram = norm(librosa.feature.tempogram(onset_envelope=onset, sr=sr, hop_length=hop_length).mean(axis=0))
        return norm(onset), tempo, beat_frames, beat_times, tempogram
    
    # Group 4: HPSS and related
    def extract_hpss_features():
        y_harmonic, y_percussive = librosa.effects.hpss(y, margin=2)  # Faster margin
        
        S_harmonic = np.abs(librosa.stft(y_harmonic, n_fft=n_fft, hop_length=hop_length))
        S_percussive = np.abs(librosa.stft(y_percussive, n_fft=n_fft, hop_length=hop_length))
        
        return {
            'harmonic': norm(librosa.feature.rms(S=S_harmonic)[0]),
            'percussive': norm(librosa.feature.rms(S=S_percussive)[0]),
            'tonnetz': norm(librosa.feature.tonnetz(y=y_harmonic, sr=sr).mean(axis=0))
        }
    
    # Group 5: MFCCs
    def extract_mfcc_features():
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
        # Compute deltas efficiently in one pass
        mfcc_delta = librosa.feature.delta(mfcc, order=1, width=3)  # Smaller width for speed
        mfcc_delta2 = librosa.feature.delta(mfcc, order=2, width=3)
        
        return {
            'mfcc': norm(mfcc.mean(axis=0)),
            'delta': norm(mfcc_delta.mean(axis=0)),
            'delta2': norm(mfcc_delta2.mean(axis=0))
        }
    
    # Group 6: Simple features
    def extract_simple_features():
        zcr = norm(librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0])
        
        # Optimized spectral flux
        spectral_flux = np.zeros(S.shape[1])
        spectral_flux[1:] = np.sum(np.abs(np.diff(S, axis=1)), axis=0)
        spectral_flux = norm(spectral_flux)
        
        return zcr, spectral_flux
    
    # Execute all feature extractions in parallel
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_basic = executor.submit(extract_basic_features)
        future_spectral = executor.submit(extract_spectral_features)
        future_rhythm = executor.submit(extract_rhythm_features)
        future_hpss = executor.submit(extract_hpss_features)
        future_mfcc = executor.submit(extract_mfcc_features)
        future_simple = executor.submit(extract_simple_features)
        
        # Gather results
        rms, bands = future_basic.result()
        spectral = future_spectral.result()
        onset, tempo, beat_frames, beat_times, tempogram = future_rhythm.result()
        hpss = future_hpss.result()
        mfcc_features = future_mfcc.result()
        zero_crossing_rate, spectral_flux = future_simple.result()

    print("[analysis] done.")
    return AudioFeatures(
        # Original features
        sr=sr,
        duration=duration,
        times=times,
        rms=rms,
        bass=bands['bass'],
        mid=bands['mid'],
        treble=bands['treble'],
        onset=onset,
        
        # Spectral features
        spectral_centroid=spectral['centroid'],
        spectral_rolloff=spectral['rolloff'],
        spectral_flatness=spectral['flatness'],
        spectral_bandwidth=spectral['bandwidth'],
        spectral_contrast=spectral['contrast'],
        
        # Rhythm & Tempo
        tempo=tempo,
        beat_frames=beat_frames,
        beat_times=beat_times,
        tempogram=tempogram,
        
        # Harmonic features
        harmonic=hpss['harmonic'],
        percussive=hpss['percussive'],
        chroma=spectral['chroma'],
        tonnetz=hpss['tonnetz'],
        
        # Dynamic features
        zero_crossing_rate=zero_crossing_rate,
        
        # Additional frequency bands
        sub_bass=bands['sub_bass'],
        low_mid=bands['low_mid'],
        high_mid=bands['high_mid'],
        presence=bands['presence'],
        brilliance=bands['brilliance'],
        
        # Advanced features
        mfcc=mfcc_features['mfcc'],
        mfcc_delta=mfcc_features['delta'],
        mfcc_delta2=mfcc_features['delta2'],
        
        # Energy and loudness
        loudness=rms,  # Reuse RMS
        
        # Novelty/complexity
        novelty=onset,  # Reuse onset
        spectral_flux=spectral_flux
    )