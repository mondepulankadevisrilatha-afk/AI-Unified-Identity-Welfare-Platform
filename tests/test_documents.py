"""Document vault tests, including file-type validation by signature."""
import io

from services.common import detect_mime


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF_BYTES = b"%PDF-1.4\n" + b"x" * 64
FAKE_BYTES = b"not a real image" + b"\x00" * 64


def test_detect_mime_png():
    assert detect_mime(io.BytesIO(PNG_BYTES)) == "image/png"


def test_detect_mime_pdf():
    assert detect_mime(io.BytesIO(PDF_BYTES)) == "application/pdf"


def test_detect_mime_rejects_fake():
    assert detect_mime(io.BytesIO(FAKE_BYTES)) is None


def test_detect_mime_resets_stream():
    stream = io.BytesIO(PNG_BYTES)
    detect_mime(stream)
    assert stream.tell() == 0   # position restored for later save


def test_upload_valid_png(auth_user):
    data = {
        "document_name": "My Aadhaar",
        "category": "Aadhaar Card",
        "file": (io.BytesIO(PNG_BYTES), "aadhaar.png"),
    }
    r = auth_user.post("/documents/upload", data=data,
                       content_type="multipart/form-data",
                       follow_redirects=True)
    assert r.status_code == 200
    assert b"uploaded" in r.data.lower()


def test_upload_rejects_fake_content(auth_user):
    data = {
        "document_name": "Fake",
        "category": "Other",
        "file": (io.BytesIO(FAKE_BYTES), "fake.png"),
    }
    r = auth_user.post("/documents/upload", data=data,
                       content_type="multipart/form-data",
                       follow_redirects=True)
    assert b"does not match" in r.data


def test_documents_list_page(auth_user):
    assert auth_user.get("/documents/").status_code == 200


def test_cannot_access_other_users_doc(auth_user):
    # No document id 999 exists / not owned -> 404
    assert auth_user.get("/documents/999").status_code == 404
