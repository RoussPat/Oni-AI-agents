"""
Known ONI IDs for traits and effects, loaded from research TypeScript sources when available.

Falls back to embedded subsets if research files are not present.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set

FALLBACK_TRAIT_IDS: Set[str] = {
    'SmallBladder',
    'Narcolepsy',
    'Flatulence',
    'Anemic',
    'MouthBreather',
    'BingeEater',
    'StressVomiter',
    'UglyCrier',
    'EarlyBird',
    'NightOwl',
    'FastLearner',
    'SlowLearner',
    'NoodleArms',
    'StrongArm',
    'IronGut',
    'WeakImmuneSystem',
    'StrongImmuneSystem',
    'DeeperDiversLungs',
    'Snorer',
    'BalloonArtist',
    'SparkleStreaker',
    'StickerBomber',
    'InteriorDecorator',
    'Uncultured',
    'Allergies',
    'Hemophobia',
    'Claustrophobic',
    'SolitarySleeper',
    'Workaholic',
    'Aggressive',
    'Foodie',
    'SimpleTastes',
    'Greasemonkey',
    'MoleHands',
    'Twinkletoes',
    'SunnyDisposition',
    'RockCrusher',
    'BedsideManner',
    'Archaeologist',
}

FALLBACK_EFFECT_IDS: Set[str] = {
    'UncomfortableSleep',
    'Sleep',
    'NarcolepticSleep',
    'RestfulSleep',
    'AnewHope',
    'Mourning',
    'DisturbedSleep',
    'NewCrewArrival',
    'UnderWater',
    'FullBladder',
    'StressfulyEmptyingBladder',
    'RedAlert',
    'MentalBreak',
    'CoolingDown',
    'WarmingUp',
    'Darkness',
    'SteppedInContaminatedWater',
    'WellFed',
    'StaleFood',
    'SmelledPutridOdour',
    'Vomiting',
    'DirtyHands',
    'Unclean',
    'LightWounds',
    'ModerateWounds',
    'SevereWounds',
    'WasAttacked',
    'SoreBack',
    'WarmAir',
    'ColdAir',
    'Hypothermia',
    'Hyperthermia',
    'CenterOfAttention',
}


def _extract_ts_string_array(ts_text: str, array_name: str) -> List[str]:
    # crude parse: find array_name = [ ... ]; then extract quoted strings
    m = re.search(rf"{re.escape(array_name)}\s*:\s*[^=]*=\s*\[(.*?)\]", ts_text, re.S)
    if not m:
        # try simple const array = [...]
        m = re.search(rf"const\s+{re.escape(array_name)}\s*:\s*[^=]*=\s*\[(.*?)\]", ts_text, re.S)
    if not m:
        return []
    inner = m.group(1)
    return [s.strip('"\'') for s in re.findall(r"['\"]([^'\"]+)['\"]", inner)]


def _load_ids_from_ts(relative_path: str, array_name: str) -> List[str]:
    # locate project root from this file
    here = Path(__file__).resolve()
    root = here.parents[4] if len(here.parents) >= 5 else here.parents[-1]
    ts_path = root / relative_path
    try:
        text = ts_path.read_text(encoding='utf-8')
        return _extract_ts_string_array(text, array_name)
    except Exception:
        return []


def load_known_trait_ids() -> Set[str]:
    ids = set(
        _load_ids_from_ts(
            'research/robophred-js/src/save-structure/game-objects/game-object-behavior/known-behaviors/ai-traits.ts',
            'AI_TRAIT_IDS',
        )
    )
    return ids or set(FALLBACK_TRAIT_IDS)


def load_known_effect_ids() -> Set[str]:
    ids = set(
        _load_ids_from_ts(
            'research/robophred-js/src/save-structure/game-objects/game-object-behavior/known-behaviors/ai-effects.ts',
            'AI_EFFECT_IDS',
        )
    )
    return ids or set(FALLBACK_EFFECT_IDS)


