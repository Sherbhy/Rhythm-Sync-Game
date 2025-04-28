# game/game_logic.py
import time
import keyboard

class GameLogic:
    def __init__(self, music_player, keyboard_handler, audio_handler, scoring):
        """
        Initialize the game logic.
        
        Args:
            music_player: Instance of MusicPlayer
            keyboard_handler: Instance of KeyboardHandler
            audio_handler: Instance of AudioHandler
            scoring: Instance of Scoring
        """
        self.music_player = music_player
        self.keyboard_handler = keyboard_handler
        self.audio_handler = audio_handler
        self.scoring = scoring
        
        self.songs = {}  # Will be populated from configuration
        self.current_song = None
        self.current_bpm = None
        self.beat_times = []
        self.is_playing = False
        self.is_tracking = False
        self.start_time = 0
        self.game_duration = 20  # seconds
        self.countdown = 5  # seconds
        self.tolerance = 0.2  # seconds
        self.score_threshold = 5
        self.input_mode = "keyboard"  # Default input mode
        
        # Set up the audio handler callback
        self.audio_handler.set_clap_callback(self.handle_audio_clap)
    
    def set_songs(self, songs_dict):
        """
        Set the available songs.
        
        Args:
            songs_dict: Dictionary mapping song names to BPM values
        """
        self.songs = songs_dict
        if not self.current_song and self.songs:
            self.current_song = next(iter(self.songs))
            self.current_bpm = self.songs[self.current_song]
    
    def set_game_settings(self, duration=20, countdown=5, tolerance=0.2, score_threshold=5):
        """
        Set game settings.
        
        Args:
            duration: Game duration in seconds
            countdown: Countdown duration in seconds
            tolerance: Beat matching tolerance in seconds
            score_threshold: Score threshold to advance to next song
        """
        self.game_duration = duration
        self.countdown = countdown
        self.tolerance = tolerance
        self.score_threshold = score_threshold
    
    def start_game(self):
        """Start the game."""
        if not self.current_song:
            print("No song selected.")
            return False
        
        # Load and play the current song
        if not self.music_player.load_song(self.current_song, self.current_bpm):
            print("Failed to load song.")
            return False
        
        self.music_player.play()
        self.is_playing = True
        
        # Begin countdown
        print(f"Game starting in {self.countdown} seconds...")
        print(f"Get ready to play: {self.current_song} at {self.current_bpm} BPM")
        time.sleep(self.countdown)
        
        # Start tracking
        self.start_tracking()
        return True
    
    def start_tracking(self):
        """Start tracking player inputs and beats."""
        self.start_time = time.time()
        self.is_tracking = True
        
        # Generate beat times
        self.beat_times = self.music_player.get_beat_times(
            self.start_time, self.game_duration)
        
        # Reset scores
        self.scoring.reset_scores()
        
        # Start appropriate input handlers based on mode
        if self.input_mode == "keyboard":
            self.keyboard_handler.start_tracking()
            print("Tracking keyboard inputs! Press your assigned keys to the beat.")
        elif self.input_mode == "audio":
            # Make sure audio handler is running
            if not self.audio_handler.running:
                self.audio_handler.start()
            print("Tracking audio claps! Clap your hands to the beat.")
        
        print("Tracking started! Play along with the beats.")
    
    def handle_audio_clap(self, timestamp):
        """
        Handle a clap detected by the audio handler.
        
        Args:
            timestamp: Time of the clap
        """
        if self.is_tracking:
            is_on_beat = self.is_on_beat(timestamp)
            # Assuming claps from audio are player 1
            self.scoring.register_clap(1, is_on_beat)
    
    def is_on_beat(self, timestamp):
        """
        Check if a timestamp is on beat.
        
        Args:
            timestamp: Time to check
        
        Returns:
            True if on beat, False otherwise
        """
        return any(abs(timestamp - beat) <= self.tolerance for beat in self.beat_times)
    
    def update(self):
        """
        Update game state.
        
        Returns:
            True if the game is still running, False if it has ended
        """
        if not self.is_playing:
            return True
        
        current_time = time.time()
        
        # Check if game should end
        if self.is_tracking and current_time - self.start_time > self.game_duration:
            self.end_game()
            return False
        
        # Process inputs based on mode
        if self.is_tracking:
            # Check keyboard inputs if in keyboard mode
            if self.input_mode == "keyboard":
                claps = self.keyboard_handler.check_inputs()
                for player_id, clap_time in claps.items():
                    is_on_beat = self.is_on_beat(clap_time)
                    self.scoring.register_clap(player_id, is_on_beat)
            
            # Audio claps are handled by the callback in handle_audio_clap()
            
            # Check for any current beats
            for beat_time in self.beat_times:
                if abs(current_time - beat_time) < 0.01 and beat_time > self.start_time:
                    # This is close enough to a beat
                    self.scoring.register_beat()
                    print("BEAT!")
        
        # Check for ESC key to end game early
        if keyboard.is_pressed('esc'):
            print("Game interrupted.")
            self.end_game()
            return False
        
        return True
    
    def end_game(self):
        """End the game and calculate final scores."""
        if not self.is_playing:
            return
        
        self.is_playing = False
        self.is_tracking = False
        
        # Stop music and input handlers
        self.music_player.stop()
        self.keyboard_handler.stop_tracking()
        
        # Print final scores
        print("\n===== Game Over! =====")
        all_scores = self.scoring.get_all_scores()
        for player_id, score in all_scores.items():
            print(f"Player {player_id}: {score['on_beat']}/{score['claps']} claps on beat ({score['percentage']:.1f}%)")
        
        # Determine winner
        winner = self.scoring.get_winner()
        if winner:
            player_id, score = winner
            print(f"Winner: Player {player_id} with {score['on_beat']} claps on beat!")
        
        # Select next song
        self.select_next_song()
    
    def select_next_song(self):
        """Select the next song based on performance."""
        winner = self.scoring.get_winner()
        if not winner:
            return
        
        _, score = winner
        performance = score['on_beat']
        
        # Get sorted list of BPMs
        bpms = sorted(self.songs.values())
        current_index = bpms.index(min(bpms, key=lambda x: abs(x - self.current_bpm)))
        
        # Determine next BPM based on performance
        if performance > self.score_threshold and current_index < len(bpms) - 1:
            next_bpm = bpms[current_index + 1]
            print("Great job! Moving to a faster song.")
        elif performance <= self.score_threshold and current_index > 0:
            next_bpm = bpms[current_index - 1]
            print("Let's try an easier tempo.")
        else:
            next_bpm = self.current_bpm
            print("Let's try this tempo again.")
        
        # Find the song with the matching BPM
        for name, bpm in self.songs.items():
            if bpm == next_bpm:
                self.current_song = name
                self.current_bpm = bpm
                print(f"Next song: {name} ({bpm} BPM)")
                return
    
    def play_next_song(self):
        """Play the selected next song."""
        return self.start_game()


