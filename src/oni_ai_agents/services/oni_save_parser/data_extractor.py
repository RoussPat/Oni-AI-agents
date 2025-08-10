from __future__ import annotations

"""
SaveFileDataExtractor (contract v0.1)

Builds a stable, section-oriented JSON document from a parsed ONI save.

Public API:
- SaveFileDataExtractor.extract(save: SaveGame, entities: Dict[str, Any]) -> Dict[str, Any]

Sections guaranteed (placeholders allowed):
- metadata
- duplicants
- world_grid_summary
- object_group_counts
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .data_structures import SaveGame
from .world_grid_histogrammer import compute_breathable_percent, compute_histograms


def _safe_get_game_info_value(game_info: Dict[str, Any], key: str, default: Any = None) -> Any:
    try:
        return game_info.get(key, default)
    except Exception:
        return default


def _map_minion_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw minion dict to the contract schema.

    The parser's entity extraction already returns a rich structure. This
    function ensures stable keys are present and types are consistent.
    """
    vitals = entry.get("vitals") if isinstance(entry.get("vitals"), dict) else {}
    identity = {
        "name": entry.get("name"),
        "gender": entry.get("gender"),
        "arrival_time": int(entry.get("arrival_time", 0) or 0),
    }
    position = {
        "x": float(entry.get("x", 0.0) or 0.0),
        "y": float(entry.get("y", 0.0) or 0.0),
        "z": float(entry.get("z", 0.0) or 0.0),
    }
    normalized = {
        "identity": identity,
        "role": entry.get("job", "NoRole") or "NoRole",
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
            "morale": vitals.get("morale"),
        },
        "traits": entry.get("traits") or [],
        "effects": entry.get("effects") or [],
        "aptitudes": entry.get("aptitudes") or {},
        "position": position,
    }
    return normalized


@dataclass
class SaveFileDataExtractor:
    """Builds the section contract v0.1 from a parsed `SaveGame`.

    The extractor does not perform parsing. It formats data produced by
    the parser into a compact JSON-ready structure.
    """

    def extract(self, save: SaveGame, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Return a JSON-serializable dict with the contract sections.

        Args:
            save: Parsed `SaveGame` model
            entities: Convenience entities emitted by the parser

        Returns:
            Dictionary containing `metadata`, `duplicants`, `world_grid_summary`,
            and `object_group_counts` (plus room for future sections).
        """
        # --- metadata ---
        game_info = save.header.game_info or {}
        metadata: Dict[str, Any] = {
            "version": str(save.version),
            "cycles": int(getattr(save.header, "num_cycles", 0) or 0),
            "duplicant_count": int(getattr(save.header, "num_duplicants", 0) or 0),
            "base_name": _safe_get_game_info_value(game_info, "baseName", "") or "",
            "cluster_id": save.header.cluster_id or _safe_get_game_info_value(game_info, "clusterId", ""),
            # Keep full `game_info` for transparency; small dict in ONI headers
            "game_info": game_info,
        }

        # --- duplicants ---
        raw_minions: List[Dict[str, Any]] = entities.get("duplicants") or []  # type: ignore[assignment]
        duplicants_list = [_map_minion_entry(m) for m in raw_minions]
        duplicants: Dict[str, Any] = {
            "count": int(getattr(save.header, "num_duplicants", len(duplicants_list)) or len(duplicants_list)),
            "list": duplicants_list,
        }

        # --- object group counts ---
        object_group_counts: Dict[str, int] = {
            str(k): int(v) for k, v in (entities.get("object_group_counts") or {}).items()
            if isinstance(v, (int, float))
        }

        # --- world grid summary ---
        world_width = int(getattr(save.world, "width_in_cells", 0) or 0)
        world_height = int(getattr(save.world, "height_in_cells", 0) or 0)
        cell_count = world_width * world_height if world_width > 0 and world_height > 0 else 0
        # Prefer parser-provided summary; fallback to lightweight computation
        wgs: Optional[Dict[str, Any]] = entities.get("world_grid_summary")
        if not isinstance(wgs, dict):
            hist = compute_histograms(save.sim_data or b"", world_width, world_height)
            breathable = compute_breathable_percent(hist, cell_count)
            wgs = {
                "width": world_width,
                "height": world_height,
                "cell_count": cell_count,
                "histograms": hist,
                "breathable_percent": breathable,
                "warnings": [],
            }

        # Ensure required keys exist even if parser supplied partial data
        wgs.setdefault("width", world_width)
        wgs.setdefault("height", world_height)
        wgs.setdefault("cell_count", cell_count)
        wgs.setdefault("histograms", {})
        wgs.setdefault("breathable_percent", None)
        wgs.setdefault("warnings", [])

        # Top-level contract document
        doc: Dict[str, Any] = {
            "metadata": metadata,
            "duplicants": duplicants,
            "world_grid_summary": wgs,
            "object_group_counts": object_group_counts,
        }

        return doc


