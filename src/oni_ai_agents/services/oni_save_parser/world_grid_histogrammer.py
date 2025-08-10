"""
World Grid Histogrammer (Scaffold)

Phase 1 implementation that provides a stable API and placeholders.

Future phases will parse `sim_blob` to compute real histograms for elements,
temperatures, diseases, and radiation, and derive breathable percentage.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List, Tuple


def compute_histograms(sim_blob: bytes, width: int, height: int) -> Dict[str, Dict[str, int]]:
    """
    Compute world grid histograms.

    Phase 1: return empty histograms with stable keys. Later phases will
    decode `sim_blob` and populate counts.

    Args:
        sim_blob: Raw simulation data bytes (may be empty in early phases)
        width: World width in cells
        height: World height in cells

    Returns:
        Dict with keys: elements, temperatures, diseases, radiation
    """
    # Placeholders to keep a stable contract for downstream consumers.
    return {
        "elements": {},
        "temperatures": {},
        "diseases": {},
        "radiation": {},
    }


def compute_breathable_percent(histograms: Dict[str, Dict[str, int]], total_cells: int) -> Optional[float]:
    """
    Compute breathable percent from histograms when available.

    Phase 1: returns None. In later phases, derive from element distribution
    and per-cell mass thresholds.
    """
    _ = (histograms, total_cells)
    return None


def compute_structures_histogram(object_group_counts: Dict[str, int], top_n: int = 50) -> Dict[str, int]:
    """
    Build a histogram of structures (object groups), keeping only top_n entries
    and aggregating the rest into an 'other' bucket.
    """
    if not object_group_counts:
        return {}
    items = sorted(object_group_counts.items(), key=lambda kv: kv[1], reverse=True)
    top = items[:max(0, top_n)]
    hist: Dict[str, int] = {k: int(v) for k, v in top}
    other = sum(v for _k, v in items[len(top):])
    if other:
        hist["other"] = int(other)
    return hist


def _scan_best_float32(buf_mv, start: int, end: int, min_val: float, max_val: float) -> Optional[float]:
    import struct, math
    best = None
    p = start
    while p + 4 <= end:
        try:
            v = struct.unpack_from('<f', buf_mv, p)[0]
            if math.isfinite(v) and min_val <= v <= max_val:
                best = float(v)
        except Exception:
            pass
        p += 1
    return best


def compute_temperature_histogram_from_body(body: bytes, bucket_edges: Optional[List[float]] = None) -> Dict[str, int]:
    """
    Compute a temperature histogram by scanning KSAV object behaviors and
    extracting plausible temperature floats.

    This is a best-effort approach until per-cell sim arrays are decoded.

    Args:
        body: Decompressed save body containing KSAV structure
        bucket_edges: Sorted list of Kelvin thresholds for buckets.

    Returns:
        Dict mapping bucket label (e.g., '280-300K') to counts.
    """
    import struct
    if not body:
        return {}

    if bucket_edges is None:
        # Kelvin buckets (approx): <240, 240-280, 280-300, 300-320, 320-360, >360
        bucket_edges = [240.0, 280.0, 300.0, 320.0, 360.0]

    def bucket_label(k: float) -> str:
        prev = None
        for edge in bucket_edges:
            if k < edge:
                return (f"<{edge:.0f}K" if prev is None else f"{prev:.0f}-{edge:.0f}K")
            prev = edge
        return f">{bucket_edges[-1]:.0f}K"

    mv = memoryview(body)
    pos = body.find(b'KSAV')
    if pos == -1:
        return {}
    p = pos + 4
    if p + 12 > len(body):
        return {}
    try:
        _maj = struct.unpack_from('<i', mv, p)[0]; p += 4
        _min = struct.unpack_from('<i', mv, p)[0]; p += 4
        group_count = struct.unpack_from('<i', mv, p)[0]; p += 4
    except Exception:
        return {}

    counts: Dict[str, int] = {}
    for _ in range(max(0, group_count)):
        if p + 4 > len(body):
            break
        try:
            name_len = struct.unpack_from('<i', mv, p)[0]; p += 4
            if name_len < 0 or p + name_len > len(body):
                break
            # group name not used; skip
            p += name_len
            if p + 8 > len(body):
                break
            instance_count = struct.unpack_from('<i', mv, p)[0]; p += 4
            data_len = struct.unpack_from('<i', mv, p)[0]; p += 4
            group_start = p
            for _i in range(max(0, instance_count)):
                if p + 12 + 16 + 12 + 1 + 4 > len(body):
                    break
                # Skip transform
                p += 12 + 16 + 12 + 1
                # Behavior count
                try:
                    bcount = struct.unpack_from('<i', mv, p)[0]; p += 4
                except Exception:
                    break
                q = p
                for _b in range(max(0, bcount)):
                    if q + 4 > len(body):
                        break
                    blen = struct.unpack_from('<i', mv, q)[0]; q += 4
                    if blen < 0 or q + blen > len(body):
                        break
                    bname = bytes(mv[q:q+blen]).decode('utf-8', errors='ignore'); q += blen
                    if q + 4 > len(body):
                        break
                    plen = struct.unpack_from('<i', mv, q)[0]; q += 4
                    bstart = q
                    bend = q + max(0, plen)
                    if bend > len(body):
                        break
                    # Heuristic: scan payload for plausible Kelvin temperatures
                    # Only consider some behaviors to reduce noise
                    if bname in ("PrimaryElement", "Modifiers", "Building", "SimCellOccupier"):
                        t = _scan_best_float32(mv, bstart, bend, 100.0, 1000.0)
                        if t is not None:
                            lbl = bucket_label(t)
                            counts[lbl] = counts.get(lbl, 0) + 1
                    q = bend
                p = q
            # Skip remainder of group payload
            p = group_start + max(0, data_len)
            if p > len(body):
                break
        except Exception:
            break

    return counts


