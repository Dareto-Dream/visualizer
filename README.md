# Python Music Visualizer

This project is a modular, audio-reactive visualizer built with Python. It uses audio analysis to drive multiple scene layouts in real time. The engine is inspired by multi-HUD visualizers such as FNF's visual style but is designed to be fully extensible.

The system is separated into clean modules:

1. Audio analysis - feature extraction from audio files
2. Scene system - modular visual scenes with base class
3. Main engine - rendering loop, timeline switching, and Pygame output

This structure keeps audio processing clean and independent from visuals.

---

## Features

* Comprehensive audio analysis (RMS, bass, mid, treble, onset detection)
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

The audio analyzer loads audio files and computes:

* RMS (overall energy/loudness)
* Bass energy (20-150 Hz)
* Mid energy (150-2000 Hz)
* Treble energy (2000-8000 Hz)
* Onset strength (percussive spikes)

These are normalized to 0-1 range and returned as time-indexed arrays for frame-by-frame access.

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
        # Store audio features you need
        self.bass = features.bass[idx]
        self.onset = features.onset[idx]
    
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

* `features.times` - Time array for each frame
* `features.rms` - Root mean square (overall loudness)
* `features.bass` - Low frequency energy (20-150 Hz)
* `features.mid` - Mid frequency energy (150-2000 Hz)
* `features.treble` - High frequency energy (2000-8000 Hz)
* `features.onset` - Onset strength (beat detection)
* `features.duration` - Total song duration
* `features.sr` - Sample rate

All feature arrays are normalized to 0-1 range and indexed by frame.

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
Add new feature extraction in `audio_analyzer.py`:

```python
# Extract spectral centroid, zero crossing rate, etc.
custom_feature = librosa.feature.spectral_centroid(y=y, sr=sr)
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