from time import sleep
from gpiozero import TonalBuzzer, LED
from gpiozero.tones import Tone

# Define buzzer and LEDs
buzzer = TonalBuzzer(26)  # GPIO4

# Tempo and note duration
tempo = 140
wholenote = (60000 * 4) / tempo  # in milliseconds

# Notes dictionary
notes = {
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784,
    'A5': 880, 'AS5': 932, 'B5': 988, 'C6': 1047, 'REST': 0
}

# Problem notes that need to be transposed down
problem_notes = ['AS5', 'C6']

# Melody as (note, duration) tuples
melody = [
    ("C5", 4), ("F5", 4), ("F5", 8), ("G5", 8), ("F5", 8), ("E5", 8),
    ("D5", 4), ("D5", 4), ("D5", 4), ("G5", 4), ("G5", 8), ("A5", 8),
    ("G5", 8), ("F5", 8), ("E5", 4), ("C5", 4), ("C5", 4), ("A5", 4),
    ("A5", 8), ("AS5", 8), ("A5", 8), ("G5", 8), ("F5", 4), ("D5", 4),
    ("C5", 8), ("C5", 8), ("D5", 4), ("G5", 4), ("E5", 4), ("F5", 2)
]

def get_safe_frequency(note, freq):
    """Adjust frequency to be within buzzer's range"""
    if freq == 0:
        return 0
        
    # If this is a known problem note, transpose down an octave
    if note in problem_notes:
        return freq // 2
    
    # For other notes, check if they're too high
    if freq > 900:  # Your buzzer seems to max out below 900Hz
        return freq // 2
    
    return freq

def play_melody():
    for note, divider in melody:
        if divider > 0:
            note_duration = wholenote / divider
        else:
            note_duration = (wholenote / abs(divider)) * 1.5

        duration_sec = note_duration / 1000

        original_freq = notes[note]
        if original_freq == 0:
            buzzer.stop()
        else:
            frequency = get_safe_frequency(note, original_freq)
            try:
                buzzer.play(Tone(frequency))
                print(f"Playing {note} at {frequency}Hz (original: {original_freq}Hz)")
            except ValueError:
                buzzer.stop()

        sleep(duration_sec * 0.9)
        buzzer.stop()
        sleep(duration_sec * 0.1)

# Only play if run directly
if __name__ == "__main__":
    play_melody()