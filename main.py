# main.py
from gpiozero import Button
from gpiozero.pins.pigpio import PiGPIOFactory
import threading
from control_module.control import open_door, close_door, get_current_time, show_boot_message, time_until_event, lcd_message, setup_test_button, shutdown
# from vision_module.vision import capture_image
from vision_module.yolo_utils import run_yolo
from vision_module.capture_utils import capture_image
from vision_module.ui_utils import launch_editor
from vision_module.edit_utils import edit_mask_interactively


import time

# State flags for door
opened = False
closed = False

# Set up PiGPIO
factory = PiGPIOFactory()

# Set up photo button
photo_button = Button(21, pull_up=True, pin_factory=factory, bounce_time=0.2)

def handle_photo_press():
    print("📷 Button pressed to capture image")
    lcd_message("📷 Taking picture", "Please wait...")  # <-- ADD THIS LINE
    image = capture_image()
    launch_editor(image, initial_conf=0.6)
    lcd_message("✅ Done!", "Image captured")



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

        # Display countdown on LCD
        if 6 <= hour < 18:
            hrs, mins = time_until_event(now, 18)
            lcd_message("Open in:", f"{hrs:02}h {mins:02}m remains")
        else:
            hrs, mins = time_until_event(now, 6)
            lcd_message("Magic sleeps in:", f"{hrs:02}h {mins:02}m")

        time.sleep(20)

try:
    show_boot_message()
    setup_test_button()  # ✅ This sets up the demo test button on GPIO 22
    threading.Thread(target=rtc_loop, daemon=True).start()

    # Keep main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Shutting down...")
    lcd_message("Shutting down...")
    time.sleep(1)
    shutdown()  # ✅ calls cleanup from control.py
