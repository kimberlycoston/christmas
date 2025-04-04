from gpiozero import Button
from gpiozero.pins.pigpio import PiGPIOFactory

factory = PiGPIOFactory()
button = Button(22, pull_up=True, pin_factory=factory)

print("Waiting for button press...")

def on_press():
    print("🎉 Button press detected!")

button.when_pressed = on_press

# Keep the program running
while True:
    pass
