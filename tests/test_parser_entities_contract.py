from pathlib import Path

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser


def test_entities_contract_and_world_grid_summary():
    save_path = Path("test_data/clone_laboratory.sav")
    parser = OniSaveParser()
    result = parser.parse_save_file(save_path)

    assert result.success, result.error_message
    # object_group_counts may be empty if KSAV missing, but in real test save it should exist
    assert isinstance(result.entities.get("object_group_counts", {}), dict)

    wgs = result.entities.get("world_grid_summary")
    assert isinstance(wgs, dict)
    for key in ("width", "height", "cell_count", "histograms", "breathable_percent", "warnings"):
        assert key in wgs


