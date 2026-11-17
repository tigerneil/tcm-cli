from __future__ import annotations

"""
Multimodal media attachments, provider payload builders, SOTA task routing,
and quantitative CIE L*a*b* tongue/herb colorimetric analysis for TCM-CLI.

Designed with zero mandatory external dependencies beyond the Python standard
library and NumPy (uses Pillow optionally when available).
"""

import base64
from dataclasses import dataclass, field
import io
import mimetypes
from pathlib import Path
import struct
from typing import Any
import urllib.parse
import zlib

import numpy as np

# Extension -> canonical MIME type mapping
_EXT_MIME_MAP: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
}

_AUDIO_FORMAT_MAP: dict[str, str] = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/m4a": "m4a",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
}


def _kind_from_mime(mime_type: str) -> str:
    """Classify a MIME type into 'image', 'audio', 'video', or 'document'."""
    m = (mime_type or "").lower().strip()
    if m.startswith("image/"):
        return "image"
    if m.startswith("audio/"):
        return "audio"
    if m.startswith("video/"):
        return "video"
    return "document"


def _sniff_mime_from_bytes(raw: bytes) -> str | None:
    """Detect common media MIME types from magic header bytes."""
    if len(raw) >= 8 and raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(raw) >= 3 and raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    if len(raw) >= 6 and raw[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if len(raw) >= 5 and raw[:5] == b"%PDF-":
        return "application/pdf"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WAVE":
        return "audio/wav"
    if len(raw) >= 4 and raw[:4] == b"OggS":
        return "audio/ogg"
    if len(raw) >= 3 and (raw[:3] == b"ID3" or raw[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        return "audio/mpeg"
    if len(raw) >= 12 and raw[4:8] == b"ftyp":
        brand = raw[8:12]
        if brand in (b"M4A ", b"M4B "):
            return "audio/mp4"
        return "video/mp4"
    return None


def _guess_mime(filename: str = "", raw: bytes | None = None, explicit: str | None = None) -> str:
    """Resolve MIME type from explicit hint, file extension, magic bytes, or stdlib."""
    if explicit and explicit.strip():
        return explicit.strip().lower()
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in _EXT_MIME_MAP:
            return _EXT_MIME_MAP[ext]
    if raw:
        sniffed = _sniff_mime_from_bytes(raw)
        if sniffed:
            return sniffed
    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            return guessed.lower()
    return "application/octet-stream"


def _clean_b64(b64_str: str) -> str:
    """Normalize a base64 string and ensure proper padding."""
    cleaned = "".join(b64_str.strip().split())
    rem = len(cleaned) % 4
    if rem:
        cleaned += "=" * (4 - rem)
    return cleaned


@dataclass
class MediaAttachment:
    """Unified multimodal attachment for images, audio, video, and documents."""

    kind: str  # "image", "audio", "document", or "video"
    mime_type: str
    data_b64: str = ""
    url: str = ""
    source_path: str = ""
    filename: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_data_uri(self) -> str:
        """Return a RFC 2397 data URI if base64 payload is present, else URL or empty string."""
        if self.data_b64:
            return f"data:{self.mime_type};base64,{self.data_b64}"
        if self.url:
            return self.url
        return ""

    def to_bytes(self) -> bytes:
        """Decode attachment content to raw bytes when available locally."""
        if self.data_b64:
            return base64.b64decode(_clean_b64(self.data_b64))
        if self.source_path:
            p = Path(self.source_path).expanduser()
            if p.is_file():
                return p.read_bytes()
        return b""

    def size_bytes(self) -> int:
        """Return decoded payload size in bytes (0 for remote-only URLs)."""
        if self.data_b64:
            s = self.data_b64.strip()
            if not s:
                return 0
            padding = 2 if s.endswith("==") else (1 if s.endswith("=") else 0)
            return max(0, (len(s) * 3) // 4 - padding)
        if self.source_path:
            p = Path(self.source_path).expanduser()
            if p.is_file():
                return p.stat().st_size
        return 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata and payload descriptor to a dictionary."""
        return {
            "kind": self.kind,
            "mime_type": self.mime_type,
            "data_b64": self.data_b64,
            "url": self.url,
            "source_path": self.source_path,
            "filename": self.filename,
            "size_bytes": self.size_bytes(),
            "metadata": dict(self.metadata),
        }


def _parse_data_uri(uri: str) -> tuple[str, str]:
    """Parse `data:[<mediatype>][;base64],<data>` into `(mime_type, data_b64)`."""
    header, sep, payload = uri.partition(",")
    if not sep:
        raise ValueError("Invalid data URI: missing comma separator.")
    meta = header[5:]  # strip "data:"
    is_b64 = False
    parts = [p for p in meta.split(";") if p]
    if parts and parts[-1].lower() == "base64":
        is_b64 = True
        parts = parts[:-1]
    mime = parts[0].lower() if parts and "/" in parts[0] else "text/plain"
    if is_b64:
        b64_data = _clean_b64(payload)
    else:
        raw = urllib.parse.unquote_to_bytes(payload)
        b64_data = base64.b64encode(raw).decode("ascii")
    return mime, b64_data


def load_attachment(
    source: str | Path | dict | bytes | MediaAttachment,
    mime_type: str | None = None,
) -> MediaAttachment:
    """Load a multimodal attachment from dict, data URI, HTTP(S) URL, bytes, or local file path."""
    if isinstance(source, MediaAttachment):
        if mime_type and mime_type != source.mime_type:
            return MediaAttachment(
                kind=_kind_from_mime(mime_type),
                mime_type=mime_type,
                data_b64=source.data_b64,
                url=source.url,
                source_path=source.source_path,
                filename=source.filename,
                metadata=dict(source.metadata),
            )
        return source

    if isinstance(source, (bytes, bytearray)):
        raw_bytes = bytes(source)
        resolved_mime = _guess_mime(raw=raw_bytes, explicit=mime_type)
        return MediaAttachment(
            kind=_kind_from_mime(resolved_mime),
            mime_type=resolved_mime,
            data_b64=base64.b64encode(raw_bytes).decode("ascii"),
        )

    if isinstance(source, dict):
        explicit_mime = mime_type or source.get("mime_type") or source.get("media_type")
        filename = str(source.get("filename") or source.get("name") or "")
        meta = dict(source.get("metadata") or {})
        raw_field = source.get("data_b64") if source.get("data_b64") is not None else source.get("data")

        if raw_field is not None and raw_field != "":
            if isinstance(raw_field, (bytes, bytearray)):
                raw_b = bytes(raw_field)
                resolved_mime = _guess_mime(filename=filename, raw=raw_b, explicit=explicit_mime)
                b64_str = base64.b64encode(raw_b).decode("ascii")
            elif isinstance(raw_field, str) and raw_field.strip().startswith("data:"):
                parsed_mime, b64_str = _parse_data_uri(raw_field.strip())
                resolved_mime = explicit_mime or parsed_mime
            else:
                b64_str = _clean_b64(str(raw_field))
                raw_sample = base64.b64decode(b64_str[:64]) if len(b64_str) >= 16 else b""
                resolved_mime = _guess_mime(
                    filename=filename, raw=raw_sample, explicit=explicit_mime
                )
            kind = source.get("kind") or _kind_from_mime(resolved_mime)
            return MediaAttachment(
                kind=kind,
                mime_type=resolved_mime,
                data_b64=b64_str,
                source_path=str(source.get("source_path") or source.get("path") or ""),
                filename=filename,
                metadata=meta,
            )

        if source.get("url"):
            att = load_attachment(str(source["url"]), mime_type=explicit_mime)
            if filename:
                att.filename = filename
            if source.get("kind"):
                att.kind = str(source["kind"])
            if meta:
                att.metadata.update(meta)
            return att

        path_val = source.get("path") or source.get("source_path")
        if path_val:
            att = load_attachment(Path(str(path_val)), mime_type=explicit_mime)
            if filename:
                att.filename = filename
            if source.get("kind"):
                att.kind = str(source["kind"])
            if meta:
                att.metadata.update(meta)
            return att

        raise ValueError("Attachment dict must provide 'data_b64', 'data', 'url', or 'path'.")

    if isinstance(source, str):
        s = source.strip()
        if s.startswith("data:"):
            parsed_mime, b64_str = _parse_data_uri(s)
            resolved_mime = (mime_type or parsed_mime).lower()
            return MediaAttachment(
                kind=_kind_from_mime(resolved_mime),
                mime_type=resolved_mime,
                data_b64=b64_str,
            )
        if s.startswith(("http://", "https://")):
            parsed_url = urllib.parse.urlparse(s)
            url_name = Path(urllib.parse.unquote(parsed_url.path)).name
            resolved_mime = _guess_mime(filename=url_name, explicit=mime_type)
            if resolved_mime == "application/octet-stream" and mime_type is None:
                # Default bare image URLs cleanly when extension is omitted
                resolved_mime = "image/jpeg"
            return MediaAttachment(
                kind=_kind_from_mime(resolved_mime),
                mime_type=resolved_mime,
                url=s,
                filename=url_name,
            )
        file_path = Path(s).expanduser()
    elif isinstance(source, Path):
        file_path = source.expanduser()
    else:
        raise TypeError(f"Unsupported attachment source type: {type(source).__name__}")

    if not file_path.is_file():
        raise FileNotFoundError(f"Attachment file not found: {file_path}")

    raw_bytes = file_path.read_bytes()
    resolved_mime = _guess_mime(
        filename=file_path.name, raw=raw_bytes, explicit=mime_type
    )
    return MediaAttachment(
        kind=_kind_from_mime(resolved_mime),
        mime_type=resolved_mime,
        data_b64=base64.b64encode(raw_bytes).decode("ascii"),
        source_path=str(file_path.resolve()),
        filename=file_path.name,
    )


# ─── Native Pure-Python + NumPy Image Decoding & TCM Colorimetry ──────────────


def _paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter_png_pass(
    raw_buf: memoryview,
    offset: int,
    width: int,
    height: int,
    bpp: int,
    row_bytes: int,
) -> tuple[np.ndarray, int]:
    """Reconstruct PNG scanlines for a single pass into shape (height, row_bytes) uint8."""
    out = np.zeros((height, row_bytes), dtype=np.uint8)
    pos = offset
    prev = np.zeros(row_bytes, dtype=np.int32)

    for y in range(height):
        ftype = raw_buf[pos]
        pos += 1
        row = np.frombuffer(raw_buf[pos:pos + row_bytes], dtype=np.uint8).astype(np.int32)
        pos += row_bytes

        if ftype == 0:  # None
            recon = row
        elif ftype == 1:  # Sub
            recon = row.copy()
            for x in range(bpp, row_bytes):
                recon[x] = (recon[x] + recon[x - bpp]) & 0xFF
        elif ftype == 2:  # Up
            recon = (row + prev) & 0xFF
        elif ftype == 3:  # Average
            recon = row.copy()
            for x in range(row_bytes):
                left = recon[x - bpp] if x >= bpp else 0
                recon[x] = (recon[x] + ((left + int(prev[x])) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            recon = row.copy()
            for x in range(row_bytes):
                a = int(recon[x - bpp]) if x >= bpp else 0
                b = int(prev[x])
                c = int(prev[x - bpp]) if x >= bpp else 0
                recon[x] = (recon[x] + _paeth_predictor(a, b, c)) & 0xFF
        else:
            raise ValueError(f"Unsupported PNG filter type: {ftype}")

        out[y] = recon.astype(np.uint8)
        prev = recon

    return out, pos


def _decode_png_native(raw: bytes) -> tuple[np.ndarray, np.ndarray | None, int, int]:
    """Decode PNG bytes in pure Python + NumPy into (rgb_uint8[H,W,3], alpha_uint8[H,W]|None, W, H)."""
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG signature.")

    pos = 8
    width = height = bit_depth = color_type = interlace = 0
    palette: np.ndarray | None = None
    idat_parts: list[bytes] = []

    while pos + 8 <= len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        cdata_start = pos + 8
        cdata_end = cdata_start + length
        if cdata_end > len(raw):
            break
        cdata = raw[cdata_start:cdata_end]
        pos = cdata_end + 4  # skip 4-byte CRC

        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", cdata[:13]
            )
        elif ctype == b"PLTE":
            n_entries = len(cdata) // 3
            palette = np.frombuffer(cdata[:n_entries * 3], dtype=np.uint8).reshape(n_entries, 3)
        elif ctype == b"IDAT":
            idat_parts.append(cdata)
        elif ctype == b"IEND":
            break

    if width <= 0 or height <= 0 or not idat_parts:
        raise ValueError("Incomplete PNG data.")

    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    if color_type not in channels_map:
        raise ValueError(f"Unsupported PNG color_type: {color_type}")
    channels = channels_map[color_type]

    decompressed = zlib.decompress(b"".join(idat_parts))
    view = memoryview(decompressed)

    if bit_depth == 8:
        bpp = channels
        if interlace == 0:
            scan, _ = _unfilter_png_pass(view, 0, width, height, bpp, width * bpp)
            pixels = scan.reshape(height, width, channels)
        else:
            # Adam7 7-pass interlace reconstruction
            pixels = np.zeros((height, width, channels), dtype=np.uint8)
            x_orig = (0, 4, 0, 2, 0, 1, 0)
            y_orig = (0, 0, 4, 0, 2, 0, 1)
            x_step = (8, 8, 4, 4, 2, 2, 1)
            y_step = (8, 8, 8, 4, 4, 2, 2)
            offset = 0
            for p in range(7):
                pw = (width - x_orig[p] + x_step[p] - 1) // x_step[p]
                ph = (height - y_orig[p] + y_step[p] - 1) // y_step[p]
                if pw <= 0 or ph <= 0:
                    continue
                sub_scan, offset = _unfilter_png_pass(view, offset, pw, ph, bpp, pw * bpp)
                ys_slice = slice(y_orig[p], None, y_step[p])
                xs_slice = slice(x_orig[p], None, x_step[p])
                pixels[ys_slice, xs_slice] = sub_scan.reshape(ph, pw, channels)
    elif bit_depth == 16 and interlace == 0:
        bpp = channels * 2
        scan, _ = _unfilter_png_pass(view, 0, width, height, bpp, width * bpp)
        # Take high-order byte of each 16-bit big-endian sample
        pixels = scan[:, 0::2].reshape(height, width, channels)
    elif bit_depth in (1, 2, 4) and interlace == 0 and channels == 1:
        row_bytes = (width * bit_depth + 7) // 8
        scan, _ = _unfilter_png_pass(view, 0, width, height, 1, row_bytes)
        pixels_2d = np.zeros((height, width), dtype=np.uint8)
        mask = (1 << bit_depth) - 1
        per_byte = 8 // bit_depth
        scale = 255 // mask if color_type == 0 else 1
        for x in range(width):
            byte_idx = x // per_byte
            shift = 8 - bit_depth * ((x % per_byte) + 1)
            vals = ((scan[:, byte_idx] >> shift) & mask) * scale
            pixels_2d[:, x] = vals.astype(np.uint8)
        pixels = pixels_2d[:, :, None]
    else:
        raise ValueError(f"Unsupported PNG bit_depth={bit_depth}, interlace={interlace}")

    alpha: np.ndarray | None = None
    if color_type == 0:  # Grayscale
        rgb = np.repeat(pixels, 3, axis=2)
    elif color_type == 2:  # Truecolor RGB
        rgb = pixels
    elif color_type == 3:  # Indexed palette
        if palette is None:
            rgb = np.repeat(pixels, 3, axis=2)
        else:
            idx = np.clip(pixels[:, :, 0], 0, len(palette) - 1)
            rgb = palette[idx]
    elif color_type == 4:  # Grayscale + Alpha
        rgb = np.repeat(pixels[:, :, :1], 3, axis=2)
        alpha = pixels[:, :, 1]
    else:  # color_type == 6: RGBA
        rgb = pixels[:, :, :3]
        alpha = pixels[:, :, 3]

    return rgb, alpha, width, height


def _parse_jpeg_fallback(raw: bytes) -> tuple[np.ndarray, int, int]:
    """Parse JPEG SOF0/SOF2 dimensions without PIL and sample entropy byte distribution."""
    if len(raw) < 4 or raw[:2] != b"\xff\xd8":
        raise ValueError("Invalid JPEG header.")

    pos = 2
    width = height = 64
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
    }
    scan_start = len(raw)

    while pos < len(raw) - 1:
        if raw[pos] != 0xFF:
            pos += 1
            continue
        while pos < len(raw) and raw[pos] == 0xFF:
            pos += 1
        if pos >= len(raw):
            break
        marker = raw[pos]
        pos += 1
        if marker in (0xD8, 0xD9, 0x01) or (0xD0 <= marker <= 0xD7):
            continue
        if pos + 2 > len(raw):
            break
        seg_len = struct.unpack(">H", raw[pos:pos + 2])[0]
        if seg_len < 2 or pos + seg_len > len(raw):
            break
        seg = raw[pos + 2:pos + seg_len]
        if marker in sof_markers and len(seg) >= 5:
            height, width = struct.unpack(">HH", seg[1:5])
        if marker == 0xDA:  # SOS
            scan_start = pos + seg_len
            break
        pos += seg_len

    entropy = raw[scan_start:-2] if scan_start < len(raw) - 2 else raw
    if not entropy:
        entropy = raw
    sample_h = min(max(height, 4), 64)
    sample_w = min(max(width, 4), 64)
    needed = sample_h * sample_w * 3
    arr = np.frombuffer(entropy, dtype=np.uint8)
    tiled = np.resize(arr, needed).reshape(sample_h, sample_w, 3)
    return tiled, max(1, width), max(1, height)


def _decode_image_pixels(raw: bytes) -> tuple[np.ndarray, np.ndarray | None, str, int, int]:
    """Decode image bytes into (rgb[H,W,3], alpha[H,W]|None, format_str, width, height)."""
    detected_fmt = "UNKNOWN"
    mime = _sniff_mime_from_bytes(raw)
    if mime == "image/png":
        detected_fmt = "PNG"
    elif mime == "image/jpeg":
        detected_fmt = "JPEG"
    elif mime == "image/webp":
        detected_fmt = "WEBP"
    elif mime == "image/gif":
        detected_fmt = "GIF"

    # Prefer Pillow when installed for JPEG, WebP, GIF, TIFF, and PNG
    try:
        from PIL import Image  # type: ignore[import-not-found]

        with Image.open(io.BytesIO(raw)) as img:
            fmt = (img.format or detected_fmt or "IMAGE").upper()
            width, height = img.size
            rgba = np.asarray(img.convert("RGBA"), dtype=np.uint8)
            rgb = rgba[:, :, :3]
            alpha = rgba[:, :, 3] if img.mode in ("RGBA", "LA", "PA") else None
            return rgb, alpha, fmt, int(width), int(height)
    except ImportError:
        pass
    except Exception:
        # Fall through to native decoders if PIL fails on an edge-case stream
        pass

    if detected_fmt == "PNG":
        rgb, alpha, w, h = _decode_png_native(raw)
        return rgb, alpha, "PNG", w, h

    if detected_fmt == "JPEG":
        rgb, w, h = _parse_jpeg_fallback(raw)
        return rgb, None, "JPEG", w, h

    if detected_fmt == "GIF" and len(raw) >= 10:
        w, h = struct.unpack("<HH", raw[6:10])
        arr = np.frombuffer(raw[10:], dtype=np.uint8)
        src = arr if len(arr) else np.array([128], dtype=np.uint8)
        grid = np.resize(src, (max(4, min(h, 64)), max(4, min(w, 64)), 3))
        return grid, None, "GIF", int(w), int(h)

    raise ValueError(
        f"Unsupported or corrupt image data (detected format: {detected_fmt}). "
        "Provide a PNG image or install Pillow for additional image formats."
    )


def _srgb_to_cielab(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert uint8/float RGB array [..., 3] (0..255) to CIE L*a*b* (D65, 2-deg observer)."""
    srgb = np.clip(rgb.astype(np.float64) / 255.0, 0.0, 1.0)
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)

    r = linear[..., 0]
    g = linear[..., 1]
    b = linear[..., 2]

    # sRGB to CIE XYZ (D65)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b

    # Reference white D65
    xr = x / 0.95047
    yr = y / 1.00000
    zr = z / 1.08883

    eps = 216.0 / 24389.0
    kappa = 24389.0 / 27.0

    fx = np.where(xr > eps, np.cbrt(np.maximum(xr, 0.0)), (kappa * xr + 16.0) / 116.0)
    fy = np.where(yr > eps, np.cbrt(np.maximum(yr, 0.0)), (kappa * yr + 16.0) / 116.0)
    fz = np.where(zr > eps, np.cbrt(np.maximum(zr, 0.0)), (kappa * zr + 16.0) / 116.0)

    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)
    return L, a, b_star


def _summarize_region(
    rgb_pixels: np.ndarray,
    L_vals: np.ndarray,
    a_vals: np.ndarray,
    b_vals: np.ndarray,
) -> dict[str, Any]:
    """Compute colorimetric summary over a 1D collection of N pixels."""
    r_m = float(np.mean(rgb_pixels[:, 0]))
    g_m = float(np.mean(rgb_pixels[:, 1]))
    b_m = float(np.mean(rgb_pixels[:, 2]))

    L_m = float(np.mean(L_vals))
    a_m = float(np.mean(a_vals))
    b_s = float(np.mean(b_vals))

    red_lab = float(np.clip((a_m + 5.0) / 65.0, 0.0, 1.0))
    red_rgb = float(np.clip((r_m - 0.5 * (g_m + b_m)) / 180.0, 0.0, 1.0))
    redness = float(np.clip(0.5 * red_lab + 0.5 * red_rgb, 0.0, 1.0))

    yel_lab = float(np.clip(b_s / 55.0, 0.0, 1.0))
    yel_rgb = float(np.clip((0.5 * (r_m + g_m) - b_m) / 180.0, 0.0, 1.0))
    yellowness = float(np.clip(0.6 * yel_lab + 0.4 * yel_rgb, 0.0, 1.0))

    chroma = np.hypot(a_vals, b_vals)
    specular_mask = (L_vals >= 85.0) & (chroma <= 20.0)
    moisture_gloss = float(np.mean(specular_mask)) if len(L_vals) > 0 else 0.0

    return {
        "rgb_mean": [round(r_m, 2), round(g_m, 2), round(b_m, 2)],
        "lab_approx": {
            "L": round(L_m, 2),
            "a": round(a_m, 2),
            "b": round(b_s, 2),
        },
        "redness_index": round(redness, 4),
        "yellowness_index": round(yellowness, 4),
        "moisture_gloss_index": round(moisture_gloss, 4),
    }


def _resolve_raw_image_bytes(data: bytes | str | Path | MediaAttachment) -> bytes:
    """Resolve raw bytes from bytes, base64/data-URI string, Path, or MediaAttachment."""
    if isinstance(data, MediaAttachment):
        raw = data.to_bytes()
        if not raw:
            raise ValueError("MediaAttachment does not contain local image bytes.")
        return raw
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, Path):
        p = data.expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"Image file not found: {p}")
        return p.read_bytes()
    if isinstance(data, str):
        s = data.strip()
        if s.startswith("data:"):
            _, b64_str = _parse_data_uri(s)
            return base64.b64decode(b64_str)
        if len(s) < 1024 and "\n" not in s and "\r" not in s:
            try:
                p = Path(s).expanduser()
                if p.is_file():
                    return p.read_bytes()
            except OSError:
                pass
        return base64.b64decode(_clean_b64(s))
    raise TypeError(f"Unsupported image input type: {type(data).__name__}")


