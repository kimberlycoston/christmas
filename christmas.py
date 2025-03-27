from ultralytics import YOLO
import cv2
import numpy as np
import subprocess
import random

model = YOLO("best.pt")  # Path to your trained model

# Use this for testing with a static image
img_path = "your_test_image.jpg"
frame = cv2.imread(img_path)

# OR use this to grab a live frame from Pi Camera (commented out for now)
# def get_frame():
#     cmd = [
#         "libcamera-still",
#         "--width", "640",
#         "--height", "480",
#         "--nopreview",
#         "--timeout", "1",
#         "--output", "frame.jpg"
#     ]
#     subprocess.run(cmd, check=True)
#     return cv2.imread("frame.jpg")

# If using live mode:
# frame = get_frame()

# Fullscreen projector display
cv2.namedWindow("Projected Output", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Projected Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Detect once
results = model(frame, conf=0.3)
boxes = results[0].boxes.xyxy.cpu().numpy()

# Red and green laser colors (BGR)
colors = [(0, 0, 255), (0, 255, 0)]

# Define snowflake character
snowflake = "❄️"

# Choose font
font = cv2.FONT_HERSHEY_SIMPLEX

while True:
    laser_frame = frame.copy()

    for box in boxes:
        if random.random() > 0.8:  # twinkle flicker
            x1, y1, x2, y2 = map(int, box)
            color = random.choice(colors)
            thickness = random.choice([1, 1])
            cv2.rectangle(laser_frame, (x1, y1), (x2, y2), color, thickness)

            # Add snowflakes at corners
            snowflake_positions = [
                # (x1 - 10, y1 - 10),  # top-left
                (x1 - 7, y1),
                # (x2 + 5, y1 - 10),   # top-right
                (x2 + 1, y1 - 5),
                (x1 - 10, y2 + 20),  # bottom-left
                (x2 + 5, y2 + 20)    # bottom-right
            ]

            for pos in snowflake_positions:
                # Simulate snowflake using text (OpenCV doesn't support emojis well, so fallback to * symbol or asterisk)
                cv2.putText(
                    laser_frame,
                    "*",  # If your OpenCV doesn't support ❄️ emoji, use a symbol fallback
                    pos,
                    font,
                    0.8,
                    color,
                    2,
                    cv2.LINE_AA
                )

    cv2.imshow("Projected Output", laser_frame)

    # Refresh every 100 ms
    if cv2.waitKey(100) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()