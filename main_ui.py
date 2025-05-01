import pygame
import sys
import os
import time
import math
import random
from pygame.locals import *
import numpy

# Import game modules
from config import (
    MUSIC_DIR, SONGS, PLAYER_KEYS, 
    DEFAULT_GAME_DURATION, COUNTDOWN_DURATION, BEAT_TOLERANCE, SCORE_THRESHOLD
)
from input.keyboard_handler import KeyboardHandler
from input.audio_handler import AudioHandler
from game.music_player import MusicPlayer
from game.scoring import Scoring
from game.game_logic import GameLogic
from utils.helpers import format_time, get_difficulty_name

# Initialize pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

# Colors - Simplified color palette with one main accent color
PRIMARY_BG = (18, 18, 35)  # Dark blue-purple background
SECONDARY_BG = (30, 30, 60)  # Slightly lighter for panels
ACCENT_COLOR = (103, 65, 217)  # Main purple accent color
ACCENT_SECONDARY = (103, 65, 217)  # Same as ACCENT_COLOR for consistency
SUCCESS_COLOR = (46, 213, 115)  # Green for success indicators
WARNING_COLOR = (255, 165, 2)  # Bright orange
WHITE = (255, 255, 255)
LIGHT_TEXT = (230, 230, 250)  # Slightly off-white for better eye comfort
GRAY = (150, 150, 180)
DARK_GRAY = (60, 60, 90)
TRANSPARENT_BLACK = (0, 0, 0, 180)

# Modify the font sizes to be smaller for better fit
TITLE_FONT = pygame.font.Font(None, 56) if pygame.font.get_default_font() else pygame.font.SysFont('Arial', 42, bold=True)
SUBTITLE_FONT = pygame.font.Font(None, 42) if pygame.font.get_default_font() else pygame.font.SysFont('Arial', 32, bold=True)
BUTTON_FONT = pygame.font.Font(None, 32) if pygame.font.get_default_font() else pygame.font.SysFont('Arial', 24, bold=True)
TEXT_FONT = pygame.font.Font(None, 24) if pygame.font.get_default_font() else pygame.font.SysFont('Arial', 20)
SMALL_FONT = pygame.font.Font(None, 18) if pygame.font.get_default_font() else pygame.font.SysFont('Arial', 16)

# Debug mode
DEBUG = True

def debug_print(message):
    """Print debug messages if DEBUG is True."""
    if DEBUG:
        print(f"[DEBUG] {message}")

