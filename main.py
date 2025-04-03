# main.py
from gpiozero import Button
from gpiozero.pins.pigpio import PiGPIOFactory
import threading
from control_module.door_control import open_door, close_door, get_current_time, show_boot_message
from vision_module.vision import capture_image
import time

factory = PiGPIOFactory()

# Buttons
door_button = Button(22, pull_up=True, pin_factory=factory, bounce_time=0.2)
photo_button = Button(23, pull_up=True, pin_factory=factory, bounce_time=0.2)

opened = False
closed = False

def handle_door_press():
    global opened, closed
    if not opened:
        open_door()
        opened = True
        closed = False
    else:
        close_door()
        closed = True
        opened = False

def handle_photo_press():
    print("📷 Button pressed to capture image")
    capture_image()

door_button.when_pressed = handle_door_press
photo_button.when_pressed = handle_photo_press

def rtc_loop():
    global opened, closed
    while True:
        now = get_current_time()
        hour = now.tm_hour
        minute = now.tm_min

        if hour == 18 and minute == 0 and not opened:
            open_door()
            opened = True
            closed = False
        elif hour == 6 and minute == 0 and not closed:
            close_door()
            closed = True
            opened = False

        time.sleep(20)

# Start up
show_boot_message()
threading.Thread(target=rtc_loop, daemon=True).start()

# Your OpenCV interface can go here if needed too
while True:
    time.sleep(1)  # Keeps the main loop alive
