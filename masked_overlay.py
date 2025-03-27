import cv2
import numpy as np
from PIL import Image
import os

# ============================
# CONFIGURATION
# ============================
mask_path = "mask_dynamic.png"
gif_path = "colour-colors.gif"
output_video_path = "masked_projection.mp4"
fullscreen_preview = True

# ============================
# LOAD MASK
# ============================
mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
if mask is None:
    raise FileNotFoundError("Could not find mask image!")

height, width = mask.shape

# ============================
# LOAD GIF FRAMES
# ============================
gif = Image.open(gif_path)
frames = []
durations = []

try:
    while True:
        frame = gif.convert("RGB")
        frame_np = np.array(frame)
        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        frame_resized = cv2.resize(frame_bgr, (width, height))
        frames.append(frame_resized)
        durations.append(gif.info.get("duration", 100))
        gif.seek(gif.tell() + 1)
except EOFError:
    pass

print(f"Loaded {len(frames)} frames from the GIF.")

# ============================
# PREPARE VIDEO OUTPUT
# ============================
fps = int(1000 / np.mean(durations))
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video_out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# ============================
# CREATE MASKED ANIMATION
# ============================
mask_3ch = cv2.merge([mask, mask, mask])

for frame in frames:
    masked = cv2.bitwise_and(frame, mask_3ch)
    video_out.write(masked)

    if fullscreen_preview:
        cv2.namedWindow("Projection", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Projection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow("Projection", masked)
        key = cv2.waitKey(int(1000 / fps))
        if key == 27:  # ESC to stop
            break

video_out.release()
cv2.destroyAllWindows()
print(f"✅ Saved masked projection video to {output_video_path}")
