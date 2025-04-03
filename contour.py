import cv2
import numpy as np
import colorsys
from ultralytics import YOLO

# ===============================
# GLOBAL SETUP
# ===============================
model = YOLO("best.pt")
image_path = "mom_house_final.png"
original_img = cv2.imread(image_path)
original_height, original_width = original_img.shape[:2]
resized_img = cv2.resize(original_img, (640, 640))

window_name = "Preview"
current_conf = 0.6
visible_classes = set()
selected_contour_idx = -1
selected_point_idx = -1
is_dragging = False
last_slider_conf = -1  # to detect slider changes
undo_stack = []

# Helper: Generate consistent colors

def generate_class_colors(class_names):
    hsv = [(i / len(class_names), 0.7, 1.0) for i in range(len(class_names))]
    rgb = [tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*h)) for h in hsv]
    return {cls: color for cls, color in zip(class_names, rgb)}

# Dummy callback for trackbar
def nothing(x):
    pass

# ===============================
# INTERACTION STORAGE
# ===============================
all_contours = []  # List of (cnt, class_name)
mouse_x, mouse_y = -1, -1

# ===============================
# MOUSE EVENTS
# ===============================
def mouse_callback(event, x, y, flags, param):
    global selected_contour_idx, selected_point_idx, is_dragging, mouse_x, mouse_y
    mouse_x, mouse_y = x * 2, y * 2

    if event == cv2.EVENT_LBUTTONDOWN:
        for idx, (cnt, _) in enumerate(all_contours):
            for pt_idx, pt in enumerate(cnt):
                px, py = pt[0]
                if abs(px - mouse_x) < 10 and abs(py - mouse_y) < 10:
                    selected_contour_idx = idx
                    selected_point_idx = pt_idx
                    is_dragging = True
                    return

        for idx, (cnt, class_name) in enumerate(all_contours):
            if cv2.pointPolygonTest(cnt, (mouse_x, mouse_y), False) >= 0:
                undo_stack.append(list(all_contours))
                print(f"🗑️ Deleted: {class_name}")
                all_contours.pop(idx)
                return

    elif event == cv2.EVENT_LBUTTONUP:
        is_dragging = False

    elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
        if 0 <= selected_contour_idx < len(all_contours):
            cnt, class_name = all_contours[selected_contour_idx]
            cnt[selected_point_idx][0] = [mouse_x, mouse_y]

# ===============================
# INITIALIZATION
# ===============================
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, mouse_callback)
cv2.createTrackbar("Confidence", window_name, int(current_conf * 100), 100, nothing)

# Initial prediction to get class names
initial_results = model.predict(source=resized_img, conf=current_conf, verbose=False, task='segment')
class_names = list(initial_results[0].names.values())
class_colors = generate_class_colors(class_names)
visible_classes = set(class_names)

# Store contours once

def update_contours(conf):
    global all_contours, selected_contour_idx, selected_point_idx, is_dragging
    selected_contour_idx = -1
    selected_point_idx = -1
    is_dragging = False
    global all_contours
    all_contours = []
    results = model.predict(source=resized_img, conf=conf, verbose=False, task='segment')
    if results[0].masks is not None:
        for i, mask in enumerate(results[0].masks.data):
            class_id = int(results[0].boxes.data[i][5])
            class_name = results[0].names[class_id]
            if class_name not in visible_classes:
                continue
            resized_mask = cv2.resize(mask.cpu().numpy().astype(np.uint8) * 255, (original_width, original_height))
            contours, _ = cv2.findContours(resized_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) > 100:
                    epsilon = 0.01 * cv2.arcLength(cnt, True)
                    smoothed_cnt = cv2.approxPolyDP(cnt, epsilon, True)
                    all_contours.append((smoothed_cnt, class_name))

# Initial load
update_contours(current_conf)

# ===============================
# MAIN LOOP
# ===============================
while True:
    slider_conf = cv2.getTrackbarPos("Confidence", window_name) / 100.0
    if abs(slider_conf - last_slider_conf) > 1e-5:
        current_conf = slider_conf
        update_contours(current_conf)
        last_slider_conf = slider_conf

    overlay_img = original_img.copy()
    mask_img = np.zeros((original_height, original_width), dtype=np.uint8)

    for idx, (cnt, class_name) in enumerate(all_contours):
        color = class_colors.get(class_name, (255, 255, 255))
        if class_name.lower() == "trim":
            cv2.drawContours(overlay_img, [cnt], -1, color, thickness=cv2.FILLED)
            cv2.drawContours(mask_img, [cnt], -1, 255, thickness=cv2.FILLED)
        elif class_name.lower() == "window":
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)
            area_ratio = cv2.contourArea(cnt) / float(w * h)
            if 0.6 < aspect_ratio < 1.8 and area_ratio > 0.6:
                rect = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]])
                cv2.polylines(overlay_img, [rect], True, color, 2)
                cv2.polylines(mask_img, [rect], True, 255, 3)
                continue
            cv2.polylines(overlay_img, [cnt], True, color, 2)
            cv2.polylines(mask_img, [cnt], True, 255, 3)
        else:
            cv2.polylines(overlay_img, [cnt], True, color, 2)
            x, y = cnt[0][0]
            cv2.putText(overlay_img, class_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.polylines(mask_img, [cnt], True, 255, 3)

        for pt_idx, pt in enumerate(cnt):
            px, py = pt[0]
            if idx == selected_contour_idx and pt_idx == selected_point_idx:
                cv2.circle(overlay_img, (px, py), 6, (0, 0, 255), -1)  # red for selected point
            else:
                cv2.circle(overlay_img, (px, py), 5, (0, 255, 255), -1)

    preview = cv2.hconcat([overlay_img, cv2.cvtColor(mask_img, cv2.COLOR_GRAY2BGR)])
    preview_small = cv2.resize(preview, (0, 0), fx=0.5, fy=0.5)
    cv2.imshow(window_name, preview_small)

    key = cv2.waitKey(50)

    if key == ord("s"):
        cv2.imwrite("mask_dynamic_final.png", mask_img)
        cv2.imwrite("overlay_dynamic_final.png", overlay_img)
        print("✅ Saved mask and overlay.")
    elif key == 27:
        break
    elif key != -1:
        char_pressed = chr(key).lower()
        toggle = [cls for cls in class_names if cls.lower().startswith(char_pressed)]
        if toggle:
            cls = toggle[0]
            if cls in visible_classes:
                visible_classes.remove(cls)
                print(f"👁️ Hiding: {cls}")
            else:
                visible_classes.add(cls)
                print(f"👁️ Showing: {cls}")
            update_contours(current_conf)
    elif key == ord("z") and undo_stack:
        all_contours = undo_stack.pop()
        print("↩️ Undo last action")
    elif key == ord("d"):
        if selected_contour_idx >= 0 and selected_point_idx >= 0:
            cnt, class_name = all_contours[selected_contour_idx]
            if len(cnt) > 3:
                undo_stack.append(list(all_contours))
                cnt = np.delete(cnt, selected_point_idx, axis=0)
                all_contours[selected_contour_idx] = (cnt, class_name)
                print("❌ Deleted point from contour")
            selected_point_idx = -1
            selected_contour_idx = -1


cv2.destroyAllWindows()
