# config.py
# Central configuration file for the Mackey Mackey game

# Path to music files
MUSIC_DIR = r""

# Song database with BPM information
SONGS = {
    "Hotel California": 74,
    "Yellow": 84,
    "Chaiyya Chaiyya": 92,
    "Chasing Cars": 104,
    "Another One Bites The Dust": 110,
    "Dynamite": 116,
    "Beat It": 140,
}

# Default game settings
DEFAULT_GAME_DURATION = 20  # seconds
COUNTDOWN_DURATION = 5  # seconds
BEAT_TOLERANCE = 0.2  # seconds allowable error
SCORE_THRESHOLD = 5  # minimum score to advance to the next level

# Keyboard mappings for different players (Makey Makey compatible keys)
PLAYER_KEYS = {
    1: "space",  # Player 1 - Space key
    2: "up",     # Player 2 - Up arrow
    3: "down",   # Player 3 - Down arrow
    4: "left",   # Player 4 - Left arrow
}

# Audio detection settings
SAMPLE_RATE = 44100
BUFFER_SIZE = 1024
AUDIO_CHANNELS = 1
DEFAULT_THRESHOLD = 0.1
MIN_TIME_BETWEEN_CLAPS = 0.5
CALIBRATION_DURATION = 3  # seconds