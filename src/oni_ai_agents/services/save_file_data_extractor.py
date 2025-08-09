from __future__ import annotations

"""
Save File Data Extractor

Provides section-oriented views of an ONI save file using the OniSaveParser.
This serves as a compatibility layer for observer agents expecting section data.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from .oni_save_parser import OniSaveParser


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
        """Parse a save file and return a structured data container."""
        result = self._parser.parse_save_file(save_file_path)
        if not result.success or result.save_game is None:
            raise ValueError(f"Failed to parse save file: {result.error_message}")

        save_game = result.save_game
        game_info = save_game.header.game_info

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
            # Placeholders for now
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

        sections = {
            "resources": resources_section,
            "duplicants": duplicants_section,
            "threats": threats_section,
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
