from gpiozero import Servo
from time import sleep
from gpiozero.pins.pigpio import PiGPIOFactory

# Use PiGPIOFactory for better PWM accuracy
factory = PiGPIOFactory()

# Replace 17 with your GPIO pin
servo = Servo(17, pin_factory=factory, min_pulse_width=0.0005, max_pulse_width=0.0025)

print("Starting servo test...")

try:
    while True:
        print("Full speed forward")
        servo.value = 0.08  # Full speed clockwise
        sleep(2.3)

        print("Stop")
        servo.value = 0  # Stop
        sleep(2)

        print("Full speed reverse")
        servo.value = -0.08  # Full speed counter-clockwise
        sleep(2.3)

        print("Stop")
        servo.value = 0
        sleep(2)

except KeyboardInterrupt:
    print("Stopped by user.")