class Button:
    def __init__(self, x, y, width, height, text, color=ACCENT_COLOR, hover_color=None, text_color=WHITE, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color or self.lighten_color(color, 30)
        self.text_color = text_color
        self.action = action
        self.is_hovered = False
        self.is_active = False
        self.animation = 0  # For button animation
        
    def lighten_color(self, color, amount):
        """Return a lighter version of the color."""
        return tuple(min(c + amount, 255) for c in color)
        
    def draw(self, screen):
        # Determine button color based on state
        if self.is_active:
            color = SUCCESS_COLOR
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color
        
        # Button animation when hovered
        anim_offset = 0
        if self.is_hovered:
            self.animation = min(1.0, self.animation + 0.1)
        else:
            self.animation = max(0.0, self.animation - 0.1)
        
        anim_offset = int(self.animation * 3)
        
        # Draw button with modern styling
        # Shadow
        shadow_rect = pygame.Rect(self.rect.x + 4, self.rect.y + 4, self.rect.width, self.rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=12)
        
        # Main button
        button_rect = pygame.Rect(self.rect.x, self.rect.y - anim_offset, self.rect.width, self.rect.height)
        pygame.draw.rect(screen, color, button_rect, border_radius=12)
        
        # Button text with shadow for better readability
        text_surf = BUTTON_FONT.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        
        # Text shadow
        shadow_surf = BUTTON_FONT.render(self.text, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(text_rect.centerx + 2, text_rect.centery + 2))
        screen.blit(shadow_surf, shadow_rect)
        
        # Main text
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            if self.action:
                self.action()
            return True
        return False

class RadioButton:
    def __init__(self, x, y, radius, text, group, value, selected=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.text = text
        self.group = group
        self.value = value
        self.selected = selected
        self.animation = 0  # For animation
        
    def draw(self, screen):
        # Outer circle
        pygame.draw.circle(screen, LIGHT_TEXT, (self.x, self.y), self.radius + 2)
        pygame.draw.circle(screen, PRIMARY_BG, (self.x, self.y), self.radius)
        
        # Inner circle animation when selected
        if self.selected:
            self.animation = min(1.0, self.animation + 0.2)
        else:
            self.animation = max(0.0, self.animation - 0.2)
            
        if self.animation > 0:
            inner_radius = int(self.radius * 0.7 * self.animation)
            # Glow effect
            for r in range(3):
                alpha = int(100 * self.animation) - r * 30
                if alpha > 0:
                    s = pygame.Surface((self.radius*2 + 10, self.radius*2 + 10), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*ACCENT_COLOR[:3], alpha), (self.radius + 5, self.radius + 5), inner_radius + r*2)
                    screen.blit(s, (self.x - self.radius - 5, self.y - self.radius - 5))
            
            # Inner circle
            pygame.draw.circle(screen, ACCENT_COLOR, (self.x, self.y), inner_radius)
            
        # Calculate text width to ensure it fits in the panel
        text_surf = TEXT_FONT.render(self.text, True, LIGHT_TEXT)
        text_width = text_surf.get_width()
        
        # Draw text with better styling - truncate if needed
        max_text_width = 250  # Maximum width for text in the panel
        if text_width > max_text_width:
            # Create a smaller font for long text
            smaller_font = pygame.font.Font(None, 24) if pygame.font.get_default_font() else pygame.font.SysFont('Arial', 20)
            text_surf = smaller_font.render(self.text, True, LIGHT_TEXT)
            text_width = text_surf.get_width()
            
            # If still too long, truncate
            if text_width > max_text_width:
                # Try to find a space to break at
                words = self.text.split()
                if len(words) > 1:
                    # Try to fit as many words as possible
                    display_text = words[0]
                    for word in words[1:]:
                        test_text = display_text + " " + word
                        test_surf = smaller_font.render(test_text, True, LIGHT_TEXT)
                        if test_surf.get_width() <= max_text_width:
                            display_text = test_text
                        else:
                            break
                    text_surf = smaller_font.render(display_text, True, LIGHT_TEXT)
                else:
                    # No spaces, just truncate
                    truncated_text = self.text[:15] + "..."
                    text_surf = smaller_font.render(truncated_text, True, LIGHT_TEXT)
        
        screen.blit(text_surf, (self.x + self.radius + 15, self.y - text_surf.get_height()//2))
        
    def check_click(self, mouse_pos):
        distance = ((mouse_pos[0] - self.x) ** 2 + (mouse_pos[1] - self.y) ** 2) ** 0.5
        return distance <= self.radius + 5  # Slightly larger hit area
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.check_click(event.pos):
                self.selected = True
                return True
        return False

class RhythmGameUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Rhythm Synchronization Game")
        
        # Game state
        self.state = "menu"  # menu, game, results, error
        self.input_mode = "keyboard"  # keyboard, audio
        self.tempo_mode = "slow"  # slow, medium
        self.game = None
        self.clock = pygame.time.Clock()
        self.beat_animation_time = 0
        self.show_beat = False
        self.score_display = {}
        self.error_message = ""
        self.particles = []  # For particle effects
        self.time_offset = 0  # For animations
        self.beat_history = []  # Store recent beats for visualization
        self.player_claps = {}  # Store recent player claps for visualization
        self.beat_indicators = []  # Visual indicators for upcoming beats
        self.beat_flash = 0  # For beat flash animation
        
        # Create UI elements
        self.create_ui_elements()
        
        # Check music directory and files
        self.verify_music_files()
        
        # Load assets
        self.load_assets()
        
    def load_assets(self):
        """Load game assets like sounds and images."""
        # Create placeholder assets
        self.beat_sound = None
        self.clap_sound = None
        
        try:
            # Try to load sound effects
            self.beat_sound = pygame.mixer.Sound("assets/beat.wav")
            self.clap_sound = pygame.mixer.Sound("assets/clap.wav")
        except:
            debug_print("Could not load sound effects. Using default sounds.")
            # Create simple sounds if files not found
            self.beat_sound = pygame.mixer.Sound(self.generate_beep_sound(440, 0.1))
            self.clap_sound = pygame.mixer.Sound(self.generate_beep_sound(880, 0.1))
            
    def generate_beep_sound(self, frequency, duration):
        """Generate a simple beep sound as a fallback."""
        sample_rate = 44100
        n_samples = int(round(duration * sample_rate))
        
        # Setup our numpy array to handle 16 bit ints, which is what we set our mixer to use
        buf = numpy.zeros((n_samples, 2), dtype=numpy.int16)
        max_sample = 2**(16 - 1) - 1
        
        for s in range(n_samples):
            t = float(s) / sample_rate  # Time in seconds
            buf[s][0] = int(max_sample * math.sin(2 * math.pi * frequency * t))  # Left channel
            buf[s][1] = int(max_sample * math.sin(2 * math.pi * frequency * t))  # Right channel
            
        return buf
        
    def verify_music_files(self):
        """Verify that music files exist."""
        debug_print(f"Music directory set to: {MUSIC_DIR}")
        
        # Check if music directory exists - if it's not empty
        if MUSIC_DIR and not os.path.exists(MUSIC_DIR):
            self.error_message = f"Music directory not found: {MUSIC_DIR}"
            debug_print(self.error_message)
            self.state = "error"
            return False
            
        # Check if song files exist
        missing_songs = []
        for song in SONGS:
            # Try multiple possible filenames and locations
            found = False
            
            # List of possible filenames and locations to check
            possible_paths = [
                # In specified music directory with no spaces
                os.path.join(MUSIC_DIR, f"{song.replace(' ', '')}.mp3"),
                # In specified music directory with spaces
                os.path.join(MUSIC_DIR, f"{song}.mp3"),
                # In root directory with no spaces
                f"{song.replace(' ', '')}.mp3",
                # In root directory with spaces
                f"{song}.mp3"
            ]
            
            for path in possible_paths:
                debug_print(f"Checking for song file at: {path}")
                if os.path.exists(path):
                    debug_print(f"Found song file: {path}")
                    found = True
                    break
                    
            if not found:
                missing_songs.append(song)
                
        if missing_songs:
            self.error_message = f"Missing song files: {', '.join(missing_songs)}\n"
            self.error_message += "Please check that the song files are in the correct location."
            debug_print(self.error_message)
            self.state = "error"
            return False
            
        debug_print("All music files verified successfully")
        return True
        
    def create_ui_elements(self):
        # Main menu buttons
        button_width = 300
        button_height = 60
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        
        self.start_button = Button(
            SCREEN_WIDTH // 2 - 125,  # Center it
            550,  # Position it below the tempo mode section
            250,  # Width
            50,   # Height
            "START GAME", 
            color=ACCENT_COLOR,
            action=self.start_game
        )
        
        # Input mode radio buttons - positioned for better spacing
        self.input_radio_buttons = [
            RadioButton(SCREEN_WIDTH // 4 - 150, 350, 12, "Makey Makey / Keyboard", "input", "keyboard", True),
            RadioButton(SCREEN_WIDTH // 4 - 150, 400, 12, "Microphone / Clap Detection", "input", "audio", False)
        ]
        
        # Tempo mode radio buttons - positioned for better spacing
        self.tempo_radio_buttons = [
            RadioButton(SCREEN_WIDTH * 3 // 4 - 100, 350, 12, "Slow → Medium → Fast", "tempo", "slow", True),
            RadioButton(SCREEN_WIDTH * 3 // 4 - 100, 400, 12, "Medium → Fast", "tempo", "medium", False)
        ]
        
        # Game UI buttons
        self.back_button = Button(
            30, 
            SCREEN_HEIGHT - 80, 
            150, 
            50, 
            "BACK", 
            color=WARNING_COLOR,
            action=self.return_to_menu
        )
        
        # Error screen buttons
        self.retry_button = Button(
            center_x, 
            SCREEN_HEIGHT - 150, 
            button_width, 
            button_height, 
            "RETRY", 
            color=SUCCESS_COLOR,
            action=self.retry_after_error
        )
        
        # Fix config button
        self.fix_config_button = Button(
            center_x,
            SCREEN_HEIGHT - 80,
            button_width,
            button_height,
            "FIX CONFIG",
            color=WARNING_COLOR,
            action=self.fix_config
        )
        
    def fix_config(self):
        """Create a fixed config.py file."""
        try:
            # Get the current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Read the current config.py file
            with open('config.py', 'r') as f:
                config_content = f.read()
                
            # Replace the MUSIC_DIR line with an empty string
            if "MUSIC_DIR =" in config_content:
                # Check if MUSIC_DIR is set to a file path
                if ".mp3" in MUSIC_DIR.lower():
                    debug_print(f"MUSIC_DIR is set to a file path: {MUSIC_DIR}")
                    config_content = config_content.replace(
                        f"MUSIC_DIR = {repr(MUSIC_DIR)}", 
                        f"MUSIC_DIR = ''"
                    )
                else:
                    # Set MUSIC_DIR to empty string to use the root directory
                    config_content = config_content.replace(
                        f"MUSIC_DIR = {repr(MUSIC_DIR)}", 
                        f"MUSIC_DIR = ''"
                    )
                
                # Update the SONGS dictionary to only include available songs
                if "SONGS = {" in config_content:
                    # Find all available song files in the current directory
                    available_songs = []
                    for song in SONGS:
                        # Check if song file exists
                        if os.path.exists(f"{song.replace(' ', '')}.mp3") or os.path.exists(f"{song}.mp3"):
                            available_songs.append(song)
                    
                    if len(available_songs) < len(SONGS):
                        # Create a new SONGS dictionary with only available songs
                        new_songs_dict = "SONGS = {\n"
                        for song in available_songs:
                            new_songs_dict += f'    "{song}": {SONGS[song]},\n'
                        new_songs_dict += "}"
                        
                        # Find the SONGS dictionary in the config file
                        start_idx = config_content.find("SONGS = {")
                        end_idx = config_content.find("}", start_idx) + 1
                        
                        # Replace the SONGS dictionary
                        config_content = config_content[:start_idx] + new_songs_dict + config_content[end_idx:]
                
                # Write the updated config file
                with open('config.py', 'w') as f:
                    f.write(config_content)
                    
                self.error_message = "Config file updated successfully!\nPlease restart the game."
                debug_print("Config file updated successfully")
            else:
                self.error_message = "Could not find MUSIC_DIR in config.py.\nPlease update it manually."
                debug_print("Could not find MUSIC_DIR in config.py")
                
        except Exception as e:
            self.error_message = f"Error updating config file: {str(e)}"
            debug_print(f"Error updating config file: {str(e)}")
    
    def create_particle(self, x, y, color, speed=3, size=5, lifetime=30):
        """Create a particle for visual effects."""
        angle = random.random() * math.pi * 2
        speed_x = math.cos(angle) * speed
        speed_y = math.sin(angle) * speed
        self.particles.append({
            'x': x, 'y': y,
            'vx': speed_x, 'vy': speed_y,
            'color': color, 'size': size,
            'life': lifetime
        })
    
    def update_particles(self):
        """Update particle positions and lifetimes."""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['size'] *= 0.95
            
            if particle['life'] <= 0 or particle['size'] < 0.5:
                self.particles.remove(particle)
    
    def draw_particles(self):
        """Draw all active particles."""
        for particle in self.particles:
            size = int(particle['size'])
            if size > 0:
                pygame.draw.circle(
                    self.screen, 
                    particle['color'], 
                    (int(particle['x']), int(particle['y'])), 
                    size
                )
    
    def create_beat_indicator(self, time_to_beat):
        """Create a visual indicator for an upcoming beat."""
        self.beat_indicators.append({
            'time_to_beat': time_to_beat,
            'radius': 200,  # Start with large radius
            'alpha': 255,   # Start fully visible
            'color': ACCENT_COLOR
        })
    
    def update_beat_indicators(self):
        """Update beat indicators as they approach the beat time."""
        for indicator in self.beat_indicators[:]:
            # Reduce time to beat
            indicator['time_to_beat'] -= 1/60  # Assuming 60 FPS
            
            # Calculate progress (0.0 to 1.0)
            progress = max(0, min(1, indicator['time_to_beat'] / 2.0))
            
            # Update radius and alpha based on progress
            indicator['radius'] = 200 - (200 - 80) * (1 - progress)
            indicator['alpha'] = int(255 * progress)
            
            # Remove indicator if it's reached the beat time
            if indicator['time_to_beat'] <= 0:
                self.beat_indicators.remove(indicator)
                self.beat_flash = 1.0  # Trigger beat flash
                
                # Create particles for visual effect
                for _ in range(20):
                    self.create_particle(
                        SCREEN_WIDTH // 2, 
                        SCREEN_HEIGHT // 2,
                        SUCCESS_COLOR,
                        speed=random.random() * 5 + 2,
                        size=random.random() * 8 + 3,
                        lifetime=random.randint(20, 40)
                    )
                
                # Play beat sound if available
                if self.beat_sound:
                    self.beat_sound.play()
    
    def draw_beat_indicators(self):
        """Draw visual indicators for upcoming beats."""
        for indicator in self.beat_indicators:
            # Create a surface with alpha channel
            s = pygame.Surface((indicator['radius']*2, indicator['radius']*2), pygame.SRCALPHA)
            
            # Draw circle with current alpha
            pygame.draw.circle(
                s, 
                (*indicator['color'][:3], indicator['alpha']), 
                (indicator['radius'], indicator['radius']), 
                int(indicator['radius'] * 0.1)
            )
            
            # Draw to screen
            self.screen.blit(
                s, 
                (SCREEN_WIDTH//2 - indicator['radius'], SCREEN_HEIGHT//2 - indicator['radius'])
            )
    
    def update_beat_flash(self):
        """Update the beat flash animation."""
        if self.beat_flash > 0:
            self.beat_flash = max(0, self.beat_flash - 0.05)  # Fade out
    
    def draw_beat_flash(self):
        """Draw the beat flash animation."""
        if self.beat_flash > 0:
            # Create a surface with alpha channel
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # Draw a semi-transparent overlay
            alpha = int(100 * self.beat_flash)
            s.fill((255, 255, 255, alpha))
            
            # Draw to screen
            self.screen.blit(s, (0, 0))
            
    def draw_menu(self):
        # Fill background with solid color
        self.screen.fill(PRIMARY_BG)
        
        # Draw animated background
        self.draw_animated_background()
        
        # Draw title with modern styling
        self.draw_title("Rhythm Synchronization Game", SCREEN_WIDTH // 2, 100)
        
        # Draw subtitle with better spacing
        subtitle_surf = SUBTITLE_FONT.render("Follow the rhythm and clap along with the beat!", True, LIGHT_TEXT)
        subtitle_rect = subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 170))
        self.screen.blit(subtitle_surf, subtitle_rect)
        
        # Draw input mode section with modern panel
        self.draw_panel(SCREEN_WIDTH // 4 - 200, 250, 350, 200, "Input Mode")
        
        for button in self.input_radio_buttons:
            button.draw(self.screen)
            
        # Draw tempo mode section with modern panel
        self.draw_panel(SCREEN_WIDTH * 3 // 4 - 150, 250, 350, 200, "Tempo Mode")
        
        for button in self.tempo_radio_buttons:
            button.draw(self.screen)
            
        # Draw start button
        self.start_button.check_hover(pygame.mouse.get_pos())
        self.start_button.draw(self.screen)
        
    def draw_title(self, text, x, y):
        """Draw a modern title with effects."""
        # Glow effect
        for i in range(3):
            alpha = 100 - i * 30
            glow_surf = TITLE_FONT.render(text, True, (*ACCENT_COLOR[:3], alpha))
            glow_rect = glow_surf.get_rect(center=(x + i, y + i))
            self.screen.blit(glow_surf, glow_rect)
        
        # Main title
        title_surf = TITLE_FONT.render(text, True, WHITE)
        title_rect = title_surf.get_rect(center=(x, y))
        self.screen.blit(title_surf, title_rect)
        
        # Animated underline
        line_width = title_surf.get_width() * (0.6 + 0.4 * math.sin(time.time() * 2) ** 2)
        line_height = 3
        line_y = y + title_rect.height // 2 + 10
        
        # Draw gradient line
        for i in range(line_height):
            line_color = self.blend_colors(ACCENT_COLOR, ACCENT_SECONDARY, (math.sin(time.time() * 3) + 1) / 2)
            pygame.draw.line(
                self.screen, 
                line_color,
                (x - line_width // 2, line_y + i), 
                (x + line_width // 2, line_y + i)
            )
    
    def blend_colors(self, color1, color2, blend_factor):
        """Blend two colors based on blend_factor (0.0 to 1.0)."""
        r = int(color1[0] * (1 - blend_factor) + color2[0] * blend_factor)
        g = int(color1[1] * (1 - blend_factor) + color2[1] * blend_factor)
        b = int(color1[2] * (1 - blend_factor) + color2[2] * blend_factor)
        return (r, g, b)
        
    def draw_panel(self, x, y, width, height, title):
        """Draw a clean panel with title."""
        # Main panel background with rounded corners
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, SECONDARY_BG, panel_rect, border_radius=15)
        
        # Panel border with glow effect
        for i in range(2):
            border_rect = pygame.Rect(x-i, y-i, width+i*2, height+i*2)
            pygame.draw.rect(self.screen, self.blend_colors(DARK_GRAY, ACCENT_COLOR, 0.3), 
                            border_rect, 1, border_radius=15+i)
        
        # Draw title with better styling
        title_surf = SUBTITLE_FONT.render(title, True, WHITE)
        title_bg = pygame.Surface((title_surf.get_width() + 20, title_surf.get_height()), pygame.SRCALPHA)
        pygame.draw.rect(title_bg, SECONDARY_BG, title_bg.get_rect(), border_radius=10)
        
        # Position the title background and text
        self.screen.blit(title_bg, (x + width//2 - title_bg.get_width()//2, y - title_surf.get_height()//2))
        self.screen.blit(title_surf, (x + width//2 - title_surf.get_width()//2, y - title_surf.get_height()//2))
        
    def draw_animated_background(self):
        """Draw an animated background with subtle patterns."""
        # Create a surface for the background pattern
        pattern_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Draw animated wave patterns
        t = time.time() * 0.5  # Time factor for animation
        
        # Draw subtle grid lines
        grid_spacing = 50
        grid_alpha = 10  # Very low alpha for subtlety
        
        # Horizontal lines
        for y in range(0, SCREEN_HEIGHT, grid_spacing):
            offset = int(math.sin(t + y * 0.01) * 5)
            pygame.draw.line(
                pattern_surface, 
                (ACCENT_COLOR[0], ACCENT_COLOR[1], ACCENT_COLOR[2], grid_alpha), 
                (0, y + offset), 
                (SCREEN_WIDTH, y + offset)
            )
            
        # Vertical lines
        for x in range(0, SCREEN_WIDTH, grid_spacing):
            offset = int(math.sin(t + x * 0.01) * 5)
            pygame.draw.line(
                pattern_surface, 
                (ACCENT_COLOR[0], ACCENT_COLOR[1], ACCENT_COLOR[2], grid_alpha), 
                (x + offset, 0), 
                (x + offset, SCREEN_HEIGHT)
            )
            
        # Add floating particles
        for i in range(15):
            x = (int(SCREEN_WIDTH * 0.1) + int(SCREEN_WIDTH * 0.8 * ((i * 73 + int(t * 20)) % 100) / 100)) % SCREEN_WIDTH
            y = (int(SCREEN_HEIGHT * 0.1) + int(SCREEN_HEIGHT * 0.8 * ((i * 57 + int(t * 15)) % 100) / 100)) % SCREEN_HEIGHT
            size = 3 + (i % 3)
            alpha = 30 + (i * 3) % 30
            
            # Pulsating effect
            pulse = (math.sin(t * 2 + i) + 1) / 2
            size = int(size * (0.8 + 0.4 * pulse))
            
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            color = self.blend_colors(ACCENT_COLOR, ACCENT_SECONDARY, (math.sin(t + i) + 1) / 2)
            pygame.draw.circle(s, (*color[:3], alpha), (size, size), size)
            pattern_surface.blit(s, (x, y))
            
        # Apply the pattern surface
        self.screen.blit(pattern_surface, (0, 0))
        
    def draw_game(self):
        # Fill background with solid color
        self.screen.fill(PRIMARY_BG)
        
        # Draw animated background
        self.draw_animated_background()
        
        # Remove the game header section
        # Draw game header - Fixed positioning and styling to ensure proper display
        # header_width = 300
        # header_height = 60
        # self.draw_panel(20, 20, header_width, header_height, "")

        # Draw "Rhythm Sync Game" text centered in the header panel
        # header_text = "Rhythm Sync Game"
        # header_surf = SUBTITLE_FONT.render(header_text, True, WHITE)
        # header_rect = header_surf.get_rect(center=(20 + header_width // 2, 20 + header_height // 2))
        # self.screen.blit(header_surf, header_rect)
        
        # Draw current song info with modern panel - Fixed position and adjusted width
        if self.game and self.game.current_song:
            # Increased width and adjusted position to prevent overlap with time bar
            now_playing_width = 450
            now_playing_x = SCREEN_WIDTH // 2 - now_playing_width // 2
            now_playing_height = 100
            self.draw_panel(now_playing_x, 20, now_playing_width, now_playing_height, "Now Playing")
            
            # Song title with shadow for better readability - Ensure it's centered
            song_text = f"{self.game.current_song}"
            song_surf = SUBTITLE_FONT.render(song_text, True, WHITE)
            song_rect = song_surf.get_rect(center=(now_playing_x + now_playing_width // 2, 70))
            
            # Text shadow
            shadow_surf = SUBTITLE_FONT.render(song_text, True, (0, 0, 0))
            shadow_rect = shadow_surf.get_rect(center=(song_rect.centerx + 2, song_rect.centery + 2))
            self.screen.blit(shadow_surf, shadow_rect)
            self.screen.blit(song_surf, song_rect)
            
            # BPM and difficulty on separate line for better spacing
            bpm_text = f"{self.game.current_bpm} BPM - {get_difficulty_name(self.game.current_bpm)}"
            bpm_surf = TEXT_FONT.render(bpm_text, True, GRAY)
            bpm_rect = bpm_surf.get_rect(center=(now_playing_x + now_playing_width // 2, 100))
            self.screen.blit(bpm_surf, bpm_rect)
        
        # Draw beat visualization with modern styling
        if self.game and self.game.is_tracking:
            current_time = time.time()
            
            # Update beat indicators
            self.update_beat_indicators()
            self.update_beat_flash()
            
            # Draw beat indicators
            self.draw_beat_indicators()
            self.draw_beat_flash()
            
            # Check if we're on a beat
            is_on_beat = self.game.is_on_beat(current_time)
            
            if is_on_beat and not self.show_beat:
                self.show_beat = True
                self.beat_animation_time = current_time
                self.beat_history.append(current_time)
                
                # Keep only recent beats
                while len(self.beat_history) > 8:
                    self.beat_history.pop(0)
                
                # Create a new beat indicator for the next beat
                seconds_per_beat = 60 / self.game.current_bpm
                self.create_beat_indicator(seconds_per_beat)
                
                # Add particles for visual effect when beat happens
                for _ in range(20):
                    self.create_particle(
                        SCREEN_WIDTH // 2, 
                        SCREEN_HEIGHT // 2,
                        SUCCESS_COLOR,
                        speed=random.random() * 5 + 2,
                        size=random.random() * 8 + 3,
                        lifetime=random.randint(20, 40)
                    )
            
            # Show beat animation for 0.2 seconds
            if self.show_beat and current_time - self.beat_animation_time < 0.2:
                beat_color = SUCCESS_COLOR
                beat_size = 100
                # Add glow effect
                for i in range(5):
                    alpha = 150 - i * 30
                    s = pygame.Surface((beat_size*2 + 20, beat_size*2 + 20), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*SUCCESS_COLOR[:3], alpha), (beat_size + 10, beat_size + 10), beat_size + i*5)
                    self.screen.blit(s, (SCREEN_WIDTH // 2 - beat_size - 10, SCREEN_HEIGHT // 2 - beat_size - 10))
            else:
                beat_color = ACCENT_COLOR
                beat_size = 80
                self.show_beat = False
                
            # Draw beat circle with modern styling
            pygame.draw.circle(self.screen, beat_color, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), beat_size)
            
            # Add inner circle for depth
            pygame.draw.circle(self.screen, self.lighten_color(beat_color, 30), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), beat_size - 10)
            
            # Add outer glow
            pygame.draw.circle(self.screen, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), beat_size, 3)
            
            # Draw "CLAP!" or "BEAT!" text with modern styling
            if self.show_beat:
                # Show different text based on input mode
                beat_text = "BEAT!" if self.game.input_mode == "keyboard" else "CLAP!"
                clap_surf = TITLE_FONT.render(beat_text, True, WHITE)
                clap_rect = clap_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                
                # Text shadow for better readability
                shadow_surf = TITLE_FONT.render(beat_text, True, (0, 0, 0))
                shadow_rect = shadow_surf.get_rect(center=(clap_rect.centerx + 3, clap_rect.centery + 3))
                self.screen.blit(shadow_surf, shadow_rect)
                self.screen.blit(clap_surf, clap_rect)
            
            # Draw time remaining with modern progress bar - Positioned below the song info
            elapsed = current_time - self.game.start_time
            remaining = max(0, self.game.game_duration - elapsed)
            progress = 1 - (remaining / self.game.game_duration)

            # Draw time text with better styling - Positioned below the song info
            time_text = f"Time: {remaining:.1f}s"
            time_surf = TEXT_FONT.render(time_text, True, WHITE)
            time_rect = time_surf.get_rect(center=(now_playing_x + now_playing_width // 2, 130))
            self.screen.blit(time_surf, time_rect)

            # Draw progress bar with better styling - Positioned below the time text
            bar_width = 300
            bar_height = 20
            bar_x = now_playing_x + (now_playing_width - bar_width) // 2
            bar_y = 150

            # Draw background
            pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=bar_height//2)

            # Draw fill with gradient
            if progress > 0:
                fill_width = int(bar_width * progress)
                for x in range(fill_width):
                    # Gradient from left to right
                    ratio = x / bar_width
                    color = self.blend_colors(SUCCESS_COLOR, ACCENT_COLOR, ratio)
                    pygame.draw.line(self.screen, color, (bar_x + x, bar_y), (bar_x + x, bar_y + bar_height))
                
                # Round the corners of the fill
                pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, fill_width, bar_height), 1, border_radius=bar_height//2)
            
            # Draw rhythm timeline
            self.draw_rhythm_timeline(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, 600, 40)
            
            # Draw scores in a modern panel
            if self.game.input_mode == "keyboard":
                scores = self.game.scoring.get_all_scores()
                
                # Draw player panels on left and right sides
                player_panel_width = 250
                player_panel_height = 300
                
                # Player 1 panel (left side)
                if 1 in scores:
                    self.draw_player_panel(
                        30, 
                        SCREEN_HEIGHT // 2 - player_panel_height // 2,
                        player_panel_width,
                        player_panel_height,
                        1,
                        scores[1]
                    )
                
                # Player 2 panel (right side)
                if 2 in scores:
                    self.draw_player_panel(
                        SCREEN_WIDTH - player_panel_width - 30,
                        SCREEN_HEIGHT // 2 - player_panel_height // 2,
                        player_panel_width,
                        player_panel_height,
                        2,
                        scores[2]
                    )
        
        # Draw countdown if not tracking yet
        elif self.game and self.game.is_playing and not self.game.is_tracking:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Draw countdown with modern styling
            countdown_text = "Get Ready..."
            countdown_surf = TITLE_FONT.render(countdown_text, True, WHITE)
            countdown_rect = countdown_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            
            # Add glow effect
            for i in range(3):
                alpha = 100 - i * 30
                glow_surf = TITLE_FONT.render(countdown_text, True, (*ACCENT_COLOR[:3], alpha))
                glow_rect = glow_surf.get_rect(center=(countdown_rect.centerx + i, countdown_rect.centery + i))
                self.screen.blit(glow_surf, glow_rect)
                
            self.screen.blit(countdown_surf, countdown_rect)
            
            # Draw input instructions with better styling
            if self.game.input_mode == "keyboard":
                instructions = "Press your assigned keys to the beat!"
            else:
                instructions = "Clap your hands to the beat!"
                
            instr_surf = SUBTITLE_FONT.render(instructions, True, WHITE)
            instr_rect = instr_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(instr_surf, instr_rect)
            
            # Add animated countdown indicator
            time_left = self.game.countdown_end - time.time()
            if time_left > 0:
                progress = time_left / self.game.countdown_duration
                radius = 50
                angle = 360 * (1 - progress)
                
                # Draw progress circle
                pygame.draw.circle(self.screen, DARK_GRAY, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120), radius)
                
                # Draw arc for countdown
                rect = pygame.Rect(SCREEN_WIDTH // 2 - radius, SCREEN_HEIGHT // 2 + 120 - radius, radius * 2, radius * 2)
                pygame.draw.arc(self.screen, ACCENT_COLOR, rect, 0, math.radians(angle), width=5)
                
                # Draw countdown number
                count_text = f"{int(time_left) + 1}"
                count_surf = TITLE_FONT.render(count_text, True, WHITE)
                count_rect = count_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
                self.screen.blit(count_surf, count_rect)
        
        # Draw back button
        self.back_button.check_hover(pygame.mouse.get_pos())
        self.back_button.draw(self.screen)
        
        # Draw particles
        self.update_particles()
        self.draw_particles()
        
    def draw_player_panel(self, x, y, width, height, player_id, score):
        """Draw a player panel with score information."""
        # Draw panel background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, SECONDARY_BG, panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect, 2, border_radius=15)
        
        # Draw player header
        player_color = ACCENT_COLOR if player_id == 1 else ACCENT_SECONDARY
        header_rect = pygame.Rect(x, y, width, 50)
        pygame.draw.rect(self.screen, player_color, header_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.lighten_color(player_color, 30), header_rect, 1, border_radius=15)
        
        # Only round the top corners
        bottom_rect = pygame.Rect(x, y + 25, width, 25)
        pygame.draw.rect(self.screen, player_color, bottom_rect)
        
        # Player title
        player_text = f"Player {player_id}"
        player_surf = SUBTITLE_FONT.render(player_text, True, WHITE)
        player_rect = player_surf.get_rect(center=(x + width // 2, y + 25))
        self.screen.blit(player_surf, player_rect)
        
        # Draw key info
        if player_id in PLAYER_KEYS:
            # Handle both string key names and integer key codes
            key_value = PLAYER_KEYS[player_id]
            if isinstance(key_value, int):
                key_name = pygame.key.name(key_value).upper()
            else:
                key_name = str(key_value).upper()
            key_text = f"Key: {key_name}"
            key_surf = TEXT_FONT.render(key_text, True, LIGHT_TEXT)
            key_rect = key_surf.get_rect(center=(x + width // 2, y + 80))
            self.screen.blit(key_surf, key_rect)
        
        # Draw score info
        y_offset = y + 120
        
        # Total claps
        claps_text = f"Total Claps: {score['claps']}"
        claps_surf = TEXT_FONT.render(claps_text, True, LIGHT_TEXT)
        claps_rect = claps_surf.get_rect(center=(x + width // 2, y_offset))
        self.screen.blit(claps_surf, claps_rect)
        y_offset += 40
        
        # On-beat claps
        on_beat_text = f"On Beat: {score['on_beat']}"
        on_beat_surf = TEXT_FONT.render(on_beat_text, True, LIGHT_TEXT)
        on_beat_rect = on_beat_surf.get_rect(center=(x + width // 2, y_offset))
        self.screen.blit(on_beat_surf, on_beat_rect)
        y_offset += 40
        
        # No accuracy display
        
        # Draw rhythm timeline
        self.draw_rhythm_timeline(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, 600, 40)
        
    def draw_rhythm_timeline(self, x, y, width, height):
        """Draw a timeline showing recent beats and player claps."""
        # Draw timeline background
        timeline_rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        pygame.draw.rect(self.screen, SECONDARY_BG, timeline_rect, border_radius=height//2)
        pygame.draw.rect(self.screen, DARK_GRAY, timeline_rect, 2, border_radius=height//2)
        
        # Draw center line
        pygame.draw.line(
            self.screen,
            GRAY,
            (x - width // 2 + 10, y),
            (x + width // 2 - 10, y),
            1
        )
        
        # Draw beat markers
        current_time = time.time()
        for beat_time in self.beat_history:
            # Calculate position based on time difference
            time_diff = current_time - beat_time
            if time_diff > 5:  # Only show beats from the last 5 seconds
                continue
                
            # Position from right to left (newer beats are more to the right)
            pos_x = int(x + width // 2 - (time_diff / 5) * width)
            
            # Draw beat marker
            marker_height = height - 10
            pygame.draw.rect(
                self.screen,
                SUCCESS_COLOR,
                (pos_x - 2, y - marker_height // 2, 4, marker_height),
                border_radius=2
            )
            
        # Draw player clap markers
        for player_id, clap_times in self.player_claps.items():
            player_color = ACCENT_COLOR if player_id == 1 else ACCENT_SECONDARY
            
            for clap_time in clap_times:
                # Calculate position based on time difference
                time_diff = current_time - clap_time
                if time_diff > 5:  # Only show claps from the last 5 seconds
                    continue
                    
                # Position from right to left (newer claps are more to the right)
                pos_x = int(x + width // 2 - (time_diff / 5) * width)
                
                # Draw clap marker
                marker_height = height - 20
                marker_y_offset = -10 if player_id == 1 else 10  # Player 1 above, Player 2 below
                
                pygame.draw.circle(
                    self.screen,
                    player_color,
                    (pos_x, y + marker_y_offset),
                    5
                )
        
    def lighten_color(self, color, amount):
        """Return a lighter version of the color."""
        return tuple(min(c + amount, 255) for c in color)
        
    # Replace the draw_results method with an improved version
    def draw_results(self):
        # Fill background with solid color
        self.screen.fill(PRIMARY_BG)
        
        # Draw animated background
        self.draw_animated_background()
        
        # Draw title with modern panel - positioned higher
        title_panel_width = 400
        title_panel_height = 70
        title_panel_x = SCREEN_WIDTH // 2 - title_panel_width // 2
        title_panel_y = 30
        self.draw_panel(title_panel_x, title_panel_y, title_panel_width, title_panel_height, "")
        
        # Draw "Game Results" text centered in the panel
        title_text = "Game Results"
        title_surf = SUBTITLE_FONT.render(title_text, True, WHITE)
        title_rect = title_surf.get_rect(center=(title_panel_x + title_panel_width // 2, title_panel_y + title_panel_height // 2))
        self.screen.blit(title_surf, title_rect)
        
        # Create a panel for scores - with more space below the title
        scores_panel_width = 700
        scores_panel_height = 300  # Reduced height
        scores_panel_x = SCREEN_WIDTH // 2 - scores_panel_width // 2
        scores_panel_y = 120  # More space after title
        self.draw_panel(scores_panel_x, scores_panel_y, scores_panel_width, scores_panel_height, "Player Scores")
        
        # Draw scores with better styling
        if self.score_display:
            # Determine number of players
            player_count = len(self.score_display)
            
            if player_count == 1:
                # Single player - center the panel
                player_id = list(self.score_display.keys())[0]
                self.draw_result_player_panel(
                    SCREEN_WIDTH // 2 - 150,
                    scores_panel_y + 60,
                    300,
                    200,
                    player_id,
                    self.score_display[player_id]
                )
            else:
                # Multiple players - arrange side by side with better spacing
                panel_width = 260  # Smaller panels
                panel_height = 200  # Shorter panels
                spacing = 100  # More spacing between panels
                total_width = panel_width * player_count + spacing * (player_count - 1)
                start_x = SCREEN_WIDTH // 2 - total_width // 2
                
                for i, (player_id, score) in enumerate(self.score_display.items()):
                    x = start_x + i * (panel_width + spacing)
                    self.draw_result_player_panel(
                        x,
                        scores_panel_y + 60,  # Position lower within the scores panel
                        panel_width,
                        panel_height,
                        player_id,
                        score
                    )
        
        # Draw winner with special styling - only if there's a valid winner
        if self.game and hasattr(self.game, 'scoring'):
            # Get all scores to check for ties
            all_scores = self.game.scoring.get_all_scores()
            
            # Find the highest on-beat score
            highest_score = 0
            for player_data in all_scores.values():
                if player_data['on_beat'] > highest_score:
                    highest_score = player_data['on_beat']
            
            # Check if there's a tie (multiple players with the highest score)
            tied_players = []
            for player_id, player_data in all_scores.items():
                if player_data['on_beat'] == highest_score and highest_score > 0:
                    tied_players.append(player_id)
            
            # Display appropriate message based on whether there's a tie
            if len(tied_players) > 1:
                # Create tie panel with better positioning - more space after scores panel
                tie_panel_width = 500
                tie_panel_height = 60
                tie_panel_x = SCREEN_WIDTH // 2 - tie_panel_width // 2
                tie_panel_y = scores_panel_y + scores_panel_height + 30  # More space after scores panel
                
                tie_panel = pygame.Surface((tie_panel_width, tie_panel_height), pygame.SRCALPHA)
                pygame.draw.rect(tie_panel, (*SUCCESS_COLOR[:3], 100), tie_panel.get_rect(), border_radius=15)
                self.screen.blit(tie_panel, (tie_panel_x, tie_panel_y))
                
                # Tie text with glow effect - smaller font
                tie_text = f"It's a tie! Players {', '.join(str(p) for p in tied_players)} tied with {highest_score} on-beat claps!"
                
                # Use TEXT_FONT instead of SUBTITLE_FONT for smaller text
                for i in range(3):
                    alpha = 100 - i * 30
                    glow_surf = TEXT_FONT.render(tie_text, True, (*SUCCESS_COLOR[:3], alpha))
                    glow_rect = glow_surf.get_rect(center=(SCREEN_WIDTH // 2 + i, tie_panel_y + tie_panel_height // 2 + i))
                    self.screen.blit(glow_surf, glow_rect)
                
                tie_surf = TEXT_FONT.render(tie_text, True, WHITE)
                tie_rect = tie_surf.get_rect(center=(SCREEN_WIDTH // 2, tie_panel_y + tie_panel_height // 2))
                self.screen.blit(tie_surf, tie_rect)
                
            elif len(tied_players) == 1:
                # Single winner with better positioning - more space after scores panel
                winner = self.game.scoring.get_winner()
                player_id, score = winner
                
                # Create winner panel
                winner_panel_width = 500
                winner_panel_height = 60
                winner_panel_x = SCREEN_WIDTH // 2 - winner_panel_width // 2
                winner_panel_y = scores_panel_y + scores_panel_height + 30  # More space after scores panel
                
                winner_panel = pygame.Surface((winner_panel_width, winner_panel_height), pygame.SRCALPHA)
                pygame.draw.rect(winner_panel, (*SUCCESS_COLOR[:3], 100), winner_panel.get_rect(), border_radius=15)
                self.screen.blit(winner_panel, (winner_panel_x, winner_panel_y))
                
                # Winner text with glow effect - smaller font
                winner_text = f"Winner: Player {player_id} with {score['on_beat']} on-beat claps!"
                
                # Use TEXT_FONT instead of SUBTITLE_FONT for smaller text
                for i in range(3):
                    alpha = 100 - i * 30
                    glow_surf = TEXT_FONT.render(winner_text, True, (*SUCCESS_COLOR[:3], alpha))
                    glow_rect = glow_surf.get_rect(center=(SCREEN_WIDTH // 2 + i, winner_panel_y + winner_panel_height // 2 + i))
                    self.screen.blit(glow_surf, glow_rect)
                
                winner_surf = TEXT_FONT.render(winner_text, True, WHITE)
                winner_rect = winner_surf.get_rect(center=(SCREEN_WIDTH // 2, winner_panel_y + winner_panel_height // 2))
                self.screen.blit(winner_surf, winner_rect)

        # Draw next song info with modern styling and better spacing
        if self.game and self.game.current_song:
            next_song_panel_width = 400
            next_song_panel_height = 60
            next_song_panel_x = SCREEN_WIDTH // 2 - next_song_panel_width // 2
            
            # Position with more gap after winner panel
            if len(self.score_display) > 0 and hasattr(self.game, 'scoring'):
                next_song_panel_y = scores_panel_y + scores_panel_height + 110  # More space after winner panel
            else:
                next_song_panel_y = scores_panel_y + scores_panel_height + 30
        
            self.draw_panel(next_song_panel_x, next_song_panel_y, next_song_panel_width, next_song_panel_height, "Next Song")
            
            next_song_text = f"{self.game.current_song} ({self.game.current_bpm} BPM)"
            next_song_surf = TEXT_FONT.render(next_song_text, True, WHITE)
            next_song_rect = next_song_surf.get_rect(center=(SCREEN_WIDTH // 2, next_song_panel_y + next_song_panel_height // 2 + 5))
            self.screen.blit(next_song_surf, next_song_rect)

        # Draw buttons with better spacing and alignment
        button_y = SCREEN_HEIGHT - 80  # Position buttons lower
        
        play_again_button = Button(
            SCREEN_WIDTH // 2 - 310, 
            button_y, 
            300, 
            60, 
            "PLAY AGAIN", 
            color=ACCENT_COLOR,
            action=self.start_game
        )

        return_button = Button(
            SCREEN_WIDTH // 2 + 10, 
            button_y, 
            300, 
            60, 
            "RETURN TO MENU", 
            color=ACCENT_COLOR,
            action=self.return_to_menu
        )
        
        play_again_button.check_hover(pygame.mouse.get_pos())
        return_button.check_hover(pygame.mouse.get_pos())
        
        play_again_button.draw(self.screen)
        return_button.draw(self.screen)
    
    # Replace the draw_result_player_panel method with an improved version
    def draw_result_player_panel(self, x, y, width, height, player_id, score):
        """Draw a player panel in the results screen."""
        # Draw panel background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, SECONDARY_BG, panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect, 2, border_radius=15)
        
        # Draw player header
        player_color = ACCENT_COLOR if player_id == 1 else ACCENT_SECONDARY
        header_rect = pygame.Rect(x, y, width, 40)  # Smaller header
        pygame.draw.rect(self.screen, player_color, header_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.lighten_color(player_color, 30), header_rect, 1, border_radius=15)
        
        # Only round the top corners
        bottom_rect = pygame.Rect(x, y + 20, width, 20)
        pygame.draw.rect(self.screen, player_color, bottom_rect)
        
        # Player title
        player_text = f"Player {player_id}"
        player_surf = TEXT_FONT.render(player_text, True, WHITE)  # Smaller font
        player_rect = player_surf.get_rect(center=(x + width // 2, y + 20))
        self.screen.blit(player_surf, player_rect)
        
        # Draw score details with better layout
        y_offset = y + 60  # Start lower
        
        details = [
            ("Total Claps:", f"{score['claps']}"),
            ("On-Beat Claps:", f"{score['on_beat']}"),
            ("Missed Beats:", f"{score.get('missed_beats', 0)}")
        ]
        
        for label, value in details:
            # Label
            label_surf = SMALL_FONT.render(label, True, GRAY)  # Smaller font
            label_rect = label_surf.get_rect(x=x + 15, y=y_offset)
            self.screen.blit(label_surf, label_rect)
            
            # Value
            value_surf = SMALL_FONT.render(value, True, WHITE)  # Smaller font
            value_rect = value_surf.get_rect(right=x + width - 15, y=y_offset)
            self.screen.blit(value_surf, value_rect)
            
            y_offset += 30  # Less space between lines
        
        # No accuracy display
        
    def draw_error(self):
        """Draw error screen with modern styling."""
        # Fill background with solid color
        self.screen.fill(PRIMARY_BG)
        
        # Draw animated background
        self.draw_animated_background()
        
        # Draw error panel with better styling
        self.draw_panel(SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT // 2 - 200, 700, 300, "Error")
        
        # Draw error icon
        icon_radius = 40
        icon_x = SCREEN_WIDTH // 2
        icon_y = SCREEN_HEIGHT // 2 - 150
        
        # Draw error icon circle
        pygame.draw.circle(self.screen, ACCENT_SECONDARY, (icon_x, icon_y), icon_radius)
        pygame.draw.circle(self.screen, PRIMARY_BG, (icon_x, icon_y), icon_radius - 3)
        
        # Draw X inside circle
        line_length = icon_radius - 10
        pygame.draw.line(self.screen, ACCENT_SECONDARY, 
                        (icon_x - line_length, icon_y - line_length),
                        (icon_x + line_length, icon_y + line_length), 5)
        pygame.draw.line(self.screen, ACCENT_SECONDARY, 
                        (icon_x + line_length, icon_y - line_length),
                        (icon_x - line_length, icon_y + line_length), 5)
        
        # Draw error message with better spacing and styling
        lines = self.error_message.split('\n')
        y_offset = SCREEN_HEIGHT // 2 - 80
        
        for line in lines:
            error_surf = TEXT_FONT.render(line, True, ACCENT_SECONDARY)
            error_rect = error_surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(error_surf, error_rect)
            y_offset += 30
            
        # Draw help text with better styling
        help_text = [
            "Please check the following:",
            "1. Make sure the music directory path in config.py is correct",
            f"   Current path: {MUSIC_DIR}",
            "2. Since your music files are in the root directory,",
            "   MUSIC_DIR should be set to an empty string in config.py",
            "3. Song filenames should match the song names in config.py",
            "   (e.g., 'Hotel California' should be 'HotelCalifornia.mp3')"
        ]
        
        # Draw help panel
        help_panel = pygame.Surface((600, 200), pygame.SRCALPHA)
        pygame.draw.rect(help_panel, (0, 0, 0, 100), help_panel.get_rect(), border_radius=10)
        self.screen.blit(help_panel, (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 + 20))
        
        y_offset = SCREEN_HEIGHT // 2 + 40
        for line in help_text:
            help_surf = SMALL_FONT.render(line, True, GRAY)
            help_rect = help_surf.get_rect(left=SCREEN_WIDTH // 2 - 280, y=y_offset)
            self.screen.blit(help_surf, help_rect)
            y_offset += 25
            
        # Draw buttons with better styling
        self.retry_button.check_hover(pygame.mouse.get_pos())
        self.retry_button.draw(self.screen)
        
        self.fix_config_button.check_hover(pygame.mouse.get_pos())
        self.fix_config_button.draw(self.screen)
        
    def initialize_game(self):
        """Initialize the game components based on selected options."""
        # Determine number of players (only relevant for keyboard mode)
        num_players = 2 if self.input_mode == "keyboard" else 1
        
        # Create music player with modified path handling
        music_player = CustomMusicPlayer(MUSIC_DIR)
        
        # Create input handlers based on selected mode
        if self.input_mode == "keyboard":
            # Create keyboard mapping for the specified number of players
            player_keys = {i: PLAYER_KEYS[i] for i in range(1, num_players + 1)}
            keyboard_handler = KeyboardHandler(player_keys)

            # Create a dummy audio handler that won't be used
            audio_handler = AudioHandler(
                sample_rate=44100,
                buffer_size=1024,
                channels=1,
                threshold=0.1,
                min_time_between_claps=0.5
            )
            # Don't start the audio handler
            audio_handler.running = False
            
        else:  # audio mode
            # Create a dummy keyboard handler with no players
            keyboard_handler = KeyboardHandler({})
            
            # Create and calibrate the audio handler
            audio_handler = AudioHandler(
                sample_rate=44100,
                buffer_size=1024,
                channels=1,
                threshold=0.1,
                min_time_between_claps=0.5
            )
            debug_print("Using audio/clap detection mode.")
            debug_print("Calibrating microphone...")
            audio_handler.calibrate(3)  # 3 seconds calibration
            
            # Start the audio handler
            audio_handler.start()
        
        # Create scoring system
        scoring = Scoring(player_count=num_players)
        
        # Create game logic
        game = GameLogic(music_player, keyboard_handler, audio_handler, scoring)
        
        # Filter songs based on tempo mode
        filtered_songs = {}
        if self.tempo_mode == "slow":
            # Include all songs
            filtered_songs = SONGS
        else:  # medium
            # Only include songs with BPM >= 90
            filtered_songs = {name: bpm for name, bpm in SONGS.items() if bpm >= 90}
        
        game.set_songs(filtered_songs)
        game.set_game_settings(
            duration=DEFAULT_GAME_DURATION, 
            countdown=COUNTDOWN_DURATION, 
            tolerance=BEAT_TOLERANCE, 
            score_threshold=SCORE_THRESHOLD
        )
        
        # Set the input mode in the game logic
        game.input_mode = self.input_mode
        
        return game
        
    def start_game(self):
        """Start the game with the selected options."""
        # Initialize game components
        self.game = self.initialize_game()
        
        # Start the game
        if self.game.start_game():
            self.state = "game"
        else:
            debug_print("Failed to start game.")
            self.error_message = "Failed to start game. Check console for details."
            self.state = "error"
            
    def end_game(self):
        """End the current game and show results."""
        if self.game:
            # Save scores for display
            self.score_display = self.game.scoring.get_all_scores()
            
            # End the game
            self.game.end_game()
            
            # Change state to results
            self.state = "results"
            
    def return_to_menu(self):
        """Return to the main menu."""
        # Clean up game resources if needed
        if self.game and self.game.is_playing:
            self.game.end_game()
            
        # Stop audio handler if it's running
        if self.game and self.game.input_mode == "audio" and self.game.audio_handler.running:
            self.game.audio_handler.stop()
            
        self.game = None
        self.state = "menu"
        
    def retry_after_error(self):
        """Retry after an error."""
        # Verify music files again
        if self.verify_music_files():
            self.state = "menu"
        # If verification fails, it will set the state to "error" again
        
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.quit_game()
                
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if self.state == "game":
                        self.end_game()
                    elif self.state == "results":
                        self.return_to_menu()
                    else:
                        self.quit_game()
                        
            elif event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == "menu":
                    # Check radio buttons
                    for button in self.input_radio_buttons:
                        if button.handle_event(event):
                            # Deselect other buttons in the same group
                            for other in self.input_radio_buttons:
                                if other != button:
                                    other.selected = False
                            self.input_mode = button.value
                            
                    for button in self.tempo_radio_buttons:
                        if button.handle_event(event):
                            # Deselect other buttons in the same group
                            for other in self.tempo_radio_buttons:
                                if other != button:
                                    other.selected = False
                            self.tempo_mode = button.value
                            
                    # Check start button
                    self.start_button.handle_event(event)
                    
                elif self.state == "game":
                    # Check back button
                    self.back_button.handle_event(event)
                    
                elif self.state == "results":
                    # Create the buttons for the results screen
                    play_again_button = Button(
                        SCREEN_WIDTH // 2 - 310, 
                        SCREEN_HEIGHT - 80, 
                        300, 
                        60, 
                        "PLAY AGAIN", 
                        color=ACCENT_COLOR,
                        action=self.start_game
                    )
                    
                    return_button = Button(
                        SCREEN_WIDTH // 2 + 10, 
                        SCREEN_HEIGHT - 80, 
                        300, 
                        60, 
                        "RETURN TO MENU", 
                        color=ACCENT_COLOR,
                        action=self.return_to_menu
                    )
                    
                    # Check if buttons are clicked
                    play_again_button.check_hover(mouse_pos)
                    if play_again_button.handle_event(event):
                        debug_print("PLAY AGAIN button clicked")
                        self.start_game()
                        return
                        
                    return_button.check_hover(mouse_pos)
                    if return_button.handle_event(event):
                        debug_print("RETURN TO MENU button clicked")
                        self.return_to_menu()
                        return
                    
                elif self.state == "error":
                    # Check retry button
                    self.retry_button.handle_event(event)
                    # Check fix config button
                    self.fix_config_button.handle_event(event)
                    
    def update(self):
        """Update game state."""
        if self.state == "game" and self.game:
            # Update game logic
            if not self.game.update():
                # Game has ended
                self.end_game()
                
    def draw(self):
        """Draw the current screen."""
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "game":
            self.draw_game()
        elif self.state == "results":
            self.draw_results()
        elif self.state == "error":
            self.draw_error()
            
        pygame.display.flip()
        
    def quit_game(self):
        """Quit the game and clean up resources."""
        # Clean up game resources if needed
        if self.game and self.game.input_mode == "audio" and hasattr(self.game, 'audio_handler') and self.game.audio_handler.running:
            self.game.audio_handler.stop()
            
        pygame.quit()
        sys.exit()
        
    def run(self):
        """Main game loop."""
        while True:
            self.clock.tick(60)  # 60 FPS
            self.handle_events()
            self.update()
            self.draw()

# Import random for particle effects
import random

# Custom music player that handles files in root directory
class CustomMusicPlayer(MusicPlayer):
    def __init__(self, music_dir):
        super().__init__(music_dir)
        
    def load_song(self, song_name, bpm):
        """
        Load a song for playback with better file path handling.
        
        Args:
            song_name: Name of the song to load
            bpm: Beats per minute of the song
        
        Returns:
            True if the song was loaded successfully, False otherwise
        """
        self.current_song = song_name
        self.current_bpm = bpm
        
        # Try multiple possible filenames and locations
        possible_paths = [
            # In specified music directory with no spaces
            os.path.join(self.music_dir, f"{song_name.replace(' ', '')}.mp3"),
            # In specified music directory with spaces
            os.path.join(self.music_dir, f"{song_name}.mp3"),
            # In root directory with no spaces
            f"{song_name.replace(' ', '')}.mp3",
            # In root directory with spaces
            f"{song_name}.mp3"
        ]
        
        for path in possible_paths:
            try:
                debug_print(f"Trying to load song from: {path}")
                pygame.mixer.music.load(path)
                debug_print(f"Successfully loaded song: {song_name} ({bpm} BPM) from {path}")
                return True
            except pygame.error as e:
                debug_print(f"Failed to load from {path}: {e}")
                continue
        
        print(f"Error loading song {song_name}: Could not find file in any expected location.")
        return False

def main():
    """Main function to run the game."""
    ui = RhythmGameUI()
    ui.run()

if __name__ == "__main__":
    main()
