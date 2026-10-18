"""Generic video-to-screenshots frame sampler (Video Extractor tab)."""
import os

import cv2


def extract_frames(video_path: str, output_folder: str, interval_seconds: float, on_progress: callable = None) -> int:
    """Saves one frame every `interval_seconds` from `video_path` into
    `output_folder`. Returns the number of frames saved.

    `on_progress(current_frame, total_frames)`, if given, is called
    after every source frame is read -- total_frames is 0 when the
    container doesn't report a frame count, callers should treat that
    as "unknown" rather than divide by it."""
    cap = cv2.VideoCapture(video_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 1.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        frame_interval = max(1, int(fps * interval_seconds))
        count, saved_count = 0, 0

        while True:
            success, image = cap.read()
            if not success:
                break
            if count % frame_interval == 0:
                cv2.imwrite(os.path.join(output_folder, f"extracted_{saved_count:03d}.png"), image)
                saved_count += 1
            count += 1
            if on_progress:
                on_progress(count, total_frames)
        return saved_count
    finally:
        cap.release()
