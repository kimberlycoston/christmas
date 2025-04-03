# vision_module/yolo_utils.py

import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO("vision_module/best.pt")  # Make sure the weights file is here!

def run_yolo(image, conf=0.6, visible_classes=None):
    """
    Runs YOLO segmentation on the image and returns contours + class names
    """
    all_contours = []
    height, width = image.shape[:2]
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
                if cv2.contourArea(cnt) > 100:
                    epsilon = 0.01 * cv2.arcLength(cnt, True)
                    smoothed = cv2.approxPolyDP(cnt, epsilon, True)
                    all_contours.append((smoothed, class_name))

    return all_contours, results[0].names
