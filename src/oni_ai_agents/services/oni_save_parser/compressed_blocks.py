"""
Compressed block utilities for ONI save streams.

Provides helpers to locate and decompress zlib blocks after the JSON header.
"""

from __future__ import annotations

from typing import Generator, Optional, Tuple


class CompressedBlocksScanner:
    """Scan ONI save bytes for compressed blocks and provide decompression helpers."""

    def parse_header_raw(self, data: bytes) -> Tuple[int, bool]:
        """Return (offset_after_header_json, is_compressed) without altering state."""
        import struct

        p = 0
        mv = memoryview(data)
        if len(data) < 12:
            return 0, False
        struct.unpack_from("<I", mv, p)[0]
        p += 4
        header_size = struct.unpack_from("<I", mv, p)[0]
        p += 4
        header_version = struct.unpack_from("<I", mv, p)[0]
        p += 4
        is_compressed = False
        if header_version >= 1:
            if p + 4 > len(data):
                return 0, False
            is_compressed = struct.unpack_from("<I", mv, p)[0] != 0
            p += 4
        p_end = p + header_size
        if p_end > len(data):
            return 0, is_compressed
        return p_end, is_compressed

    def decompress_body_block(self, data: bytes) -> Optional[bytes]:
        """Find and decompress the main save body block (zlib) by scanning after header JSON."""
        import zlib

        start_after_header, _ = self.parse_header_raw(data)
        search = data[start_after_header:]
        candidates = []
        for sig in (b"\x78\x9c", b"\x78\xda", b"\x78\x01"):
            idx = 0
            while True:
                pos = search.find(sig, idx)
                if pos == -1:
                    break
                candidates.append(start_after_header + pos)
                idx = pos + 1
        for pos in sorted(set(candidates)):
            try:
                decompressed = zlib.decompress(data[pos:])
                if b"KSAV" in decompressed:
                    return decompressed
            except Exception:
                continue
        return None

    def iter_decompressed_blocks(self, data: bytes) -> Generator[bytes, None, None]:
        """Yield all successfully decompressed zlib blocks after header JSON."""
        import zlib

        start_after_header, _ = self.parse_header_raw(data)
        search = data[start_after_header:]
        seen = set()
        for sig in (b"\x78\x9c", b"\x78\xda", b"\x78\x01"):
            idx = 0
            while True:
                pos = search.find(sig, idx)
                if pos == -1:
                    break
                abs_pos = start_after_header + pos
                if abs_pos in seen:
                    idx = pos + 1
                    continue
                seen.add(abs_pos)
                try:
                    decompressed = zlib.decompress(data[abs_pos:])
                    yield decompressed
                except Exception:
                    pass
                idx = pos + 1


