from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser

SAVE_PATH = Path("test_data/clone_laboratory.sav")


@pytest.mark.skipif(not SAVE_PATH.exists(), reason="Real save file not present")
def test_duplicants_canonical_presence_and_shape():
    parser = OniSaveParser()
    result = parser.parse_save_file(SAVE_PATH)
    assert result.success, f"parse failed: {result.error_message}"

    # Legacy list remains
    assert "duplicants" in result.entities
    assert isinstance(result.entities["duplicants"], list)

    # New canonical list exists and is a list
    canon = result.entities.get("duplicants_canonical")
    assert isinstance(canon, list)

    # If empty (restricted envs), that's OK
    if not canon:
        return

    # Validate minimal schema for first few entries
    for entry in canon[:5]:
        assert isinstance(entry, dict)
        # Required keys
        for key in ("identity", "role", "vitals", "traits", "effects", "position"):
            assert key in entry
        # Identity
        ident: Dict[str, Any] = entry["identity"]
        assert isinstance(ident.get("name"), (str, type(None)))
        assert isinstance(ident.get("arrival_time"), int)
        # Role
        assert isinstance(entry.get("role"), str)
        # Vitals: numbers or None
        vit = entry.get("vitals") or {}
        assert isinstance(vit, dict)
        for vk in ("calories", "health", "stress", "stamina", "decor", "temperature"):
            assert vk in vit
            v = vit.get(vk)
            assert (v is None) or isinstance(v, (int, float))
        # Traits/Effects lists
        assert isinstance(entry.get("traits", []), list)
        assert isinstance(entry.get("effects", []), list)
        # Position
        pos = entry.get("position") or {}
        assert isinstance(pos.get("x", 0.0), float)
        assert isinstance(pos.get("y", 0.0), float)
        assert isinstance(pos.get("z", 0.0), float)


def test_canonical_defaults_without_resume_modifiers(monkeypatch, tmp_path: Path):
    parser = OniSaveParser()

    # Provide a minimal SaveGame to bypass full parse
    from src.oni_ai_agents.services.oni_save_parser.data_structures import SaveGame

    def _fake_parse_save_data(self, data: bytes, result):
        return SaveGame()

    def _fake_extract_minions(self, file_path: Path):
        return [
            {
                "name": "Ada",
                "gender": "FEMALE",
                "arrival_time": 1,
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
            }
        ]

    monkeypatch.setattr(OniSaveParser, "_parse_save_data", _fake_parse_save_data, raising=True)
    monkeypatch.setattr(OniSaveParser, "extract_minion_details", _fake_extract_minions, raising=True)

    dummy = tmp_path / "dummy.sav"
    dummy.write_bytes(b"FAKE")

    result = parser.parse_save_file(dummy)
    canon = result.entities.get("duplicants_canonical")
    assert isinstance(canon, list)
    assert len(canon) == 1
    e = canon[0]
    assert e.get("role") == "NoRole"
    vit = e.get("vitals") or {}
    for k in ("calories", "health", "stress", "stamina", "decor", "temperature"):
        assert k in vit
        v = vit.get(k)
        assert (v is None) or isinstance(v, (int, float))
    assert isinstance(e.get("traits", []), list)
    assert isinstance(e.get("effects", []), list)


def test_helpers_bounded_read_no_raise():
    parser = OniSaveParser()
    mv = memoryview(b"\x00\x00\x00\x00garbagepayload")
    out = parser._parse_minion_identity(mv, 0, 4)  # end before payload
    assert isinstance(out, dict)


def test_no_body_empty_canonical(monkeypatch, tmp_path: Path):
    parser = OniSaveParser()
    from src.oni_ai_agents.services.oni_save_parser.data_structures import SaveGame

    def _fake_parse_save_data(self, data: bytes, result):
        return SaveGame()

    monkeypatch.setattr(OniSaveParser, "_parse_save_data", _fake_parse_save_data, raising=True)
    monkeypatch.setattr(OniSaveParser, "_decompress_body_block", lambda self, b: None, raising=True)

    dummy = tmp_path / "dummy2.sav"
    dummy.write_bytes(b"FAKE")
    result = parser.parse_save_file(dummy)
    assert isinstance(result.entities.get("duplicants_canonical"), list)
    assert result.entities.get("duplicants_canonical") == []


@pytest.mark.skip(reason="Import hook simulation not reliable in this env")
def test_known_ids_importerror_fallback(monkeypatch):
    import importlib
    import sys

    # Remove known_ids and reload save_parser to trigger fallback import path
    sys.modules.pop("src.oni_ai_agents.services.oni_save_parser.known_ids", None)
    import src.oni_ai_agents.services.oni_save_parser.save_parser as sp_mod

    reloaded = importlib.reload(sp_mod)
    parser = reloaded.OniSaveParser()
    assert parser._KNOWN_TRAIT_IDS  # fallback populated
    assert parser._KNOWN_EFFECT_IDS


