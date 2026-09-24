"""Manual post-recording annotation pass (blur/highlight boxes) over the
captured step screenshots, via OpenCV's own window/mouse-callback UI.

Rewritten from studio.py's draw_shape()/run_post_annotation() to keep
per-image drawing state on an instance instead of module-level globals
(the original's annot_img/annot_clone/annot_history/mode/ix/iy were
shared mutable globals -- harmless single-threaded, but a footgun the
moment this is reused or called twice in the same process).
"""
import logging
import os

import cv2

logger = logging.getLogger("autodoc.annotator")

INSTRUCTIONS = (
    "Left-Click Drag: Red Box\n"
    "Right-Click Drag: Blur\n"
    "'z': Undo\n"
    "'s': Save & Next\n"
    "'x': Discard Step\n"
    "'q': Skip Annotating Image"
)


class _ImageAnnotator:
    """One-shot annotator bound to a single image; not reused across images."""

    def __init__(self, image):
        self.image = image.copy()
        self.clone = image.copy()
        self.history = [image.copy()]
        self.drawing = False
        self.mode = "highlight"
        self.ix, self.iy = -1, -1

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
            self.mode = "highlight"
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
            self.mode = "blur"
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.image = self.clone.copy()
                if self.mode == "highlight":
                    cv2.rectangle(self.image, (self.ix, self.iy), (x, y), (0, 0, 255), 2)
                else:
                    cv2.rectangle(self.image, (self.ix, self.iy), (x, y), (180, 180, 180), 1)
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                cv2.rectangle(self.clone, (self.ix, self.iy), (x, y), (0, 0, 255), 3)
                self.image = self.clone.copy()
                self.history.append(self.clone.copy())
        elif event == cv2.EVENT_RBUTTONUP:
            if self.drawing:
                self.drawing = False
                y1, y2 = min(self.iy, y), max(self.iy, y)
                x1, x2 = min(self.ix, x), max(self.ix, x)
                if y2 > y1 and x2 > x1:
                    roi = self.clone[y1:y2, x1:x2]
                    roi = cv2.GaussianBlur(roi, (51, 51), 0)
                    self.clone[y1:y2, x1:x2] = roi
                self.image = self.clone.copy()
                self.history.append(self.clone.copy())

    def undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.clone = self.history[-1].copy()
            self.image = self.clone.copy()


def annotate_steps(steps: list, show_instructions: callable = None) -> list:
    """Runs the interactive OpenCV annotation loop over each step's
    screenshot. Returns the subset of steps the user kept (didn't
    discard with 'x'). `show_instructions`, if given, is called once
    before the loop starts (e.g. to show a UI toast/messagebox)."""
    if show_instructions:
        show_instructions(INSTRUCTIONS)

    kept = []
    for step in steps:
        filepath = step.path
        image = cv2.imread(filepath)
        if image is None:
            logger.warning("Could not load %s for annotation, keeping as-is", filepath)
            kept.append(step)
            continue

        annotator = _ImageAnnotator(image)
        h, w = image.shape[:2]
        scale = min(1280 / w, 720 / h)
        view_w, view_h = (int(w * scale), int(h * scale)) if scale < 1 else (w, h)

        cv2.namedWindow(step.file, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(step.file, view_w, view_h)
        cv2.setMouseCallback(step.file, annotator.on_mouse)

        while True:
            cv2.imshow(step.file, annotator.image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("s"):
                cv2.imwrite(filepath, annotator.clone)
                kept.append(step)
                break
            if key == ord("x"):
                if os.path.exists(filepath):
                    os.remove(filepath)
                break
            if key == ord("q"):
                kept.append(step)
                break
            if key == ord("z"):
                annotator.undo()
        cv2.destroyAllWindows()

    return kept
