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


