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
    GraffitiRapperScene,
    VinylRecordScene
)

# Configuration
AUDIO_PATH = "unbeatable.mp3"
INITIAL_WINDOW_SIZE = (1280, 720)
FPS = 60

def main():
    """
    Main entry point for the visualizer.
    Handles pygame initialization, audio playback, and scene management.
    Supports resizing and fullscreen toggle.
    """
    # Analyze audio
    features = analyze_audio(AUDIO_PATH)
    
    # Initialize pygame
    pygame.init()
    pygame.display.set_caption("FNF-style Advanced Song Visualizer")
    screen = pygame.display.set_mode(INITIAL_WINDOW_SIZE, pygame.RESIZABLE)
    clock = pygame.time.Clock()
    
    current_size = INITIAL_WINDOW_SIZE
    is_fullscreen = False
    
    # Create scenes with initial size
    stripes = EnhancedStripesScene(current_size)
    vinyl = VinylRecordScene(current_size)
    skeleton = SkeletonXRayScene(current_size)
    graffiti = GraffitiRapperScene(current_size)
    brain = BrainHUDScene(current_size)
    
    # Define scene timeline (split into 5 equal parts)
    fifth = features.duration / 5
    scenes = [
        SceneEntry(0.0, fifth, stripes),
        SceneEntry(fifth, fifth * 2, vinyl),
        SceneEntry(fifth * 2, fifth * 3, skeleton),
        SceneEntry(fifth * 3, fifth * 4, graffiti),
        SceneEntry(fifth * 4, features.duration, brain),
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
            
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                current_size = (event.w, event.h)
                screen = pygame.display.set_mode(current_size, pygame.RESIZABLE)
                
                # Recreate all scenes with new size
                stripes = EnhancedStripesScene(current_size)
                vinyl = VinylRecordScene(current_size)
                skeleton = SkeletonXRayScene(current_size)
                graffiti = GraffitiRapperScene(current_size)
                brain = BrainHUDScene(current_size)
                
                # Update scene entries
                scenes = [
                    SceneEntry(0.0, fifth, stripes),
                    SceneEntry(fifth, fifth * 2, vinyl),
                    SceneEntry(fifth * 2, fifth * 3, skeleton),
                    SceneEntry(fifth * 3, fifth * 4, graffiti),
                    SceneEntry(fifth * 4, features.duration, brain),
                ]
                manager = SceneManager(scenes)
            
            elif event.type == pygame.KEYDOWN:
                # Toggle fullscreen with F11 or F key
                if event.key in (pygame.K_F11, pygame.K_f):
                    is_fullscreen = not is_fullscreen
                    
                    if is_fullscreen:
                        # Switch to fullscreen
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        current_size = screen.get_size()
                    else:
                        # Switch back to windowed mode
                        screen = pygame.display.set_mode(INITIAL_WINDOW_SIZE, pygame.RESIZABLE)
                        current_size = INITIAL_WINDOW_SIZE
                    
                    # Recreate all scenes with new size
                    stripes = EnhancedStripesScene(current_size)
                    vinyl = VinylRecordScene(current_size)
                    skeleton = SkeletonXRayScene(current_size)
                    graffiti = GraffitiRapperScene(current_size)
                    brain = BrainHUDScene(current_size)
                    
                    # Update scene entries
                    scenes = [
                        SceneEntry(0.0, fifth, stripes),
                        SceneEntry(fifth, fifth * 2, vinyl),
                        SceneEntry(fifth * 2, fifth * 3, skeleton),
                        SceneEntry(fifth * 3, fifth * 4, graffiti),
                        SceneEntry(fifth * 4, features.duration, brain),
                    ]
                    manager = SceneManager(scenes)
                
                # Exit with ESC key
                elif event.key == pygame.K_ESCAPE:
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