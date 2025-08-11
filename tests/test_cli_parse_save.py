#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

SAVE = Path("test_data/clone_laboratory.sav")


@pytest.mark.skipif(not SAVE.exists(), reason="Sample save missing")
def test_cli_emits_required_sections(tmp_path: Path):
    cmd = [
        "python",
        "scripts/parse_save.py",
        str(SAVE),
        "--out",
        "-",
        "--pretty",
        "--quiet",
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert proc.stdout.strip()
    data = json.loads(proc.stdout)
    # Required top-level keys
    for key in ("metadata", "duplicants", "world_grid_summary", "object_group_counts"):
        assert key in data
    # Quick sanity on sub-keys
    assert isinstance(data["duplicants"].get("list"), list)
    assert isinstance(data["metadata"].get("version"), str)



