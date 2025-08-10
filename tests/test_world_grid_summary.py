from pathlib import Path

from src.oni_ai_agents.services.save_file_data_extractor import SaveFileDataExtractor


def test_world_grid_summary_exists_and_has_placeholders():
    save_path = Path("test_data/clone_laboratory.sav")
    extractor = SaveFileDataExtractor()

    data = extractor.parse_save_file(save_path)
    sections = data.sections

    assert "world_grid_summary" in sections, "world_grid_summary section missing"
    wgs = sections["world_grid_summary"]

    # Required keys
    for key in ("width", "height", "cell_count", "histograms", "breathable_percent", "warnings"):
        assert key in wgs, f"Missing key in world_grid_summary: {key}"

    width = wgs["width"]
    height = wgs["height"]
    cell_count = wgs["cell_count"]
    hist = wgs["histograms"]

    # Types
    assert isinstance(width, int)
    assert isinstance(height, int)
    assert isinstance(cell_count, int)
    assert isinstance(hist, dict)

    # Contract for placeholders (Phase 1)
    assert set(hist.keys()) == {"elements", "temperatures", "diseases", "radiation"}
    assert isinstance(hist["elements"], dict)
    assert isinstance(hist["temperatures"], dict)
    assert isinstance(hist["diseases"], dict)
    assert isinstance(hist["radiation"], dict)

    # Cell count logic
    if width > 0 and height > 0:
        assert cell_count == width * height
    else:
        assert cell_count == 0

    # Breathable percent is placeholder for now
    assert wgs["breathable_percent"] is None


