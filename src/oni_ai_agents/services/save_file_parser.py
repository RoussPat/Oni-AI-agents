from __future__ import annotations

"""
Save File Parser (Adapter)

Provides a stable interface expected by agents/workflow while delegating
to the internal SaveFileDataExtractor that parses ONI save files into
section-oriented dictionaries.
"""

from pathlib import Path
from typing import Any, Dict

from .save_file_data_extractor import SaveFileDataExtractor


class SaveFileParser:
    """Adapter that exposes sectioned data from an ONI save file.

    This maintains backward compatibility with existing imports
    (..services.save_file_parser.SaveFileParser) used by agents and
    workflow code.
    """

    def __init__(self) -> None:
        self._extractor = SaveFileDataExtractor()

    def parse_save_file(self, save_file_path: Path) -> Dict[str, Dict[str, Any]]:
        """Parse a save file and return a mapping of section name to data.

        Args:
            save_file_path: Path to the ONI .sav file

        Returns:
            Dict keyed by section name (e.g. "resources", "duplicants", "threats").
        """
        extracted = self._extractor.parse_save_file(save_file_path)
        return extracted.sections

    def get_section_data(self, save_file_path: Path, section_name: str) -> Dict[str, Any]:
        """Return a single section's dictionary."""
        return self._extractor.get_section_data(save_file_path, section_name)

    def get_all_sections(self, save_file_path: Path) -> Dict[str, Dict[str, Any]]:
        """Return all sections as a dict of dicts."""
        return self._extractor.get_all_sections(save_file_path)


