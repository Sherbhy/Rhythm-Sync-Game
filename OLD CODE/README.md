# Rhythm Sync Game

A rhythm-based multiplayer game where players clap in sync with the beat of popular songs.  
This repository contains the core backend logic of the game.

> **Note:** The active development is happening in the `dev` branch.

---

## ✅ Current Features

- Beat sync detection based on BPM and timing evaluation
- Keyboard input-based clap simulation
- Audio playback of songs
- Next song selection logic based on player performance

All functionalities are under active development and tuning.

---

## 🔜 Upcoming Features

- **Clap Detection via Audio Input**  
  Integration of real-time audio-based clap detection.

- **Multiple Input Modes (Makey Makey Integration)**  
  Support for detecting and evaluating claps through alternative input sources like Makey Makey.

- **UI Development**  
  A suitable UI framework (e.g., `pygame`) will be finalized.  
  Frontend development is yet to begin and will be synced with backend functionality.

## 🛠️ Setup Instructions

### Step 1: Clone the repository

```
git clone https://github.com/Sherbhy/Rhythm-Sync-Game.git
cd Rhythm-Sync-Game
```

> Make sure to check out the `dev` branch for the latest updates:

```
git checkout dev
```

### Step 2: Activate the virtual environment

- **Windows:**
  ```
  RhythmGameEnv\Scripts\activate
  ```

- **macOS/Linux:**
  ```
  source RhythmGameEnv/bin/activate
  ```

### Step 3: Install dependencies (if `requirements.txt` is available)

```
pip install -r requirements.txt
```

### Step 4: Run the backend

```
python rhythm_backend.py
```

---
```
