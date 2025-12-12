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
    SkeletonXRayScene,
    GraffitiRapperScene,
    BrainHUDScene,
    VinylRecordScene,
    BeatSlicerScene,
    PulseCharacterSilhouetteScene,
)

# Configuration
AUDIO_PATH = "powerdown.mp3"
INITIAL_WINDOW_SIZE = (1280, 720)
FPS = 60


def build_scenes(size, duration):
    """
    Helper to (re)build scenes and timeline for a given window size.
    Mirrors existing behavior exactly.
    """
    stripes = EnhancedStripesScene(size)
    vinyl = VinylRecordScene(size)
    slicer = BeatSlicerScene(size)
    skeleton = SkeletonXRayScene(size)
    graffiti = GraffitiRapperScene(size)
    pulse_char = PulseCharacterSilhouetteScene(size)
    brain = BrainHUDScene(size)

    segment = duration / 7

    scenes = [
        SceneEntry(0.0, segment, stripes),
        SceneEntry(segment, segment * 2, vinyl),
        SceneEntry(segment * 2, segment * 3, slicer),
        SceneEntry(segment * 3, segment * 4, skeleton),
        SceneEntry(segment * 4, segment * 5, graffiti),
        SceneEntry(segment * 5, segment * 6, pulse_char),
        SceneEntry(segment * 6, duration, brain),
    ]

    return scenes


def main():
    # Analyze audio
    features = analyze_audio(AUDIO_PATH)

    # Init pygame
    pygame.init()
    pygame.display.set_caption("FNF-style Advanced Song Visualizer")
    screen = pygame.display.set_mode(INITIAL_WINDOW_SIZE, pygame.RESIZABLE)
    clock = pygame.time.Clock()

    current_size = INITIAL_WINDOW_SIZE
    is_fullscreen = False

    # Initial scene setup
    scenes = build_scenes(current_size, features.duration)
    manager = SceneManager(scenes)
    current_scene_index = 0  # Track manual scene selection
    manual_mode = False  # Toggle between auto and manual scene selection

    # Audio playback thread
    audio_thread = threading.Thread(
        target=play_audio_blocking,
        args=(AUDIO_PATH,),
        daemon=True
    )
    audio_thread.start()

    start_time = time.time()
    last_t = start_time
    running = True

    while running:
        dt = time.time() - last_t
        last_t = time.time()
        t = last_t - start_time

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                current_size = (event.w, event.h)
                screen = pygame.display.set_mode(current_size, pygame.RESIZABLE)
                scenes = build_scenes(current_size, features.duration)
                manager = SceneManager(scenes)

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_F11, pygame.K_f):
                    is_fullscreen = not is_fullscreen

                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        current_size = screen.get_size()
                    else:
                        screen = pygame.display.set_mode(
                            INITIAL_WINDOW_SIZE,
                            pygame.RESIZABLE
                        )
                        current_size = INITIAL_WINDOW_SIZE

                    scenes = build_scenes(current_size, features.duration)
                    manager = SceneManager(scenes)

                elif event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_m:
                    # Toggle manual mode
                    manual_mode = not manual_mode
                    if manual_mode:
                        # When entering manual mode, set to current auto scene
                        scene = manager.get_scene_for_time(t)
                        for i, entry in enumerate(scenes):
                            if entry.scene == scene:
                                current_scene_index = i
                                break

                elif event.key in (pygame.K_SPACE, pygame.K_TAB):
                    # Cycle to next scene
                    manual_mode = True
                    current_scene_index = (current_scene_index + 1) % len(scenes)

        # End when song finishes
        if t > features.duration:
            running = False

        # Feature index
        idx = np.searchsorted(features.times, t)
        idx = int(np.clip(idx, 0, len(features.times) - 1))

        # Active scene
        if manual_mode:
            # Use manually selected scene
            scene = scenes[current_scene_index].scene
        else:
            # Use automatic time-based scene
            scene = manager.get_scene_for_time(t)
            if scene is None:
                scene = scenes[0].scene

        # Update + draw
        scene.update(dt, t, features, idx)
        scene.draw(screen)

        # Draw mode indicator
        if manual_mode:
            font = pygame.font.Font(None, 24)
            scene_names = ["Stripes", "Vinyl", "Beat Slicer", "Skeleton", "Graffiti", "Pulse", "Brain"]
            mode_text = f"MANUAL MODE - Scene {current_scene_index + 1}/7: {scene_names[current_scene_index]}"
            text_surf = font.render(mode_text, True, (255, 255, 0))
            screen.blit(text_surf, (10, 10))
            
            help_text = font.render("SPACE/TAB: Next Scene | M: Auto Mode | ESC: Quit", True, (200, 200, 200))
            screen.blit(help_text, (10, 35))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()