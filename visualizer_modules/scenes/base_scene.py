import pygame
from visualizer_modules.audio_analyzer import AudioFeatures


class BaseScene:
    """Base class for all visualization scenes."""
    
    def __init__(self, size):
        self.width, self.height = size

    def enter(self):
        """Called when scene becomes active."""
        pass

    def exit(self):
        """Called when scene is left."""
        pass

    def update(self, dt: float, t: float, features: AudioFeatures, idx: int):
        """
        Update scene state.
        
        Args:
            dt: Frame delta time
            t: Current song time in seconds
            features: AudioFeatures object
            idx: Current feature frame index
        """
        raise NotImplementedError

    def draw(self, surface: pygame.Surface):
        """
        Draw the scene.
        
        Args:
            surface: Pygame surface to draw on
        """
        raise NotImplementedError
