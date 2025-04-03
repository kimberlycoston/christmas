# vision_module/ui_utils.py
import cv2
import numpy as np
import colorsys

# === HELPER TO GENERATE CLASS COLORS ===
def generate_class_colors(class_names):
    hsv = [(i / len(class_names), 0.7, 1.0) for i in range(len(class_names))]
    rgb = [tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*h)) for h in hsv]
    return {cls: color for cls, color in zip(class_names, rgb)}

# === MAIN UI FUNCTION ===
def show_preview(image, contours, class_names):
    class_colors = generate_class_colors(class_names)
    height, width = image.shape[:2]
    overlay = image.copy()
    mask = np.zeros((height, width), dtype=np.uint8)

    for cnt, class_name in contours:
        color = class_colors.get(class_name, (255, 255, 255))

        if class_name.lower() == "trim":
            cv2.drawContours(overlay, [cnt], -1, color, thickness=cv2.FILLED)
            cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)

        elif class_name.lower() == "window":
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)
            area_ratio = cv2.contourArea(cnt) / float(w * h)
            if 0.6 < aspect_ratio < 1.8 and area_ratio > 0.6:
                rect = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]])
                cv2.polylines(overlay, [rect], True, color, 2)
                cv2.polylines(mask, [rect], True, 255, 3)
                continue
            cv2.polylines(overlay, [cnt], True, color, 2)
            cv2.polylines(mask, [cnt], True, 255, 3)

        else:
            cv2.polylines(overlay, [cnt], True, color, 2)
            x, y = cnt[0][0]
            cv2.putText(overlay, class_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.polylines(mask, [cnt], True, 255, 3)

    preview = cv2.hconcat([overlay, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])
    preview_small = cv2.resize(preview, (0, 0), fx=0.5, fy=0.5)

    window_name = "Preview"
    cv2.imshow(window_name, preview_small)
    key = cv2.waitKey(0)  # Wait for key press
    if key == ord("s"):
        cv2.imwrite("mask_dynamic_final.png", mask)
        cv2.imwrite("overlay_dynamic_final.png", overlay)
        print("✅ Saved mask and overlay.")
    cv2.destroyAllWindows()