def extract_image_biometrics(data: bytes | str | Path | MediaAttachment) -> dict[str, Any]:
    """Extract quantitative CIE L*a*b* colorimetry, tongue somatotopy zones, and TCM visual hints."""
    raw = _resolve_raw_image_bytes(data)
    rgb, alpha, fmt, width, height = _decode_image_pixels(raw)

    h, w, _ = rgb.shape
    L_map, a_map, b_map = _srgb_to_cielab(rgb)

    fg_mask = (alpha >= 32) if alpha is not None else np.ones((h, w), dtype=bool)
    if not np.any(fg_mask):
        fg_mask = np.ones((h, w), dtype=bool)

    def _extract_zone(mask_2d: np.ndarray, organ_label: str) -> dict[str, Any]:
        combined = mask_2d & fg_mask
        if not np.any(combined):
            combined = mask_2d if np.any(mask_2d) else fg_mask
        summary = _summarize_region(
            rgb[combined], L_map[combined], a_map[combined], b_map[combined]
        )
        summary["organ_correspondence"] = organ_label
        return summary

    overall = _summarize_region(
        rgb[fg_mask], L_map[fg_mask], a_map[fg_mask], b_map[fg_mask]
    )

    # Build normalized coordinate grids for TCM tongue somatotopy
    ys = (np.arange(h, dtype=np.float64) + 0.5) / max(h, 1)
    xs = (np.arange(w, dtype=np.float64) + 0.5) / max(w, 1)
    yy, xx = np.meshgrid(ys, xs, indexing="ij")

    # Root (Kidney / Lower Jiao): upper 25%, central 60%
    root_mask = (yy <= 0.25) & (xx >= 0.20) & (xx <= 0.80)
    # Center (Spleen / Stomach): middle 50%, central 50%
    center_mask = (yy > 0.25) & (yy < 0.75) & (xx >= 0.25) & (xx <= 0.75)
    # Sides (Liver / Gallbladder): lateral 25% margins across body
    sides_mask = (yy >= 0.20) & (yy <= 0.80) & ((xx < 0.25) | (xx > 0.75))
    # Tip (Heart / Lung): lower 25%, central 60%
    tip_mask = (yy >= 0.75) & (xx >= 0.20) & (xx <= 0.80)

    zones = {
        "tip": _extract_zone(tip_mask, "Heart/Lung (心肺)"),
        "center": _extract_zone(center_mask, "Spleen/Stomach (脾胃)"),
        "sides": _extract_zone(sides_mask, "Liver/Gallbladder (肝胆)"),
        "root": _extract_zone(root_mask, "Kidney (肾)"),
    }

    # Quantitative TCM visual syndrome/sign hints from CIE L*a*b* & somatotopy
    L_val = overall["lab_approx"]["L"]
    a_val = overall["lab_approx"]["a"]
    b_val = overall["lab_approx"]["b"]
    gloss = overall["moisture_gloss_index"]
    center_b = zones["center"]["lab_approx"]["b"]
    center_a = zones["center"]["lab_approx"]["a"]
    tip_a = zones["tip"]["lab_approx"]["a"]
    sides_a = zones["sides"]["lab_approx"]["a"]

    hints: list[str] = []
    if L_val > 68.0 and a_val < 16.0:
        hints.append(
            f"Pale chromatic profile (淡白舌倾向, L*={L_val:.1f} > 68, a*={a_val:.1f} < 16): "
            "consider Yang/Qi/Blood deficiency pattern."
        )
    if a_val > 42.0:
        hints.append(
            f"Crimson/deep-red chromaticity (绛舌倾向, a*={a_val:.1f} > 42): "
            "consider intense Heat or Yin-deficiency fire."
        )
    elif a_val > 32.0:
        hints.append(
            f"Elevated magenta-redness (红舌倾向, a*={a_val:.1f} > 32): "
            "consider Heat syndrome or Yin deficiency fire."
        )

    if center_b > 22.0 or b_val > 22.0:
        hints.append(
            f"Elevated yellowness in Spleen/Stomach center (黄腻苔倾向, center b*={center_b:.1f}): "
            "consider Damp-Heat or Phlegm-Heat in Middle Jiao."
        )

    if b_val < 5.0 and a_val < 20.0:
        hints.append(
            f"Bluish/cyanotic shift with low a*/b* (青紫舌倾向, a*={a_val:.1f}, b*={b_val:.1f} < 5): "
            "consider Blood stasis (血瘀) or Cold congealing."
        )

    if tip_a > 34.0 and (tip_a - center_a) > 6.0:
        hints.append(
            f"Focal hyperemia at Tip zone (舌尖偏红, tip a*={tip_a:.1f}): "
            "correlates with Heart/Lung Heat (心肺火旺)."
        )
    if sides_a > 34.0 and (sides_a - center_a) > 6.0:
        hints.append(
            f"Focal redness at Sides zone (舌边偏红, sides a*={sides_a:.1f}): "
            "correlates with Liver/Gallbladder Fire or Qi stagnation transforming into Heat."
        )

    if gloss > 0.18:
        hints.append(
            f"High specular surface gloss ({gloss:.1%} highlight pixels): "
            "suggests moist/slippery coating (水滑苔) or Dampness retention."
        )
    elif gloss < 0.005 and L_val < 52.0:
        hints.append(
            "Low surface specular gloss with dark body: "
            "evaluate for dry coating / fluid depletion (津亏燥苔)."
        )

    if not hints:
        hints.append(
            f"Balanced light-red colorimetric range (淡红舌参考区间, L*={L_val:.1f}, a*={a_val:.1f}, b*={b_val:.1f}): "
            "correlate visually with coating thickness, fissures, and pulse."
        )

    return {
        "format": fmt,
        "width": width,
        "height": height,
        "rgb_mean": overall["rgb_mean"],
        "lab_approx": overall["lab_approx"],
        "redness_index": overall["redness_index"],
        "yellowness_index": overall["yellowness_index"],
        "moisture_gloss_index": overall["moisture_gloss_index"],
        "zones": zones,
        "tcm_visual_hints": hints,
    }


