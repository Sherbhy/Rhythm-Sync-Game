import pyaudio
import numpy as np
import scipy.signal as signal
import time
from collections import deque

class ClapDetector:
    def __init__(self, 
                 sample_rate=44100, 
                 buffer_size=1024, 
                 channels=1,
                 threshold=0.1,
                 min_time_between_claps=0.5,  # Increased from 0.3 to 0.5 seconds
                 history_size=10,
                 visualization=False):
        """
        Initialize the clap detector.
        
        Args:
            sample_rate: Audio sample rate (Hz)
            buffer_size: Number of samples per buffer
            channels: Number of audio channels (1 for mono)
            threshold: Amplitude threshold for clap detection
            min_time_between_claps: Minimum time between claps (seconds)
            history_size: Number of buffers to keep for visualization
            visualization: Whether to show real-time visualization (not currently used)
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channels = channels
        self.threshold = threshold
        self.min_time_between_claps = min_time_between_claps
        self.visualization = False  # Disabling visualization to avoid errors
        
        # Audio buffer history
        self.buffer_history = deque(maxlen=history_size)
        self.energy_history = deque(maxlen=30)  # Increased to track more history for peak detection
        
        # State variables
        self.last_clap_time = 0
        self.running = False
        self.clap_count = 0
        self.clap_timestamps = []
        
        # Peak detection state
        self.rising_energy = False
        self.peak_in_progress = False
    
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
        
        # Store data for potential visualization
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
            print("Clap detector started. Listening for claps...")
            
            # Start the stream
            self.stream.start_stream()
            
        except Exception as e:
            print(f"Error starting clap detector: {e}")
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
        
        print("Clap detector stopped.")
        print(f"Detected {self.clap_count} claps at timestamps: {self.clap_timestamps}")
        
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
        print(f"Calibrating for {duration} seconds. Please remain silent...")
        
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
            # Increased from 5 to 8 to reduce false positives
            self.threshold = ambient_energy + 8 * std_dev
            print(f"Calibration complete. Threshold set to: {self.threshold:.6f}")
            print(f"Ambient noise level: {ambient_energy:.6f}")
        else:
            print("Calibration failed. Using default threshold.")


def main():
    """Main function to run the clap detector."""
    # Create a clap detector with visualization
    detector = ClapDetector(visualization=True)
    
    # Calibrate the detector
    detector.calibrate(duration=3)
    
    try:
        # Start detecting claps
        detector.start()
        
        # Keep the program running until Ctrl+C is pressed
        while detector.running:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nStopping...")
    
    finally:
        # Clean up
        detector.stop()


if __name__ == "__main__":
    main()