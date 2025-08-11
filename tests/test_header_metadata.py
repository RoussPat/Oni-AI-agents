import os
from pathlib import Path

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser


def test_header_and_metadata_completeness():
    save_path = Path("test_data/clone_laboratory.sav")
    parser = OniSaveParser()
    result = parser.parse_save_file(save_path)

    assert result.success, f"Parser failed: {result.error_message}"
    sg = result.save_game
    assert sg is not None

    # Header core fields
    assert isinstance(sg.header.num_cycles, int) and sg.header.num_cycles >= 0
    assert isinstance(sg.header.num_duplicants, int) and sg.header.num_duplicants >= 0
    assert isinstance(sg.header.cluster_id, str)

    # DLC / mods flags (present and normalized)
    assert isinstance(sg.header.has_dlc, bool)
    assert isinstance(sg.header.dlc_ids, list)
    assert isinstance(sg.header.has_mods, bool)

    # Version range acceptance
    assert sg.version.major == 7
    assert 11 <= sg.version.minor <= 36

    # KSAV summary keys when present
    ksav = sg.metadata.ksav_summary
    assert isinstance(ksav, dict)
    # Keys should always exist; integers even when KSAV not found
    assert "group_count" in ksav and isinstance(ksav["group_count"], int)
    assert "total_instances" in ksav and isinstance(ksav["total_instances"], int)


def test_version_fallback_and_warning_when_header_missing_versions(monkeypatch):
    """If header lacks version fields, parser should fallback to KSAV and warn."""
    save_path = Path("test_data/clone_laboratory.sav")
    parser = OniSaveParser()

    # Monkeypatch the internal header parser to strip version fields from game_info
    orig_parse_header = parser._parse_header

    def _wrapped(reader, result):
        header = orig_parse_header(reader, result)
        # Remove explicit version fields to force fallback path
        header.game_info.pop("saveMajorVersion", None)
        header.game_info.pop("saveMinorVersion", None)
        return header

    monkeypatch.setattr(parser, "_parse_header", _wrapped)

    # In FAST_TESTS mode, run the real parse for this test only to exercise fallback
    prev_fast = os.getenv("FAST_TESTS")
    try:
        if prev_fast == "1":
            os.environ["FAST_TESTS"] = "0"
        result = parser.parse_save_file(save_path)
    finally:
        if prev_fast is not None:
            os.environ["FAST_TESTS"] = prev_fast
        else:
            os.environ.pop("FAST_TESTS", None)
    assert result.success
    sg = result.save_game
    assert sg is not None
    # Fallback still constrains major to 7, minor within known range
    assert sg.version.major == 7
    assert 11 <= sg.version.minor <= 36
    # Warning should be present
    assert any("KSAV fallback" in w for w in result.warnings)
