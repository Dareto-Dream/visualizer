# Python Stereo Music Visualizer

This project is a modular, audio-reactive visualizer built with Python. It uses stereo audio analysis to drive multiple scene layouts in real time. The engine is inspired by multi-HUD visualizers such as FNF’s Erect Sampler but is designed to be fully extensible.

The system is separated into two parts:

1. `L_R.py` – stereo audio analysis (feature extraction)
2. `main.py` – scene system, rendering loop, timeline switching, and Pygame output

This structure keeps audio processing clean and independent from visuals.

---

## Features

* Stereo audio support (left and right channels analyzed independently)
* RMS, bass, mid, treble, and onset detection per channel
* Extensible scene system with a base Scene class
* Timeline-based scene switching
* Real-time rendering at 60 FPS
* Supports MP3, WAV, OGG, FLAC and most other audio formats

---

## Requirements

Python 3.10 or newer
Recommended: a virtual environment

Install dependencies:

```
pip install pygame librosa numpy sounddevice
```

If librosa raises codec issues on Windows, install FFmpeg:

```
choco install ffmpeg
```

---

## File Structure

```
visualizer/
│
├── L_R.py            # Stereo analyzer: loads audio, extracts features
├── main.py           # Visualizer engine, scenes, rendering loop
├── song.mp3          # Your audio file (any format supported)
└── README.md
```

---

## How It Works

### 1. Audio Analysis (`L_R.py`)

`L_R.py` loads the audio file in stereo and computes:

* RMS per channel
* Bass energy (20–150 Hz)
* Mid energy (150–2000 Hz)
* Treble energy (2000–8000 Hz)
* Onset strength (percussive spikes)

These are returned as arrays indexed by time so visuals can access them frame-by-frame.

### 2. Visualizer Engine (`main.py`)

`main.py` handles:

* Loading features from `L_R.py`
* Starting audio playback in a background thread
* Running the Pygame loop
* Selecting a scene based on the timeline
* Calling `update()` and `draw()` on the active scene

### 3. Scenes

Each scene subclasses the `BaseScene` class and implements:

```
update(dt, t, features, idx)
draw(surface)
```

Scenes can react to any stereo feature:

```
features.L_bass[idx]
features.R_rms[idx]
features.L_onset[idx]
...
```

You can create new files for additional scenes or define multiple scenes inside `main.py`.

---

## Running the Visualizer

Place an audio file in the project folder.
Update `AUDIO_PATH` in `main.py` if necessary:

```
AUDIO_PATH = "song.mp3"
```

Run:

```
python main.py
```

A window will open and the visualizer will run in real time while playing the music.

---

## Adding New Scenes

To create a new scene:

1. Subclass `BaseScene`
2. Implement `update()` and `draw()`
3. Add it to the timeline:

```
timeline = [
    SceneEntry(0, 20, stripes_scene),
    SceneEntry(20, 45, my_new_scene),
    SceneEntry(45, F.duration, brain_scene),
]
```

Scene transitions are instantaneous, but you can implement custom effects (crossfades, wipes, etc.)

---

## Notes

* For precise sync, audio playback runs in a dedicated thread while Pygame renders independently.
* Stereo features enable panning-based effects, left/right separation, and multi-HUD layouts.
* This is a framework, not a fixed visualizer; extend it as needed.