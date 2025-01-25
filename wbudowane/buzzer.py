import RPi.GPIO as GPIO
import time

# Pin configuration
BUZZER_PIN = 4  # GPIO pin connected to SIG

# Melody (list of frequencies in Hz and their durations in seconds)
melody = [
    (440, 0.5),  # A4
    (494, 0.5),  # B4
    (523, 0.5),  # C5
    (587, 0.5),  # D5
    (659, 0.5),  # E5
    (698, 0.5),  # F5
    (784, 0.5),  # G5
]

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

def play_tone(frequency, duration):
    """Play a tone on the passive buzzer."""
    period = 1.0 / frequency
    cycles = int(frequency * duration)
    for _ in range(cycles):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(period / 2)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(period / 2)

try:
    print("Playing melody...")
    for note, duration in melody:
        if note == 0:  # Rest
            time.sleep(duration)
        else:
            play_tone(note, duration)
        time.sleep(0.1)  # Short pause between notes
finally:
    GPIO.cleanup()
    print("Done.")
