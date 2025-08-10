"""
Metadata builder for ONI saves.

Computes compressed block diagnostics and KSAV summaries.
"""

from __future__ import annotations

from typing import Optional

from .compressed_blocks import CompressedBlocksScanner
from .data_structures import SaveBlockInfo, SaveGameMetadata
from .ksav_index import KSAVGroupCounter


class MetadataBuilder:
    """Build `SaveGameMetadata` using scanners and counters."""

    def __init__(self) -> None:
        self._blocks = CompressedBlocksScanner()
        self._ksav = KSAVGroupCounter()

    def build(self, file_bytes: bytes, cached_body: Optional[bytes]) -> SaveGameMetadata:
        import binascii
        import zlib

        metadata = SaveGameMetadata()
        # Maintain default keys expected by current consumers
        metadata.ksav_summary = {"group_count": 0, "total_instances": 0}
        if not file_bytes:
            return metadata

        start_after_header, _ = self._blocks.parse_header_raw(file_bytes)
        search = file_bytes[start_after_header:]
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
                header_preview = file_bytes[abs_pos : abs_pos + 10].hex()
                try:
                    decompressed = zlib.decompress(file_bytes[abs_pos:])
                    crc_hex = format(binascii.crc32(decompressed) & 0xFFFFFFFF, "08x")
                    comp_size = len(file_bytes) - abs_pos
                    decomp_size = len(decompressed)
                    metadata.blocks.append(
                        SaveBlockInfo(
                            offset=abs_pos,
                            header=header_preview,
                            compressed_size=comp_size,
                            decompressed_size=decomp_size,
                            crc32=crc_hex,
                        )
                    )
                except Exception:
                    pass
                idx = pos + 1

        body = cached_body or self._blocks.decompress_body_block(file_bytes) or b""
        if body:
            metadata.ksav_summary = self._ksav.summarize(body)
        return metadata


