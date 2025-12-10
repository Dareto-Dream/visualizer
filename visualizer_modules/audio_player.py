import librosa
import sounddevice as sd


def play_audio_blocking(path: str):
    """
    Play audio file using sounddevice.
    This is blocking and should be run in a separate thread.
    
    Args:
        path: Path to audio file
    """
    y, sr = librosa.load(path, sr=None, mono=True)
    sd.play(y, sr)
    sd.wait()
