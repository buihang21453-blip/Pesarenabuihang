"""Dispute evidence image/storage helpers.

Extracted from app.py in V1.3.61. The module uses the same configure(context)
compatibility pattern as the other core modules so existing route modules can
keep using the public helper names without circular imports.
"""
from __future__ import annotations

import io
import uuid
from PIL import Image, ImageOps, UnidentifiedImageError

_ctx = {}

EXPORTED_NAMES = (
    "prepare_dispute_evidence_bytes",
    "upload_dispute_evidence",
    "remove_dispute_evidence_object",
    "get_dispute_evidence_signed_url",
)


def configure(context):
    global _ctx
    _ctx = context


def _get(name):
    return _ctx[name]


def _normalize_storage_public_url(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("publicUrl") or value.get("public_url") or value.get("signedURL") or value.get("signed_url")
    return str(value or "")


def prepare_dispute_evidence_bytes(file_storage):
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None

    max_bytes = _get("DISPUTE_EVIDENCE_MAX_BYTES")
    raw = file_storage.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("Ảnh bằng chứng không được vượt quá 4 MB.")
    if not raw:
        raise ValueError("File ảnh bằng chứng đang trống.")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            image_format = (probe.format or "").upper()
            width, height = probe.size
            probe.verify()
        if image_format not in _get("DISPUTE_EVIDENCE_ALLOWED_FORMATS"):
            raise ValueError("Bằng chứng chỉ chấp nhận ảnh JPG, PNG hoặc WEBP.")
        if width < 100 or height < 100:
            raise ValueError("Ảnh bằng chứng quá nhỏ. Vui lòng chọn ảnh từ 100×100 pixel trở lên.")
        if width * height > 30_000_000:
            raise ValueError("Ảnh bằng chứng có độ phân giải quá lớn.")

        with Image.open(io.BytesIO(raw)) as source:
            source = ImageOps.exif_transpose(source).convert("RGB")
            source.thumbnail(
                (_get("DISPUTE_EVIDENCE_MAX_SIDE"), _get("DISPUTE_EVIDENCE_MAX_SIDE")),
                Image.Resampling.LANCZOS,
            )
            output = io.BytesIO()
            source.save(output, format="WEBP", quality=86, method=6)
            return output.getvalue()
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValueError("File bằng chứng không phải ảnh hợp lệ hoặc đã bị lỗi.")


def upload_dispute_evidence(match_id, user_id, evidence_bytes):
    _get("require_db")()
    db = _get("db")
    object_path = f"{match_id}/{user_id}/{uuid.uuid4().hex}.webp"
    bucket = db.storage.from_(_get("DISPUTE_EVIDENCE_BUCKET"))
    bucket.upload(
        object_path,
        evidence_bytes,
        {
            "content-type": "image/webp",
            "cache-control": "3600",
            "upsert": "false",
        },
    )
    return object_path


def remove_dispute_evidence_object(object_path):
    db = _ctx.get("db")
    if not object_path or db is None:
        return
    try:
        db.storage.from_(_get("DISPUTE_EVIDENCE_BUCKET")).remove([object_path])
    except Exception as exc:
        _get("log_system_event")(
            "dispute_evidence_remove_failed",
            level=30,
            object_path=object_path,
            error_type=type(exc).__name__,
            error=str(exc),
        )


def get_dispute_evidence_signed_url(object_path, expires_in=3600):
    db = _ctx.get("db")
    if not object_path or db is None:
        return None
    try:
        response = db.storage.from_(_get("DISPUTE_EVIDENCE_BUCKET")).create_signed_url(
            object_path,
            max(60, int(expires_in)),
        )
        return _normalize_storage_public_url(response)
    except Exception as exc:
        _get("log_system_event")(
            "dispute_evidence_signed_url_failed",
            level=30,
            object_path=object_path,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return None
