from pathlib import Path
import json


def test_real_save_generated_fields_present():
    """Validate that the generated parse_results.json contains expected fields and non-null values."""
    results_path = Path("test_data/analysis_results/parse_results.json")
    assert results_path.exists(), "parse_results.json not found; run real save parsing test first"

    data = json.loads(results_path.read_text())

    # Top-level checks
    assert data.get("success") is True
    assert isinstance(data.get("warnings"), list)
    assert isinstance(data.get("save_summary"), dict)
    entities = data.get("entities")
    assert isinstance(entities, dict)

    # Duplicants checks (entities contain raw minion list for backward compatibility)
    dups = entities.get("duplicants")
    assert isinstance(dups, list) and len(dups) > 0

    for d in dups:
        # required basic fields
        assert all(k in d for k in ("x", "y", "z"))
        assert isinstance(d["x"], (int, float))
        assert isinstance(d["y"], (int, float))
        assert isinstance(d["z"], (int, float))

        # identity
        assert "name" in d and isinstance(d["name"], str) and len(d["name"]) > 0
        assert "gender" in d and d["gender"] in ("MALE", "FEMALE", "NB")
        assert "arrival_time" in d and isinstance(d["arrival_time"], int)

        # job defaulted when unknown
        assert "job" in d and isinstance(d["job"], str) and len(d["job"]) > 0

        # vitals block present with numeric values in sensible ranges
        vitals = d.get("vitals")
        assert isinstance(vitals, dict)
        assert "calories" in vitals and isinstance(vitals["calories"], (int, float)) and vitals["calories"] >= 0
        assert "stamina" in vitals and isinstance(vitals["stamina"], (int, float)) and 0 <= vitals["stamina"] <= 100
        assert "stress" in vitals and isinstance(vitals["stress"], (int, float)) and 0 <= vitals["stress"] <= 100
        # new vitals extensions exist
        for key in ("decor", "temperature", "breath", "bladder", "immune_level", "toxicity", "radiation_balance"):
            assert key in vitals


