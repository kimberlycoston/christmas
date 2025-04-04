import cv2
import numpy as np
from PIL import Image, ImageSequence

# Load the binary mask
mask = cv2.imread("mask_dynamic.png", cv2.IMREAD_GRAYSCALE)
mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

# Resize your mask and GIF to match
h, w = mask.shape[:2]

# Load GIF and convert frames to OpenCV format
gif = Image.open("colors.gif")
frames = []

for frame in ImageSequence.Iterator(gif):
    rgb = frame.convert("RGB").resize((w, h))  # Resize to match mask
    opencv_frame = np.array(rgb)[..., ::-1]  # Convert RGB → BGR
    frames.append(opencv_frame)

# Loop through frames and project them only on white mask regions
while True:
    for f in frames:
        # Keep only the parts where mask is white
        light_overlay = cv2.bitwise_and(f, f, mask=mask)

        # Optional: blend with a background image (like your original photo)
        # bg = cv2.imread("captured_image.jpg")
        # result = cv2.addWeighted(bg, 0.6, light_overlay, 0.4, 0)
        # cv2.imshow("Projected Lights", result)

        # Or just show the overlay
        cv2.imshow("Projected Lights", light_overlay)

        if cv2.waitKey(100) & 0xFF == 27:
            break

    if cv2.waitKey(10) & 0xFF == 27:
        break

cv2.destroyAllWindows()
