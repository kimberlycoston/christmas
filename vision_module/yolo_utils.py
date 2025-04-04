import cv2
import numpy as np
from ultralytics import YOLO
from vision_module.ui_utils import launch_editor 

model = YOLO("vision_module/best.pt")

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

                # === WINDOWS ===
                if class_name.lower() == "window":
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = w / float(h)
                    area_ratio = cv2.contourArea(cnt) / float(w * h)
                    if 0.4 < aspect_ratio < 2.5 and area_ratio > 0.5:
                        rect = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]])
                        all_contours.append((rect, class_name))
                        cv2.drawContours(mask_img, [rect], -1, 255, cv2.FILLED)
                        continue

                # === TRIM ===
                elif class_name.lower() == "trim":
                    epsilon = 0.05 * cv2.arcLength(cnt, True)
                    smoothed = cv2.approxPolyDP(cnt, epsilon, False)
                    all_contours.append((smoothed, class_name))
                    continue

                # === ROOF ===
                elif class_name.lower() == "roof":
                    epsilon = 0.05 * cv2.arcLength(cnt, True)
                    smoothed = cv2.approxPolyDP(cnt, epsilon, True)

                    if len(smoothed) > 2:
                        clean = []
                        for i in range(len(smoothed)):
                            pt1 = smoothed[i][0]
                            pt2 = smoothed[(i + 1) % len(smoothed)][0]
                            if np.linalg.norm(pt1 - pt2) > 10:
                                clean.append([pt1])
                        clean = np.array(clean, dtype=np.int32).reshape(-1, 1, 2)
                        all_contours.append((clean, class_name))
                        cv2.drawContours(mask_img, [clean], -1, 255, cv2.FILLED)
                    continue

                # === DEFAULT: door, other objects ===
                smoothed = cv2.approxPolyDP(cnt, epsilon, True)
                all_contours.append((smoothed, class_name))
                cv2.drawContours(mask_img, [smoothed], -1, 255, cv2.FILLED)

    # Save binary mask (optional use)
    cv2.imwrite("mask_dynamic.png", mask_img)

  
    launch_editor(image, initial_conf=conf)
    
    return all_contours, results[0].names.values()
