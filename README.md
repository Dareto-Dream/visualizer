# Python Music Visualizer

This project is a modular, audio-reactive visualizer built with Python. It uses audio analysis to drive multiple scene layouts in real time. The engine is inspired by multi-HUD visualizers such as FNF's visual style but is designed to be fully extensible.

The system is separated into clean modules:

1. Audio analysis - feature extraction from audio files
2. Scene system - modular visual scenes with base class
3. Main engine - rendering loop, timeline switching, and Pygame output

This structure keeps audio processing clean and independent from visuals.

---

## Features

* Comprehensive audio analysis with 36 extracted features including:
  - Energy metrics (RMS, loudness)
  - Frequency band analysis (bass, mid, treble, sub-bass, low-mid, high-mid, presence, brilliance)
  - Spectral features (centroid, rolloff, flatness, bandwidth, contrast, flux)
  - Rhythm analysis (tempo/BPM, beat detection, tempogram)
  - Harmonic/percussive separation
  - Tonal features (chroma, tonnetz)
  - Dynamic features (zero crossing rate)
  - Advanced timbral analysis (MFCCs with velocity and acceleration)
  - Onset detection and novelty curves
* Extensible scene system with base Scene class
* Timeline-based scene switching
* Real-time rendering at 60 FPS
* Supports MP3, WAV, OGG, FLAC and most other audio formats
* Four unique pre-built scenes with distinct aesthetics

---

## Requirements

Python 3.10 or newer
Recommended: a virtual environment

Install dependencies:

```bash
pip install pygame librosa numpy sounddevice
```

If librosa raises codec issues on Windows, install FFmpeg:

```bash
choco install ffmpeg
```

---

## File Structure

```
visualizer/
│
├── main.py                              # Main entry point, rendering loop
├── visualizer_modules/
│   ├── __init__.py                      # Package exports
│   ├── audio_analyzer.py                # Audio feature extraction
│   ├── audio_player.py                  # Audio playback thread
│   ├── scene_manager.py                 # Timeline-based scene switching
│   └── scenes/
│       ├── __init__.py                  # Scene exports
│       ├── base_scene.py                # Base scene class
│       ├── stripes_scene.py             # Frequency bars with cars scene
│       ├── skeleton_scene.py            # X-ray skeleton monitor scene
│       ├── graffiti_scene.py            # Urban graffiti rapper scene
│       └── brain_hud_scene.py           # Futuristic brain HUD scene
├── powerdown.mp3                        # Your audio file
└── README.md
```

---

## How It Works

### 1. Audio Analysis (`audio_analyzer.py`)

The audio analyzer loads audio files and computes a comprehensive set of features:

**Energy & Loudness:**
* RMS (root mean square energy)
* Perceptual loudness

**Frequency Band Analysis:**
* Bass (20-150 Hz)
* Sub-bass (20-60 Hz)
* Mid (150-2000 Hz)
* Low-mid (250-500 Hz)
* High-mid (2000-4000 Hz)
* Treble (2000-8000 Hz)
* Presence (4000-6000 Hz)
* Brilliance (6000+ Hz)

**Spectral Features:**
* Spectral centroid (brightness/timbre)
* Spectral rolloff (high-frequency content)
* Spectral flatness (noise vs tone character)
* Spectral bandwidth (frequency range)
* Spectral contrast (peak/valley differences)
* Spectral flux (rate of spectral change)

**Rhythm & Timing:**
* Tempo (BPM estimation)
* Beat frames and times (precise beat locations)
* Tempogram (tempo strength over time)
* Onset strength (percussive spikes)

**Harmonic & Tonal:**
* Harmonic component energy
* Percussive component energy
* Chroma features (pitch class distribution)
* Tonnetz (harmonic network relationships)

**Dynamic Features:**
* Zero crossing rate (percussiveness indicator)
* Novelty curve (change detection)

**Advanced Timbral Analysis:**
* MFCCs (mel-frequency cepstral coefficients)
* MFCC delta (velocity of timbral change)
* MFCC delta-delta (acceleration of timbral change)

All features are normalized to 0-1 range and returned as time-indexed arrays for frame-by-frame access during visualization.

### 2. Scene System (`scenes/`)

Each scene subclasses the `BaseScene` class and implements:

```python
def update(self, dt, t, features, idx):
    # Update scene state based on audio features
    self.bass = features.bass[idx]
    self.treble = features.treble[idx]
    # ...

def draw(self, surface):
    # Draw the scene to the Pygame surface
    pass
```