# ─── Multimodal Provider Message Formatters ──────────────────────────────────


def _normalize_attachments(
    attachments: list[MediaAttachment | dict | str | Path] | None,
) -> list[MediaAttachment]:
    if not attachments:
        return []
    return [
        a if isinstance(a, MediaAttachment) else load_attachment(a)
        for a in attachments
    ]


def _decode_text_attachment(att: MediaAttachment) -> str:
    raw = att.to_bytes()
    if raw:
        return raw.decode("utf-8", errors="replace")
    return f"[Remote document: {att.url}]"


def build_anthropic_messages(
    messages: list[dict],
    attachments: list[MediaAttachment] | None = None,
) -> list[dict]:
    """Format chat messages with multimodal image/PDF/document blocks for Anthropic API."""
    copied = [dict(m) for m in messages]
    norm_atts = _normalize_attachments(attachments)
    if not norm_atts:
        return copied

    blocks: list[dict[str, Any]] = []
    for att in norm_atts:
        if att.kind == "image":
            if att.data_b64:
                blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": att.mime_type,
                        "data": att.data_b64,
                    },
                })
            elif att.url:
                blocks.append({
                    "type": "image",
                    "source": {"type": "url", "url": att.url},
                })
        elif att.kind == "document" and att.mime_type == "application/pdf":
            if att.data_b64:
                blocks.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": att.data_b64,
                    },
                })
            elif att.url:
                blocks.append({
                    "type": "document",
                    "source": {"type": "url", "url": att.url},
                })
        elif att.kind == "document":
            doc_text = _decode_text_attachment(att)
            label = att.filename or "document"
            blocks.append({
                "type": "text",
                "text": f"[Attached document: {label}]\n{doc_text}",
            })
        else:
            # Audio / video fallback descriptor for Anthropic Messages API
            label = att.filename or att.url or att.mime_type
            transcript = att.metadata.get("transcript", "")
            extra = f"\nTranscript: {transcript}" if transcript else ""
            blocks.append({
                "type": "text",
                "text": (
                    f"[Attached {att.kind}: {label} ({att.mime_type}, "
                    f"{att.size_bytes()} bytes)]{extra}"
                ),
            })

    target_idx = None
    for idx in range(len(copied) - 1, -1, -1):
        if copied[idx].get("role") == "user":
            target_idx = idx
            break

    if target_idx is None:
        copied.append({"role": "user", "content": blocks})
        return copied

    target = dict(copied[target_idx])
    existing = target.get("content", "")
    if isinstance(existing, list):
        target["content"] = list(blocks) + list(existing)
    elif existing:
        target["content"] = list(blocks) + [{"type": "text", "text": str(existing)}]
    else:
        target["content"] = list(blocks)
    copied[target_idx] = target
    return copied


