import cv2
import numpy as np
from ultralytics import YOLO
from vision_module.edit_utils import edit_mask_interactively

model = YOLO("vision_module/best.pt")  # Update path if needed

def run_yolo(image, conf=0.6, visible_classes=None):
    all_contours = []
    height, width = image.shape[:2]
    mask_img = np.zeros((height, width), dtype=np.uint8)

    results = model.predict(source=image, conf=conf, verbose=False, task='segment')

    if results[0].masks is not None:
        for i, mask in enumerate(results[0].masks.data):
            class_id = int(results[0].boxes.data[i][5])
            class_name = results[0].names[class_id]

            if visible_classes and class_name not in visible_classes:
                continue

            resized_mask = cv2.resize(mask.cpu().numpy().astype(np.uint8) * 255, (width, height))
            contours, _ = cv2.findContours(resized_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if cv2.contourArea(cnt) < 100:
                    continue

                epsilon = 0.005 * cv2.arcLength(cnt, True)

                # --- WINDOWS: Replace with perfect rectangle if shape fits ---
                if class_name.lower() == "window":
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = w / float(h)
                    area_ratio = cv2.contourArea(cnt) / float(w * h)

                    if 0.4 < aspect_ratio < 2.5 and area_ratio > 0.5:
                        rect = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]])
                        all_contours.append((rect, class_name))
                        cv2.drawContours(mask_img, [rect], -1, 255, cv2.FILLED)
                        continue

                # --- TRIM: Outline only, no filled mask ---
                elif class_name.lower() == "trim":
                    smoothed = cv2.approxPolyDP(cnt, epsilon, False)
                    all_contours.append((smoothed, class_name))
                    continue  # Don't draw on mask

                # --- ROOF / DOOR / OTHER: Draw filled shape ---
                smoothed = cv2.approxPolyDP(cnt, epsilon, True)
                all_contours.append((smoothed, class_name))
                if class_name.lower() in ["roof", "door"]:
                    cv2.drawContours(mask_img, [smoothed], -1, 255, cv2.FILLED)

    # Save the mask for interactive editing
    cv2.imwrite("mask_dynamic.png", mask_img)
    edit_mask_interactively("mask_dynamic.png", "mask_edited.png")

    return all_contours, results[0].names.values()
