import time
import keyboard
import pygame
import os
import sys

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rhythm Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 0)

# Fonts
font_large = pygame.font.SysFont('Arial', 40)
font_medium = pygame.font.SysFont('Arial', 30)
font_small = pygame.font.SysFont('Arial', 20)

# Song database
songs = {
    "Hotel California": 74,
    "Yellow": 84,
    "Chaiyya Chaiyya": 92,
    "Chasing Cars": 104,
    "Another One Bites The Dust": 110,
    "Dynamite": 116,
    "Beat It": 140,
}

# Music directory - update this to your music folder
music_dir = r"C:\Users\Surbhi Agarwal\Music"

class LogDisplay:
    def __init__(self, max_lines=10):
        self.max_lines = max_lines
        self.lines = []
    
    def add_line(self, text):
        print(text)  # Also print to console for debugging
        self.lines.append(text)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
    
    def draw(self, surface, x, y):
        for i, line in enumerate(self.lines):
            text = font_small.render(line, True, WHITE)
            surface.blit(text, (x, y + i * 25))

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)
        
        text_surface = font_medium.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

class RhythmGame:
    def __init__(self):
        self.current_song = next(iter(songs))
        self.current_bpm = songs[self.current_song]
        self.log = LogDisplay(max_lines=15)
        self.clap_times = []
        self.beat_times = []
        self.start_time = 0
        self.interval = 60 / self.current_bpm * 2  # seconds between beats
        self.tolerance = 0.2  # tighter tolerance for visual feedback
        self.game_duration = 20
        self.countdown = 5  # countdown before starting
        self.is_playing = False
        self.is_tracking = False
        self.beat_flash = 0
        self.clap_flash = 0
        self.on_beat_count = 0
        self.last_beat_index = -1
        
        # Create buttons
        self.start_button = Button(WIDTH//2 - 100, HEIGHT - 100, 200, 50, "Start Game", BLUE, (100, 100, 255))
        
        # Load song list
        self.load_songs()
        
    def load_songs(self):
        self.log.add_line("Loading songs...")
        for song_name in songs.keys():
            # Expected filename format: SongName.mp3
            filename = f"{song_name.replace(' ', '')}.mp3"
            full_path = os.path.join(music_dir, filename)
            if not os.path.exists(full_path):
                self.log.add_line(f"Warning: {filename} not found!")
        
    def start_game(self):
        self.is_playing = True
        filename = f"{self.current_song.replace(' ', '')}.mp3"
        full_path = os.path.join(music_dir, f"{self.current_song.replace(' ', '')}.mp3")
        
        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.play()
            self.log.add_line(f"Now playing: {self.current_song} ({self.current_bpm} BPM)")
            self.countdown = 5
            self.is_tracking = False
            self.clap_times = []
            self.on_beat_count = 0
            self.last_beat_index = -1
        except pygame.error as e:
            self.log.add_line(f"Error loading music: {e}")
            self.is_playing = False
    
    def start_tracking(self):
        self.start_time = time.time()
        self.is_tracking = True
        self.beat_times = [self.start_time + i * self.interval for i in range(int(self.game_duration / self.interval) + 1)]
        self.log.add_line("Tracking started! Press SPACE to clap along.")
    
    def register_clap(self):
        if self.is_tracking:
            clap_time = time.time()
            self.clap_times.append(clap_time)
            self.clap_flash = 10  # visual feedback frames
            
            # Immediate feedback
            if self.is_on_beat(clap_time):
                self.log.add_line("CORRECT: Good timing!")
                self.on_beat_count += 1
            else:
                self.log.add_line("WRONG: Off beat!")
    
    def is_on_beat(self, clap_time):
        return any(abs(clap_time - beat) <= self.tolerance for beat in self.beat_times)
    
    def end_game(self):
        self.is_playing = False
        self.is_tracking = False
        pygame.mixer.music.stop()
        
        if len(self.clap_times) > 0:
            accuracy = (self.on_beat_count / len(self.clap_times)) * 100
            self.log.add_line(f"Game Over! Score: {self.on_beat_count}/{len(self.clap_times)} ({accuracy:.1f}%)")
            
            # Select next song based on performance
            self.select_next_song()
        else:
            self.log.add_line("Game over! No claps registered.")
    
    def select_next_song(self, threshold=5):
        bpms = sorted(songs.values())
        current_index = bpms.index(min(bpms, key=lambda x: abs(x - self.current_bpm)))
        
        if self.on_beat_count > threshold and current_index < len(bpms) - 1:
            next_bpm = bpms[current_index + 1]
            self.log.add_line("Great job! Moving to a faster song.")
        elif self.on_beat_count <= threshold and current_index > 0:
            next_bpm = bpms[current_index - 1]
            self.log.add_line("Let's try an easier tempo.")
        else:
            next_bpm = self.current_bpm
            self.log.add_line("Let's try this tempo again.")
        
        for name, bpm in songs.items():
            if bpm == next_bpm:
                self.log.add_line(f"Next song: {name} ({next_bpm} BPM)")
                self.current_song = name
                self.current_bpm = next_bpm
                return
    
    def update(self):
        now = time.time()
        
        # Handle countdown
        if self.is_playing and not self.is_tracking:
            if self.countdown > 0:
                self.countdown -= 1/60  # assuming 60 FPS
                if self.countdown <= 0:
                    self.start_tracking()
        
        # Handle beats visualization
        if self.is_tracking:
            elapsed = now - self.start_time
            
            # Check if game should end
            if elapsed > self.game_duration:
                self.end_game()
                return
            
            # Find current beat
            beat_index = int(elapsed / self.interval)
            if beat_index != self.last_beat_index and beat_index < len(self.beat_times):
                self.last_beat_index = beat_index
                self.beat_flash = 10  # visual feedback frames
                self.log.add_line("BEAT!")
        
        # Decay visual effects
        if self.beat_flash > 0:
            self.beat_flash -= 1
        if self.clap_flash > 0:
            self.clap_flash -= 1
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.register_clap()
            elif event.key == pygame.K_ESCAPE:
                if self.is_playing:
                    self.end_game()
                else:
                    return False  # Signal to quit
        
        # Handle mouse events for buttons
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                if not self.is_playing and self.start_button.is_clicked(mouse_pos, True):
                    self.start_game()
        
        # Handle mouse movement for button hover
        elif event.type == pygame.MOUSEMOTION:
            if not self.is_playing:
                self.start_button.check_hover(event.pos)
                
        return True
    
    def draw(self, surface):
        # Clear screen
        surface.fill(BLACK)
        
        # Draw title
        title = font_large.render("Rhythm Game", True, WHITE)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw song info
        song_info = font_medium.render(f"Song: {self.current_song} - {self.current_bpm} BPM", True, WHITE)
        surface.blit(song_info, (WIDTH//2 - song_info.get_width()//2, 80))
        
        # Draw log area
        pygame.draw.rect(surface, GRAY, (50, 130, WIDTH-100, 320), border_radius=10)
        self.log.draw(surface, 60, 140)
        
        # Draw beat and clap indicators
        if self.is_tracking:
            # Beat indicator
            beat_color = GREEN if self.beat_flash > 0 else GRAY
            pygame.draw.circle(surface, beat_color, (WIDTH//4, HEIGHT-180), 50)
            beat_text = font_small.render("Beat", True, WHITE)
            surface.blit(beat_text, (WIDTH//4 - beat_text.get_width()//2, HEIGHT-150))
            
            # Clap indicator
            clap_color = YELLOW if self.clap_flash > 0 else GRAY
            pygame.draw.circle(surface, clap_color, (3*WIDTH//4, HEIGHT-180), 50)
            clap_text = font_small.render("Clap", True, WHITE)
            surface.blit(clap_text, (3*WIDTH//4 - clap_text.get_width()//2, HEIGHT-150))
            
            # Draw score
            if len(self.clap_times) > 0:
                score_text = font_medium.render(
                    f"Score: {self.on_beat_count}/{len(self.clap_times)}", True, WHITE)
                surface.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT-200))
            
            # Draw time remaining
            elapsed = time.time() - self.start_time
            remaining = max(0, self.game_duration - elapsed)
            time_text = font_medium.render(f"Time: {remaining:.1f}s", True, WHITE)
            surface.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT-150))
            
            # Draw instructions
            instr = font_small.render("Press SPACE to clap | ESC to quit", True, WHITE)
            surface.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT-100))
        elif self.is_playing:
            # Countdown
            count_text = font_large.render(f"Starting in: {int(self.countdown)+1}", True, RED)
            surface.blit(count_text, (WIDTH//2 - count_text.get_width()//2, HEIGHT-180))
        else:
            # Draw start button
            self.start_button.draw(surface)
            
            # Draw instructions
            instr = font_small.render("Press SPACE to clap along with the beat!", True, WHITE)
            surface.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT-150))

def main():
    clock = pygame.time.Clock()
    game = RhythmGame()
    
    # Initialize with welcome message
    game.log.add_line("Welcome to the Rhythm Game!")
    game.log.add_line("Press the Start button to begin.")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Let the game handle events
            if not game.handle_event(event):
                running = False
        
        # Update game state
        game.update()
        
        # Draw everything
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()