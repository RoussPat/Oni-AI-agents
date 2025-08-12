"""
Header reader for ONI save files.

Parses the JSON header region and extracts key metadata and version info.
"""

from __future__ import annotations

from typing import Any

from .binary_reader import BinaryReader
from .data_structures import SaveGameHeader


class SaveHeaderReader:
    """Parse the ONI save header JSON and normalize fields."""

    def parse_header(self, reader: BinaryReader, result) -> SaveGameHeader:
        import json

        header = SaveGameHeader()
        build_version = reader.read_uint32()
        header_size = reader.read_uint32()
        header_version = reader.read_uint32()

        is_compressed = False
        if header_version >= 1:
            is_compressed = bool(reader.read_uint32())

        info_bytes = reader.read_bytes(header_size)
        info_str = info_bytes.decode("utf-8")
        game_info = json.loads(info_str)

        header.game_info = game_info

        header.cluster_id = str(
            game_info.get("clusterId") or game_info.get("ClusterId") or ""
        )

        def _nn_int(val: Any) -> int:
            try:
                iv = int(val)
                return iv if iv >= 0 else 0
            except Exception:
                return 0

        header.num_cycles = _nn_int(
            game_info.get("numberOfCycles") or game_info.get("cycles") or 0
        )
        header.num_duplicants = _nn_int(
            game_info.get("numberOfDuplicants") or game_info.get("duplicants") or 0
        )

        dlc_ids = game_info.get("dlcIds") or game_info.get("DlcIds") or []
        if isinstance(dlc_ids, str):
            dlc_ids = [dlc_ids]
        if not isinstance(dlc_ids, list):
            dlc_ids = []
        header.dlc_ids = [str(d) for d in dlc_ids]
        has_dlc_flag = bool(
            game_info.get("hasDlc")
            or game_info.get("hasDLc")
            or game_info.get("hasDLC")
            or game_info.get("enableDlc")
            or game_info.get("expansionEnabled")
        )
        header.has_dlc = has_dlc_flag or (len(header.dlc_ids) > 0)

        mods_info = (
            game_info.get("mods")
            or game_info.get("Mods")
            or game_info.get("enabledMods")
            or []
        )
        header.has_mods = bool(mods_info) and isinstance(mods_info, (list, dict))

        header.game_info.update(
            {
                "buildVersion": build_version,
                "headerVersion": header_version,
                "isCompressed": is_compressed,
            }
        )
        if "saveMajorVersion" not in header.game_info:
            mv = game_info.get("saveMajorVersion")
            if isinstance(mv, int):
                header.game_info["saveMajorVersion"] = mv
        if "saveMinorVersion" not in header.game_info:
            mv2 = game_info.get("saveMinorVersion")
            if isinstance(mv2, int):
                header.game_info["saveMinorVersion"] = mv2

        return header


