from dataclasses import dataclass
from typing import List
from visualizer_modules.scenes.base_scene import BaseScene


@dataclass
class SceneEntry:
    """Defines when a scene should be active."""
    start: float
    end: float
    scene: BaseScene


class SceneManager:
    """
    Manages scene transitions based on song timeline.
    """
    
    def __init__(self, scenes: List[SceneEntry]):
        self.scenes = scenes
        self.current = None

    def get_scene_for_time(self, t: float) -> BaseScene:
        """
        Get the appropriate scene for the current time.
        
        Args:
            t: Current time in seconds
            
        Returns:
            BaseScene instance that should be active
        """
        for entry in self.scenes:
            if entry.start <= t < entry.end:
                if self.current is not entry.scene:
                    if self.current:
                        self.current.exit()
                    self.current = entry.scene
                    self.current.enter()
                return entry.scene
        return self.current
