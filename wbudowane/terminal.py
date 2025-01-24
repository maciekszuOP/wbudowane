# Importowanie niezbędnych bibliotek
from pad4pi import rpi_gpio
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import serial
import time
import requests
import atexit

# Konfiguracja klawiatury
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]
ROW_PINS = [5, 6, 13, 19]  # Piny GPIO dla wierszy klawiatury
COL_PINS = [26, 16, 20, 21]  # Piny GPIO dla kolumn klawiatury
factory = rpi_gpio.KeypadFactory()  # Tworzenie fabryki klawiatury
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)  # Tworzenie instancji klawiatury

# Konfiguracja czytnika RFID
reader = SimpleMFRC522()  # Tworzenie instancji czytnika RFID

# Konfiguracja wyświetlacza szeregowego
ser = serial.Serial('/dev/serial0', 9600)  # Ustawienie połączenia szeregowego na /dev/serial0 z prędkością 9600 bps

# Konfiguracja buzzera
BUZZER_PIN = 4  # Pin GPIO dla buzzera
GPIO.setmode(GPIO.BCM)  # Ustawienie trybu numeracji pinów na BCM
GPIO.setup(BUZZER_PIN, GPIO.OUT)  # Ustawienie pinu buzzera jako wyjście

# Funkcja do wysyłania dwóch linii tekstu na wyświetlacz
def send_two_lines(line1, line2):
    ser.write(f"{line1}\n{line2}\n".encode())

# Funkcja do obsługi naciśnięcia klawisza
def print_key(key):
    global current_amount, blik_code, blik_on
    if key == "A":
        # Obsługa metody płatności kartą
        send_two_lines("Card payment", "Place your card")
        try:
            id, text = reader.read()
            print(f"Card ID: {id}")
            send_two_lines("Card read", "Processing...")
            # Wysłanie żądania do serwera w celu sprawdzenia salda
            response = requests.post("http://yourserver/check_balance", json={"card_id": id, "amount": current_amount})
            if response.status_code == 200:
                send_two_lines("Payment successful", f"New balance: {response.json()['new_balance']}")
            else:
                send_two_lines("Payment failed", response.json()["message"])
        except Exception as e:
            print(f"Error: {e}")
        finally:
            current_amount = ""
    elif key == "B":
        # Obsługa metody płatności BLIK
        blik_on = True
        send_two_lines("Enter BLIK code", "")
    elif key == "#":
        if blik_on:
            # Weryfikacja kodu BLIK
            send_two_lines("Verifying BLIK", "Please wait...")
            try:
                response = requests.post("http://yourserver/verify_blik", json={"blik_code": blik_code, "amount": current_amount})
                if response.status_code == 200:
                    send_two_lines("Payment successful", f"New balance: {response.json()['new_balance']}")
                else:
                    send_two_lines("Payment failed", response.json()["message"])
            except Exception as e:
                print(f"Error: {e}")
            finally:
                blik_code = ""
                current_amount = ""
                blik_on = False
        else:
            # Dodanie cyfry do kwoty
            current_amount += key
            send_two_lines("Current amount:", current_amount)
    elif key == "*":
        # Resetowanie kwoty
        current_amount = ""
        send_two_lines("Amount reset", "")
    else:
        if blik_on:
            # Dodanie cyfry do kodu BLIK
            blik_code += key
            send_two_lines("Enter BLIK code", blik_code)
        else:
            # Dodanie cyfry do kwoty
            current_amount += key
            send_two_lines("Current amount:", current_amount)

# Zmienna globalna
current_amount = ""
blik_code = ""
blik_on = False

# Rejestracja obsługi naciśnięcia klawisza
keypad.registerKeyPressHandler(print_key)

# Główna pętla programu
try:
    send_two_lines("Choose method:", "A-card  B-BLIK")
    while True:
        pass
except KeyboardInterrupt:
    print("\nExiting...")
    GPIO.cleanup()  # Czyszczenie ustawień GPIO przy wyjściu
    ser.close()  # Zamknięcie połączenia szeregowego