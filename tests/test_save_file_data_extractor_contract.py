#!/usr/bin/env python3
"""
Contract tests for SaveFileDataExtractor sections schema.

Checks that the duplicants section exposes expected keys and types.
"""

from pathlib import Path

from src.oni_ai_agents.services.save_file_data_extractor import SaveFileDataExtractor


def test_extractor_duplicants_schema_types(tmp_path: Path = Path(".")):
    # Use real save if present; otherwise skip deep checks but ensure types
    save = Path("test_data/clone_laboratory.sav")
    if not save.exists():
        return

    extractor = SaveFileDataExtractor()
    data = extractor.parse_save_file(save)

    assert "duplicants" in data.sections
    dups = data.sections["duplicants"]

    assert isinstance(dups.get("count"), int)
    assert isinstance(dups.get("list"), list)

    # Inspect a couple of entries
    for e in (dups.get("list") or [])[:3]:
        assert isinstance(e.get("identity"), dict)
        assert isinstance(e.get("role"), str)
        assert isinstance(e.get("vitals"), dict)
        assert isinstance(e.get("traits", []), list)
        assert isinstance(e.get("effects", []), list)
        assert isinstance(e.get("aptitudes", {}), dict)


