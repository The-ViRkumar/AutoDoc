"""OCR-assisted step text, translation, and Markdown/PDF-HTML/
Interactive-HTML export. Ported from studio.py's process_exports(),
split into small testable functions and with real logging instead of
bare `except Exception: pass` swallowing every failure silently.
"""
import logging
import os
from dataclasses import dataclass, field

import markdown as md
import pytesseract
from PIL import Image

from .redaction import blur_region, contains_sensitive
from ..theme import PRIMARY
from ..version import AUTHOR_NAME, AUTHOR_URL

logger = logging.getLogger("autodoc.exporter")

LANGUAGE_CODES = {"Hindi": "hi", "Gujarati": "gu"}


@dataclass
class ExportOptions:
    tesseract_path: str | None
    client_facing: bool = False
    redact_sensitive: bool = False
    languages: set = field(default_factory=set)  # subset of {"hi", "gu"}
    want_markdown: bool = True
    want_pdf: bool = True
    want_html: bool = True


def _ocr_scan(step, tesseract_path: str | None, redact_sensitive: bool) -> tuple[str | None, bool]:
    """OCRs the region around the click. Returns (clean_text_or_None,
    was_redacted). Side effect: blurs that region in the saved
    screenshot if redact_sensitive is on and the text looks sensitive."""
    if not tesseract_path:
        return None, False
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    try:
        img = Image.open(step.path)
        x, y = step.x, step.y
        box = (max(0, x - 150), max(0, y - 50), min(img.width, x + 150), min(img.height, y + 50))
        text = pytesseract.image_to_string(img.crop(box)).strip()
    except Exception:
        logger.exception("OCR failed for %s", step.path)
        return None, False

    if not text:
        return None, False

    if redact_sensitive and contains_sensitive(text):
        try:
            blur_region(step.path, box)
        except Exception:
            logger.exception("Failed to blur sensitive region for %s", step.path)
        return None, True

    return " ".join(text.split()[:5]), False


def _step_caption(step, options: ExportOptions) -> str:
    ocr_text, was_redacted = _ocr_scan(step, options.tesseract_path, options.redact_sensitive)
    if was_redacted:
        return "\U0001f512 **Sensitive content redacted**"

    override = (getattr(step, "caption_override", "") or "").strip()
    if override:
        return override

    window_title = getattr(step, "window_title", "") or ""
    if window_title:
        caption_source, result = window_title, f"Action in: **{window_title}**"
    elif ocr_text:
        caption_source, result = ocr_text, f"Action on: **{ocr_text}**"
    else:
        caption_source, result = "", "Clicked here"

    if options.client_facing and caption_source and any(w in caption_source.lower() for w in ("admin", "settings", "config")):
        result = "⚠️ **WARNING: Do not modify system settings here.**\n\n" + result
    return result


def build_step_content(steps: list, options: ExportOptions) -> list[dict]:
    content = []
    for index, step in enumerate(steps):
        text = _step_caption(step, options)
        if step.keys:
            text += f"\n*Keyboard Input:* `{step.keys}`"
        content.append({"num": index + 1, "text_en": text, "img": step.file, "time": step.time})
    return content


def translate_steps(steps_content: list[dict], languages: set) -> None:
    """Mutates each step dict in-place, adding text_hi/text_gu keys.
    Any translation failure is logged and just leaves those keys absent
    (Markdown/HTML builders already treat them as optional)."""
    if not languages:
        return
    try:
        from deep_translator import GoogleTranslator
    except Exception:
        logger.exception("deep_translator unavailable, skipping translation")
        return

    translators = {}
    for code in languages:
        try:
            translators[code] = GoogleTranslator(source="en", target=code)
        except Exception:
            logger.exception("Could not init translator for %s", code)

    for step in steps_content:
        plain = step["text_en"].replace("**", "")
        for code, translator in translators.items():
            key = f"text_{code}"
            try:
                step[key] = translator.translate(plain)
            except Exception:
                logger.exception("Translation to %s failed for step %s", code, step["num"])


def build_markdown(project_name: str, steps_content: list[dict]) -> str:
    lines = [f"# {project_name} Deployment Guide\n"]
    for s in steps_content:
        lines.append(f"### Step {s['num']}\n{s['text_en']}")
        if "text_hi" in s:
            lines.append(f"*(Hindi): {s['text_hi']}*")
        if "text_gu" in s:
            lines.append(f"*(Gujarati): {s['text_gu']}*")
        lines.append(f"\n![Step {s['num']}]({s['img']})\n---\n")
    lines.append(f"\n*Generated with AutoDoc — made by [{AUTHOR_NAME}]({AUTHOR_URL})*\n")
    return "\n".join(lines)


def build_pdf_html(md_text: str) -> str:
    html_content = md.markdown(md_text)
    return f"""<html><head>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #333; }}
    img {{ max-width: 100%; border: 1px solid #ccc; border-radius: 5px; margin: 10px 0; }}
    h1 {{ color: {PRIMARY}; border-bottom: 2px solid {PRIMARY}; padding-bottom: 10px; }}
    h3 {{ color: #003049; }}
    @media print {{ button {{ display: none; }} }}
</style>
</head><body>
<button onclick="window.print()" style="padding: 15px; background: {PRIMARY}; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-bottom: 20px;">🖨️ Click Here to Save as PDF</button>
{html_content}
</body></html>"""


