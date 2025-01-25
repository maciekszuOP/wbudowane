from pad4pi import rpi_gpio

# Define the layout for a 4x4 keypad
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

# Define GPIO pins for rows and columns
ROW_PINS = [5, 6, 13, 19]  # Change to your GPIO pins
COL_PINS = [26, 16, 20, 21]  # Change to your GPIO pins

# Setup keypad
factory = rpi_gpio.KeypadFactory()
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

def process_payment():
    print("Processing payment...")

def process_blik_payment():
    print("Processing BLIK payment...")

def print_key(key):
    print(f"Key pressed: {key}")
    if key == "#":
        process_payment()
    elif key == "A":
        process_blik_payment()

# Attach key press handler
keypad.registerKeyPressHandler(print_key)

try:
    print("Press keys on the keypad. Ctrl+C to exit.")
    while True:
        pass
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    keypad.cleanup()
