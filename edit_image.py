import cv2
import numpy as np

drawing = False
erasing = False
last_point = None

# Load the mask as grayscale and convert to color for drawing
img = cv2.imread("mask.png", cv2.IMREAD_GRAYSCALE)
img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

def mouse_events(event, x, y, flags, param):
    global drawing, erasing, last_point

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        last_point = (x, y)

    elif event == cv2.EVENT_RBUTTONDOWN:
        erasing = True
        last_point = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing and last_point:
            cv2.line(img_color, last_point, (x, y), (255, 255, 255), thickness=3)
            last_point = (x, y)
        elif erasing and last_point:
            cv2.line(img_color, last_point, (x, y), (0, 0, 0), thickness=15)
            last_point = (x, y)

    elif event in [cv2.EVENT_LBUTTONUP, cv2.EVENT_RBUTTONUP]:
        drawing = False
        erasing = False
        last_point = None

# Create window and bind mouse callback
cv2.namedWindow("Edit Contour Mask")
cv2.setMouseCallback("Edit Contour Mask", mouse_events)

print("🖱️ Left-click to draw (white lines)")
print("🖱️ Right-click to erase (black)")
print("💾 Press 's' to save")
print("❌ Press ESC to quit")

while True:
    cv2.imshow("Edit Contour Mask", img_color)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        final = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("mask_edited.png", final)
        print("✅ Saved as 'mask_edited.png'")
    elif key == 27:  # ESC
        break

cv2.destroyAllWindows()
