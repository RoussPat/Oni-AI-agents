"""
KSAV index helpers.

Count groups and instances from a decompressed KSAV body and provide summaries.
"""

from __future__ import annotations

from typing import Dict


class KSAVGroupCounter:
    """Count KSAV groups and instances from a decompressed body."""

    def extract_object_group_counts(self, body: bytes) -> Dict[str, int]:
        import struct

        counts: Dict[str, int] = {}
        if not body:
            return counts
        mv = memoryview(body)
        ksav_pos = body.find(b"KSAV")
        if ksav_pos == -1:
            return counts
        p = ksav_pos + 4
        if p + 12 > len(body):
            return counts
        try:
            _major = struct.unpack_from("<i", mv, p)[0]
            p += 4
            _minor = struct.unpack_from("<i", mv, p)[0]
            p += 4
            group_count = struct.unpack_from("<i", mv, p)[0]
            p += 4
        except Exception:
            return counts
        if group_count < 0:
            return counts
        for _ in range(group_count):
            if p + 4 > len(body):
                break
            name_len = struct.unpack_from("<i", mv, p)[0]
            p += 4
            if name_len < 0 or p + name_len > len(body):
                break
            try:
                name = bytes(mv[p : p + name_len]).decode("utf-8", errors="ignore")
            except Exception:
                name = ""
            p += name_len
            if p + 8 > len(body):
                break
            instance_count = struct.unpack_from("<i", mv, p)[0]
            p += 4
            payload_len = struct.unpack_from("<i", mv, p)[0]
            p += 4
            counts[name] = int(instance_count)
            if payload_len < 0:
                break
            p += payload_len
            if p > len(body):
                break
        return counts

    def summarize(self, body: bytes) -> Dict[str, int]:
        import struct

        summary = {"group_count": 0, "total_instances": 0}
        if not body:
            return summary
        mv = memoryview(body)
        pos = body.find(b"KSAV")
        if pos == -1 or pos + 12 > len(body):
            return summary
        p = pos + 4
        _maj = struct.unpack_from("<i", mv, p)[0]
        p += 4
        _min = struct.unpack_from("<i", mv, p)[0]
        p += 4
        group_count = struct.unpack_from("<i", mv, p)[0]
        p += 4
        total_instances = 0
        for _ in range(max(0, group_count)):
            if p + 4 > len(body):
                break
            name_len = struct.unpack_from("<i", mv, p)[0]
            p += 4
            if name_len < 0 or p + name_len > len(body):
                break
            p += name_len
            if p + 8 > len(body):
                break
            instance_count = struct.unpack_from("<i", mv, p)[0]
            p += 4
            data_length = struct.unpack_from("<i", mv, p)[0]
            p += 4
            total_instances += int(instance_count)
            p = p + max(0, data_length)
            if p > len(body):
                break
        summary["group_count"] = int(group_count)
        summary["total_instances"] = int(total_instances)
        return summary