def build_interactive_html(steps_content: list[dict]) -> str:
    html_steps = ""
    for s in steps_content:
        extra_langs = ""
        if "text_hi" in s:
            extra_langs += f"<br><small style='color: #666;'>{s['text_hi']}</small>"
        if "text_gu" in s:
            extra_langs += f"<br><small style='color: #666;'>{s['text_gu']}</small>"
        html_steps += f"""
        <div class="step-card" onclick="jumpTo({s['time']})" id="step-{s['num']}">
            <h4>Step {s['num']}</h4>
            <p>{s['text_en']}{extra_langs}</p>
            <img src="{s['img']}" />
        </div>
        """

    return f"""<!DOCTYPE html>
<html><head><title>Interactive Setup Guide</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #0F1117; color: #ECEDF5; }}
    .video-pane {{ flex: 6; display: flex; align-items: center; justify-content: center; background: #000; padding: 20px; }}
    video {{ width: 100%; max-height: 90vh; border-radius: 8px; border: 2px solid {PRIMARY}; }}
    .steps-pane {{ flex: 4; overflow-y: auto; padding: 20px; background: #1B1E2B; }}
    .step-card {{ background: #232739; padding: 15px; margin-bottom: 15px; border-radius: 8px; cursor: pointer; transition: 0.3s; border-left: 4px solid transparent; }}
    .step-card:hover {{ background: #2B2F42; }}
    .step-card.active {{ border-left: 4px solid {PRIMARY}; background: #262244; }}
    .step-card img {{ width: 100%; margin-top: 10px; border-radius: 4px; display: none; }}
    .step-card.active img {{ display: block; }}
    h2 {{ color: {PRIMARY}; }}
</style>
</head><body>
    <div class="video-pane">
        <video id="guideVideo" controls><source src="recording.mp4" type="video/mp4"></video>
    </div>
    <div class="steps-pane">
        <h2>Interactive Guide</h2>
        <p>Click any step to jump to that moment in the video.</p>
        {html_steps}
        <p style="opacity:0.5;font-size:11px;margin-top:20px;">Generated with AutoDoc &mdash; made by <a href="{AUTHOR_URL}" style="color:{PRIMARY};">{AUTHOR_NAME}</a></p>
    </div>
    <script>
        const vid = document.getElementById("guideVideo");
        function jumpTo(time) {{ vid.currentTime = time; vid.play(); }}
    </script>
</body></html>"""


def run_export(project_dir: str, project_name: str, steps: list, options: ExportOptions) -> list[dict]:
    """Orchestrates OCR -> translate -> write files. Returns the built
    steps_content (useful for tests/inspection)."""
    steps_content = build_step_content(steps, options)
    translate_steps(steps_content, options.languages)

    if options.want_markdown or options.want_pdf:
        md_text = build_markdown(project_name, steps_content)
        if options.want_markdown:
            with open(os.path.join(project_dir, "guide.md"), "w", encoding="utf-8") as f:
                f.write(md_text)
        if options.want_pdf:
            with open(os.path.join(project_dir, "Export_to_PDF.html"), "w", encoding="utf-8") as f:
                f.write(build_pdf_html(md_text))

    if options.want_html:
        with open(os.path.join(project_dir, "Interactive_Wizard.html"), "w", encoding="utf-8") as f:
            f.write(build_interactive_html(steps_content))

    return steps_content


def demo():
    """Minimal self-check: no tesseract/translation, just verifies the
    Markdown/HTML shape stays correct. Run: python -m autodoc.core.exporter"""

    class FakeStep:
        def __init__(self, num, window_title="", caption_override=""):
            self.file = f"step_{num:03d}.png"
            self.path = self.file
            self.x, self.y = 10, 10
            self.keys = "hello"
            self.time = float(num)
            self.window_title = window_title
            self.caption_override = caption_override

    steps = [FakeStep(1), FakeStep(2)]
    options = ExportOptions(tesseract_path=None)
    content = build_step_content(steps, options)
    assert len(content) == 2
    assert content[0]["text_en"].startswith("Clicked here")
    assert "Keyboard Input" in content[0]["text_en"]

    # window title takes priority over the OCR "Clicked here" default,
    # and the client-facing admin/settings warning checks it too
    titled_step = FakeStep(3, window_title="Settings")
    caption = _step_caption(titled_step, ExportOptions(tesseract_path=None, client_facing=True))
    assert "Action in: **Settings**" in caption
    assert "WARNING" in caption

    # an explicit review-grid override beats both window title and OCR
    overridden_step = FakeStep(4, window_title="Settings", caption_override="Click the gear icon")
    caption = _step_caption(overridden_step, ExportOptions(tesseract_path=None))
    assert caption == "Click the gear icon"

    md_text = build_markdown("Demo Project", content)
    assert "# Demo Project Deployment Guide" in md_text
    assert "![Step 1](step_001.png)" in md_text
    assert AUTHOR_URL in md_text

    html = build_interactive_html(content)
    assert "step-2" in html
    assert AUTHOR_URL in html
    print("exporter self-check OK")


if __name__ == "__main__":
    demo()
