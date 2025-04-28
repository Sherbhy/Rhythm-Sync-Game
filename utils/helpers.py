# utils/helpers.py

def format_time(seconds):
    """
    Format seconds into a readable time string.
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted time string (MM:SS)
    """
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def calculate_accuracy(on_beat, total):
    """
    Calculate accuracy percentage.
    
    Args:
        on_beat: Number of on-beat claps
        total: Total number of claps
    
    Returns:
        Accuracy percentage
    """
    if total == 0:
        return 0
    return (on_beat / total) * 100

def get_difficulty_name(bpm):
    """
    Get a difficulty name based on BPM.
    
    Args:
        bpm: Beats per minute
    
    Returns:
        Difficulty name
    """
    if bpm < 80:
        return "Easy"
    elif bpm < 100:
        return "Medium"
    elif bpm < 120:
        return "Hard"
    else:
        return "Expert"