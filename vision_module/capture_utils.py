import os
from datetime import datetime
import cv2

def capture_image():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captured_image_{timestamp}.jpg"
    os.system(f"libcamera-still -o {filename} --width 640 --height 480 --timeout 1000")
    print(f"📷 Image saved to {filename}")
    return cv2.imread(filename)
