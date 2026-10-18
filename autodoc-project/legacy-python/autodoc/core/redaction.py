"""Opt-in sensitive-text detection + blur. Scans the same OCR text the
exporter already extracts near a click -- if it looks like an email,
an IP, or a password/key/serial value, the caption is replaced with a
redaction notice and that region of the screenshot is blurred.
"""
import re

_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # email
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),  # IPv4
    re.compile(r"(?i)\b(password|passwd|pwd|secret|api[_ -]?key|license[_ -]?key|serial(?:\s*(?:no|number))?)\b\s*[:=]?\s*\S+"),
]


def contains_sensitive(text: str) -> bool:
    return any(p.search(text) for p in _PATTERNS)


def blur_region(image_path: str, box: tuple) -> None:
    """Gaussian-blurs `box` (left, top, right, bottom) in the image at
    image_path and saves it back in place."""
    from PIL import Image, ImageFilter

    img = Image.open(image_path)
    region = img.crop(box).filter(ImageFilter.GaussianBlur(radius=18))
    img.paste(region, box)
    img.save(image_path)


if __name__ == "__main__":
    assert contains_sensitive("contact me at foo@bar.com")
    assert contains_sensitive("server is at 192.168.1.10")
    assert contains_sensitive("password: hunter2")
    assert not contains_sensitive("Save Settings button")
    print("redaction self-check OK")
