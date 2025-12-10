import time
import threading
import numpy as np
import pygame

from visualizer_modules import (
    analyze_audio,
    play_audio_blocking,
    SceneManager,
    SceneEntry,
    EnhancedStripesScene,
    BrainHUDScene,
    SkeletonXRayScene,
    GraffitiRapperScene
)


# Configuration
AUDIO_PATH = "unbeatable.mp3"
WINDOW_SIZE = (1280, 720)
FPS = 60


def main():
    """
    Main entry point for the visualizer.
    Handles pygame initialization, audio playback, and scene management.
    """
    # Analyze audio
    features = analyze_audio(AUDIO_PATH)

    # Initialize pygame
    pygame.init()
    pygame.display.set_caption("FNF-style Advanced Song Visualizer")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()

    # Create scenes
    stripes = EnhancedStripesScene(WINDOW_SIZE)
    skeleton = SkeletonXRayScene(WINDOW_SIZE)
    graffiti = GraffitiRapperScene(WINDOW_SIZE)
    brain = BrainHUDScene(WINDOW_SIZE)

    # Define scene timeline (split into 4 equal parts)
    quarter = features.duration / 4
    scenes = [
        SceneEntry(0.0, quarter, stripes),
        SceneEntry(quarter, quarter * 2, skeleton),
        SceneEntry(quarter * 2, quarter * 3, graffiti),
        SceneEntry(quarter * 3, features.duration, brain),
    ]
    manager = SceneManager(scenes)

    # Start audio playback in background thread
    audio_thread = threading.Thread(
        target=play_audio_blocking,
        args=(AUDIO_PATH,),
        daemon=True
    )
    audio_thread.start()
    start_time = time.time()

    # Main loop
    running = True
    last_t = start_time
    
    while running:
        dt = time.time() - last_t
        last_t = time.time()
        t = last_t - start_time

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Stop when song ends
        if t > features.duration:
            running = False

        # Find current feature index
        idx = np.searchsorted(features.times, t)
        idx = int(np.clip(idx, 0, len(features.times) - 1))

        # Get active scene
        scene = manager.get_scene_for_time(t)
        if scene is None:
            scene = scenes[0].scene

        # Update and draw
        scene.update(dt, t, features, idx)
        scene.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