Scenes can react to any audio feature at any time.

### 3. Main Engine (`main.py`)

The main engine handles:

* Loading features from audio analyzer
* Starting audio playback in a background thread
* Running the Pygame rendering loop
* Managing scene timeline and transitions
* Coordinating update/draw calls to active scene

---

## Pre-Built Scenes

### EnhancedStripesScene
Vertical frequency bars with moving cars and dancing stick figures on top. Pink/magenta color scheme with halftone texture effects and animated road elements.

### SkeletonXRayScene
Medical monitor aesthetic with blue skeleton character featuring pink brain and cyan details. Hexagon honeycomb background with technical HUD panels, waveforms, and digital timer.

### GraffitiRapperScene
Urban graffiti style with orange spray paint aesthetic. Animated rapper character with dynamic particles, barcode, technical diagrams, and rhythm game arrow controls.

### BrainHUDScene
Futuristic body monitor with glowing character silhouette. Features brain (treble-responsive) and speaker (bass-responsive) visualization, frequency spectrum, waveform display, and status panels.

---

## Running the Visualizer

Place an audio file in the project folder.
Update `AUDIO_PATH` in `main.py` if necessary:

```python
AUDIO_PATH = "powerdown.mp3"
```

Run:

```bash
python main.py
```

A window will open and the visualizer will run in real time while playing the music.

---

## Adding New Scenes

To create a new scene:

1. Create a new file in `visualizer_modules/scenes/`
2. Subclass `BaseScene`
3. Implement `update()` and `draw()` methods
4. Import and add to timeline in `main.py`

Example:

```python
from visualizer_modules.scenes.base_scene import BaseScene
from visualizer_modules.audio_analyzer import AudioFeatures

class MyCustomScene(BaseScene):
    def __init__(self, size):
        super().__init__(size)
        self.width, self.height = size
    
    def update(self, dt, t, features, idx):
        # Access any of the 36+ available features
        self.bass = features.bass[idx]
        self.onset = features.onset[idx]
        
        # Use spectral features for visual effects
        self.brightness = features.spectral_centroid[idx]
        self.complexity = features.spectral_flatness[idx]
        
        # Separate harmonic and percussive elements
        self.melody_strength = features.harmonic[idx]
        self.drum_strength = features.percussive[idx]
        
        # Use tempo for rhythm sync
        self.bpm = features.tempo
        
        # Detect changes and transitions
        self.change_intensity = features.novelty[idx]
    
    def draw(self, surface):
        # Draw your visualization
        surface.fill((0, 0, 0))
        # ... your drawing code
```

Then in `main.py`:

```python
from visualizer_modules import MyCustomScene

# In main():
my_scene = MyCustomScene(WINDOW_SIZE)
scenes = [
    SceneEntry(0.0, 30.0, my_scene),
    # ... other scenes
]
```

---

## Scene Timeline

By default, the visualizer splits the song into 4 equal parts:

* 0-25%: EnhancedStripesScene
* 25-50%: SkeletonXRayScene
* 50-75%: GraffitiRapperScene
* 75-100%: BrainHUDScene

Modify the timeline in `main.py` to customize scene order and duration.

---

## Configuration

Key settings in `main.py`:

```python
AUDIO_PATH = "powerdown.mp3"    # Audio file to visualize
WINDOW_SIZE = (1280, 720)       # Resolution
FPS = 60                         # Target framerate
```

---

## Audio Features Reference

Access these in your scene's `update()` method via `features`:

**Core Metadata:**
* `features.sr` - Sample rate
* `features.duration` - Total song duration
* `features.times` - Time array for each frame

**Energy & Loudness:**
* `features.rms` - Root mean square energy
* `features.loudness` - Perceptual loudness

**Frequency Bands (Original):**
* `features.bass` - Low frequency energy (20-150 Hz)
* `features.mid` - Mid frequency energy (150-2000 Hz)
* `features.treble` - High frequency energy (2000-8000 Hz)

**Additional Frequency Bands:**
* `features.sub_bass` - Sub-bass (20-60 Hz)
* `features.low_mid` - Low-midrange (250-500 Hz)
* `features.high_mid` - High-midrange (2000-4000 Hz)
* `features.presence` - Presence range (4000-6000 Hz)
* `features.brilliance` - Brilliance (6000+ Hz)

