#!/usr/bin/env python3
"""Deliver entry.png to the output directory, byte for byte.

The PNG sitting beside this file is validated first (signature, IHDR
dimensions, total size, and every chunk's CRC).  If anything fails the
check the program exits non-zero and writes nothing.  After a successful
write the output is read back and compared with the source so a partial
or corrupted copy can never pass silently.
"""

import os
import struct
import sys
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_DIMENSION = 1024
MAX_BYTES = 1_048_576


def fail(message: str) -> "SystemExit":
    print(f"error: {message}", file=sys.stderr)
    return SystemExit(1)


def validate_png(data: bytes) -> None:
    if len(data) > MAX_BYTES:
        raise ValueError(f"file is {len(data)} bytes, over the {MAX_BYTES} byte limit")
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("missing PNG signature")

    pos = len(PNG_SIGNATURE)
    seen_ihdr = False
    seen_iend = False
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated chunk header")
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        crc_bytes = data[pos + 8 + length : pos + 12 + length]
        if len(chunk_data) != length or len(crc_bytes) != 4:
            raise ValueError("truncated chunk body")
        (stored_crc,) = struct.unpack(">I", crc_bytes)
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ValueError(f"CRC mismatch in chunk {chunk_type!r}")

        if not seen_ihdr:
            if chunk_type != b"IHDR":
                raise ValueError("first chunk is not IHDR")
            width, height = struct.unpack(">II", chunk_data[0:8])
            if width == 0 or height == 0:
                raise ValueError("IHDR has a zero dimension")
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise ValueError(
                    f"IHDR is {width}x{height}, over the {MAX_DIMENSION}px limit"
                )
            seen_ihdr = True
        if chunk_type == b"IEND":
            seen_iend = True
            pos += 12 + length
            break
        pos += 12 + length

    if not seen_ihdr:
        raise ValueError("no IHDR chunk found")
    if not seen_iend:
        raise ValueError("no IEND chunk found")


def main() -> int:
    source = Path(__file__).resolve().parent / "entry.png"
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise fail(f"cannot read {source}: {exc}")

    try:
        validate_png(data)
    except ValueError as exc:
        raise fail(f"entry.png is not a valid deliverable: {exc}")

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "entry.png"
        target.write_bytes(data)
        written = target.read_bytes()
    except OSError as exc:
        raise fail(f"cannot write output: {exc}")

    if written != data:
        raise fail("output read-back does not match the source bytes")

    print(f"wrote {target} ({len(data)} bytes, verified identical)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