def build_openai_messages(
    system: str,
    messages: list[dict],
    attachments: list[MediaAttachment] | None = None,
) -> list[dict]:
    """Format chat messages with multimodal content blocks for OpenAI & compatible APIs."""
    oai_messages: list[dict[str, Any]] = []
    if system is not None:
        oai_messages.append({"role": "system", "content": system})
    for m in messages:
        oai_messages.append(dict(m))

    norm_atts = _normalize_attachments(attachments)
    if not norm_atts:
        return oai_messages

    att_parts: list[dict[str, Any]] = []
    for att in norm_atts:
        if att.kind == "image":
            uri = att.to_data_uri() or att.url
            att_parts.append({
                "type": "image_url",
                "image_url": {"url": uri},
            })
        elif att.kind == "audio":
            audio_fmt = _AUDIO_FORMAT_MAP.get(
                att.mime_type.lower(),
                att.mime_type.split("/")[-1].lower() or "wav",
            )
            att_parts.append({
                "type": "input_audio",
                "input_audio": {
                    "data": att.data_b64,
                    "format": audio_fmt,
                },
            })
        elif att.kind == "document" and att.mime_type == "application/pdf" and att.data_b64:
            att_parts.append({
                "type": "file",
                "file": {
                    "filename": att.filename or "document.pdf",
                    "file_data": att.to_data_uri(),
                },
            })
        else:
            if att.kind == "document":
                doc_text = _decode_text_attachment(att)
                label = att.filename or "document"
                att_parts.append({
                    "type": "text",
                    "text": f"[Attached document: {label}]\n{doc_text}",
                })
            else:
                label = att.filename or att.url or att.mime_type
                att_parts.append({
                    "type": "text",
                    "text": f"[Attached {att.kind}: {label} ({att.mime_type})]",
                })

    target_idx = None
    for idx in range(len(oai_messages) - 1, -1, -1):
        if oai_messages[idx].get("role") == "user":
            target_idx = idx
            break

    if target_idx is None:
        oai_messages.append({"role": "user", "content": att_parts})
        return oai_messages

    target = dict(oai_messages[target_idx])
    existing = target.get("content", "")
    content_list: list[dict[str, Any]] = []
    if isinstance(existing, list):
        content_list.extend(existing)
    elif existing:
        content_list.append({"type": "text", "text": str(existing)})
    content_list.extend(att_parts)
    target["content"] = content_list
    oai_messages[target_idx] = target
    return oai_messages


