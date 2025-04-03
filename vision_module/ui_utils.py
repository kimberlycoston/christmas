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
        cv2.imwrite("mask_dynamic.png", mask)  # required by edit_utils
        cv2.imwrite("overlay_dynamic_final.png", overlay)
        print("✅ Saved mask and overlay.")
    cv2.destroyAllWindows()

def interactive_contour_editor(image, contours, class_names):
    class_colors = generate_class_colors(class_names)
    height, width = image.shape[:2]
    window_name = "Edit Contours"

    visible_classes = set(class_names)
    selected_contour_idx = -1
    selected_point_idx = -1
    is_dragging = False
    undo_stack = []
    mouse_x, mouse_y = -1, -1

    def update_overlay():
        overlay = image.copy()
        for idx, (cnt, class_name) in enumerate(contours):
            if class_name not in visible_classes:
                continue
            color = class_colors.get(class_name, (255, 255, 255))
            cv2.polylines(overlay, [cnt], True, color, 2)
            x, y = cnt[0][0]
            cv2.putText(overlay, class_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            for pt_idx, pt in enumerate(cnt):
                px, py = pt[0]
                if idx == selected_contour_idx and pt_idx == selected_point_idx:
                    cv2.circle(overlay, (px, py), 6, (0, 0, 255), -1)  # red selected
                else:
                    cv2.circle(overlay, (px, py), 5, (0, 255, 255), -1)  # yellow

        return overlay

    def mouse_callback(event, x, y, flags, param):
        nonlocal selected_contour_idx, selected_point_idx, is_dragging, mouse_x, mouse_y
        mouse_x, mouse_y = x, y

        if event == cv2.EVENT_LBUTTONDOWN:
            for idx, (cnt, _) in enumerate(contours):
                for pt_idx, pt in enumerate(cnt):
                    px, py = pt[0]
                    if abs(px - x) < 10 and abs(py - y) < 10:
                        selected_contour_idx = idx
                        selected_point_idx = pt_idx
                        is_dragging = True
                        return
            for idx, (cnt, class_name) in enumerate(contours):
                if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                    undo_stack.append(list(contours))
                    contours.pop(idx)
                    print(f"🗑️ Deleted: {class_name}")
                    return

        elif event == cv2.EVENT_LBUTTONUP:
            is_dragging = False

        elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
            if 0 <= selected_contour_idx < len(contours):
                cnt, class_name = contours[selected_contour_idx]
                cnt[selected_point_idx][0] = [x, y]

    # Init window and bindings
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("🖱️ Drag to move points | Press 's' to save | 'z' to undo | 'd' to delete pt | Type a letter to hide/show class")

    while True:
        preview = update_overlay()
        cv2.imshow(window_name, preview)
        key = cv2.waitKey(50)

        if key == 27:  # ESC
            break
        elif key == ord("s"):
            mask = np.zeros((height, width), dtype=np.uint8)
            for cnt, _ in contours:
                cv2.drawContours(mask, [cnt], -1, 255, thickness=2)
            cv2.imwrite("mask_dynamic.png", mask)
            cv2.imwrite("overlay_dynamic_final.png", preview)
            print("✅ Saved mask and overlay.")
        elif key == ord("z") and undo_stack:
            contours[:] = undo_stack.pop()
            print("↩️ Undo last")
        elif key == ord("d"):
            if selected_contour_idx >= 0 and selected_point_idx >= 0:
                cnt, class_name = contours[selected_contour_idx]
                if len(cnt) > 3:
                    undo_stack.append(list(contours))
                    cnt = np.delete(cnt, selected_point_idx, axis=0)
                    contours[selected_contour_idx] = (cnt, class_name)
                    print("❌ Deleted point")
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

    cv2.destroyAllWindows()
