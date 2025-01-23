import serial
import time

# Inicjalizacja portu szeregowego (dopasuj port, np. /dev/serial0)
ser = serial.Serial('/dev/serial0', 9600)  # Port szeregowy na Raspberry Pi Zero

# Funkcja do wysyłania dwóch linii tekstu
def send_two_lines(line1, line2):
    text = f"{line1}\n{line2}"  # Połącz teksty z '\n' jako separatorem
    ser.write(text.encode())    # Wyślij dane przez port szeregowy

# Testowanie
while True:
    send_two_lines("oczekiwanie na ", "dane....")  # Wysłanie dwóch linii
    time.sleep(5)  # Wysyłanie tekstu co 2 sekundy

    send_two_lines("jebac zydow", "i czarnych")  # Inny tekst na LCD
    time.sleep(2)
