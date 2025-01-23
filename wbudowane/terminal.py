from pad4pi import rpi_gpio
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import serial
import time
import requests
import atexit

# Keypad setup
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]
ROW_PINS = [5, 6, 13, 19]
COL_PINS = [26, 16, 20, 21]
factory = rpi_gpio.KeypadFactory()
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

# RFID reader setup
reader = SimpleMFRC522()

# Serial display setup
ser = serial.Serial('/dev/serial0', 9600)

# Buzzer setup
BUZZER_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Cleanup function for GPIO and serial
@atexit.register
def cleanup():
    GPIO.cleanup()
    ser.close()

def send_two_lines(line1, line2):
    """Send two lines of text to the serial display."""
    text = f"{line1}\n{line2}"
    ser.write(text.encode())

def play_tone(frequency, duration):
    """Play a tone on the buzzer."""
    period = 1.0 / frequency
    cycles = int(frequency * duration)
    for _ in range(cycles):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(period / 2)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(period / 2)

def validate_amount(amount):
    """Validate if the entered amount is a positive number."""
    try:
        value = float(amount)
        return value > 0
    except ValueError:
        return False

def print_key(key):
    """Handle key press events."""
    global current_amount, blik_code, blik_on
    print(f"Key pressed: {key}")
    
    if key == "A":
        send_two_lines("Enter amount", "Press C to confirm")
        current_amount = ""
        blik_on = False  # Reset BLIK mode if user presses "A"
    elif key == "#":
        current_amount += "."
        send_two_lines("Amount:", current_amount)
    elif key == "C":
        if blik_on == "waiting_for_amount":  # If BLIK mode is active
            if current_amount:  # Make sure amount is entered first
                send_two_lines("Enter BLIK code", "Press B to confirm")
                blik_on = "waiting_for_blik_code"  # Change state to waiting for BLIK code
            else:
                send_two_lines("Enter amount first", "Press A to start")
        elif blik_on == "waiting_for_blik_code" and blik_code:
            verify_blik_code()
        elif current_amount and validate_amount(current_amount):
            process_card_payment(float(current_amount))
        else:
            send_two_lines("Invalid amount", "Try again")
    elif key == "D":
        # Reset everything if "D" is pressed
        current_amount = ""
        blik_code = ""
        blik_on = False
        send_two_lines("Choose method", "A-card B-BLIK")
    elif key == "*":
        # Backspace functionality
        if current_amount:
            current_amount = current_amount[:-1]
            send_two_lines("Amount:", current_amount)
    elif key.isdigit():
        if blik_on == "waiting_for_amount":
            current_amount += key
            send_two_lines("Amount:", current_amount)
        elif blik_on == "waiting_for_blik_code":
            blik_code += key
            send_two_lines("BLIK code:", blik_code)
        else:
            current_amount += key
            send_two_lines("Amount:", current_amount)
    elif key == "B":
        blik_on = "waiting_for_amount"
        send_two_lines("Enter amount:", "...")


def process_card_payment(amount):
    """Process payment using card."""
    send_two_lines("Hold card", "near reader")
    try:
        card_id, text = reader.read()
        try:
            response = requests.post("http://localhost:5000/check_balance", json={"card_id": card_id, "amount": amount})
            if response.status_code == 200:
                send_two_lines("Transaction", "successful")
                play_tone(440, 0.5)
            elif response.status_code == 400:
                send_two_lines("Insufficient", "funds")
            elif response.status_code == 403:
                send_two_lines("Access denied", "Check card")
            else:
                send_two_lines("Transaction", "failed")
        except requests.exceptions.RequestException as e:
            send_two_lines("Network error", "Try again")
            print(f"Error: {e}")
    except Exception as e:
        send_two_lines("Read error", str(e))

def verify_blik_code():
    """Verify the entered BLIK code."""
    global blik_code, current_amount, blik_on
    try:
        response = requests.post("http://localhost:5000/verify_blik", json={"blik_code": blik_code, "amount": float(current_amount)})
        """
        Invoke-WebRequest -Uri "http://127.0.0.1:5000/verify_blik" `
        -Method POST `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body '{"blik_code": "980260", "amount": 10.0}'
        """
    
        if response.status_code == 200:
            send_two_lines("Transaction", "successful")
            play_tone(440, 0.5)
        else:
            send_two_lines("Transaction", "failed")
    except requests.exceptions.RequestException as e:
        send_two_lines("Network error", "Try again")
        print(f"Error: {e}")
    finally:
        blik_code = ""
        current_amount = ""
        blik_on = False

# Global variables
current_amount = ""
blik_code = ""
blik_on = False

# Attach key press handler
keypad.registerKeyPressHandler(print_key)

# Main program loop
try:
    send_two_lines("Choose method:", "A-card  B-BLIK")
    while True:
        pass
except KeyboardInterrupt:
    print("\nExiting...")
#koniec3
