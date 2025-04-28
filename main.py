# main.py
import pygame
import sys
import time
import os

# Import game modules
from config import (
    MUSIC_DIR, SONGS, PLAYER_KEYS, 
    SAMPLE_RATE, BUFFER_SIZE, AUDIO_CHANNELS, 
    DEFAULT_THRESHOLD, MIN_TIME_BETWEEN_CLAPS, CALIBRATION_DURATION,
    DEFAULT_GAME_DURATION, COUNTDOWN_DURATION, BEAT_TOLERANCE, SCORE_THRESHOLD
)
from input.keyboard_handler import KeyboardHandler
from input.audio_handler import AudioHandler
from game.music_player import MusicPlayer
from game.scoring import Scoring
from game.game_logic import GameLogic
from utils.helpers import format_time, get_difficulty_name


def initialize_game(input_mode, num_players=1):
    """
    Initialize the game components.
    
    Args:
        input_mode: "keyboard" for Makey Makey or "audio" for clap detection
        num_players: Number of players (only used for keyboard mode)
    
    Returns:
        GameLogic instance
    """
    # Initialize pygame if not already initialized
    if pygame.get_init() is None:
        pygame.init()
    if pygame.mixer.get_init() is None:
        pygame.mixer.init()
    
    # Create music player
    music_player = MusicPlayer(MUSIC_DIR)
    
    # Create input handlers based on selected mode
    if input_mode == "keyboard":
        # Create keyboard mapping for the specified number of players
        player_keys = {i: PLAYER_KEYS[i] for i in range(1, num_players + 1)}
        print(f"\nKeyboard mapping for {num_players} players:")
        for player_num, key in player_keys.items():
            print(f"Player {player_num}: '{key}' key")
        
        keyboard_handler = KeyboardHandler(player_keys)
        # Create a dummy audio handler that won't be used
        audio_handler = AudioHandler(
            sample_rate=SAMPLE_RATE,
            buffer_size=BUFFER_SIZE,
            channels=AUDIO_CHANNELS,
            threshold=DEFAULT_THRESHOLD,
            min_time_between_claps=MIN_TIME_BETWEEN_CLAPS
        )
        # Don't start the audio handler
        audio_handler.running = False
        
    else:  # audio mode
        # Create a dummy keyboard handler with no players
        keyboard_handler = KeyboardHandler({})
        # Create and calibrate the audio handler
        audio_handler = AudioHandler(
            sample_rate=SAMPLE_RATE,
            buffer_size=BUFFER_SIZE,
            channels=AUDIO_CHANNELS,
            threshold=DEFAULT_THRESHOLD,
            min_time_between_claps=MIN_TIME_BETWEEN_CLAPS
        )
        print("\nUsing audio/clap detection mode.")
        print("Calibrating microphone...")
        audio_handler.calibrate(CALIBRATION_DURATION)
        # Player count is always 1 for audio mode (shared microphone)
        num_players = 1
    
    # Create scoring system
    scoring = Scoring(player_count=num_players)
    
    # Create game logic
    game = GameLogic(music_player, keyboard_handler, audio_handler, scoring)
    game.set_songs(SONGS)
    game.set_game_settings(
        duration=DEFAULT_GAME_DURATION, 
        countdown=COUNTDOWN_DURATION, 
        tolerance=BEAT_TOLERANCE, 
        score_threshold=SCORE_THRESHOLD
    )
    
    # Set the input mode in the game logic
    game.input_mode = input_mode
    
    return game


def main():
    """Main function to run the game."""
    print("======================================")
    print("Welcome to Mackey Mackey Rhythm Game!")
    print("======================================")
    
    # Select input mode
    print("\nSelect input mode:")
    print("1. Makey Makey / Keyboard")
    print("2. Audio (Clap Detection)")
    
    input_mode_choice = ""
    while input_mode_choice not in ["1", "2"]:
        input_mode_choice = input("Enter your choice (1-2): ")
    
    input_mode = "keyboard" if input_mode_choice == "1" else "audio"
    
    num_players = 1
    if input_mode == "keyboard":
        # Ask user how many players (only for keyboard mode)
        while num_players < 2 or num_players > 4:
            try:
                num_players = int(input("\nHow many players? (2-4): "))
                if num_players < 2 or num_players > 4:
                    print("Please enter a number between 2 and 4.")
            except ValueError:
                print("Please enter a valid number.")
    
    # Initialize the game
    game = initialize_game(input_mode, num_players)
    
    # Display available songs
    print("\nAvailable songs:")
    for i, (song, bpm) in enumerate(SONGS.items(), 1):
        difficulty = get_difficulty_name(bpm)
        print(f"{i}. {song} - {bpm} BPM ({difficulty})")
    
    # Main game loop
    running = True
    while running:
        print("\nMenu:")
        print("1. Start Game")
        print("2. Quit")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == '1':
            # Start the game
            print("\nStarting game...")
            if input_mode == "audio" and not game.audio_handler.running:
                game.audio_handler.start()
                
            if game.start_game():
                try:
                    # Game loop
                    while game.update():
                        # Display remaining time
                        if game.is_tracking:
                            elapsed = time.time() - game.start_time
                            remaining = max(0, game.game_duration - elapsed)
                            print(f"Time: {remaining:.1f}s", end="\r", flush=True)
                        time.sleep(0.01)  # Small sleep to prevent CPU hogging
                
                except KeyboardInterrupt:
                    print("\nGame interrupted.")
                    game.end_game()
                
                # Game ended
                play_again = input("\nPlay again? (y/n): ")
                if play_again.lower() != 'y':
                    running = False
            else:
                print("Failed to start game. Please try again.")
        
        elif choice == '2':
            running = False
        
        else:
            print("Invalid choice. Please try again.")
    
    # Cleanup
    if input_mode == "audio" and hasattr(game, 'audio_handler') and game.audio_handler.running:
        game.audio_handler.stop()
    
    pygame.quit()
    print("Thanks for playing!")
    sys.exit()


if __name__ == "__main__":
    main()