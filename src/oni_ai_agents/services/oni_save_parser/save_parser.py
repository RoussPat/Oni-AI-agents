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
    SaveGame, SaveGameHeader, SaveGameVersion, TypeTemplates, TypeTemplate,
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
        # Known IDs for cleaner extraction fallback (subset curated from research)
        self._KNOWN_TRAIT_IDS = {
            'SmallBladder','Narcolepsy','Flatulence','Anemic','MouthBreather','BingeEater','StressVomiter',
            'UglyCrier','EarlyBird','NightOwl','FastLearner','SlowLearner','NoodleArms','StrongArm',
            'IronGut','WeakImmuneSystem','StrongImmuneSystem','DeeperDiversLungs','Snorer','BalloonArtist',
            'SparkleStreaker','StickerBomber','InteriorDecorator','Uncultured','Allergies','Hemophobia',
            'Claustrophobic','SolitarySleeper','Workaholic','Aggressive','Foodie','SimpleTastes','Greasemonkey',
            'MoleHands','Twinkletoes','SunnyDisposition','RockCrusher','BedsideManner','Archaeologist',
        }
        self._KNOWN_EFFECT_IDS = {
            'UncomfortableSleep','Sleep','NarcolepticSleep','RestfulSleep','AnewHope','Mourning','DisturbedSleep',
            'NewCrewArrival','UnderWater','FullBladder','StressfulyEmptyingBladder','RedAlert','MentalBreak',
            'CoolingDown','WarmingUp','Darkness','SteppedInContaminatedWater','WellFed','StaleFood',
            'SmelledPutridOdour','Vomiting','DirtyHands','Unclean','LightWounds','ModerateWounds','SevereWounds',
            'WasAttacked','SoreBack','WarmAir','ColdAir','Hypothermia','Hyperthermia','CenterOfAttention'
        }
    
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
                                # Parse as a series of key/value payloads: [nameStr][len][payload]
                                q = beh_start
                                found_name = False
                                found_gender = False
                                while q < beh_end:
                                    key, q2 = self._read_klei_string(mv, q, beh_end)
                                    if key is None:
                                        q += 1
                                        continue
                                    if q2 + 4 > beh_end:
                                        break
                                    kv_len = struct.unpack_from('<i', mv, q2)[0]
                                    q2 += 4
                                    if kv_len < 0 or q2 + kv_len > beh_end:
                                        q = q2
                                        continue
                                    # Interpret payload based on key
                                    if key in ('name', 'nameStringKey', 'gender', 'genderStringKey'):
                                        # Read first Klei string from payload
                                        try:
                                            # Copy payload bytes for safe decoding
                                            payload = bytes(mv[q2:q2+kv_len])
                                            import struct as _st
                                            if len(payload) >= 4:
                                                slen = _st.unpack_from('<i', payload, 0)[0]
                                                if 0 <= slen <= len(payload) - 4:
                                                    s = payload[4:4+slen].decode('utf-8', errors='ignore')
                                                    if key == 'name' and s and self._is_plausible_name(s):
                                                        minion_info['name'] = s
                                                        found_name = True
                                                    elif key == 'gender' and s in ("MALE", "FEMALE", "NB"):
                                                        minion_info['gender'] = s
                                                        found_gender = True
                                        except Exception:
                                            pass
                                    elif key == 'arrivalTime':
                                        # arrivalTime may be stored as int32/int64/float
                                        try:
                                            if kv_len >= 4:
                                                at32 = struct.unpack_from('<i', mv, q2)[0]
                                                if 0 <= at32 < 10**10:
                                                    minion_info['arrival_time'] = int(at32)
                                            if 'arrival_time' not in minion_info and kv_len >= 8:
                                                at64 = struct.unpack_from('<q', mv, q2)[0]
                                                if 0 <= at64 < 10**12:
                                                    minion_info['arrival_time'] = int(at64)
                                            if 'arrival_time' not in minion_info and kv_len >= 4:
                                                af32 = struct.unpack_from('<f', mv, q2)[0]
                                                if 0.0 <= af32 < 10**10:
                                                    minion_info['arrival_time'] = int(af32)
                                            if 'arrival_time' not in minion_info and kv_len >= 8:
                                                af64 = struct.unpack_from('<d', mv, q2)[0]
                                                if 0.0 <= af64 < 10**12:
                                                    minion_info['arrival_time'] = int(af64)
                                        except Exception:
                                            pass
                                    elif key == 'voiceIdx':
                                        # Not currently used
                                        pass
                                    # Advance to next kv
                                    q = q2 + kv_len
                                # Fallbacks if name/gender not found
                                if not found_name:
                                    strings = self._scan_klei_strings(mv, beh_start, beh_end, max_strings=32)
                                    for s in strings:
                                        if self._is_plausible_name(s):
                                            minion_info['name'] = s
                                            break
                                # Fallback: positional decode (legacy layout)
                                if 'arrival_time' not in minion_info:
                                    try:
                                        off = beh_start
                                        nm, off = self._read_klei_string(mv, off, beh_end)
                                        _nm_key, off = self._read_klei_string(mv, off, beh_end)
                                        gender_s, off = self._read_klei_string(mv, off, beh_end)
                                        _gender_key, off = self._read_klei_string(mv, off, beh_end)
                                        if gender_s in ("MALE", "FEMALE", "NB") and 'gender' not in minion_info:
                                            minion_info['gender'] = gender_s
                                        if off + 4 <= beh_end:
                                            at = struct.unpack_from('<i', mv, off)[0]; off += 4
                                            if at >= 0:
                                                minion_info['arrival_time'] = int(at)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        elif beh_name in ('MinionResume',):
                            # Try to extract current role/job from strings in this block
                            try:
                                # Parse key/value payloads within MinionResume
                                q = beh_start
                                role_val = None
                                # Prepare aptitude accumulator
                                aptitudes: Dict[str, int] = {}
                                # Known skill groups (lowercase keys)
                                known_groups = {
                                    'building': 'Building',
                                    'digging': 'Digging',
                                    'mining': 'Digging',
                                    'research': 'Research',
                                    'cooking': 'Cooking',
                                    'farming': 'Farming',
                                    'ranching': 'Ranching',
                                    'doctoring': 'Doctoring',
                                    'medical': 'Doctoring',
                                    'artist': 'Art',
                                    'operating': 'Operating',
                                    'hauling': 'Hauling',
                                    'tidying': 'Tidying',
                                    'engineering': 'Engineering',
                                    'supplying': 'Hauling',
                                }
                                while q < beh_end:
                                    key, q2 = self._read_klei_string(mv, q, beh_end)
                                    if key is None:
                                        q += 1
                                        continue
                                    if q2 + 4 > beh_end:
                                        break
                                    kv_len = struct.unpack_from('<i', mv, q2)[0]
                                    q2 += 4
                                    if kv_len < 0 or q2 + kv_len > beh_end:
                                        q = q2
                                        continue
                                    if key == 'currentRole':
                                        try:
                                            payload = bytes(mv[q2:q2+kv_len])
                                            import struct as _st
                                            if len(payload) >= 4:
                                                slen = _st.unpack_from('<i', payload, 0)[0]
                                                if 0 <= slen <= len(payload) - 4:
                                                    s = payload[4:4+slen].decode('utf-8', errors='ignore')
                                                    if s:
                                                        role_val = s
                                        except Exception:
                                            pass
                                    elif key == 'AptitudeBySkillGroup':
                                        # Attempt to parse pairs of (group, level)
                                        try:
                                            import struct as _st
                                            pay = memoryview(mv[q2:q2+kv_len])
                                            rp = 0
                                            cnt = None
                                            if rp + 4 <= len(pay):
                                                cnt = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                            # Guard: if count not plausible, ignore structured parse
                                            if cnt is not None and 0 <= cnt <= 128:
                                                for _ in range(cnt):
                                                    # Read group name as Klei string (best effort)
                                                    if rp + 4 > len(pay):
                                                        break
                                                    glen = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                                    if glen < 0 or rp + glen > len(pay):
                                                        break
                                                    graw = bytes(pay[rp:rp+glen]).decode('utf-8', errors='ignore'); rp += glen
                                                    # Read numeric level (try int32 then float32)
                                                    lvl = None
                                                    if rp + 4 <= len(pay):
                                                        cand = _st.unpack_from('<i', pay, rp)[0]
                                                        if 0 <= cand <= 10:
                                                            lvl = int(cand); rp += 4
                                                    if lvl is None and rp + 4 <= len(pay):
                                                        fv = _st.unpack_from('<f', pay, rp)[0]
                                                        if 0.0 <= fv <= 10.0:
                                                            lvl = int(round(fv)); rp += 4
                                                    if lvl is None:
                                                        # Skip 4 bytes to avoid infinite loop
                                                        rp = min(len(pay), rp + 4)
                                                        continue
                                                    group_key = map_group(graw)
                                                    if group_key:
                                                        prev = aptitudes.get(group_key, 0)
                                                        if lvl > prev:
                                                            aptitudes[group_key] = lvl
                                        except Exception:
                                            pass
                                    elif key == 'MasteryByRoleID':
                                        # Parse mastered roles: array of (roleId, bool)
                                        try:
                                            import struct as _st
                                            pay = memoryview(mv[q2:q2+kv_len])
                                            rp = 0
                                            mastered: List[str] = []
                                            cnt = None
                                            if rp + 4 <= len(pay):
                                                cnt = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                            if cnt is not None and 0 <= cnt <= 256:
                                                for _ in range(cnt):
                                                    if rp + 4 > len(pay):
                                                        break
                                                    glen = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                                    if glen < 0 or rp + glen > len(pay):
                                                        break
                                                    role_id = bytes(pay[rp:rp+glen]).decode('utf-8', errors='ignore'); rp += glen
                                                    # bool may be 1 byte or 4-byte int; try both
                                                    mastered_flag = None
                                                    if rp + 1 <= len(pay):
                                                        mastered_flag = pay[rp] != 0; rp += 1
                                                    if mastered_flag is None and rp + 4 <= len(pay):
                                                        mastered_flag = _st.unpack_from('<i', pay, rp)[0] != 0; rp += 4
                                                    if mastered_flag and role_id:
                                                        mastered.append(role_id)
                                            if mastered:
                                                minion_info.setdefault('mastered_roles', mastered)
                                        except Exception:
                                            pass
                                    # advance
                                    q = q2 + kv_len
                                if role_val:
                                    minion_info.setdefault('job', role_val)
                            except Exception:
                                pass
                            # Secondary pass: scan strings and raw payload to derive aptitudes like Building1, Hauling2, Mining3
                            try:
                                import re
                                # Normalization helpers
                                def map_group(raw: str) -> str:
                                    raw_l = raw.lower()
                                    alias = {
                                        'mining': 'Mining',
                                        'building': 'Building',
                                        'farming': 'Farming',
                                        'ranching': 'Ranching',
                                        'researching': 'Research',
                                        'research': 'Research',
                                        'cooking': 'Cooking',
                                        'arting': 'Art',
                                        'art': 'Art',
                                        'hauling': 'Hauling',
                                        'suits': 'Suits',
                                        'technicals': 'Technicals',
                                        'engineering': 'Engineering',
                                        'basekeeping': 'Basekeeping',
                                        'astronauting': 'Management',
                                        'medicine': 'MedicalAid',
                                        'rocketpiloting': 'Management',
                                        'medicalaid': 'MedicalAid',
                                    }.get(raw_l)
                                    if alias:
                                        return alias
                                    # Prefix mapping for truncated tokens
                                    for pref, mapped in [
                                        ('build', 'Building'), ('resear', 'Research'), ('resea', 'Research'),
                                        ('min', 'Mining'), ('farm', 'Farming'), ('ranch', 'Ranching'),
                                        ('operat', 'Operating'), ('engin', 'Engineering'), ('medica', 'MedicalAid'),
                                        ('med', 'MedicalAid'), ('cook', 'Cooking'), ('art', 'Art'),
                                        ('haul', 'Hauling'), ('tidy', 'Basekeeping'), ('suit', 'Suits'),
                                        ('tech', 'Technicals'), ('pyrotech', 'Technicals'), ('astron', 'Management'),
                                        ('manage', 'Management'),
                                    ]:
                                        if raw_l.startswith(pref):
                                            return mapped
                                    # Fallback: title case the raw
                                    return raw.capitalize()

                                # Allowed max levels per group (based on ONI tiers)
                                max_level = {
                                    'Mining': 3, 'Building': 3, 'Farming': 3, 'Ranching': 2,
                                    'Research': 3, 'Cooking': 2, 'Art': 3, 'Hauling': 2,
                                    'Suits': 1, 'Technicals': 2, 'Engineering': 1,
                                    'Basekeeping': 2, 'Management': 2, 'MedicalAid': 3,
                                }

                                # Pass 1: Klei string scan
                                for s in self._scan_klei_strings(mv, beh_start, beh_end, max_strings=256):
                                    m = re.fullmatch(r"([A-Za-z]+)(\d+)", s)
                                    if m:
                                        group_raw = m.group(1)
                                        level = int(m.group(2))
                                        group_key = map_group(group_raw)
                                        if group_key and group_key in max_level and 1 <= level <= max_level[group_key]:
                                            prev = aptitudes.get(group_key, 0)
                                            if level > prev:
                                                aptitudes[group_key] = level
                                # Pass 2: Raw payload scan (handles fused tokens)
                                payload = bytes(mv[beh_start:beh_end])
                                text = payload.decode('utf-8', errors='ignore')
                                for m in re.finditer(r"\b([A-Za-z]+)(\d+)\b", text):
                                    group_raw = m.group(1)
                                    level = int(m.group(2))
                                    group_key = map_group(group_raw)
                                    if group_key and group_key in max_level and 1 <= level <= max_level[group_key]:
                                        prev = aptitudes.get(group_key, 0)
                                        if level > prev:
                                            aptitudes[group_key] = level
                                if aptitudes:
                                    minion_info.setdefault('aptitudes', aptitudes)
                            except Exception:
                                pass
                            # Fallback: derive from hat tokens present in MinionResume payload
                            if 'job' not in minion_info or minion_info.get('job') in (None, '', 'NoRole'):
                                try:
                                    payload = bytes(mv[beh_start:beh_end])
                                    idx = payload.find(b'hat_role_')
                                    if idx != -1:
                                        j = idx + len(b'hat_role_')
                                        group_bytes = bytearray()
                                        while j < len(payload) and (65 <= payload[j] <= 90 or 97 <= payload[j] <= 122):
                                            group_bytes.append(payload[j]); j += 1
                                        group = group_bytes.decode('ascii', errors='ignore').lower()
                                        exact_map = {
                                            'building': 'Builder', 'mining': 'Miner', 'digging': 'Miner',
                                            'research': 'Researcher', 'cooking': 'Cook', 'cook': 'Cook',
                                            'farming': 'Farmer', 'farmer': 'Farmer', 'ranching': 'Rancher',
                                            'doctor': 'Doctor', 'medical': 'Doctor', 'artist': 'Artist',
                                            'operating': 'Operator', 'operator': 'Operator', 'engineering': 'Engineer',
                                            'engineer': 'Engineer', 'hauling': 'Courier', 'supply': 'Courier',
                                            'tidying': 'Sweeper', 'pyrotechnics': 'Pyrotechnician'
                                        }
                                        base = exact_map.get(group)
                                        if not base:
                                            for pref, role_name in [
                                                ('build', 'Builder'), ('resear', 'Researcher'), ('resea', 'Researcher'), ('min', 'Miner'),
                                                ('farm', 'Farmer'), ('ranch', 'Rancher'), ('operat', 'Operator'),
                                                ('engin', 'Engineer'), ('med', 'Doctor'), ('cook', 'Cook'),
                                                ('art', 'Artist'), ('haul', 'Courier'), ('suppl', 'Courier'),
                                                ('tidy', 'Sweeper'), ('pyrotech', 'Pyrotechnician'), ('ranc', 'Rancher')
                                            ]:
                                                if group.startswith(pref):
                                                    base = role_name
                                                    break
                                        if base:
                                            minion_info.setdefault('job', base)
                                except Exception:
                                    pass
                        elif beh_name in ('Accessorizer', 'WearableAccessorizer'):
                            # Infer role from worn hat strings like 'hat_role_building3'
                            try:
                                strings = self._scan_klei_strings(mv, beh_start, beh_end, max_strings=128)
                                hat_tokens = [s for s in strings if 'hat_role_' in s]
                                def map_hat_to_role(token: str) -> str:
                                    # Extract segment after 'hat_role_'
                                    try:
                                        seg = token.split('hat_role_', 1)[1]
                                    except Exception:
                                        return ''
                                    # Normalize, pick leading alpha+digits
                                    import re
                                    m = re.match(r"([a-zA-Z]+)(\d*)", seg)
                                    if not m:
                                        return ''
                                    group = m.group(1).lower()
                                    tier = m.group(2) or ''
                                    # Map by exact key or by common prefixes to handle truncated tokens
                                    exact_map = {
                                        'building': 'Builder',
                                        'mining': 'Miner',
                                        'digging': 'Miner',
                                        'research': 'Researcher',
                                        'cooking': 'Cook',
                                        'cook': 'Cook',
                                        'farming': 'Farmer',
                                        'farmer': 'Farmer',
                                        'ranching': 'Rancher',
                                        'doctor': 'Doctor',
                                        'medical': 'Doctor',
                                        'artist': 'Artist',
                                        'operating': 'Operator',
                                        'operator': 'Operator',
                                        'engineering': 'Engineer',
                                        'engineer': 'Engineer',
                                        'hauling': 'Courier',
                                        'supply': 'Courier',
                                        'tidying': 'Sweeper',
                                    }
                                    base = exact_map.get(group)
                                    if not base:
                                        # Prefix-based mapping for truncated tokens (e.g., 'build', 'resea', 'min')
                                        prefix_map = [
                                            ('build', 'Builder'),
                                            ('resear', 'Researcher'),
                                            ('min', 'Miner'),
                                            ('farm', 'Farmer'),
                                            ('ranch', 'Rancher'),
                                            ('operat', 'Operator'),
                                            ('engin', 'Engineer'),
                                            ('med', 'Doctor'),
                                            ('cook', 'Cook'),
                                            ('art', 'Artist'),
                                            ('haul', 'Courier'),
                                            ('suppl', 'Courier'),
                                            ('tidy', 'Sweeper'),
                                            ('pyrotech', 'Pyrotechnician'),
                                        ]
                                        for pref, role_name in prefix_map:
                                            if group.startswith(pref):
                                                base = role_name
                                                break
                                    if not base:
                                        base = group.capitalize()
                                    return f"{base}{(' T' + tier) if tier else ''}"
                                for t in hat_tokens:
                                    mapped = map_hat_to_role(t)
                                    if mapped:
                                        minion_info.setdefault('job', mapped)
                                        break
                            except Exception:
                                pass
                        elif beh_name in ('Klei.AI.Traits', 'Traits'):
                            # Extract trait identifiers (structured parse with fallback)
                            try:
                                import struct as _st
                                traits: List[str] = []
                                pay = memoryview(mv[beh_start:beh_end])
                                rp = 0
                                if rp + 4 <= len(pay):
                                    cnt = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                else:
                                    cnt = -1
                                parsed = 0
                                if 0 <= cnt <= 256:
                                    while parsed < cnt and rp < len(pay):
                                        if rp + 4 > len(pay):
                                            break
                                        sl = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                        if sl < 0 or rp + sl > len(pay):
                                            break
                                        s = bytes(pay[rp:rp+sl]).decode('utf-8', errors='ignore'); rp += sl
                                        if s:
                                            traits.append(s)
                                        parsed += 1
                                # Skip generic string scan fallback for traits to avoid unreadable tokens
                                if traits:
                                    # Normalize and keep only known trait ids
                                    alias = {'DiversLung': 'DeeperDiversLungs'}
                                    norm = [alias.get(t, t) for t in traits]
                                    known_only = [t for t in norm if t in self._KNOWN_TRAIT_IDS]
                                    if known_only:
                                        minion_info.setdefault('traits', sorted(list(dict.fromkeys(known_only))))
                            except Exception:
                                pass
                        elif beh_name in ('Klei.AI.Effects', 'Effects'):
                            # Extract active effects/statuses (structured parse with fallback)
                            try:
                                import struct as _st, re
                                effects: List[str] = []
                                pay = memoryview(mv[beh_start:beh_end])
                                # The above had a typo; correct variable name
                            except Exception:
                                pass
                            try:
                                import struct as _st, re
                                effects: List[str] = []
                                pay = memoryview(mv[beh_start:beh_end])
                                rp = 0
                                cnt = None
                                if rp + 4 <= len(pay):
                                    cnt = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                parsed = 0
                                if cnt is not None and 0 <= cnt <= 512:
                                    while parsed < cnt and rp < len(pay):
                                        if rp + 4 > len(pay):
                                            break
                                        sl = _st.unpack_from('<i', pay, rp)[0]; rp += 4
                                        if sl < 0 or rp + sl > len(pay):
                                            break
                                        s = bytes(pay[rp:rp+sl]).decode('utf-8', errors='ignore'); rp += sl
                                        if s:
                                            effects.append(s)
                                        parsed += 1
                                if not effects:
                                    strings = self._scan_klei_strings(mv, beh_start, beh_end, max_strings=256)
                                    for s in strings:
                                        if not s or len(s) > 64:
                                            continue
                                        if any(ch in s for ch in (' ', '/', '\\')):
                                            continue
                                        if '_' in s or re.fullmatch(r"[A-Z][A-Za-z]+", s):
                                            effects.append(s)
                                if effects:
                                    known = [e for e in effects if e in self._KNOWN_EFFECT_IDS]
                                    if known:
                                        minion_info.setdefault('effects', sorted(list(dict.fromkeys(known))))
                                    else:
                                        # Prefer empty effects list over unreadable placeholders
                                        minion_info.setdefault('effects', [])
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
                                    'Decor': ('decor', -1000.0, 1000.0),
                                    'Temperature': ('temperature', 0.0, 1000.0),
                                    'Breath': ('breath', 0.0, 100.0),
                                    'Bladder': ('bladder', 0.0, 100.0),
                                    'ImmuneLevel': ('immune_level', 0.0, 100.0),
                                    'Toxicity': ('toxicity', 0.0, 100.0),
                                    'RadiationBalance': ('radiation_balance', -10000.0, 10000.0),
                                    'QualityOfLife': ('morale', -1000.0, 1000.0),
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
                    # Always provide list fields
                    minion_info.setdefault('traits', [])
                    minion_info.setdefault('effects', [])
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
        """Parse type templates section (minimal frame reader with names only).

        This does not fully decode template schemas, but collects template
        names so downstream object parsing can align by behavior name.
        """
        templates = TypeTemplates()
        try:
            # Heuristic: peek remaining bytes and scan for behavior/template names.
            start_pos = reader.get_position()
            remaining = reader.remaining_bytes()
            blob = reader.read_bytes(remaining) if remaining > 0 else b""
            # Restore stream position for subsequent sections
            reader.seek(start_pos)

            mv = memoryview(blob)
            names: List[str] = []
            # Collect plausible ASCII names like MinionIdentity, MinionResume, MinionModifiers
            for key in (b"MinionIdentity", b"MinionResume", b"MinionModifiers", b"Klei.AI.Traits", b"Klei.AI.Effects"):
                idx = blob.find(key)
                if idx != -1:
                    names.append(key.decode('utf-8'))
            # Deduplicate and store
            seen = set()
            for n in names:
                if n in seen:
                    continue
                seen.add(n)
                templates.templates.append(TypeTemplate(name=n, template_data={}))
            if not names:
                result.add_warning("Type templates parsing minimal: names not detected")
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
