import board
import busio
import adafruit_ds3231
import time

# Setup I2C
i2c = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_ds3231.DS3231(i2c)

# Set RTC time to match the Pi's system time
now = time.localtime()
rtc.datetime = now

print("RTC time set to:", rtc.datetime)
