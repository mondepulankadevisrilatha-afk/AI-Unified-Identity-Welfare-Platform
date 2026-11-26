"""Pure-text OCR parsing & masking tests (no Tesseract needed)."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services import ocr_service as ocr

SAMPLE = """Government of India
Name: Asha Kumari
DOB: 14/05/2004
1234 5678 9012
Address: 12 Main Road
Chennai 600001
"""


def test_mask_aadhaar():
    masked = ocr.mask_aadhaar("my number is 1234 5678 9012 ok")
    assert "1234 5678" not in masked
    assert "XXXX XXXX 9012" in masked


def test_mask_pan():
    masked = ocr.mask_pan("PAN ABCDE1234F here")
    assert "ABCDE1234F" not in masked
    assert masked.count("X") >= 5


def test_mask_voter_id():
    masked = ocr.mask_voter_id("ABC1234567")
    assert "ABC1234567" not in masked


def test_extract_id_number_is_masked():
    num = ocr.extract_id_number(SAMPLE)
    assert num == "XXXX XXXX 9012"


def test_extract_dob():
    assert ocr.extract_dob(SAMPLE) == "14/05/2004"


def test_extract_name():
    assert ocr.extract_name(SAMPLE) == "Asha Kumari"


def test_extract_address():
    addr = ocr.extract_address(SAMPLE)
    assert addr and "Main Road" in addr


def test_parse_fields_masks_text():
    fields = ocr.parse_fields(SAMPLE)
    assert "1234 5678 9012" not in fields["masked_text"]
    assert fields["extracted_name"] == "Asha Kumari"


def test_empty_text_safe():
    assert ocr.extract_name("") is None
    assert ocr.extract_dob(None) is None
    assert ocr.mask_sensitive("") == ""
