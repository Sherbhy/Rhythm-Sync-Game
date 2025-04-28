# game/music_player.py
import pygame
import os
import time

class MusicPlayer:
    def __init__(self, music_dir):
        """
        Initialize the music player.
        
        Args:
            music_dir: Directory containing music files
        """
        self.music_dir = music_dir
        self.current_song = None
        self.current_bpm = None
        self.is_playing = False
        
        # Initialize pygame mixer if not already initialized
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
    
    def load_song(self, song_name, bpm):
        """
        Load a song for playback.
        
        Args:
            song_name: Name of the song to load
            bpm: Beats per minute of the song
        
        Returns:
            True if the song was loaded successfully, False otherwise
        """
        self.current_song = song_name
        self.current_bpm = bpm
        
        # Build filename (assuming format: SongName.mp3)
        filename = f"{song_name.replace(' ', '')}.mp3"
        full_path = os.path.join(self.music_dir, filename)
        
        try:
            pygame.mixer.music.load(full_path)
            print(f"Loaded song: {song_name} ({bpm} BPM)")
            return True
        except pygame.error as e:
            print(f"Error loading song {song_name}: {e}")
            return False
    
    def play(self):
        """Start playback of the loaded song."""
        if self.current_song:
            pygame.mixer.music.play()
            self.is_playing = True
            print(f"Now playing: {self.current_song} ({self.current_bpm} BPM)")
            return True
        else:
            print("No song loaded.")
            return False
    
    def stop(self):
        """Stop playback of the current song."""
        pygame.mixer.music.stop()
        self.is_playing = False
        print("Playback stopped.")
    
    def pause(self):
        """Pause playback of the current song."""
        pygame.mixer.music.pause()
        self.is_playing = False
        print("Playback paused.")
    
    def unpause(self):
        """Resume playback of the current song."""
        pygame.mixer.music.unpause()
        self.is_playing = True
        print("Playback resumed.")
    
    def get_beat_times(self, start_time, duration):
        """
        Calculate beat times based on BPM.
        
        Args:
            start_time: Time when tracking starts
            duration: Duration to generate beat times for
        
        Returns:
            List of beat timestamps
        """
        if not self.current_bpm:
            print("No BPM information available.")
            return []
        
        # Calculate beat interval (assuming 4/4 time signature)
        interval = 60 / self.current_bpm * 2  # seconds between beats
        
        # Generate beat times
        beat_times = [start_time + i * interval for i in range(int(duration / interval) + 1)]
        return beat_times
    
    def is_beat_active(self, current_time, beat_times, tolerance):
        """
        Check if a beat is currently active.
        
        Args:
            current_time: Current time to check
            beat_times: List of beat timestamps
            tolerance: Tolerance window for beat matching
        
        Returns:
            True if a beat is active, False otherwise
        """
        return any(abs(current_time - beat) <= tolerance for beat in beat_times)


# Test function for the music player
def test_music_player():
    """Test function for the music player."""
    import sys
    import os
    
    # Add the project root to the path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import MUSIC_DIR, SONGS
    
    # Initialize pygame
    pygame.init()
    
    # Create music player
    player = MusicPlayer(MUSIC_DIR)
    
    # Get the first song
    first_song = next(iter(SONGS))
    first_bpm = SONGS[first_song]
    
    # Load and play the song
    if player.load_song(first_song, first_bpm):
        player.play()
        
        # Generate beat times
        start_time = time.time()
        beat_times = player.get_beat_times(start_time, 10)
        
        print("Tracking beats for 10 seconds...")
        for i in range(100):
            current_time = time.time()
            elapsed = current_time - start_time
            
            if elapsed > 10:
                break
            
            if player.is_beat_active(current_time, beat_times, 0.1):
                print("BEAT!")
            
            time.sleep(0.1)
        
        # Stop the player
        player.stop()
    else:
        print("Failed to load song. Check the music directory and file name.")


if __name__ == "__main__":
    test_music_player()