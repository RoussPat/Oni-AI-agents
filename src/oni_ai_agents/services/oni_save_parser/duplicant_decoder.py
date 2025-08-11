"""
Duplicant decoder utilities.

Extract duplicant identities, roles, vitals, traits, and effects from KSAV
body.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from .known_ids import load_known_effect_ids, load_known_trait_ids


class DuplicantDecoder:
    """Decode duplicant-related info from a decompressed KSAV body."""

    def __init__(self) -> None:
        self._known_traits: Set[str] = load_known_trait_ids()
        self._known_effects: Set[str] = load_known_effect_ids()

    # ---- small helpers mirroring existing parser private methods ----
    def _read_klei_string(
        self, mv: memoryview, off: int, end: int
    ) -> Tuple[Optional[str], int]:
        import struct

        if off + 4 > end:
            return None, off
        length = struct.unpack_from("<i", mv, off)[0]
        off += 4
        if length < 0 or off + length > end:
            return None, off
        s = bytes(mv[off:off + length]).decode("utf-8", errors="ignore")
        off += length
        return s, off

    def _scan_klei_strings(
        self, mv: memoryview, start: int, end: int, max_strings: int = 32
    ) -> List[str]:
        import struct

        strings: List[str] = []
        p = start
        scanned = 0
        while p + 4 <= end and scanned < max_strings:
            try:
                strlen = struct.unpack_from("<i", mv, p)[0]
                if strlen < 0 or strlen > (end - p - 4):
                    p += 1
                    continue
                p += 4
                s = bytes(mv[p:p + strlen]).decode("utf-8", errors="ignore")
                p += strlen
                if s:
                    strings.append(s)
                    scanned += 1
            except Exception:
                p += 1
        return strings

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

    def _scan_best_float32(
        self,
        mv: memoryview,
        start: int,
        end: int,
        min_val: float,
        max_val: float,
    ) -> Optional[float]:
        import math
        import struct

        best = None
        p = start
        while p + 4 <= end:
            try:
                v = struct.unpack_from("<f", mv, p)[0]
                if math.isfinite(v) and min_val <= v <= max_val:
                    best = float(v)
            except Exception:
                pass
            p += 1
        return best

    # ---- behavior decoders ----
    def _parse_minion_identity(
        self, mv: memoryview, beh_start: int, beh_end: int
    ) -> Dict[str, Any]:
        import struct as _st

        identity: Dict[str, Any] = {}
        q = beh_start
        found_name = False
        while q < beh_end:
            key, q2 = self._read_klei_string(mv, q, beh_end)
            if key is None:
                q += 1
                continue
            if q2 + 4 > beh_end:
                break
            kv_len = _st.unpack_from("<i", mv, q2)[0]
            q2 += 4
            if kv_len < 0 or q2 + kv_len > beh_end:
                q = q2
                continue
            if key in ("name", "nameStringKey", "gender", "genderStringKey"):
                try:
                    payload = bytes(mv[q2 : q2 + kv_len])
                    if len(payload) >= 4:
                        slen = _st.unpack_from("<i", payload, 0)[0]
                        if 0 <= slen <= len(payload) - 4:
                            s = payload[4 : 4 + slen].decode("utf-8", errors="ignore")
                            if key == "name" and s and self._is_plausible_name(s):
                                identity["name"] = s
                                found_name = True
                            elif key == "gender" and s in ("MALE", "FEMALE", "NB"):
                                identity["gender"] = s
                except Exception:
                    pass
            elif key == "arrivalTime":
                try:
                    if kv_len >= 4:
                        at32 = _st.unpack_from("<i", mv, q2)[0]
                        if 0 <= at32 < 10 ** 10:
                            identity["arrival_time"] = int(at32)
                    if "arrival_time" not in identity and kv_len >= 8:
                        at64 = _st.unpack_from("<q", mv, q2)[0]
                        if 0 <= at64 < 10 ** 12:
                            identity["arrival_time"] = int(at64)
                    if "arrival_time" not in identity and kv_len >= 4:
                        af32 = _st.unpack_from("<f", mv, q2)[0]
                        if 0.0 <= af32 < 10 ** 10:
                            identity["arrival_time"] = int(af32)
                    if "arrival_time" not in identity and kv_len >= 8:
                        af64 = _st.unpack_from("<d", mv, q2)[0]
                        if 0.0 <= af64 < 10 ** 12:
                            identity["arrival_time"] = int(af64)
                except Exception:
                    pass
            q = q2 + kv_len

        if not found_name:
            for cand in self._scan_klei_strings(mv, beh_start, beh_end, max_strings=32):
                if self._is_plausible_name(cand):
                    identity["name"] = cand
                    break
        return identity

    def _parse_minion_resume(
        self, mv: memoryview, beh_start: int, beh_end: int
    ) -> Dict[str, Any]:
        import struct as _st

        result: Dict[str, Any] = {}
        aptitudes: Dict[str, int] = {}

        def map_group(raw: str) -> str:
            raw_l = raw.lower()
            alias = {
                "mining": "Mining",
                "building": "Building",
                "farming": "Farming",
                "ranching": "Ranching",
                "researching": "Research",
                "research": "Research",
                "cooking": "Cooking",
                "arting": "Art",
                "art": "Art",
                "hauling": "Hauling",
                "suits": "Suits",
                "technicals": "Technicals",
                "engineering": "Engineering",
                "basekeeping": "Basekeeping",
                "astronauting": "Management",
                "medicine": "MedicalAid",
                "rocketpiloting": "Management",
                "medicalaid": "MedicalAid",
            }.get(raw_l)
            if alias:
                return alias
            for pref, mapped in [
                ("build", "Building"),
                ("resear", "Research"),
                ("resea", "Research"),
                ("min", "Mining"),
                ("farm", "Farming"),
                ("ranch", "Ranching"),
                ("operat", "Operating"),
                ("engin", "Engineering"),
                ("medica", "MedicalAid"),
                ("med", "MedicalAid"),
                ("cook", "Cooking"),
                ("art", "Art"),
                ("haul", "Hauling"),
                ("tidy", "Basekeeping"),
                ("suit", "Suits"),
                ("tech", "Technicals"),
                ("pyrotech", "Technicals"),
                ("astron", "Management"),
                ("manage", "Management"),
            ]:
                if raw_l.startswith(pref):
                    return mapped
            return raw.capitalize()

        q = beh_start
        while q < beh_end:
            key, q2 = self._read_klei_string(mv, q, beh_end)
            if key is None:
                q += 1
                continue
            if q2 + 4 > beh_end:
                break
            kv_len = _st.unpack_from("<i", mv, q2)[0]
            q2 += 4
            if kv_len < 0 or q2 + kv_len > beh_end:
                q = q2
                continue
            if key == "currentRole":
                try:
                    payload = bytes(mv[q2 : q2 + kv_len])
                    if len(payload) >= 4:
                        slen = _st.unpack_from("<i", payload, 0)[0]
                        if 0 <= slen <= len(payload) - 4:
                            s = payload[4 : 4 + slen].decode("utf-8", errors="ignore")
                            if s:
                                result["currentRole"] = s
                except Exception:
                    pass
            elif key == "AptitudeBySkillGroup":
                try:
                    pay = memoryview(mv[q2 : q2 + kv_len])
                    rp = 0
                    cnt = None
                    if rp + 4 <= len(pay):
                        cnt = _st.unpack_from("<i", pay, rp)[0]
                        rp += 4
                    if cnt is not None and 0 <= cnt <= 128:
                        for _ in range(cnt):
                            if rp + 4 > len(pay):
                                break
                            glen = _st.unpack_from("<i", pay, rp)[0]
                            rp += 4
                            if glen < 0 or rp + glen > len(pay):
                                break
                            graw = bytes(pay[rp : rp + glen]).decode("utf-8", errors="ignore")
                            rp += glen
                            lvl = None
                            if rp + 4 <= len(pay):
                                cand = _st.unpack_from("<i", pay, rp)[0]
                                if 0 <= cand <= 10:
                                    lvl = int(cand)
                                    rp += 4
                            if lvl is None and rp + 4 <= len(pay):
                                fv = _st.unpack_from("<f", pay, rp)[0]
                                if 0.0 <= fv <= 10.0:
                                    lvl = int(round(fv))
                                    rp += 4
                            if lvl is None:
                                rp = min(len(pay), rp + 4)
                                continue
                            group_key = map_group(graw)
                            if group_key:
                                prev = aptitudes.get(group_key, 0)
                                if lvl > prev:
                                    aptitudes[group_key] = lvl
                except Exception:
                    pass
            elif key == "MasteryByRoleID":
                try:
                    pay = memoryview(mv[q2 : q2 + kv_len])
                    rp = 0
                    mastered: List[str] = []
                    cnt = None
                    if rp + 4 <= len(pay):
                        cnt = _st.unpack_from("<i", pay, rp)[0]
                        rp += 4
                    if cnt is not None and 0 <= cnt <= 256:
                        for _ in range(cnt):
                            if rp + 4 > len(pay):
                                break
                            glen = _st.unpack_from("<i", pay, rp)[0]
                            rp += 4
                            if glen < 0 or rp + glen > len(pay):
                                break
                            role_id = bytes(pay[rp : rp + glen]).decode("utf-8", errors="ignore")
                            rp += glen
                            mastered_flag = None
                            if rp + 1 <= len(pay):
                                mastered_flag = pay[rp] != 0
                                rp += 1
                            if mastered_flag is None and rp + 4 <= len(pay):
                                mastered_flag = _st.unpack_from("<i", pay, rp)[0] != 0
                                rp += 4
                            if mastered_flag and role_id:
                                mastered.append(role_id)
                    if mastered:
                        result["mastered_roles"] = mastered
                except Exception:
                    pass
            q = q2 + kv_len

        if aptitudes:
            result["aptitudes"] = aptitudes
        return result

    def _parse_minion_modifiers(
        self, mv: memoryview, beh_start: int, beh_end: int
    ) -> Dict[str, float]:
        import struct as _st

        vitals: Dict[str, float] = {}
        label_map = {
            "Calories": ("calories", 0.0, 1e9),
            "Health": ("health", 0.0, 1000.0),
            "Stress": ("stress", 0.0, 100.0),
            "Stamina": ("stamina", 0.0, 100.0),
            "Decor": ("decor", -1000.0, 1000.0),
            "Temperature": ("temperature", 0.0, 1000.0),
            "Breath": ("breath", 0.0, 100.0),
            "Bladder": ("bladder", 0.0, 100.0),
            "ImmuneLevel": ("immune_level", 0.0, 100.0),
            "Toxicity": ("toxicity", 0.0, 100.0),
            "RadiationBalance": ("radiation_balance", -10000.0, 10000.0),
            "QualityOfLife": ("morale", -1000.0, 1000.0),
        }
        q = beh_start
        while q + 8 <= beh_end:
            name_s, q2 = self._read_klei_string(mv, q, beh_end)
            if name_s is None:
                q += 1
                continue
            if q2 + 4 > beh_end:
                break
            c_len = _st.unpack_from("<i", mv, q2)[0]
            q2 += 4
            if c_len < 0 or q2 + c_len > beh_end:
                q = q2
                continue
            if name_s in label_map:
                key, vmin, vmax = label_map[name_s]
                val = self._scan_best_float32(mv, q2, q2 + c_len, vmin, vmax)
                if val is not None:
                    vitals[key] = float(val)
            q = q2 + c_len
        return vitals

    # ---- main entry ----
    def extract_minion_details_from_body(self, body: bytes) -> List[Dict[str, Any]]:
        import re
        import struct

        mv = memoryview(body)
        ksav = body.find(b"KSAV")
        if ksav == -1:
            return []
        p = ksav + 4
        if p + 8 > len(body):
            return []
        _ = struct.unpack_from("<i", mv, p)[0]
        p += 4
        _ = struct.unpack_from("<i", mv, p)[0]
        p += 4
        if p + 4 > len(body):
            return []
        try:
            group_count = struct.unpack_from("<i", mv, p)[0]
            p += 4
        except Exception:
            return []
        minions: List[Dict[str, Any]] = []
        for _ in range(max(0, group_count)):
            if p + 4 > len(body):
                break
            name_len = struct.unpack_from("<i", mv, p)[0]
            p += 4
            if name_len < 0 or p + name_len > len(body):
                break
            name = bytes(mv[p : p + name_len]).decode("utf-8", errors="ignore")
            p += name_len
            if p + 8 > len(body):
                break
            instance_count = struct.unpack_from("<i", mv, p)[0]
            p += 4
            data_length = struct.unpack_from("<i", mv, p)[0]
            p += 4
            group_data_start = p
            if name == "Minion" and instance_count > 0:
                for _i in range(instance_count):
                    if p + (3 + 4 + 3) * 4 + 1 + 4 > len(body):
                        break
                    x, y, z = struct.unpack_from("<fff", mv, p)
                    p += 12
                    p += 16
                    p += 12
                    p += 1
                    behavior_count = struct.unpack_from("<i", mv, p)[0]
                    p += 4
                    minion_info: Dict[str, Any] = {"x": float(x), "y": float(y), "z": float(z)}
                    for _b in range(max(0, behavior_count)):
                        if p + 4 > len(body):
                            break
                        beh_name_len = struct.unpack_from("<i", mv, p)[0]
                        p += 4
                        if beh_name_len < 0 or p + beh_name_len > len(body):
                            break
                        beh_name = bytes(mv[p : p + beh_name_len]).decode("utf-8", errors="ignore")
                        p += beh_name_len
                        if p + 4 > len(body):
                            break
                        beh_len = struct.unpack_from("<i", mv, p)[0]
                        p += 4
                        beh_start = p
                        beh_end = p + max(0, beh_len)
                        if beh_end > len(body):
                            break
                        if beh_name == "MinionIdentity":
                            try:
                                ident = self._parse_minion_identity(mv, beh_start, beh_end)
                                if ident.get("name"):
                                    minion_info["name"] = ident["name"]
                                if ident.get("gender"):
                                    minion_info["gender"] = ident["gender"]
                                if ident.get("arrival_time") is not None:
                                    minion_info["arrival_time"] = int(ident["arrival_time"])
                            except Exception:
                                pass
                        elif beh_name in ("MinionResume",):
                            try:
                                resume = self._parse_minion_resume(mv, beh_start, beh_end)
                                if resume.get("currentRole"):
                                    minion_info.setdefault("job", resume["currentRole"])
                                if resume.get("aptitudes"):
                                    minion_info.setdefault("aptitudes", resume["aptitudes"])
                                if resume.get("mastered_roles"):
                                    minion_info.setdefault("mastered_roles", resume["mastered_roles"])
                            except Exception:
                                pass
                        elif beh_name in ("Klei.AI.Traits", "Traits"):
                            try:
                                import struct as _st

                                traits: List[str] = []
                                pay = memoryview(mv[beh_start:beh_end])
                                rp = 0
                                if rp + 4 <= len(pay):
                                    cnt = _st.unpack_from("<i", pay, rp)[0]
                                    rp += 4
                                else:
                                    cnt = -1
                                parsed = 0
                                if 0 <= cnt <= 256:
                                    while parsed < cnt and rp < len(pay):
                                        if rp + 4 > len(pay):
                                            break
                                        sl = _st.unpack_from("<i", pay, rp)[0]
                                        rp += 4
                                        if sl < 0 or rp + sl > len(pay):
                                            break
                                        s = bytes(pay[rp : rp + sl]).decode("utf-8", errors="ignore")
                                        rp += sl
                                        if s:
                                            traits.append(s)
                                        parsed += 1
                                if traits:
                                    alias = {"DiversLung": "DeeperDiversLungs"}
                                    norm = [alias.get(t, t) for t in traits]
                                    known_only = [t for t in norm if t in self._known_traits]
                                    if known_only:
                                        minion_info.setdefault("traits", sorted(list(dict.fromkeys(known_only))))
                            except Exception:
                                pass
                        elif beh_name in ("Klei.AI.Effects", "Effects"):
                            try:
                                import struct as _st

                                effects: List[str] = []
                                pay = memoryview(mv[beh_start:beh_end])
                                rp = 0
                                cnt = None
                                if rp + 4 <= len(pay):
                                    cnt = _st.unpack_from("<i", pay, rp)[0]
                                    rp += 4
                                parsed = 0
                                if cnt is not None and 0 <= cnt <= 512:
                                    while parsed < cnt and rp < len(pay):
                                        if rp + 4 > len(pay):
                                            break
                                        sl = _st.unpack_from("<i", pay, rp)[0]
                                        rp += 4
                                        if sl < 0 or rp + sl > len(pay):
                                            break
                                        s = bytes(pay[rp : rp + sl]).decode("utf-8", errors="ignore")
                                        rp += sl
                                        if s:
                                            effects.append(s)
                                        parsed += 1
                                if effects:
                                    known = [e for e in effects if e in self._known_effects]
                                    if known:
                                        minion_info.setdefault("effects", sorted(list(dict.fromkeys(known))))
                                    else:
                                        minion_info.setdefault("effects", [])
                            except Exception:
                                pass
                        elif beh_name in ("MinionModifiers", "Modifiers"):
                            try:
                                vit = self._parse_minion_modifiers(mv, beh_start, beh_end)
                                if vit:
                                    minion_info.setdefault("vitals", {}).update(vit)
                            except Exception:
                                pass
                        elif beh_name in ("MinionResume",):
                            # Secondary pass: derive aptitudes by scanning payload text for tokens like Building1
                            try:
                                def map_group(raw: str) -> str:
                                    raw_l = raw.lower()
                                    alias = {
                                        "mining": "Mining",
                                        "building": "Building",
                                        "farming": "Farming",
                                        "ranching": "Ranching",
                                        "researching": "Research",
                                        "research": "Research",
                                        "cooking": "Cooking",
                                        "arting": "Art",
                                        "art": "Art",
                                        "hauling": "Hauling",
                                        "suits": "Suits",
                                        "technicals": "Technicals",
                                        "engineering": "Engineering",
                                        "basekeeping": "Basekeeping",
                                        "astronauting": "Management",
                                        "medicine": "MedicalAid",
                                        "rocketpiloting": "Management",
                                        "medicalaid": "MedicalAid",
                                    }.get(raw_l)
                                    if alias:
                                        return alias
                                    for pref, mapped in [
                                        ("build", "Building"),
                                        ("resear", "Research"),
                                        ("resea", "Research"),
                                        ("min", "Mining"),
                                        ("farm", "Farming"),
                                        ("ranch", "Ranching"),
                                        ("operat", "Operating"),
                                        ("engin", "Engineering"),
                                        ("medica", "MedicalAid"),
                                        ("med", "MedicalAid"),
                                        ("cook", "Cooking"),
                                        ("art", "Art"),
                                        ("haul", "Hauling"),
                                        ("tidy", "Basekeeping"),
                                        ("suit", "Suits"),
                                        ("tech", "Technicals"),
                                        ("pyrotech", "Technicals"),
                                        ("astron", "Management"),
                                        ("manage", "Management"),
                                    ]:
                                        if raw_l.startswith(pref):
                                            return mapped
                                    return raw.capitalize()

                                max_level = {
                                    "Mining": 3,
                                    "Building": 3,
                                    "Farming": 3,
                                    "Ranching": 2,
                                    "Research": 3,
                                    "Cooking": 2,
                                    "Art": 3,
                                    "Hauling": 2,
                                    "Suits": 1,
                                    "Technicals": 2,
                                    "Engineering": 1,
                                    "Basekeeping": 2,
                                    "Management": 2,
                                    "MedicalAid": 3,
                                }

                                payload = bytes(mv[beh_start:beh_end])
                                text = payload.decode("utf-8", errors="ignore")
                                found: Dict[str, int] = {}
                                for m in re.finditer(r"\b([A-Za-z]+)(\d+)\b", text):
                                    group_raw = m.group(1)
                                    level = int(m.group(2))
                                    group_key = map_group(group_raw)
                                    if group_key and group_key in max_level and 1 <= level <= max_level[group_key]:
                                        prev = found.get(group_key, 0)
                                        if level > prev:
                                            found[group_key] = level
                                if found:
                                    minion_info.setdefault("aptitudes", found)
                            except Exception:
                                pass
                        elif beh_name in ("Accessorizer", "WearableAccessorizer"):
                            # Infer role from worn hat strings like 'hat_role_building3'
                            try:
                                strings = self._scan_klei_strings(
                                    mv, beh_start, beh_end, max_strings=128
                                )
                                hat_tokens = [s for s in strings if "hat_role_" in s]

                                def map_hat_to_role(token: str) -> str:
                                    try:
                                        seg = token.split("hat_role_", 1)[1]
                                    except Exception:
                                        return ""
                                    m2 = re.match(r"([a-zA-Z]+)(\d*)", seg)
                                    if not m2:
                                        return ""
                                    group = (m2.group(1) or "").lower()
                                    tier = m2.group(2) or ""
                                    exact_map = {
                                        "building": "Builder",
                                        "mining": "Miner",
                                        "digging": "Miner",
                                        "research": "Researcher",
                                        "cooking": "Cook",
                                        "cook": "Cook",
                                        "farming": "Farmer",
                                        "farmer": "Farmer",
                                        "ranching": "Rancher",
                                        "doctor": "Doctor",
                                        "medical": "Doctor",
                                        "artist": "Artist",
                                        "operating": "Operator",
                                        "operator": "Operator",
                                        "engineering": "Engineer",
                                        "engineer": "Engineer",
                                        "hauling": "Courier",
                                        "supply": "Courier",
                                        "tidying": "Sweeper",
                                    }
                                    base = exact_map.get(group)
                                    if not base:
                                        prefix_map = [
                                            ("build", "Builder"),
                                            ("resear", "Researcher"),
                                            ("min", "Miner"),
                                            ("farm", "Farmer"),
                                            ("ranch", "Rancher"),
                                            ("operat", "Operator"),
                                            ("engin", "Engineer"),
                                            ("med", "Doctor"),
                                            ("cook", "Cook"),
                                            ("art", "Artist"),
                                            ("haul", "Courier"),
                                            ("suppl", "Courier"),
                                            ("tidy", "Sweeper"),
                                            ("pyrotech", "Pyrotechnician"),
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
                                        minion_info.setdefault("job", mapped)
                                        break
                            except Exception:
                                pass
                        p = beh_end
                    minion_info.setdefault("arrival_time", 0)
                    minion_info.setdefault("job", "NoRole")
                    minion_info.setdefault("traits", [])
                    minion_info.setdefault("effects", [])
                    minions.append(minion_info)
            else:
                p = group_data_start + max(0, data_length)
                if p > len(body):
                    break
        return minions


