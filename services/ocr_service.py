"""OCR service.

Two clearly separated layers:

1. PURE text functions (no Tesseract, no Flask, no filesystem) that parse
   fields out of already-extracted text and mask sensitive ID numbers.
   These are fully unit-testable and run everywhere.

2. The Tesseract pipeline (load image/PDF -> preprocess -> OCR) which needs
   Pillow + pytesseract installed. It is imported lazily so the pure
   functions keep working even when those libraries are absent.
"""
import re

# --------------------------------------------------------------------------
#  Pure text parsing  (safe to import anywhere)
# --------------------------------------------------------------------------

# Regexes for Indian ID formats
# Groups are separated by an optional single space (never a newline), so a
# 4-digit year on the preceding line cannot be mis-joined into the number.
AADHAAR_RE = re.compile(r"\b(\d{4}) ?(\d{4}) ?(\d{4})\b")
PAN_RE = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b")
VOTER_RE = re.compile(r"\b([A-Z]{3}[0-9]{7})\b")
DOB_RE = re.compile(
    r"\b(\d{2}[/\-.]\d{2}[/\-.]\d{4})\b"
)


def mask_aadhaar(text):
    """Replace any 12-digit Aadhaar number with XXXX XXXX 1234 form."""
    def repl(m):
        return "XXXX XXXX " + m.group(3)
    return AADHAAR_RE.sub(repl, text)


def mask_pan(text):
    """Mask a PAN, keeping only the last 2 characters."""
    def repl(m):
        pan = m.group(1)
        return "XXXXX" + pan[5:8] + "X" + pan[-1]
    return PAN_RE.sub(repl, text)


def mask_voter_id(text):
    def repl(m):
        vid = m.group(1)
        return vid[:3] + "XXXXX" + vid[-2:]
    return VOTER_RE.sub(repl, text)


def mask_sensitive(text):
    """Apply all masks. Used before any extracted text is stored/displayed."""
    if not text:
        return text
    text = mask_aadhaar(text)
    text = mask_pan(text)
    text = mask_voter_id(text)
    return text


def extract_id_number(text):
    """Return a *masked* ID number if one is found, else None."""
    if not text:
        return None
    m = AADHAAR_RE.search(text)
    if m:
        return "XXXX XXXX " + m.group(3)
    m = PAN_RE.search(text)
    if m:
        pan = m.group(1)
        return "XXXXX" + pan[5:8] + "X" + pan[-1]
    m = VOTER_RE.search(text)
    if m:
        vid = m.group(1)
        return vid[:3] + "XXXXX" + vid[-2:]
    return None


def extract_dob(text):
    """Find the first plausible date of birth (dd/mm/yyyy etc.)."""
    if not text:
        return None
    m = DOB_RE.search(text)
    return m.group(1) if m else None


_NAME_LABELS = ("name", "naam")
_SKIP_LINE = ("government", "india", "unique", "authority", "male",
              "female", "dob", "date of birth", "year of birth",
              "father", "address", "income", "tax", "department")


def extract_name(text):
    """Best-effort name extraction from OCR text.

    Strategy: first look for a line that begins with a 'Name' label; else
    pick the first clean title-case line that is not a known header word.
    """
    if not text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # 1) explicit "Name: ..." label
    for ln in lines:
        low = ln.lower()
        for label in _NAME_LABELS:
            if low.startswith(label):
                after = ln.split(":", 1)[-1] if ":" in ln else ln[len(label):]
                after = after.strip(" :-")
                if after and not any(c.isdigit() for c in after):
                    return after.title()

    # 2) first clean alphabetic line
    for ln in lines:
        low = ln.lower()
        if any(skip in low for skip in _SKIP_LINE):
            continue
        letters = ln.replace(" ", "")
        if letters.isalpha() and 2 < len(ln) <= 40 and len(ln.split()) <= 4:
            return ln.title()
    return None


def extract_address(text):
    """Return the text following an 'Address' label, up to a few lines."""
    if not text:
        return None
    lines = [ln.strip() for ln in text.splitlines()]
    collecting = False
    chunk = []
    for ln in lines:
        low = ln.lower()
        if not collecting and low.startswith("address"):
            collecting = True
            rest = ln.split(":", 1)[-1].strip()
            if rest and rest.lower() != "address":
                chunk.append(rest)
            continue
        if collecting:
            if not ln:
                break
            chunk.append(ln)
            if len(chunk) >= 4:
                break
    return ", ".join(chunk) if chunk else None


def parse_fields(text):
    """Convenience: parse all fields from raw OCR text and mask the text."""
    return {
        "extracted_name": extract_name(text),
        "extracted_dob": extract_dob(text),
        "extracted_address": extract_address(text),
        "extracted_number": extract_id_number(text),
        "masked_text": mask_sensitive(text),
    }


# --------------------------------------------------------------------------
#  Tesseract pipeline  (imported lazily)
# --------------------------------------------------------------------------
def _load_image(path):
    from PIL import Image, ImageOps, ImageFilter
    img = Image.open(path)
    img = img.convert("L")                 # grayscale
    img = ImageOps.autocontrast(img)       # stretch contrast
    img = img.filter(ImageFilter.MedianFilter(size=3))   # denoise
    # simple binary threshold
    img = img.point(lambda p: 255 if p > 140 else 0)
    return img


def run_ocr(path):
    """Run OCR on an image or single-page PDF. Returns (text, confidence).

    Requires pytesseract + Tesseract. Raises RuntimeError with a friendly
    message if the engine is unavailable, so routes can show a clean flash.
    """
    try:
        import pytesseract
        from config import Config
        if Config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
    except ImportError as exc:        # pragma: no cover - env dependent
        raise RuntimeError(
            "OCR engine not available. Install pytesseract and Tesseract-OCR."
        ) from exc

    lower = path.lower()
    try:
        if lower.endswith(".pdf"):
            text = _ocr_pdf(path, pytesseract)
        else:
            img = _load_image(path)
            text = pytesseract.image_to_string(img)
        conf = _mean_confidence(path, pytesseract)
        return text, conf
    except Exception as exc:          # pragma: no cover - env dependent
        raise RuntimeError(f"OCR failed: {exc}") from exc


def _ocr_pdf(path, pytesseract):      # pragma: no cover - env dependent
    """Render the first PDF page to an image, then OCR it."""
    from PIL import Image
    try:
        import fitz  # PyMuPDF, optional
        doc = fitz.open(path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=200)
        import io
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img.convert("L"))
    except ImportError:
        # Fallback: let Pillow try (works for image-based PDFs it can open)
        img = _load_image(path)
        return pytesseract.image_to_string(img)


def _mean_confidence(path, pytesseract):   # pragma: no cover - env dependent
    try:
        if path.lower().endswith(".pdf"):
            return None
        img = _load_image(path)
        data = pytesseract.image_to_data(
            img, output_type=pytesseract.Output.DICT
        )
        vals = [int(c) for c in data.get("conf", []) if c not in ("-1", -1, "")]
        if not vals:
            return None
        return round(sum(vals) / len(vals), 1)
    except Exception:
        return None