# Test function for the game logic
def test_game_logic():
    """Test function for the game logic."""
    import sys
    import os
    import pygame
    
    # Add the project root to the path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import MUSIC_DIR, SONGS, PLAYER_KEYS, SAMPLE_RATE, BUFFER_SIZE, AUDIO_CHANNELS, DEFAULT_THRESHOLD, MIN_TIME_BETWEEN_CLAPS
    
    # Import needed modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from input.keyboard_handler import KeyboardHandler
    from input.audio_handler import AudioHandler
    from game.music_player import MusicPlayer
    from game.scoring import Scoring
    
    # Initialize pygame
    pygame.init()
    
    # Create components
    music_player = MusicPlayer(MUSIC_DIR)
    keyboard_handler = KeyboardHandler({1: PLAYER_KEYS[1], 2: PLAYER_KEYS[2]})
    audio_handler = AudioHandler(
        sample_rate=SAMPLE_RATE,
        buffer_size=BUFFER_SIZE,
        channels=AUDIO_CHANNELS,
        threshold=DEFAULT_THRESHOLD,
        min_time_between_claps=MIN_TIME_BETWEEN_CLAPS
    )
    scoring = Scoring(player_count=2)
    
    # Create game logic
    game = GameLogic(music_player, keyboard_handler, audio_handler, scoring)
    game.set_songs(SONGS)
    game.set_game_settings(duration=20, countdown=3, tolerance=0.2, score_threshold=5)
    
    # Start the game
    if game.start_game():
        print("Game started successfully!")
        
        # Main game loop
        while game.update():
            time.sleep(0.01)  # Small sleep to prevent CPU hogging
    
    print("Game test complete.")


if __name__ == "__main__":
    test_game_logic()