from pathlib import Path

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser


def test_object_group_counts_present_from_real_save():
    save_path = Path("test_data/clone_laboratory.sav")
    assert save_path.exists(), "Real save file missing under test_data/."

    parser = OniSaveParser()
    result = parser.parse_save_file(save_path)

    assert result.success, f"Parser failed: {result.error_message}"
    ogc = result.entities.get("object_group_counts", {})

    # Expect non-empty counts when KSAV is present in real save
    assert isinstance(ogc, dict)
    assert len(ogc) > 0, "object_group_counts should not be empty for real save"


def test_object_group_counts_no_ksav_returns_empty():
    parser = OniSaveParser()
    # Provide a minimal body without 'KSAV'
    empty_counts = parser._extract_object_group_counts_from_body(b"NOT_KSAV.....")
    assert empty_counts == {}


def test_object_group_counts_truncated_payload_returns_empty():
    parser = OniSaveParser()
    # Build a truncated KSAV header: 'KSAV' + major + minor + group_count=1, then cut off
    import struct
    body = bytearray()
    body.extend(b"KSAV")
    body.extend(struct.pack('<i', 7))  # major
    body.extend(struct.pack('<i', 36))  # minor
    body.extend(struct.pack('<i', 1))  # 1 group, but no group data
    counts = parser._extract_object_group_counts_from_body(bytes(body))
    assert counts == {}

