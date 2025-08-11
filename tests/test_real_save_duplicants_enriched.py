#!/usr/bin/env python3
"""
Integration tests for enriched Duplicants data parsed from a real ONI save.

Validates that the `SaveFileDataExtractor` exposes a `duplicants.list` with
identity, role, extended vitals, and normalized aptitudes.
"""

from pathlib import Path
from typing import Dict

import pytest

from src.oni_ai_agents.services.save_file_data_extractor import SaveFileDataExtractor

SAVE_PATH = Path("test_data/clone_laboratory.sav")


@pytest.mark.skipif(not SAVE_PATH.exists(), reason="Real save file not present")
def test_enriched_duplicants_section_contract():
    extractor = SaveFileDataExtractor()
    data = extractor.parse_save_file(SAVE_PATH)

    dups_section = data.sections.get("duplicants")
    assert isinstance(dups_section, dict)
    assert isinstance(dups_section.get("count"), int)

    dlist = dups_section.get("list")
    assert isinstance(dlist, list)
    assert len(dlist) == dups_section["count"]

    # Allowed aptitude groups and max levels based on game tiers
    max_level: Dict[str, int] = {
        'Mining': 3, 'Building': 3, 'Farming': 3, 'Ranching': 2,
        'Research': 3, 'Cooking': 2, 'Art': 3, 'Hauling': 2,
        'Suits': 1, 'Technicals': 2, 'Engineering': 1,
        'Basekeeping': 2, 'Management': 2, 'MedicalAid': 3,
    }

    saw_non_default_role = False

    for e in dlist:
        # Identity
        ident = e.get("identity") or {}
        assert isinstance(ident.get("name"), str) and ident["name"].strip()
        assert ident.get("arrival_time") is not None

        # Role
        role = e.get("role")
        assert isinstance(role, str)
        if role and role != "NoRole":
            saw_non_default_role = True

        # Vitals
        vit = e.get("vitals") or {}
        for key in ("calories", "stamina", "stress", "decor", "temperature"):
            assert key in vit

        # Aptitudes
        ap = e.get("aptitudes") or {}
        assert isinstance(ap, dict)
        for g, lvl in ap.items():
            assert g in max_level, f"Unexpected aptitude group: {g}"
            assert isinstance(lvl, int) and 1 <= lvl <= max_level[g], f"Invalid level for {g}: {lvl}"

        # Traits/Effects keys present (may be empty lists)
        assert isinstance(e.get("traits", []), list)
        assert isinstance(e.get("effects", []), list)

    assert saw_non_default_role, "Expected at least one duplicant with a non-default role"


