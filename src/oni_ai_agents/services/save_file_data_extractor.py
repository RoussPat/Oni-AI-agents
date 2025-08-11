from __future__ import annotations

"""
Save File Data Extractor

Provides section-oriented views of an ONI save file using the OniSaveParser.
This serves as a compatibility layer for observer agents expecting section data.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .oni_save_parser import OniSaveParser
from .oni_save_parser.world_grid_histogrammer import (
    compute_breathable_percent,
    compute_histograms,
)


@dataclass
class ExtractedSaveData:
    header: Dict[str, Any]
    sections: Dict[str, Dict[str, Any]]


class SaveFileDataExtractor:
    """Extracts section-specific dictionaries from an ONI save file."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._parser = OniSaveParser()

    def parse_save_file(self, save_file_path: Path) -> ExtractedSaveData:
        """Parse a save file and return a structured data container.

        The returned structure includes minimal but actionable data for
        observer agents. For the `duplicants` section, this method augments
        header counts with a concrete `list` of duplicant entries derived
        from the parser's entity extraction. If a canonical list is available
        it is preferred; otherwise raw entries are mapped into canonical form.
        """
        result = self._parser.parse_save_file(save_file_path)
        if not result.success or result.save_game is None:
            raise ValueError(f"Failed to parse save file: {result.error_message}")

        save_game = result.save_game
        game_info = save_game.header.game_info
        # Prefer canonical duplicants structure if provided by parser
        canonical = result.entities.get("duplicants_canonical")
        raw_minions = result.entities.get("duplicants") or self._parser.extract_minion_details(save_file_path)

        def to_canonical(m: Dict[str, Any]) -> Dict[str, Any]:
            vitals: Dict[str, Any] = m.get("vitals", {}) if isinstance(m.get("vitals"), dict) else {}
            identity = {
                "name": m.get("name"),
                "gender": m.get("gender"),
                "arrival_time": int(m.get("arrival_time", 0) or 0),
            }
            position = {
                "x": float(m.get("x", 0.0)),
                "y": float(m.get("y", 0.0)),
                "z": float(m.get("z", 0.0)),
            }
            return {
                "identity": identity,
                "role": m.get("job", "NoRole") or "NoRole",
                "vitals": {
                    "calories": vitals.get("calories"),
                    "health": vitals.get("health"),
                    "stress": vitals.get("stress"),
                    "stamina": vitals.get("stamina"),
                    "decor": vitals.get("decor"),
                    "temperature": vitals.get("temperature"),
                    "breath": vitals.get("breath"),
                    "bladder": vitals.get("bladder"),
                    "immune_level": vitals.get("immune_level"),
                    "toxicity": vitals.get("toxicity"),
                    "radiation_balance": vitals.get("radiation_balance"),
                },
                "aptitudes": m.get("aptitudes") or {},
                "traits": m.get("traits", []) or [],
                "effects": m.get("effects", []) or [],
                "position": position,
            }

        if isinstance(canonical, list) and canonical:
            duplicant_list = canonical
        else:
            duplicant_list = [to_canonical(m) for m in (raw_minions or [])]

        # Minimal sections derived from header until full parsing is implemented
        resources_section = {
            "cycles": save_game.header.num_cycles,
            "base_name": game_info.get("baseName", ""),
            "cluster_id": game_info.get("clusterId", ""),
            # Placeholders until full parsing
            "food": None,
            "oxygen": None,
            "power": None,
            "materials": {},
            "storage_usage": {},
        }

        duplicants_section = {
            "count": save_game.header.num_duplicants,
            "list": duplicant_list,
            # Placeholders pending template parsing
            "health_status": {},
            "morale_levels": {},
            "skill_assignments": {},
            "current_tasks": {},
            "stress_levels": {},
        }

        threats_section = {
            # Placeholders for now
            "diseases": {},
            "temperature_zones": {},
            "pressure_issues": {},
            "contamination": {},
            "hostile_creatures": {},
        }

        # World grid summary (Phase 1 scaffold)
        world_width = int(save_game.world.width_in_cells or 0)
        world_height = int(save_game.world.height_in_cells or 0)
        cell_count = world_width * world_height if world_width > 0 and world_height > 0 else 0
        histograms = compute_histograms(save_game.sim_data or b"", world_width, world_height)
        breathable_percent = compute_breathable_percent(histograms, cell_count)
        world_warnings = list(result.warnings)

        world_grid_summary = {
            "width": world_width,
            "height": world_height,
            "cell_count": cell_count,
            "histograms": histograms,
            "breathable_percent": breathable_percent,
            "warnings": world_warnings,
        }

        sections = {
            "resources": resources_section,
            "duplicants": duplicants_section,
            "threats": threats_section,
            "world_grid_summary": world_grid_summary,
        }

        header = {
            "version": str(save_game.version),
            "game_info": game_info,
        }

        return ExtractedSaveData(header=header, sections=sections)

    def get_section_data(self, save_file_path: Path, section_name: str) -> Dict[str, Any]:
        data = self.parse_save_file(save_file_path)
        if section_name not in data.sections:
            available = list(data.sections.keys())
            raise ValueError(f"Unknown section '{section_name}'. Available: {available}")
        return data.sections[section_name]

    def get_all_sections(self, save_file_path: Path) -> Dict[str, Dict[str, Any]]:
        return self.parse_save_file(save_file_path).sections