**Spectral Features:**
* `features.spectral_centroid` - Brightness/timbre indicator
* `features.spectral_rolloff` - High-frequency content measure
* `features.spectral_flatness` - Noise vs tone character (0=tonal, 1=noisy)
* `features.spectral_bandwidth` - Width of frequency range
* `features.spectral_contrast` - Peak/valley differences in spectrum
* `features.spectral_flux` - Rate of spectral change

**Rhythm & Timing:**
* `features.tempo` - Estimated BPM (scalar value, not array)
* `features.beat_frames` - Frame indices where beats occur
* `features.beat_times` - Time values where beats occur
* `features.tempogram` - Tempo strength over time
* `features.onset` - Onset strength (percussive spike detection)

**Harmonic & Tonal:**
* `features.harmonic` - Harmonic component energy
* `features.percussive` - Percussive component energy
* `features.chroma` - Pitch class distribution (musical notes)
* `features.tonnetz` - Tonal centroid features (harmonic relationships)

**Dynamic Features:**
* `features.zero_crossing_rate` - Zero crossing rate (percussiveness)
* `features.novelty` - Novelty curve (change detection)

**Advanced Timbral (MFCCs):**
* `features.mfcc` - Mel-frequency cepstral coefficients (timbral texture)
* `features.mfcc_delta` - MFCC velocity (rate of timbral change)
* `features.mfcc_delta2` - MFCC acceleration (acceleration of timbral change)

All feature arrays are normalized to 0-1 range and indexed by frame (except `tempo`, `beat_frames`, and `beat_times` which have special formats).

### Feature Usage Tips

**For Bass-Heavy Visuals:**
Use `features.bass` or `features.sub_bass` for kick drum reactions, camera shake, or large particle explosions.

**For Melodic Content:**
Use `features.harmonic`, `features.chroma`, or `features.spectral_centroid` to react to singing, instruments, or tonal changes.

**For Drums/Percussion:**
Use `features.percussive`, `features.onset`, or `features.zero_crossing_rate` for hit markers, flash effects, or rhythmic animations.

**For Transitions/Drops:**
Use `features.novelty`, `features.spectral_flux`, or `features.spectral_contrast` to detect major changes and trigger scene transitions.

**For Brightness/Energy:**
Use `features.spectral_centroid`, `features.brilliance`, or `features.presence` for color intensity, particle density, or glow effects.

**For Rhythm Sync:**
Use `features.tempo`, `features.beat_times`, and `features.tempogram` to synchronize animations precisely to the beat.

**For Texture/Timbre:**
Use `features.mfcc`, `features.spectral_flatness`, or `features.spectral_bandwidth` to distinguish between different instruments or vocal characteristics.

---

## Performance Notes

* Audio playback runs in a separate thread for precise timing
* Visual rendering runs at target FPS (default 60)
* Feature extraction happens once at startup, not in real-time
* Pygame surface operations are the main performance bottleneck
* For better performance, reduce window size or simplify scene draw calls

---

## Extending the System

### Custom Audio Features
The audio analyzer already includes 36 comprehensive features. To add additional custom features:

```python
# In audio_analyzer.py, after existing feature extraction:
# Example: Extract polynomial features from spectral centroid
poly_features = librosa.feature.poly_features(S=S, sr=sr, order=1)

# Or extract rhythm patterns
rhythm_pattern = librosa.feature.fourier_tempogram(y=y, sr=sr)

# Add to AudioFeatures dataclass and return statement
```

### Using Beat Detection
The analyzer provides precise beat timing for synchronization:

```python
# In your scene's update method:
current_beats = features.beat_times[features.beat_times <= t]
if len(current_beats) > 0:
    time_since_last_beat = t - current_beats[-1]
    # Trigger effects on beats
```

### Scene Transitions
Implement custom transitions in `scene_manager.py`:

```python
# Add crossfade, wipe, or other transition effects
```

### Multiple Windows
Create separate Pygame windows for multi-monitor setups.

### Video Export
Integrate with moviepy or ffmpeg to render to video file.

---

## Troubleshooting

**Audio doesn't play:**
* Check audio file path is correct
* Ensure sounddevice can access your audio device
* Try a different audio format (MP3, WAV)

**Visualizer lags:**
* Reduce window size
* Lower FPS target
* Simplify scene drawing code
* Close other applications

**Import errors:**
* Ensure all dependencies are installed
* Check Python version (3.10+)
* Verify file structure matches documentation

**Features not responding:**
* Check audio file has dynamic content
* Verify feature extraction completed (watch console output)
* Ensure idx is within bounds of feature arrays

---

## License

This is a framework designed for customization and extension. Modify and build upon it as needed for your projects.