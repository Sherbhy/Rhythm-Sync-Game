# input/keyboard_handler.py
import keyboard
import time
from collections import defaultdict

class KeyboardHandler:
    def __init__(self, player_keys):
        """
        Initialize the keyboard handler for multiple players.
        
        Args:
            player_keys: Dictionary mapping player numbers to their assigned keys
        """
        self.player_keys = player_keys
        self.num_players = len(player_keys)
        self.player_claps = defaultdict(list)
        self.is_tracking = False
        self.last_press_time = {}  # To prevent key bouncing
        
        # Initialize last press time for each player
        for player_num in player_keys:
            self.last_press_time[player_num] = 0
    
    def start_tracking(self):
        """Start tracking keyboard inputs for all players."""
        self.is_tracking = True
        self.player_claps = defaultdict(list)
        print(f"Tracking keyboard inputs for {self.num_players} players...")
        for player_num, key in self.player_keys.items():
            print(f"Player {player_num}: Press '{key}' to clap")
    
    def stop_tracking(self):
        """Stop tracking keyboard inputs."""
        self.is_tracking = False
        print("Keyboard tracking stopped.")
    
    def check_inputs(self):
        """
        Check for keyboard inputs from all players.
        
        Returns:
            Dictionary mapping player numbers to clap times if they clapped, empty dict otherwise
        """
        if not self.is_tracking:
            return {}
        
        current_claps = {}
        current_time = time.time()
        
        for player_num, key in self.player_keys.items():
            # Check if enough time has passed since last press (debounce)
            time_since_last_press = current_time - self.last_press_time.get(player_num, 0)
            
            if keyboard.is_pressed(key) and time_since_last_press > 0.2:
                self.last_press_time[player_num] = current_time
                self.player_claps[player_num].append(current_time)
                current_claps[player_num] = current_time
                print(f"Player {player_num} clapped at: {current_time}")
        
        return current_claps
    
    def get_all_claps(self):
        """
        Get all recorded claps for all players.
        
        Returns:
            Dictionary mapping player numbers to their clap timestamps
        """
        return dict(self.player_claps)


# Test function for the keyboard handler
def test_keyboard_handler():
    """Test function for the keyboard handler."""
    import sys
    import os
    
    # Add the project root to the path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import PLAYER_KEYS
    
    # Create keyboard handler for 2 players
    handler = KeyboardHandler({1: PLAYER_KEYS[1], 2: PLAYER_KEYS[2]})
    
    # Start tracking
    handler.start_tracking()
    
    print("Press assigned keys to test claps. Press 'esc' to stop.")
    try:
        while True:
            claps = handler.check_inputs()
            for player, clap_time in claps.items():
                print(f"Player {player} clapped!")
            
            if keyboard.is_pressed('esc'):
                break
            
            time.sleep(0.01)  # Small sleep to prevent CPU hogging
    
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    
    finally:
        # Print results
        handler.stop_tracking()
        all_claps = handler.get_all_claps()
        for player, claps in all_claps.items():
            print(f"Player {player} made {len(claps)} claps")


if __name__ == "__main__":
    test_keyboard_handler()