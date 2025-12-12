import numpy as np
import librosa
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')


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
    Balanced optimization - fast processing with smooth visual output.
    
    Args:
        path: Path to audio file
        
    Returns:
        AudioFeatures dataclass with all extracted features
    """
    # BALANCED settings - good speed, smooth visuals
    sr = 22050  # Good quality for visualization
    hop_length = 512  # Standard hop = ~43 fps for smooth animation
    n_fft = 2048
    
    print("[analysis] loading audio...")
    y, _ = librosa.load(path, sr=sr, mono=True)
    duration = len(y) / sr
    
    # === COMPUTE STFT ONCE ===
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    n_frames = S.shape[1]
    times = np.arange(n_frames) * hop_length / sr
    
    # Pre-compute frequency masks
    masks = {
        'bass': (freqs >= 20) & (freqs < 150),
        'mid': (freqs >= 150) & (freqs < 2000),
        'treble': (freqs >= 2000) & (freqs < 8000),
        'sub_bass': (freqs >= 20) & (freqs < 60),
        'low_mid': (freqs >= 250) & (freqs < 500),
        'high_mid': (freqs >= 2000) & (freqs < 4000),
        'presence': (freqs >= 4000) & (freqs < 6000),
        'brilliance': (freqs >= 6000) & (freqs < sr/2)
    }
    
    def norm(x):
        m = x.max()
        return x / m if m > 1e-10 else x
    
    print("[analysis] extracting features...")
    
    # === TASK 1: Energy features - optimized extraction ===
    def task_energy_features():
        # All frequency bands in one pass
        bands = {}
        for name, mask in masks.items():
            if mask.any():
                bands[name] = norm(S[mask].mean(axis=0))
            else:
                bands[name] = np.zeros(n_frames)
        
        # RMS
        rms = norm(np.sqrt(np.mean(S**2, axis=0)))
        
        # Spectral flux
        flux = np.zeros(n_frames)
        flux[1:] = np.abs(np.diff(S, axis=1)).sum(axis=0)
        flux = norm(flux)
        
        return bands, rms, flux
    
    # === TASK 2: Spectral features - vectorized ===
    def task_spectral():
        S_sum = S.sum(axis=0) + 1e-10
        
        # Centroid
        centroid = norm(np.dot(freqs, S) / S_sum)
        
        # Rolloff
        cumsum = np.cumsum(S, axis=0)
        rolloff_idx = np.argmax(cumsum >= 0.85 * cumsum[-1], axis=0)
        rolloff = norm(freqs[rolloff_idx])
        
        # Flatness
        S_safe = S + 1e-10
        flatness = norm(np.exp(np.mean(np.log(S_safe), axis=0)) / (S.mean(axis=0) + 1e-10))
        
        # Bandwidth
        centroid_2d = centroid[None, :]
        freq_sq_diff = (freqs[:, None] - centroid_2d) ** 2
        bandwidth = norm(np.sqrt(np.sum(freq_sq_diff * S, axis=0) / S_sum))
        
        # Contrast - simplified but still meaningful
        mid_idx = len(S) // 2
        contrast = norm(S[:mid_idx].max(axis=0) - S[mid_idx:].min(axis=0))
        
        return centroid, rolloff, flatness, bandwidth, contrast
    
    # === TASK 3: Rhythm ===
    def task_rhythm():
        # Fast onset computation
        onset = np.sqrt(np.mean(np.abs(np.diff(S, axis=1, prepend=S[:, :1])), axis=0))
        onset = norm(onset)
        
        # Beat tracking
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, 
                                              hop_length=hop_length, start_bpm=120,
                                              units='frames', trim=False)
        beat_times = beats * hop_length / sr
        
        # Tempogram - use onset envelope
        tempogram = np.abs(np.gradient(onset))
        tempogram = norm(tempogram)
        
        return onset, tempo, beats, beat_times, tempogram
    
    # === TASK 4: Chroma ===
    def task_chroma():
        chroma = librosa.feature.chroma_stft(S=S, sr=sr, n_chroma=12, hop_length=hop_length)
        return norm(chroma.mean(axis=0))
    
    # === TASK 5: Fast HPSS approximation ===
    def task_hpss_approx():
        # Use median filtering approach - much faster than full HPSS
        # Harmonic = horizontal median (stable across time)
        # Percussive = vertical median (stable across frequency)
        
        from scipy.ndimage import median_filter
        
        # Very small kernel for speed
        kernel_h = (1, 5)  # Harmonic: stable across time
        kernel_p = (5, 1)  # Percussive: stable across freq
        
        S_harmonic_mask = median_filter(S, size=kernel_h, mode='reflect')
        S_percussive_mask = median_filter(S, size=kernel_p, mode='reflect')
        
        # Soft masking
        S_harmonic = S * (S_harmonic_mask / (S_harmonic_mask + S_percussive_mask + 1e-10))
        S_percussive = S * (S_percussive_mask / (S_harmonic_mask + S_percussive_mask + 1e-10))
        
        harmonic = norm(np.sqrt(np.mean(S_harmonic**2, axis=0)))
        percussive = norm(np.sqrt(np.mean(S_percussive**2, axis=0)))
        
        # Tonnetz approximation from harmonic energy
        tonnetz = np.convolve(harmonic, [0.25, 0.5, 0.25], mode='same')
        tonnetz = norm(tonnetz)
        
        return harmonic, percussive, tonnetz
    
    # === TASK 6: MFCCs ===
    def task_mfcc():
        # Optimized MFCC
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length,
                                    n_fft=n_fft, n_mels=40)  # Reasonable mel count
        
        # Fast deltas
        mfcc_d = np.diff(mfcc, axis=1, prepend=mfcc[:, :1])
        mfcc_d2 = np.diff(mfcc_d, axis=1, prepend=mfcc_d[:, :1])
        
        return norm(mfcc.mean(axis=0)), norm(mfcc_d.mean(axis=0)), norm(mfcc_d2.mean(axis=0))
    
    # === TASK 7: ZCR ===
    def task_zcr():
        # Fast vectorized ZCR
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length, center=False)[0]
        return norm(zcr)
    
    # Parallel execution
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(task_energy_features): 'energy',
            executor.submit(task_spectral): 'spectral',
            executor.submit(task_rhythm): 'rhythm',
            executor.submit(task_chroma): 'chroma',
            executor.submit(task_hpss_approx): 'hpss',
            executor.submit(task_mfcc): 'mfcc',
            executor.submit(task_zcr): 'zcr'
        }
        
        results = {}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    
    # Unpack results
    bands, rms, spectral_flux = results['energy']
    spectral_centroid, spectral_rolloff, spectral_flatness, spectral_bandwidth, spectral_contrast = results['spectral']
    onset, tempo, beat_frames, beat_times, tempogram = results['rhythm']
    chroma = results['chroma']
    harmonic, percussive, tonnetz = results['hpss']
    mfcc, mfcc_delta, mfcc_delta2 = results['mfcc']
    zero_crossing_rate = results['zcr']
    
    print("[analysis] done.")
    return AudioFeatures(
        sr=sr,
        duration=duration,
        times=times,
        rms=rms,
        bass=bands['bass'],
        mid=bands['mid'],
        treble=bands['treble'],
        onset=onset,
        spectral_centroid=spectral_centroid,
        spectral_rolloff=spectral_rolloff,
        spectral_flatness=spectral_flatness,
        spectral_bandwidth=spectral_bandwidth,
        spectral_contrast=spectral_contrast,
        tempo=tempo,
        beat_frames=beat_frames,
        beat_times=beat_times,
        tempogram=tempogram,
        harmonic=harmonic,
        percussive=percussive,
        chroma=chroma,
        tonnetz=tonnetz,
        zero_crossing_rate=zero_crossing_rate,
        sub_bass=bands['sub_bass'],
        low_mid=bands['low_mid'],
        high_mid=bands['high_mid'],
        presence=bands['presence'],
        brilliance=bands['brilliance'],
        mfcc=mfcc,
        mfcc_delta=mfcc_delta,
        mfcc_delta2=mfcc_delta2,
        loudness=rms,
        novelty=onset,
        spectral_flux=spectral_flux
    )