def build_google_contents(
    system: str,
    messages: list[dict],
    attachments: list[MediaAttachment] | None = None,
) -> list[Any]:
    """Build `google.genai.types.Content` list with native image/audio/PDF/video `Part`s."""
    from google.genai import types as genai_types

    contents: list[Any] = []
    if system:
        contents.append(genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=f"[System instructions]\n{system}")],
        ))
        contents.append(genai_types.Content(
            role="model",
            parts=[genai_types.Part(text="Understood. I will follow those instructions.")],
        ))

    for m in messages:
        role = m.get("role", "user")
        api_role = "model" if role == "assistant" else "user"
        msg_text = m.get("content", "")
        parts = [genai_types.Part(text=str(msg_text))] if msg_text != "" else [genai_types.Part(text="")]
        contents.append(genai_types.Content(role=api_role, parts=parts))

    norm_atts = _normalize_attachments(attachments)
    if not norm_atts:
        return contents

    media_parts: list[Any] = []
    for att in norm_atts:
        raw = att.to_bytes()
        if raw:
            media_parts.append(
                genai_types.Part.from_bytes(data=raw, mime_type=att.mime_type)
            )
        elif att.url:
            media_parts.append(
                genai_types.Part.from_uri(file_uri=att.url, mime_type=att.mime_type)
            )

    target_idx = None
    for idx in range(len(contents) - 1, -1, -1):
        if getattr(contents[idx], "role", None) == "user":
            target_idx = idx
            break

    if target_idx is None:
        contents.append(genai_types.Content(role="user", parts=media_parts))
    else:
        existing_parts = list(contents[target_idx].parts or [])
        contents[target_idx] = genai_types.Content(
            role="user",
            parts=existing_parts + media_parts,
        )
    return contents


