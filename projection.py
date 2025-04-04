import cv2
import numpy as np
from PIL import Image, ImageSequence


def play_animated_projection(mask_path="mask_dynamic.png", gif_path="gifs/colors.gif"):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print("❌ Error: Could not load mask.")
        return
    # h, w = mask.shape[:2]
    w, h = 1280, 768
    mask = cv2.resize(mask, (w, h))


    gif = Image.open(gif_path)
    frames = []
    for frame in ImageSequence.Iterator(gif):
        rgb = frame.convert("RGB").resize((w, h))
        frame_cv = np.array(rgb)[..., ::-1]
        frames.append(frame_cv)

    cv2.namedWindow("Projected Lights", cv2.WND_PROP_FULLSCREEN)
    cv2.moveWindow("Projected Lights", 0, 0)
    cv2.setWindowProperty("Projected Lights", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        for f in frames:
            overlay = cv2.bitwise_and(f, f, mask=mask)
            cv2.imshow("Projected Lights", overlay)
            if cv2.waitKey(100) & 0xFF == 27:  # ESC to quit
                cv2.destroyAllWindows()
                return
        if cv2.waitKey(10) & 0xFF == 27:
            break

    cv2.destroyAllWindows()