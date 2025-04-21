import time
import keyboard
import pygame

songs = {
    "Hotel California": 74,
    "Yellow": 84,
    "Chaiyya Chaiyya": 92,
    "Chasing Cars": 104,
    "Another One Bites The Dust": 110,
    "Dynamite": 116,
    "Beat It": 140,
}

# Starting with the first song
first_song = next(iter(songs))
print("Let's start with:", first_song)
current_bpm = 80

# Setup beat interval and tolerances
interval = 60 / current_bpm * 2  # seconds between beats
tolerance = 1  # allowable delay/advance
duration = 20  # total duration for testing after 10s buffer

pygame.mixer.init()
pygame.mixer.music.load(r"C:\Users\Surbhi Agarwal\Music\HotelCalifornia.mp3")
pygame.mixer.music.play()
print(f"Now playing: {first_song} ({current_bpm} BPM)")

# Wait 10 seconds before tracking
print("Get ready... tracking starts in 10 seconds!")
time.sleep(10)

# Now begin tracking
start_time = time.time()
end_time = start_time + duration
clap_times = []

# Generate correct beat times upfront
beat_times = [start_time + i * interval for i in range(int(duration / interval))]

print("Press SPACE to clap (ESC to stop)\n")

i = 0
while time.time() < end_time:
    now = time.time()

    if i < len(beat_times) and now >= beat_times[i]:
        print("CLAP!")
        i += 1

    if keyboard.is_pressed('space'):
        clap_time = time.time()
        print(f"Clap at: {clap_time}")
        clap_times.append(clap_time)
        time.sleep(0.2)

    if keyboard.is_pressed('esc'):
        print("Stopped early.")
        break

    time.sleep(0.01)

# Check if claps are on beat
def is_on_beat(clap_time, beat_times, tolerance):
    return any(abs(clap_time - beat) <= tolerance for beat in beat_times)

on_beat = 0

for clap in clap_times:
    if is_on_beat(clap, beat_times, tolerance):
        print(f"CORRECT: On beat: {clap}")
        on_beat += 1
    else:
        print(f"WRONG: Off beat: {clap}")

print(f"\nYou got {on_beat} / {len(clap_times)} claps on beat!")

# Select next song
def select_next_song(correct_beats, current_bpm, songs, threshold=10):
    bpms = sorted(songs.values())
    current_index = bpms.index(min(bpms, key=lambda x: abs(x - current_bpm)))

    if correct_beats > threshold and current_index < len(bpms) - 1:
        next_bpm = bpms[current_index + 1]
    elif correct_beats <= threshold and current_index > 0:
        next_bpm = bpms[current_index - 1]
    else:
        next_bpm = current_bpm

    for name, bpm in songs.items():
        if bpm == next_bpm:
            print(f"Next song: {name} ({next_bpm} BPM)")
            return name, next_bpm

    return None, next_bpm

next_song, next_bpm = select_next_song(on_beat, current_bpm, songs)