# ─── Task-Specific SOTA Model Recommendations ────────────────────────────────

SUPPORTED_RECOMMENDATION_TASKS: tuple[str, ...] = (
    "general",
    "tongue_vision",
    "herb_identification",
    "classical_ocr",
    "network_pharmacology",
    "clinical_safety",
    "bilingual_synthesis",
    "offline_local",
)

# Curated task affinities: model_id -> (score_bonus, clinical/research rationale)
_TASK_MODEL_PRIORITIES: dict[str, dict[str, tuple[float, str]]] = {
    "general": {
        "claude-sonnet-5-5": (
            32.0,
            "Optimal balance of frontier multimodal clinical reasoning, 1M context, and low latency.",
        ),
        "gpt-6.1-sol": (
            30.0,
            "Near-Astra multimodal intelligence with strong tool orchestration and cost efficiency.",
        ),
        "gemini-3.6-flash": (
            29.0,
            "Native omni-modal Flash (text, vision, audio, video, PDF) at $0.20/M input.",
        ),
        "claude-opus-5-5": (
            28.0,
            "Flagship deep pharmacology and integrative syndrome synthesis.",
        ),
        "deepseek-v4.1-flash": (
            27.0,
            "552B MoE with native vision, 1M context, and native bilingual TCM fluency.",
        ),
    },
    "tongue_vision": {
        "gemini-3.6-flash": (
            38.0,
            "Native omni-modal vision + cough/voice audio fusion for Four Examinations (四诊合参).",
        ),
        "qwen-vl-max": (
            36.0,
            "Specialized high-resolution Chinese tongue coating, sublingual vein, and clinical VLM.",
        ),
        "gpt-6.1-terra": (
            35.0,
            "Precision visual inspection tuned for tongue somatotopy and specimen diagnostics.",
        ),
        "claude-opus-5-5": (
            32.0,
            "Nuanced integrative reasoning linking CIE L*a*b* colorimetry with syndrome differentiation.",
        ),
        "glm-4v-plus": (
            30.0,
            "Purpose-trained on Chinese clinical imaging and tongue/prescription photography.",
        ),
        "ollama/huatuogpt-vision:7b": (
            26.0,
            "Private on-premise Chinese medical and tongue diagnosis VLM.",
        ),
    },
    "herb_identification": {
        "gpt-6.1-terra": (
            38.0,
            "High-precision macroscopic morphology & Materia Medica decoction-piece (饮片) inspection.",
        ),
        "qwen-vl-max": (
            36.0,
            "Strong Chinese botanical taxonomy, slice cross-section, and pharmacopoeia visual matching.",
        ),
        "gemini-3.6-flash": (
            34.0,
            "Fast omni-modal specimen photography & video inspection with 1M context.",
        ),
        "claude-sonnet-5-5": (
            31.0,
            "Reliable adulterant differentiation and structured pharmacognosy reporting.",
        ),
        "pixtral-large-latest": (
            28.0,
            "High-resolution botanical & specimen document vision.",
        ),
    },
    "classical_ocr": {
        "qwen-vl-max": (
            40.0,
            "SOTA vertical woodblock printing, traditional characters, and handwritten prescription OCR.",
        ),
        "kimi-k3.1-pro": (
            36.0,
            "1M-context classical medical canon (伤寒论, 本草纲目) philology & multimodal synthesis.",
        ),
        "gemini-3.1-pro-preview": (
            35.0,
            "Native multi-page scanned PDF ingestion and classical commentary cross-referencing.",
        ),
        "claude-opus-5-5": (
            33.0,
            "High-accuracy PDF treatise parsing with scholarly textual criticism.",
        ),
        "deepseek-v4.1-flash": (
            31.0,
            "Native vision + 384k max output for full-treatise bilingual transcription.",
        ),
    },
    "network_pharmacology": {
        "gpt-rosalind-research": (
            42.0,
            "Purpose-built life sciences model for ADMET, SMILES/target docking, and pathway reasoning.",
        ),
        "claude-fable-5-2": (
            39.0,
            "Frontier long-horizon adaptive reasoning for multi-herb compound-target-disease networks.",
        ),
        "deepseek-v4-pro": (
            36.0,
            "1.6T MoE quantitative reasoning for systems pharmacology and Jun-Chen-Zuo-Shi synergy.",
        ),
        "gpt-6-astra": (
            35.0,
            "Maximum frontier reasoning depth across molecular biology and clinical trials.",
        ),
        "claude-opus-5-5": (
            33.0,
            "Rigorous multi-database synthesis (TCMSP, BATMAN-TCM, ChEMBL, UniProt).",
        ),
    },
    "clinical_safety": {
        "claude-opus-5-5": (
            40.0,
            "Conservative grounded synthesis for CYP450 herb-drug interactions & 十八反 safety.",
        ),
        "claude-fable-5-2": (
            38.0,
            "Deep multi-step safety verification, hepatotoxicity/nephrotoxicity & pregnancy screening.",
        ),
        "gpt-6-astra": (
            36.0,
            "Frontier biomedical safety review across polypharmacy and contraindication guidelines.",
        ),
        "gpt-rosalind-research": (
            35.0,
            "Mechanistic toxicology, metabolic enzyme inhibition, and DILI risk evaluation.",
        ),
        "glm-5.3": (
            31.0,
            "Chinese Pharmacopoeia (中国药典) dosage ceilings and toxic herb processing (炮制减毒) rules.",
        ),
    },
    "bilingual_synthesis": {
        "qwen3.8-max": (
            40.0,
            "SOTA classical Chinese (文言文) philology paired with modern biomedical terminology.",
        ),
        "deepseek-v4-pro": (
            38.0,
            "1.6T MoE bilingual medical fluency bridging syndrome differentiation & molecular targets.",
        ),
        "kimi-k3.1-pro": (
            36.0,
            "1M-context cross-canon synthesis across classical treatises and English clinical literature.",
        ),
        "glm-5.3": (
            34.0,
            "Authoritative Chinese TCM syndrome differentiation (辨证论治) and WHO ICD-11 alignment.",
        ),
        "claude-opus-5-5": (
            32.0,
            "Publication-grade English/Chinese integrative medicine manuscript synthesis.",
        ),
    },
    "offline_local": {
        "ollama/medgemma:27b": (
            45.0,
            "Local multimodal medical imaging & clinical decision support with zero cloud data egress.",
        ),
        "ollama/huatuogpt-vision:7b": (
            43.0,
            "Specialized local Chinese TCM & tongue diagnosis vision-language model via Ollama.",
        ),
        "ollama/qwen3:32b": (
            41.0,
            "Private on-premise bilingual TCM syndrome & pharmacology reasoning via Ollama.",
        ),
        "qwen3.8-27b": (
            24.0,
            "Open-weight 27B agentic model deployable on local/self-hosted GPU endpoints.",
        ),
        "together/deepseek-v4-pro": (
            20.0,
            "Open-weight MoE fallback when scaling beyond local VRAM.",
        ),
    },
}

