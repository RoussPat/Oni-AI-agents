"""
ONI Save Parser

Main parser class for reading Oxygen Not Included save files.
Based on analysis of RoboPhred's JavaScript implementation.
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .binary_reader import BinaryReader
from .data_structures import (
    SaveGame, SaveGameHeader, SaveGameVersion, TypeTemplates, 
    SaveGameWorld, SaveGameSettings, GameObjectGroups, SaveGameData,
    ParseResult
)


class OniSaveParser:
    """
    Parser for ONI save files.
    
    Reads and parses Oxygen Not Included save files into structured Python objects.
    Based on the format analysis from RoboPhred's JavaScript parser.
    """
    
    # Supported save file versions
    SUPPORTED_MAJOR_VERSION = 7
    MIN_MINOR_VERSION = 11  # Based on analyzed parsers
    MAX_MINOR_VERSION = 36  # Updated to latest observed version
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_save_file(self, file_path: Path) -> ParseResult:
        """
        Parse an ONI save file.
        
        Args:
            file_path: Path to the .sav file
            
        Returns:
            ParseResult containing the parsed save game or error information
        """
        start_time = time.time()
        result = ParseResult()
        
        try:
            if not file_path.exists():
                result.error_message = f"Save file not found: {file_path}"
                return result
            
            self.logger.info(f"Parsing ONI save file: {file_path}")
            
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Parse the save file
            save_game = self._parse_save_data(file_data, result)
            
            if save_game:
                result.success = True
                result.save_game = save_game
                result.parse_time_seconds = time.time() - start_time
                # Extract key entities for convenience (duplicants)
                try:
                    minions = self.extract_minion_details(file_path)
                    result.entities["duplicants"] = minions
                except Exception as _:
                    # Non-fatal if entity extraction fails
                    pass
                
                self.logger.info(f"Successfully parsed save file in {result.parse_time_seconds:.2f}s")
                self.logger.info(f"Save version: {save_game.version}")
                self.logger.info(f"Cycles: {save_game.header.num_cycles}")
                self.logger.info(f"Duplicants: {save_game.header.num_duplicants}")
            
        except Exception as e:
            self.logger.error(f"Error parsing save file: {e}")
            result.error_message = str(e)
        
        return result

    def extract_minion_positions(self, file_path: Path) -> List[Dict[str, float]]:
        """Back-compat: return only positions. Prefer extract_minion_details."""
        try:
            file_bytes = file_path.read_bytes()
        except Exception:
            return []

        # Decompress the save body (heuristic): find zlib block after header JSON
        body = self._decompress_body_block(file_bytes)
        if not body:
            return []

        details = self._extract_minion_details_from_body(body)
        return [{"x": d["x"], "y": d["y"], "z": d["z"]} for d in details]

    def extract_minion_details(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract duplicant positions and identity info (name, gender, arrival_time)."""
        try:
            file_bytes = file_path.read_bytes()
        except Exception:
            return []

        body = self._decompress_body_block(file_bytes)
        if not body:
            return []
        return self._extract_minion_details_from_body(body)

    def _parse_header_raw(self, data: bytes) -> Tuple[int, bool]:
        """Return (offset_after_header_json, is_compressed) without altering state."""
        import struct
        p = 0
        mv = memoryview(data)
        # buildVersion, headerSize, headerVersion
        if len(data) < 12:
            return 0, False
        _build = struct.unpack_from('<I', mv, p)[0]; p += 4
        header_size = struct.unpack_from('<I', mv, p)[0]; p += 4
        header_version = struct.unpack_from('<I', mv, p)[0]; p += 4
        is_compressed = False
        if header_version >= 1:
            if p + 4 > len(data):
                return 0, False
            is_compressed = struct.unpack_from('<I', mv, p)[0] != 0; p += 4
        # JSON info
        p_end = p + header_size
        if p_end > len(data):
            return 0, is_compressed
        return p_end, is_compressed

    def _decompress_body_block(self, data: bytes) -> Optional[bytes]:
        """Find and decompress the main save body block (zlib) by scanning after header JSON.

        Returns decompressed bytes if successful, otherwise None.
        """
        import zlib
        start_after_header, _ = self._parse_header_raw(data)
        search = data[start_after_header:]
        # Scan for zlib headers
        candidates = []
        for sig in (b"\x78\x9c", b"\x78\xda", b"\x78\x01"):
            idx = 0
            while True:
                pos = search.find(sig, idx)
                if pos == -1:
                    break
                candidates.append(start_after_header + pos)
                idx = pos + 1
        for pos in sorted(set(candidates)):
            try:
                decompressed = zlib.decompress(data[pos:])
                # Heuristic validation: decompressed should contain 'KSAV'
                if b'KSAV' in decompressed:
                    return decompressed
            except Exception:
                continue
        return None

    def _scan_klei_strings(self, mv: memoryview, start: int, end: int, max_strings: int = 32) -> List[str]:
        """Scan a memory block for Klei strings (int32 length + bytes)."""
        import struct
        strings: List[str] = []
        p = start
        scanned = 0
        while p + 4 <= end and scanned < max_strings:
            try:
                l = struct.unpack_from('<i', mv, p)[0]
                if l < 0 or l > (end - p - 4):
                    p += 1
                    continue
                p += 4
                s = bytes(mv[p:p+l]).decode('utf-8', errors='ignore')
                p += l
                if s:
                    strings.append(s)
                    scanned += 1
            except Exception:
                p += 1
        return strings

    def _scan_first_int32(self, mv: memoryview, start: int, end: int, min_val: int = -2**31, max_val: int = 2**31-1) -> Optional[int]:
        """Find first plausible int32 value in range in block."""
        import struct
        p = start
        while p + 4 <= end:
            try:
                v = struct.unpack_from('<i', mv, p)[0]
                if min_val <= v <= max_val:
                    return int(v)
            except Exception:
                pass
            p += 1
        return None

    def _scan_first_float32(self, mv: memoryview, start: int, end: int, min_val: float, max_val: float) -> Optional[float]:
        """Find first plausible float32 value in range in block."""
        import struct, math
        p = start
        while p + 4 <= end:
            try:
                v = struct.unpack_from('<f', mv, p)[0]
                if math.isfinite(v) and min_val <= v <= max_val:
                    return float(v)
            except Exception:
                pass
            p += 1
        return None

    def _scan_best_float32(self, mv: memoryview, start: int, end: int, min_val: float, max_val: float) -> Optional[float]:
        """Scan a block and return the most plausible float32 in range (last match)."""
        import struct, math
        best = None
        p = start
        while p + 4 <= end:
            try:
                v = struct.unpack_from('<f', mv, p)[0]
                if math.isfinite(v) and min_val <= v <= max_val:
                    best = float(v)
            except Exception:
                pass
            p += 1
        return best

    def _read_klei_string(self, mv: memoryview, off: int, end: int) -> Tuple[Optional[str], int]:
        """Read a single Klei string (length-prefixed) at offset, return (str, new_off)."""
        import struct
        if off + 4 > end:
            return None, off
        l = struct.unpack_from('<i', mv, off)[0]
        off += 4
        if l < 0 or off + l > end:
            return None, off
        s = bytes(mv[off:off+l]).decode('utf-8', errors='ignore')
        off += l
        return s, off

    def _is_plausible_name(self, s: str) -> bool:
        if not s or len(s) < 2 or len(s) > 40:
            return False
        bad = {"Minion", "MinionIdentity", "MALE", "FEMALE", "NB"}
        if s in bad:
            return False
        if any(c in s for c in ("+", ":", "/", "\\", ".", "[", "]")):
            return False
        import re
        return re.fullmatch(r"[A-Za-z][A-Za-z '\-]*", s) is not None

    def _extract_minion_details_from_body(self, body: bytes) -> List[Dict[str, Any]]:
        """Extract minion positions and identity data from decompressed body."""
        import struct
        mv = memoryview(body)
        ksav = body.find(b'KSAV')
        if ksav == -1:
            return []
        p = ksav + 4
        # Version major/minor
        if p + 8 > len(body):
            return []
        _ver_major = struct.unpack_from('<i', mv, p)[0]; p += 4
        _ver_minor = struct.unpack_from('<i', mv, p)[0]; p += 4
        # Group count
        if p + 4 > len(body):
            return []
        try:
            group_count = struct.unpack_from('<i', mv, p)[0]; p += 4
        except Exception:
            return []
        minions: List[Dict[str, Any]] = []
        for _ in range(max(0, group_count)):
            if p + 4 > len(body):
                break
            name_len = struct.unpack_from('<i', mv, p)[0]; p += 4
            if name_len < 0 or p + name_len > len(body):
                break
            name = bytes(mv[p:p+name_len]).decode('utf-8', errors='ignore'); p += name_len
            if p + 8 > len(body):
                break
            instance_count = struct.unpack_from('<i', mv, p)[0]; p += 4
            data_length = struct.unpack_from('<i', mv, p)[0]; p += 4
            group_data_start = p
            if name == 'Minion' and instance_count > 0:
                for _i in range(instance_count):
                    if p + (3+4+3)*4 + 1 + 4 > len(body):
                        break
                    x, y, z = struct.unpack_from('<fff', mv, p); p += 12
                    p += 16  # rotation
                    p += 12  # scale
                    p += 1   # folder
                    behavior_count = struct.unpack_from('<i', mv, p)[0]; p += 4
                    minion_info: Dict[str, Any] = {"x": float(x), "y": float(y), "z": float(z)}
                    # Parse behaviors to extract identity info
                    for _b in range(max(0, behavior_count)):
                        if p + 4 > len(body):
                            break
                        beh_name_len = struct.unpack_from('<i', mv, p)[0]; p += 4
                        if beh_name_len < 0 or p + beh_name_len > len(body):
                            break
                        beh_name = bytes(mv[p:p+beh_name_len]).decode('utf-8', errors='ignore'); p += beh_name_len
                        if p + 4 > len(body):
                            break
                        beh_len = struct.unpack_from('<i', mv, p)[0]; p += 4
                        beh_start = p
                        beh_end = p + max(0, beh_len)
                        if beh_end > len(body):
                            break
                        if beh_name == 'MinionIdentity':
                            # Heuristic: first 4 fields are strings (name, nameStringKey, gender, genderStringKey),
                            # then an int32 arrivalTime.
                            try:
                                off = beh_start
                                # Read four consecutive Klei strings
                                nm, off = self._read_klei_string(mv, off, beh_end)
                                nm_key, off = self._read_klei_string(mv, off, beh_end)
                                gender, off = self._read_klei_string(mv, off, beh_end)
                                gender_key, off = self._read_klei_string(mv, off, beh_end)
                                # Arrival time and voice index
                                arrival = None
                                voice_idx = None
                                if off + 4 <= beh_end:
                                    arrival = struct.unpack_from('<i', mv, off)[0]; off += 4
                                if off + 4 <= beh_end:
                                    voice_idx = struct.unpack_from('<i', mv, off)[0]; off += 4
                                # Validate/assign fields; fallback to scan if needed
                                if nm and self._is_plausible_name(nm):
                                    minion_info['name'] = nm
                                else:
                                    strings = self._scan_klei_strings(mv, beh_start, beh_end, max_strings=32)
                                    for s in strings:
                                        if self._is_plausible_name(s):
                                            minion_info['name'] = s
                                            break
                                if gender in ("MALE", "FEMALE", "NB"):
                                    minion_info['gender'] = gender
                                if arrival is not None and 0 <= arrival < 10**9:
                                    minion_info['arrival_time'] = int(arrival)
                            except Exception:
                                pass
                        elif beh_name in ('MinionResume',):
                            # Try to extract current role/job from strings in this block
                            try:
                                strings = self._scan_klei_strings(mv, beh_start, beh_end, max_strings=64)
                                # Heuristic: prefer strings that look like Role IDs (CamelCase words)
                                import re
                                camel = [s for s in strings if re.fullmatch(r"[A-Z][A-Za-z]+", s)]
                                if camel:
                                    minion_info.setdefault('job', camel[0])
                            except Exception:
                                pass
                        elif beh_name in ('MinionModifiers', 'Modifiers'):
                            # Extract some vitals from known amount names
                            try:
                                vitals = minion_info.setdefault('vitals', {})
                                label_map = {
                                    'Calories': ('calories', 0.0, 1e9),
                                    'Health': ('health', 0.0, 1000.0),
                                    'Stress': ('stress', 0.0, 100.0),
                                    'Stamina': ('stamina', 0.0, 100.0),
                                }
                                q = beh_start
                                while q + 8 <= beh_end:
                                    name_s, q2 = self._read_klei_string(mv, q, beh_end)
                                    if name_s is None:
                                        q += 1
                                        continue
                                    if q2 + 4 > beh_end:
                                        break
                                    c_len = struct.unpack_from('<i', mv, q2)[0]
                                    q2 += 4
                                    if c_len < 0 or q2 + c_len > beh_end:
                                        q = q2
                                        continue
                                    # Now [q2, q2+c_len) is the modifier payload; pick first plausible float
                                    if name_s in label_map:
                                        key, vmin, vmax = label_map[name_s]
                                        val = self._scan_best_float32(mv, q2, q2 + c_len, vmin, vmax)
                                        if val is not None:
                                            vitals[key] = float(val)
                                    q = q2 + c_len
                            except Exception:
                                pass
                        # Skip to end of behavior block
                        p = beh_end
                    # Ensure defaults for required fields
                    minion_info.setdefault('arrival_time', 0)
                    minion_info.setdefault('job', 'NoRole')
                    minions.append(minion_info)
            else:
                # Skip group payload
                p = group_data_start + max(0, data_length)
                if p > len(body):
                    break
        return minions
    
    def _parse_save_data(self, file_data: bytes, result: ParseResult) -> Optional[SaveGame]:
        """
        Parse raw save file data.
        
        Args:
            file_data: Raw bytes from save file
            result: ParseResult to store warnings
            
        Returns:
            Parsed SaveGame object or None if parsing failed
        """
        reader = BinaryReader(file_data)
        save_game = SaveGame()
        
        try:
            # Parse header first (contains version and other metadata)
            save_game.header = self._parse_header(reader, result)
            
            # Extract version from header and validate
            if hasattr(save_game.header, 'game_info') and save_game.header.game_info:
                major = save_game.header.game_info.get('saveMajorVersion', 7)
                minor = save_game.header.game_info.get('saveMinorVersion', 36)
                save_game.version = SaveGameVersion(major=major, minor=minor)
                self._validate_version(save_game.version)
            
            # Parse remaining sections in order
            save_game.templates = self._parse_templates(reader, result)
            save_game.world = self._parse_world(reader, result)
            save_game.settings = self._parse_settings(reader, result)
            save_game.sim_data = self._parse_sim_data(reader, result)
            save_game.game_objects = self._parse_game_objects(reader, result)
            save_game.game_data = self._parse_game_data(reader, result)
            
            return save_game
            
        except Exception as e:
            self.logger.error(f"Error in save data parsing: {e}")
            raise
    
    def _parse_version(self, reader: BinaryReader) -> SaveGameVersion:
        """Parse save file version from header JSON data."""
        # Based on RoboPhred's parser - version is in the JSON header
        # We'll parse it during header parsing and set a default here
        return SaveGameVersion(major=7, minor=36)  # Will be updated during header parsing
    
    def _validate_version(self, version: SaveGameVersion):
        """Validate that the save file version is supported."""
        if version.major != self.SUPPORTED_MAJOR_VERSION:
            raise ValueError(
                f"Unsupported major version {version.major}. "
                f"Expected {self.SUPPORTED_MAJOR_VERSION}"
            )
        
        if not (self.MIN_MINOR_VERSION <= version.minor <= self.MAX_MINOR_VERSION):
            self.logger.warning(
                f"Minor version {version.minor} may not be fully supported. "
                f"Supported range: {self.MIN_MINOR_VERSION}-{self.MAX_MINOR_VERSION}"
            )
    
    def _parse_header(self, reader: BinaryReader, result: ParseResult) -> SaveGameHeader:
        """Parse save file header based on RoboPhred's format."""
        import json
        
        header = SaveGameHeader()
        
        try:
            # Based on RoboPhred's header parser:
            # uint32: buildVersion
            # uint32: headerSize  
            # uint32: headerVersion
            # uint32: isCompressed (if headerVersion >= 1)
            # bytes[headerSize]: JSON game info
            
            build_version = reader.read_uint32()
            header_size = reader.read_uint32()
            header_version = reader.read_uint32()
            
            is_compressed = False
            if header_version >= 1:
                is_compressed = bool(reader.read_uint32())
            
            # Read JSON game info
            info_bytes = reader.read_bytes(header_size)
            info_str = info_bytes.decode('utf-8')
            game_info = json.loads(info_str)
            
            # Populate header
            header.game_info = game_info
            header.cluster_id = game_info.get('clusterId', '')
            header.num_cycles = game_info.get('numberOfCycles', 0)
            header.num_duplicants = game_info.get('numberOfDuplicants', 0)
            
            self.logger.info(f"Parsed header - Version: {header_version}, Compressed: {is_compressed}")
            self.logger.info(f"Game: {game_info.get('baseName', 'Unknown')}, Cycles: {header.num_cycles}")
            
            # Store additional header info
            header.game_info.update({
                'buildVersion': build_version,
                'headerVersion': header_version,
                'isCompressed': is_compressed
            })
            # Keep a ref for heuristics in later sections
            self.last_game_info = game_info
            
        except Exception as e:
            result.add_warning(f"Header parsing error: {e}")
            self.logger.error(f"Header parsing failed: {e}")
            raise
        
        return header
    
    def _parse_templates(self, reader: BinaryReader, result: ParseResult) -> TypeTemplates:
        """Parse type templates section."""
        # TODO: Implement type templates parsing
        templates = TypeTemplates()
        
        try:
            # Type templates are complex - this would need detailed implementation
            result.add_warning("Type templates parsing not yet implemented")
            
        except Exception as e:
            result.add_warning(f"Template parsing error: {e}")
        
        return templates
    
    def _parse_world(self, reader: BinaryReader, result: ParseResult) -> SaveGameWorld:
        """Parse world data section (minimal fields).

        Tries header-derived dimensions; if unavailable, heuristically scans
        the remaining bytes for WidthInCells/HeightInCells labels and nearby
        int32 values.
        """
        world = SaveGameWorld()
        
        try:
            # Without templates, extract nothing structural yet.
            # Populate dimensions from header if present (best effort).
            gi = getattr(self, 'last_game_info', {}) or {}
            world.width_in_cells = int(gi.get('WidthInCells', 0) or gi.get('widthInCells', 0) or 0)
            world.height_in_cells = int(gi.get('HeightInCells', 0) or gi.get('heightInCells', 0) or 0)
            
            # Heuristic fallback: scan for labels and proximate int32 values
            if world.width_in_cells == 0 or world.height_in_cells == 0:
                import struct
                start_pos = reader.get_position()
                try:
                    remaining = reader.remaining_bytes()
                    body = reader.read_bytes(remaining) if remaining > 0 else b""
                finally:
                    # Restore position to avoid affecting later sections
                    reader.seek(start_pos)

                def find_int_after(label: bytes, default_val: int = 0) -> int:
                    idx = body.find(label)
                    if idx == -1:
                        return default_val
                    window = body[idx: idx + 256]
                    # look for first plausible little-endian int32 after the label bytes
                    for offset in range(len(label), max(len(label), len(window) - 4)):
                        try:
                            val = struct.unpack_from('<i', window, offset)[0]
                        except Exception:
                            continue
                        # Plausible cell dimensions range
                        if 8 <= val <= 10000:
                            return int(val)
                    return default_val

                if world.width_in_cells == 0:
                    world.width_in_cells = find_int_after(b"WidthInCells", world.width_in_cells)
                if world.height_in_cells == 0:
                    world.height_in_cells = find_int_after(b"HeightInCells", world.height_in_cells)
            
            # Note preservation until template-based parsing is implemented
            result.add_warning("World data preserved as binary (not parsed)")
        except Exception as e:
            result.add_warning(f"World parsing error: {e}")
        
        return world
    
    def _parse_settings(self, reader: BinaryReader, result: ParseResult) -> SaveGameSettings:
        """Parse game settings section."""
        # TODO: Implement settings parsing
        settings = SaveGameSettings()
        
        try:
            result.add_warning("Settings parsing not yet implemented")
            
        except Exception as e:
            result.add_warning(f"Settings parsing error: {e}")
        
        return settings
    
    def _parse_sim_data(self, reader: BinaryReader, result: ParseResult) -> bytes:
        """Parse simulation data section."""
        # TODO: Implement sim data parsing
        try:
            # Simulation data is typically a binary blob
            # Size would be read from file, then the blob
            result.add_warning("Simulation data preserved as binary")
            return b""  # Placeholder
            
        except Exception as e:
            result.add_warning(f"Sim data parsing error: {e}")
            return b""
    
    def _parse_game_objects(self, reader: BinaryReader, result: ParseResult) -> GameObjectGroups:
        """Parse game objects section."""
        # TODO: Implement game objects parsing
        game_objects = GameObjectGroups()
        
        try:
            result.add_warning("Game objects parsing not yet implemented")
            
        except Exception as e:
            result.add_warning(f"Game objects parsing error: {e}")
        
        return game_objects
    
    def _parse_game_data(self, reader: BinaryReader, result: ParseResult) -> SaveGameData:
        """Parse additional game data section."""
        # TODO: Implement game data parsing
        game_data = SaveGameData()
        
        try:
            result.add_warning("Game data parsing not yet implemented")
            
        except Exception as e:
            result.add_warning(f"Game data parsing error: {e}")
        
        return game_data
    
    def get_supported_versions(self) -> Dict[str, Any]:
        """Get information about supported save file versions."""
        return {
            "major_version": self.SUPPORTED_MAJOR_VERSION,
            "minor_version_range": {
                "min": self.MIN_MINOR_VERSION,
                "max": self.MAX_MINOR_VERSION
            },
            "based_on": "RoboPhred's oni-save-parser analysis",
            "last_updated": "2025-08-09"
        }
