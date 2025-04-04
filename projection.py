import cv2
import numpy as np
from PIL import Image, ImageSequence

# Load binary mask
mask = cv2.imread("mask_dynamic.png", cv2.IMREAD_GRAYSCALE)
mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
h, w = mask.shape[:2]

# Load GIF frames
gif = Image.open("gifs/colors.gif")
frames = []
for frame in ImageSequence.Iterator(gif):
    rgb = frame.convert("RGB").resize((w, h))
    frame_cv = np.array(rgb)[..., ::-1]
    frames.append(frame_cv)

# Set up full-screen window on projector
cv2.namedWindow("Projected Lights", cv2.WND_PROP_FULLSCREEN)
cv2.moveWindow("Projected Lights", 0, 0)
cv2.setWindowProperty("Projected Lights", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
    for f in frames:
        # Apply the light effect only where the mask is white
        light_overlay = cv2.bitwise_and(f, f, mask=mask)

        # Display on projector
        cv2.imshow("Projected Lights", light_overlay)
        if cv2.waitKey(100) & 0xFF == 27:  # ESC to quit
            break

    if cv2.waitKey(10) & 0xFF == 27:
        break

cv2.destroyAllWindows()