_IMPLICIT_TASK_MODALITIES: dict[str, tuple[str, ...]] = {
    "tongue_vision": ("vision",),
    "herb_identification": ("vision",),
    "classical_ocr": ("vision",),
}

_TIER_BASE_SCORES: dict[str, float] = {
    "frontier": 62.0,
    "specialized": 60.0,
    "flagship": 58.0,
    "balanced": 52.0,
    "fast": 48.0,
    "local": 50.0,
}


def recommend_models_for_task(
    task: str = "general",
    modalities: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return top 5 ranked SOTA models from MODEL_CATALOG for a TCM task and modality set."""
    from tcm.models.llm import MODEL_CATALOG

    norm_task = (task or "general").strip().lower()
    if norm_task not in _TASK_MODEL_PRIORITIES:
        norm_task = "general"

    required_mods: list[str]
    if modalities is not None:
        required_mods = [m.strip().lower() for m in modalities if m and m.strip()]
    else:
        required_mods = list(_IMPLICIT_TASK_MODALITIES.get(norm_task, ()))

    task_bonuses = _TASK_MODEL_PRIORITIES[norm_task]
    candidates: list[dict[str, Any]] = []

    for model in MODEL_CATALOG.values():
        if required_mods and not all(model.supports_modality(req) for req in required_mods):
            continue

        score = _TIER_BASE_SCORES.get(model.tier, 50.0)
        if norm_task == "offline_local":
            if model.tier == "local" or model.provider == "ollama":
                score += 25.0
            else:
                score -= 20.0

        # Context window & thinking bonuses
        if model.context_window >= 1_000_000:
            score += 4.0
        if model.supports_modality("thinking") and norm_task in {
            "network_pharmacology",
            "clinical_safety",
            "bilingual_synthesis",
            "general",
        }:
            score += 3.0
        if norm_task in model.tcm_strengths:
            score += 5.0

        reason: str
        if model.id in task_bonuses:
            bonus, reason = task_bonuses[model.id]
            score += bonus
        else:
            reason = model.description or f"{model.display_name} ({model.tier} {model.provider} model)"

        candidates.append({
            "id": model.id,
            "provider": model.provider,
            "display_name": model.display_name,
            "modalities": list(model.modalities),
            "tier": model.tier,
            "context_window": model.context_window,
            "score": round(min(100.0, max(0.0, score)), 1),
            "reason": reason,
        })

    candidates.sort(key=lambda item: (-item["score"], item["id"]))
    return candidates[:5]
