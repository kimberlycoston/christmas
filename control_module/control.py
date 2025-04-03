from gpiozero import Servo, Button
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import board
import busio
import adafruit_ds3231
import threading
from RPLCD.i2c import CharLCD
from datetime import datetime, timedelta
from buzzer_utils import play_melody


# === SETUP ===

# RTC (DS3231)
i2c = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_ds3231.DS3231(i2c)

# PiGPIO for servo + button (ensure pigpiod is running!)
factory = PiGPIOFactory()

# Servo using your tested pulse widths
servo = Servo(17, pin_factory=factory, min_pulse_width=0.0005, max_pulse_width=0.0025)
servo.value = 0
sleep(0.3)
servo.detach()

# LCD (adjust I2C address if needed)
lcd = CharLCD('PCF8574', 0x27)

# Button on GPIO 22
test_button = Button(22, pull_up=True, pin_factory=factory, bounce_time=0.2)

import threading

test_toggle = [True]
test_lock = threading.Lock()

def handle_test_press():
    if test_lock.locked():
        return  # Ignore if still running

    with test_lock:
        if test_toggle[0]:
            lcd_message("Test: Opening")
            print("Test mode: Opening")
            open_door()
        else:
            lcd_message("Test: Closing")
            print("Test mode: Closing")
            close_door()
        test_toggle[0] = not test_toggle[0]
        sleep(0.5)  # small delay to avoid bouncing
test_button.when_pressed = handle_test_press



def time_until_event(now, target_hour):
    """Returns (hours, minutes) until target hour (24h format)"""
    current_time = datetime(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
    target_time = datetime(now.tm_year, now.tm_mon, now.tm_mday, target_hour, 0)

    if target_time <= current_time:
        # If target time already passed today, set it for tomorrow
        target_time += timedelta(days=1)

    delta = target_time - current_time
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return hours, minutes


# === FUNCTIONS ===

def lcd_message(line1="", line2=""):
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string(line1[:16])
    lcd.cursor_pos = (1, 0)
    lcd.write_string(line2[:16])

def open_door():
    print("Opening door...")
    lcd_message("Opening door...")
    servo.value = 0.08
    sleep(2.1)
    servo.value = 0
    sleep(0.3)
    servo.detach()
    play_melody()



def close_door():
    print("Closing door...")
    lcd_message("Closing door...")
    servo.value = -0.11
    sleep(2.6)
    servo.value = 0
    sleep(0.3)
    servo.detach()


# === MAIN LOOP ===

opened = False
closed = False

try:
    lcd_message("Booting up...")
    sleep(2)
    lcd.clear()

    while True:
        now = rtc.datetime
        hour = now.tm_hour
        minute = now.tm_min

        # Open at 6 PM
        if hour == 18 and minute == 0 and not opened:
            open_door()
            opened = True
            closed = False

        # Close at 6 AM
        elif hour == 6 and minute == 0 and not closed:
            close_door()
            closed = True
            opened = False

        # Otherwise just display time
        if 6 <= hour < 18:
            # Between 6 AM and 6 PM → waiting for open
            hrs, mins = time_until_event(now, 18)
            lcd_message("Open in:", f"{hrs:02}h {mins:02}m remains")
        else:
            # Between 6 PM and 6 AM → waiting for close
            hrs, mins = time_until_event(now, 6)
            lcd_message("Magic sleeps in:", f"{hrs:02}h {mins:02}m")


        sleep(20)

except KeyboardInterrupt:
    print("Shutting down...")
    lcd.clear()
    lcd.write_string("Shutting down...")

finally:
    print("Detaching servo and cleaning up...")
    servo.detach()
    lcd.clear()



