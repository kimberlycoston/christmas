# vision_module/ui_utils.py
import cv2
import numpy as np
import colorsys
from ultralytics import YOLO
import subprocess

model = YOLO("vision_module/best.pt")

# === GLOBAL STATE ===
visible_classes = set()
selected_contour_idx = -1
selected_point_idx = -1
is_dragging = False
undo_stack = []

def generate_class_colors(class_names):
    hsv = [(i / len(class_names), 0.7, 1.0) for i in range(len(class_names))]
    rgb = [tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*h)) for h in hsv]
    return {cls: color for cls, color in zip(class_names, rgb)}

def mouse_callback(event, x, y, flags, param):
    global selected_contour_idx, selected_point_idx, is_dragging
    all_contours, scale = param
    x, y = int(x * scale), int(y * scale)

    if event == cv2.EVENT_LBUTTONDOWN:
        for idx, (cnt, _) in enumerate(all_contours):
            for pt_idx, pt in enumerate(cnt):
                px, py = pt[0]
                if abs(px - x) < 10 and abs(py - y) < 10:
                    selected_contour_idx = idx
                    selected_point_idx = pt_idx
                    is_dragging = True
                    return

        for idx, (cnt, class_name) in enumerate(all_contours):
            if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                undo_stack.append(all_contours.copy())
                print(f"🗑️ Deleted: {class_name}")
                all_contours.pop(idx)
                return

    elif event == cv2.EVENT_LBUTTONUP:
        is_dragging = False

    elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
        if 0 <= selected_contour_idx < len(all_contours):
            cnt, class_name = all_contours[selected_contour_idx]
            cnt[selected_point_idx][0] = [x, y]

def launch_editor(image, initial_conf=0.6):
    # Launch on-screen keyboard
    keyboard_proc = subprocess.Popen(["matchbox-keyboard"])
    global visible_classes, selected_contour_idx, selected_point_idx, is_dragging
    height, width = image.shape[:2]
    window_name = "Preview"
    scale = 0.5

    cv2.namedWindow(window_name)
    cv2.createTrackbar("Confidence", window_name, int(initial_conf * 100), 100, lambda x: None)


    def get_yolo_contours(conf):
        results = model.predict(source=image, conf=conf, verbose=False, task='segment')
        contours = []
        mask_img = np.zeros((height, width), dtype=np.uint8)
        names = list(results[0].names.values())

        if results[0].masks is not None:
            for i, mask in enumerate(results[0].masks.data):
                class_id = int(results[0].boxes.data[i][5])
                class_name = results[0].names[class_id]
                resized_mask = cv2.resize(mask.cpu().numpy().astype(np.uint8) * 255, (width, height))
                cnts, _ = cv2.findContours(resized_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in cnts:
                    if cv2.contourArea(cnt) < 100:
                        continue
                    epsilon = 0.005 * cv2.arcLength(cnt, True)
                    if class_name.lower() == "window":
                        x, y, w, h = cv2.boundingRect(cnt)
                        ar = w / float(h)
                        fill = cv2.contourArea(cnt) / float(w * h)
                        if 0.4 < ar < 2.5 and fill > 0.5:
                            rect = np.array([[[x, y]], [[x+w, y]], [[x+w, y+h]], [[x, y+h]]])
                            contours.append((rect, class_name))
                            continue
                    elif class_name.lower() == "trim":
                        smooth = cv2.approxPolyDP(cnt, epsilon, False)
                        contours.append((smooth, class_name))
                        continue
                    smooth = cv2.approxPolyDP(cnt, epsilon, True)
                    contours.append((smooth, class_name))
        return contours, names

    contours, class_names = get_yolo_contours(initial_conf)
    visible_classes = set(class_names)
    class_colors = generate_class_colors(class_names)
    cv2.setMouseCallback(window_name, mouse_callback, param=(contours, scale))

    last_conf = initial_conf

    while True:
        conf_slider = cv2.getTrackbarPos("Confidence", window_name) / 100.0
        if abs(conf_slider - last_conf) > 0.001:
            print(f"🔁 Rerunning YOLO at confidence {conf_slider:.2f}")
            new_contours, _ = get_yolo_contours(conf_slider)
            contours[:] = new_contours  # ✅ in-place update
            selected_contour_idx = -1
            selected_point_idx = -1
            is_dragging = False
            last_conf = conf_slider

        overlay = image.copy()
        mask = np.zeros((height, width), dtype=np.uint8)

        for idx, (cnt, class_name) in enumerate(contours):
            if class_name not in visible_classes:
                continue
            color = class_colors.get(class_name, (255, 255, 255))
            cv2.polylines(overlay, [cnt], True, color, 2)
            cv2.polylines(mask, [cnt], True, 255, 3)
            for pt_idx, pt in enumerate(cnt):
                px, py = pt[0]
                if idx == selected_contour_idx and pt_idx == selected_point_idx:
                    cv2.circle(overlay, (px, py), 6, (0, 0, 255), -1)
                else:
                    cv2.circle(overlay, (px, py), 5, (0, 255, 255), -1)
            x, y = cnt[0][0]
            cv2.putText(overlay, class_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        preview = cv2.hconcat([overlay, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)])
        preview_small = cv2.resize(preview, (0, 0), fx=scale, fy=scale)
        cv2.imshow(window_name, preview_small)
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break

        key = cv2.waitKey(50)
        if key == ord("s"):
            cv2.imwrite("mask_dynamic.png", mask)
            cv2.imwrite("overlay_dynamic_final.png", overlay)
            print("✅ Saved mask and overlay.")
        elif key == 27:
            break
        elif key == ord("z") and undo_stack:
            contours[:] = undo_stack.pop()
            print("↩️ Undo last action")
        elif key == ord("d"):
            if selected_contour_idx >= 0 and selected_point_idx >= 0:
                cnt, class_name = contours[selected_contour_idx]
                if len(cnt) > 3:
                    undo_stack.append(contours.copy())
                    cnt = np.delete(cnt, selected_point_idx, axis=0)
                    contours[selected_contour_idx] = (cnt, class_name)
                    print("❌ Deleted point from contour")
                selected_point_idx = -1
                selected_contour_idx = -1
        elif key != -1:
            char = chr(key).lower()
            toggle = [cls for cls in class_names if cls.lower().startswith(char)]
            if toggle:
                cls = toggle[0]
                if cls in visible_classes:
                    visible_classes.remove(cls)
                    print(f"👁️ Hiding: {cls}")
                else:
                    visible_classes.add(cls)
                    print(f"👁️ Showing: {cls}")

    # Close the keyboard after editing
    if keyboard_proc.poll() is None:  # Still running
        keyboard_proc.terminate()

    cv2.destroyAllWindows()
