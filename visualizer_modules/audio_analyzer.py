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
    BRUTAL OPTIMIZATION - targeting consistent sub-2-second performance.
    
    Args:
        path: Path to audio file
        
    Returns:
        AudioFeatures dataclass with all extracted features
    """
    # Extreme speed settings
    sr = 8000  # Phone quality - still great for visualization
    hop_length = 4096  # Massive hop for minimal computation
    n_fft = 2048
    
    print("[analysis] loading audio...")
    y, _ = librosa.load(path, sr=sr, mono=True)
    duration = len(y) / sr
    
    # === SINGLE STFT - ALL FEATURES DERIVED FROM THIS ===
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    n_frames = S.shape[1]
    times = np.arange(n_frames) * hop_length / sr
    
    # Pre-compute ALL frequency indices
    masks = {
        'bass': (freqs >= 20) & (freqs < 150),
        'mid': (freqs >= 150) & (freqs < 2000),
        'treble': (freqs >= 2000) & (freqs < 4000),
        'sub_bass': (freqs >= 20) & (freqs < 60),
        'low_mid': (freqs >= 250) & (freqs < 500),
        'high_mid': (freqs >= 2000) & (freqs < 4000),
        'presence': (freqs >= 4000),
        'brilliance': (freqs >= 4000)  # Same as presence at 8kHz
    }
    
    def norm(x):
        m = x.max()
        return x / m if m > 1e-10 else x
    
    print("[analysis] extracting features...")
    
    # === TASK 1: All energy-based features from S (super fast) ===
    def task_energy_features():
        # All frequency bands
        bands = {name: norm(S[mask].mean(axis=0)) if mask.any() else np.zeros(n_frames)
                for name, mask in masks.items()}
        
        # RMS
        rms = norm(np.sqrt(np.mean(S**2, axis=0)))
        
        # Spectral flux
        flux = np.zeros(n_frames)
        flux[1:] = np.abs(np.diff(S, axis=1)).sum(axis=0)
        flux = norm(flux)
        
        return bands, rms, flux
    
    # === TASK 2: Fast spectral features ===
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
        centroid_2d = np.dot(freqs, S) / S_sum
        freq_sq_diff = (freqs[:, None] - centroid_2d[None, :]) ** 2
        bandwidth = norm(np.sqrt(np.sum(freq_sq_diff * S, axis=0) / S_sum))
        
        # Contrast (single split)
        mid_idx = len(S) // 2
        contrast = norm(S[:mid_idx].max(axis=0) - S[mid_idx:].min(axis=0))
        
        return centroid, rolloff, flatness, bandwidth, contrast
    
    # === TASK 3: Rhythm - simplified ===
    def task_rhythm():
        # Minimal onset
        onset = np.sqrt(np.mean(np.diff(S, axis=1, prepend=S[:, :1])**2, axis=0))
        onset = norm(onset)
        
        # Quick tempo - use onset for beat tracking
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, 
                                              hop_length=hop_length, start_bpm=120,
                                              units='frames')
        beat_times = beats * hop_length / sr
        
        # Minimal tempogram - just use onset variations
        tempogram = np.abs(np.diff(onset, prepend=onset[0]))
        tempogram = norm(tempogram)
        
        return onset, tempo, beats, beat_times, tempogram
    
    # === TASK 4: Chroma ===
    def task_chroma():
        chroma = librosa.feature.chroma_stft(S=S, sr=sr, n_chroma=12, hop_length=hop_length)
        return norm(chroma.mean(axis=0))
    
    # === TASK 5: FAKE HPSS - use frequency approximation (MUCH faster) ===
    def task_fake_hpss():
        # Harmonic = low frequency content (stable tones)
        # Percussive = high frequency content (transients)
        
        # Simple frequency split as proxy
        harmonic_mask = freqs < 2000
        percussive_mask = freqs >= 2000
        
        harmonic = norm(S[harmonic_mask].mean(axis=0))
        percussive = norm(S[percussive_mask].mean(axis=0))
        
        # Tonnetz - approximate from chroma instead of recomputing
        # Use simple phase relationship approximation
        tonnetz = np.roll(harmonic, 1) * 0.7 + harmonic * 0.3
        tonnetz = norm(tonnetz)
        
        return harmonic, percussive, tonnetz
    
    # === TASK 6: Fast MFCCs ===
    def task_mfcc():
        # Minimal MFCC computation
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length,
                                    n_fft=n_fft, n_mels=16)  # Minimal mels
        
        # Simple differences for deltas
        mfcc_d = np.diff(mfcc, axis=1, prepend=mfcc[:, :1])
        mfcc_d2 = np.diff(mfcc_d, axis=1, prepend=mfcc_d[:, :1])
        
        return norm(mfcc.mean(axis=0)), norm(mfcc_d.mean(axis=0)), norm(mfcc_d2.mean(axis=0))
    
    # === TASK 7: ZCR - ultra fast ===
    def task_zcr():
        # Simplified ZCR from waveform chunks
        n_chunks = n_frames
        chunk_size = len(y) // n_chunks
        
        zcr = np.zeros(n_frames)
        for i in range(min(n_chunks, n_frames)):
            start = i * chunk_size
            end = min(start + chunk_size, len(y))
            if end > start:
                chunk = y[start:end]
                zcr[i] = np.sum(np.abs(np.diff(np.sign(chunk)))) / (2 * len(chunk))
        
        return norm(zcr)
    
    # Run everything in parallel
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(task_energy_features): 'energy',
            executor.submit(task_spectral): 'spectral',
            executor.submit(task_rhythm): 'rhythm',
            executor.submit(task_chroma): 'chroma',
            executor.submit(task_fake_hpss): 'hpss',
            executor.submit(task_mfcc): 'mfcc',
            executor.submit(task_zcr): 'zcr'
        }
        
        results = {}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    
    # Unpack all results
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