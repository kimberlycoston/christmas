import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_state = 1
while True:
    current = GPIO.input(18)
    if current != last_state:
        print("Pressed!" if current == 0 else "Released!")
        last_state = current
    time.sleep(0.01)