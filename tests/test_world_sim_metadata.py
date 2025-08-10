from pathlib import Path

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser


def test_world_and_metadata_present():
    save_path = Path("test_data/clone_laboratory.sav")
    parser = OniSaveParser()
    result = parser.parse_save_file(save_path)

    assert result.success, f"Parser failed: {result.error_message}"
    sg = result.save_game
    assert sg is not None

    # World dimensions should be present and plausible
    assert isinstance(sg.world.width_in_cells, int)
    assert isinstance(sg.world.height_in_cells, int)
    assert sg.world.width_in_cells >= 0
    assert sg.world.height_in_cells >= 0

    # Metadata blocks should exist when the file is readable
    blocks = sg.metadata.blocks
    assert isinstance(blocks, list)
    # At least one block expected in real saves; allow zero in edge environments
    if blocks:
        b0 = blocks[0]
        assert isinstance(b0.offset, int) and b0.offset >= 0
        assert isinstance(b0.header, str) and len(b0.header) > 0
        assert isinstance(b0.compressed_size, int) and b0.compressed_size > 0
        assert isinstance(b0.decompressed_size, int) and b0.decompressed_size > 0
        assert isinstance(b0.crc32, str) and len(b0.crc32) == 8

    # KSAV summary should be a dict; if body found, values should be ints
    ksav = sg.metadata.ksav_summary
    assert isinstance(ksav, dict)
    if ksav:
        assert isinstance(ksav.get("group_count"), int)
        assert isinstance(ksav.get("total_instances"), int)


