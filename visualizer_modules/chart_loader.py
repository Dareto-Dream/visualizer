import json
import numpy as np
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChartNote:
    """Represents a single note from a chart."""
    time: float          # Time in seconds
    lane: int           # Lane index (0-3)
    sustain: float      # Sustain length in seconds
    is_player: bool     # True if player note, False if opponent


@dataclass
class ChartData:
    """
    Contains all parsed chart information.
    Provides a clean interface for scenes to access chart data.
    """
    bpm: float
    scroll_speed: float
    duration: float
    player1: str
    player2: str
    notes: List[ChartNote]
    player_notes: List[ChartNote]
    opponent_notes: List[ChartNote]
    
    def get_notes_in_range(self, start_time: float, end_time: float, 
                          player_only: bool = True) -> List[ChartNote]:
        """
        Get all notes within a time range.
        
        Args:
            start_time: Start of time range in seconds
            end_time: End of time range in seconds
            player_only: If True, only return player notes
            
        Returns:
            List of ChartNote objects in the time range
        """
        notes = self.player_notes if player_only else self.notes
        return [
            note for note in notes
            if start_time <= note.time <= end_time
        ]
    
    def get_note_density(self, time: float, window: float = 1.0,
                        player_only: bool = True) -> float:
        """
        Calculate note density (notes per second) around a given time.
        
        Args:
            time: Center time in seconds
            window: Time window in seconds (default 1.0)
            player_only: If True, only count player notes
            
        Returns:
            Notes per second in the window
        """
        notes_in_window = self.get_notes_in_range(
            time - window/2, 
            time + window/2,
            player_only
        )
        return len(notes_in_window) / window
    
    def is_note_at_time(self, time: float, lane: int, 
                       threshold: float = 0.05,
                       player_only: bool = True) -> bool:
        """
        Check if there's a note at a specific time and lane.
        
        Args:
            time: Time to check in seconds
            lane: Lane to check (0-3)
            threshold: Time tolerance in seconds
            player_only: If True, only check player notes
            
        Returns:
            True if a note exists within threshold
        """
        notes = self.player_notes if player_only else self.notes
        for note in notes:
            if note.lane == lane and abs(note.time - time) < threshold:
                return True
        return False


class ChartLoader:
    """
    Loads and parses Psych Engine chart files.
    Provides chart data in a clean format for visualizer scenes.
    """
    
    @staticmethod
    def load(chart_path: str, audio_duration: Optional[float] = None) -> ChartData:
        """
        Load a Psych Engine chart JSON file.
        
        Args:
            chart_path: Path to the chart JSON file
            audio_duration: Optional audio duration for validation
            
        Returns:
            ChartData object with parsed chart information
            
        Raises:
            FileNotFoundError: If chart file doesn't exist
            ValueError: If chart format is invalid
        """
        try:
            with open(chart_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Chart file not found: {chart_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in chart file: {e}")
        
        # Extract song data
        song_data = data.get('song', {})
        if not song_data:
            raise ValueError("Chart missing 'song' data")
        
        # Basic info
        bpm = song_data.get('bpm', 120)
        scroll_speed = song_data.get('speed', 3.0)
        player1 = song_data.get('player1', 'bf')
        player2 = song_data.get('player2', 'dad')
        
        # Parse notes from sections
        all_notes = []
        sections = song_data.get('notes', [])
        
        for section in sections:
            section_notes = section.get('sectionNotes', [])
            must_hit = section.get('mustHitSection', False)
            
            for note_data in section_notes:
                # Validate note format
                if not isinstance(note_data, list) or len(note_data) < 3:
                    continue
                
                # Skip events (lane -1)
                if not isinstance(note_data[1], (int, float)) or note_data[1] < 0:
                    continue
                
                time_ms = float(note_data[0])
                lane = int(note_data[1])
                sustain_ms = float(note_data[2])
                
                # Determine if it's a player or opponent note
                # In Psych Engine:
                # - Lanes 0-3: Opponent by default
                # - Lanes 4-7: Player by default
                # - mustHitSection swaps this behavior
                
                if lane >= 4:
                    # Remove offset for lanes 4-7
                    lane = lane - 4
                    is_player = True
                else:
                    is_player = False
                
                # mustHitSection swaps player/opponent
                if must_hit:
                    is_player = not is_player
                
                # Create note
                note = ChartNote(
                    time=time_ms / 1000.0,
                    lane=lane,
                    sustain=sustain_ms / 1000.0,
                    is_player=is_player
                )
                all_notes.append(note)
        
        # Sort notes by time
        all_notes.sort(key=lambda n: n.time)
        
        # Separate player and opponent notes
        player_notes = [n for n in all_notes if n.is_player]
        opponent_notes = [n for n in all_notes if not n.is_player]
        
        # Calculate duration from last note if not provided
        if audio_duration is None:
            if all_notes:
                duration = max(n.time + n.sustain for n in all_notes) + 2.0
            else:
                duration = 60.0  # Default fallback
        else:
            duration = audio_duration
        
        print(f"[ChartLoader] Loaded chart from {chart_path}")
        print(f"[ChartLoader]   BPM: {bpm}")
        print(f"[ChartLoader]   Speed: {scroll_speed}")
        print(f"[ChartLoader]   Total notes: {len(all_notes)}")
        print(f"[ChartLoader]   Player notes: {len(player_notes)}")
        print(f"[ChartLoader]   Opponent notes: {len(opponent_notes)}")
        
        return ChartData(
            bpm=bpm,
            scroll_speed=scroll_speed,
            duration=duration,
            player1=player1,
            player2=player2,
            notes=all_notes,
            player_notes=player_notes,
            opponent_notes=opponent_notes
        )
    
    @staticmethod
    def create_empty(bpm: float = 120, duration: float = 60.0) -> ChartData:
        """
        Create an empty chart data object.
        Useful for scenes that don't require chart data.
        
        Args:
            bpm: Beats per minute
            duration: Duration in seconds
            
        Returns:
            Empty ChartData object
        """
        return ChartData(
            bpm=bpm,
            scroll_speed=3.0,
            duration=duration,
            player1='bf',
            player2='dad',
            notes=[],
            player_notes=[],
            opponent_notes=[]
        )