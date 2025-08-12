"""
Data structures for ONI Save Files

Python equivalents of the TypeScript interfaces from RoboPhred's parser.
These represent the structured data found in ONI save files.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Vector3:
    """3D vector for positions, rotations, scales."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class SaveGameHeader:
    """Header information from save file.

    Attributes
    ----------
    game_info: Raw header JSON preserved for consumers.
    cluster_id: Cluster/world identifier.
    num_cycles: Current cycle count (non-negative).
    num_duplicants: Current duplicant count (non-negative).
    has_dlc: Whether any DLC appears enabled in the header.
    dlc_ids: List of DLC identifiers from the header (may be empty).
    has_mods: Whether any mods appear enabled in the header.
    """

    game_info: Dict[str, Any] = field(default_factory=dict)
    cluster_id: str = ""
    num_cycles: int = 0
    num_duplicants: int = 0
    # Normalized convenience flags derived from header JSON
    has_dlc: bool = False
    dlc_ids: List[str] = field(default_factory=list)
    has_mods: bool = False


@dataclass
class TypeTemplate:
    """Template definition for game object types."""

    name: str = ""
    template_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypeTemplates:
    """Collection of all type templates in save file."""

    templates: List[TypeTemplate] = field(default_factory=list)

    def get(self, name: str) -> Optional[TypeTemplate]:
        for t in self.templates:
            if t.name == name:
                return t
        return None


@dataclass
class GameObject:
    """Individual game object (duplicant, building, item, etc.)."""

    name: str = ""
    position: Vector3 = field(default_factory=Vector3)
    rotation: Vector3 = field(default_factory=Vector3)
    scale: Vector3 = field(default_factory=Vector3)

    # Component data
    components: List[Dict[str, Any]] = field(default_factory=list)
    behaviors: List[Dict[str, Any]] = field(default_factory=list)

    # Nested game objects
    game_objects: List["GameObject"] = field(default_factory=list)


@dataclass
class GameObjectGroup:
    """Group of game objects of the same type."""

    name: str = ""
    game_objects: List[GameObject] = field(default_factory=list)


@dataclass
class GameObjectGroups:
    """All game object groups in the save file."""

    groups: List[GameObjectGroup] = field(default_factory=list)

    def find_group(self, name: str) -> Optional[GameObjectGroup]:
        """Find a game object group by name."""
        for group in self.groups:
            if group.name == name:
                return group
        return None


@dataclass
class SaveGameWorld:
    """World/map data (mostly preserved as binary)."""

    data: bytes = b""
    width_in_cells: int = 0
    height_in_cells: int = 0
    # Optional: index of streamed chunks (name -> size in bytes)
    streamed_index: Dict[str, int] = field(default_factory=dict)
    # TODO: Parse world data structure when needed


@dataclass
class SaveBlockInfo:
    """Information about a compressed block found in the save stream."""

    offset: int
    header: str  # first up to 10 bytes of the compressed stream, hex-encoded
    compressed_size: int
    decompressed_size: int
    crc32: str  # hex string, lowercase without 0x


@dataclass
class SaveGameMetadata:
    """Additional metadata extracted from the save stream for diagnostics."""

    blocks: List[SaveBlockInfo] = field(default_factory=list)
    ksav_summary: Dict[str, int] = field(default_factory=dict)  # {group_count, total_instances}


@dataclass
class SaveGameSettings:
    """Game settings and configuration."""

    game_settings: Dict[str, Any] = field(default_factory=dict)
    world_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SaveGameData:
    """Additional game data (research, statistics, etc.)."""

    research: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    achievements: Dict[str, Any] = field(default_factory=dict)

    # Raw data for unparsed sections
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SaveGameVersion:
    """Save file version information."""

    major: int = 0
    minor: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass
class SaveGame:
    """Complete save game data structure."""

    header: SaveGameHeader = field(default_factory=SaveGameHeader)
    templates: TypeTemplates = field(default_factory=TypeTemplates)
    world: SaveGameWorld = field(default_factory=SaveGameWorld)
    settings: SaveGameSettings = field(default_factory=SaveGameSettings)
    sim_data: bytes = b""  # Simulation data (binary blob)
    version: SaveGameVersion = field(default_factory=SaveGameVersion)
    game_objects: GameObjectGroups = field(default_factory=GameObjectGroups)
    game_data: SaveGameData = field(default_factory=SaveGameData)
    metadata: SaveGameMetadata = field(default_factory=SaveGameMetadata)

    def get_duplicants(self) -> List[GameObject]:
        """Get all duplicant game objects."""
        minion_group = self.game_objects.find_group("Minion")
        return minion_group.game_objects if minion_group else []

    def get_buildings(self) -> List[GameObject]:
        """Get all building game objects."""
        buildings = []
        # Buildings can be in various groups, collect them all
        for group in self.game_objects.groups:
            if group.name != "Minion":  # Exclude duplicants
                buildings.extend(group.game_objects)
        return buildings

    def get_object_count_by_type(self) -> Dict[str, int]:
        """Get count of objects by group type."""
        counts = {}
        for group in self.game_objects.groups:
            counts[group.name] = len(group.game_objects)
        return counts

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of save file contents."""
        return {
            "version": str(self.version),
            "cycles": self.header.num_cycles,
            "duplicants": self.header.num_duplicants,
            "object_groups": len(self.game_objects.groups),
            "total_objects": sum(len(group.game_objects) for group in self.game_objects.groups),
            "object_counts": self.get_object_count_by_type(),
            "world_data_size": len(self.world.data),
            "sim_data_size": len(self.sim_data),
        }


# Helper classes for specific game object types


@dataclass
class DuplicantStats:
    """Duplicant-specific stats and attributes."""

    name: str = ""
    health: float = 100.0
    stress: float = 0.0
    calories: float = 1000.0
    skills: Dict[str, int] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)

    @classmethod
    def from_game_object(cls, game_object: GameObject) -> "DuplicantStats":
        """Extract duplicant stats from a game object."""
        # TODO: Implement parsing of duplicant-specific components
        return cls(name=game_object.name)


@dataclass
class BuildingInfo:
    """Building-specific information."""

    building_type: str = ""
    is_operational: bool = False
    efficiency: float = 1.0
    temperature: float = 293.15  # Room temperature in Kelvin

    @classmethod
    def from_game_object(cls, game_object: GameObject) -> "BuildingInfo":
        """Extract building info from a game object."""
        # TODO: Implement parsing of building-specific components
        return cls(building_type=game_object.name)


# Parsing result containers


@dataclass
class ParseResult:
    """Result of parsing operation."""

    success: bool = False
    save_game: Optional[SaveGame] = None
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)
    parse_time_seconds: float = 0.0
    entities: Dict[str, Any] = field(default_factory=dict)

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
