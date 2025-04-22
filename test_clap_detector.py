from clap_detector import ClapDetector
import time

def test_clap_detector():
    """Test the clap detector for a fixed duration."""
    # Create a clap detector
    detector = ClapDetector(
        threshold=0.1,  # Starting threshold (will be updated by calibration)
        min_time_between_claps=0.5,  # 500ms minimum between claps (increased from 300ms)
        visualization=False  # Visualization disabled to avoid errors
    )
    
    # Calibrate based on ambient noise
    detector.calibrate(duration=3)
    
    # Start the detector
    detector.start()
    
    # Run for 20 seconds
    print("Listening for claps for 20 seconds. Clap your hands to test!")
    print("Press Ctrl+C to stop early.")
    try:
        for i in range(20):
            time.sleep(1)
            # Print a countdown
            print(f"Time remaining: {20-i-1} seconds", end="\r", flush=True)
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    
    # Stop the detector
    detector.stop()
    
    # Report results
    print(f"\nTest complete. Detected {detector.clap_count} claps.")


if __name__ == "__main__":
    test_clap_detector()