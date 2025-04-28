# input/audio_handler.py
import pyaudio
import numpy as np
import time
from collections import deque

class AudioHandler:
    def __init__(self, 
                 sample_rate=44100, 
                 buffer_size=1024, 
                 channels=1,
                 threshold=0.1,
                 min_time_between_claps=0.5,
                 history_size=10):
        """
        Initialize the audio handler for clap detection.
        
        Args:
            sample_rate: Audio sample rate (Hz)
            buffer_size: Number of samples per buffer
            channels: Number of audio channels (1 for mono)
            threshold: Amplitude threshold for clap detection
            min_time_between_claps: Minimum time between claps (seconds)
            history_size: Number of buffers to keep for analysis
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channels = channels
        self.threshold = threshold
        self.min_time_between_claps = min_time_between_claps
        
        # Audio buffer history
        self.buffer_history = deque(maxlen=history_size)
        self.energy_history = deque(maxlen=30)  # Track more history for peak detection
        
        # State variables
        self.last_clap_time = 0
        self.running = False
        self.clap_count = 0
        self.clap_timestamps = []
        
        # Peak detection state
        self.rising_energy = False
        self.peak_in_progress = False
        
        # Callback function for clap events
        self.on_clap_callback = None
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Process incoming audio data.
        
        This is called by PyAudio for each audio buffer.
        """
        if not self.running:
            return (in_data, pyaudio.paContinue)
        
        # Convert buffer to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Calculate energy
        energy = np.mean(np.abs(audio_data))
        
        # Store data for analysis
        self.buffer_history.append(audio_data)
        self.energy_history.append(energy)
        
        # Debug output - print current energy level periodically
        if len(self.energy_history) % 10 == 0:
            print(f"Current energy: {energy:.6f}, Threshold: {self.threshold:.6f}")
        
        # Check for clap using improved peak detection logic
        current_time = time.time()
        time_since_last_clap = current_time - self.last_clap_time
        
        # Only consider claps if enough time has passed since the last one
        if time_since_last_clap > self.min_time_between_claps:
            # Detect when energy rises above threshold
            if energy > self.threshold and not self.peak_in_progress:
                self.peak_in_progress = True
                self.rising_energy = True
            
            # Detect when we've passed the peak (energy starts decreasing)
            elif self.peak_in_progress and self.rising_energy and energy < self.threshold:
                self.rising_energy = False
                # Only register a clap when the energy drops back below threshold
                self.clap_detected(current_time)
                self.peak_in_progress = False
            
            # Reset peak detection state when energy is low for a while
            elif energy < self.threshold * 0.5:
                self.peak_in_progress = False
                self.rising_energy = False
        
        return (in_data, pyaudio.paContinue)
    
    def clap_detected(self, timestamp):
        """Handle a detected clap event."""
        self.clap_count += 1
        self.last_clap_time = timestamp
        self.clap_timestamps.append(timestamp)
        print(f"👏 Clap detected! Total: {self.clap_count}")
        
        # Call the callback if it exists
        if self.on_clap_callback:
            self.on_clap_callback(timestamp)
    
    def set_clap_callback(self, callback_function):
        """
        Set a callback function to be called when a clap is detected.
        
        Args:
            callback_function: Function to call with timestamp parameter
        """
        self.on_clap_callback = callback_function
    
    def start(self):
        """Start listening for claps."""
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                output=False,
                frames_per_buffer=self.buffer_size,
                stream_callback=self.audio_callback
            )
            
            self.running = True
            print("Audio handler started. Listening for claps...")
            
            # Start the stream
            self.stream.start_stream()
            
        except Exception as e:
            print(f"Error starting audio handler: {e}")
            self.stop()
    
    def stop(self):
        """Stop listening for claps."""
        self.running = False
        
        # Clean up resources
        if hasattr(self, 'stream') and self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        
        if hasattr(self, 'audio') and self.audio is not None:
            self.audio.terminate()
        
        print("Audio handler stopped.")
        print(f"Detected {self.clap_count} claps.")
        
        # Print time intervals between claps if we have more than one
        if len(self.clap_timestamps) > 1:
            intervals = [round(self.clap_timestamps[i] - self.clap_timestamps[i-1], 3) 
                        for i in range(1, len(self.clap_timestamps))]
            print(f"Time intervals between claps (seconds): {intervals}")
    
    def calibrate(self, duration=5):
        """
        Calibrate the threshold based on ambient noise.
        
        Args:
            duration: Number of seconds to sample ambient noise
        """
        print(f"Calibrating microphone for {duration} seconds. Please remain silent...")
        
        # Start a temporary stream for calibration
        audio = pyaudio.PyAudio()
        energy_values = []
        
        def calibration_callback(in_data, frame_count, time_info, status):
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            energy = np.mean(np.abs(audio_data))
            energy_values.append(energy)
            return (in_data, pyaudio.paContinue)
        
        stream = audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            output=False,
            frames_per_buffer=self.buffer_size,
            stream_callback=calibration_callback
        )
        
        stream.start_stream()
        time.sleep(duration)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Calculate threshold based on ambient noise
        if energy_values:
            ambient_energy = np.mean(energy_values)
            std_dev = np.std(energy_values)
            
            # Set threshold to mean + 8 standard deviations for more reliable detection
            self.threshold = ambient_energy + 8 * std_dev
            print(f"Calibration complete. Threshold set to: {self.threshold:.6f}")
            print(f"Ambient noise level: {ambient_energy:.6f}")
        else:
            print("Calibration failed. Using default threshold.")
    
    def get_clap_timestamps(self):
        """Get all recorded clap timestamps."""
        return self.clap_timestamps


# Test function for the audio handler
def test_audio_handler():
    """Test function for the audio handler."""
    import sys
    import os
    
    # Add the project root to the path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import SAMPLE_RATE, BUFFER_SIZE, AUDIO_CHANNELS, DEFAULT_THRESHOLD, MIN_TIME_BETWEEN_CLAPS, CALIBRATION_DURATION
    
    # Create audio handler
    handler = AudioHandler(
        sample_rate=SAMPLE_RATE, 
        buffer_size=BUFFER_SIZE, 
        channels=AUDIO_CHANNELS,
        threshold=DEFAULT_THRESHOLD,
        min_time_between_claps=MIN_TIME_BETWEEN_CLAPS
    )
    
    # Set up a callback function
    def on_clap(timestamp):
        print(f"Clap callback called at {timestamp}")
    
    handler.set_clap_callback(on_clap)
    
    # Calibrate the detector
    handler.calibrate(duration=CALIBRATION_DURATION)
    
    # Start the handler
    handler.start()
    
    print("Listening for claps for 20 seconds. Press Ctrl+C to stop early.")
    try:
        for i in range(20):
            time.sleep(1)
            print(f"Time remaining: {20-i-1} seconds", end="\r", flush=True)
    
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    
    finally:
        # Stop the handler
        handler.stop()
        
        # Print results
        claps = handler.get_clap_timestamps()
        print(f"Test complete. Detected {len(claps)} claps.")


if __name__ == "__main__":
    test_audio_handler()