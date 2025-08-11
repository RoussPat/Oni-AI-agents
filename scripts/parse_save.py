#!/usr/bin/env python3
from __future__ import annotations

"""
CLI: Parse an ONI .sav file and emit the extractor contract JSON.

Usage:
  python scripts/parse_save.py test_data/clone_laboratory.sav \
    --out test_data/analysis_results/parse_results.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from src.oni_ai_agents.services.oni_save_parser import OniSaveParser
    from src.oni_ai_agents.services.oni_save_parser.data_extractor import (
        SaveFileDataExtractor,
    )
except Exception:  # pragma: no cover - fallback for direct script runs
    # Ensure project root is on sys.path so `src` is importable
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.oni_ai_agents.services.oni_save_parser import OniSaveParser
    from src.oni_ai_agents.services.oni_save_parser.data_extractor import (
        SaveFileDataExtractor,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse ONI save and output JSON contract"
    )
    parser.add_argument("save_path", type=str, help="Path to .sav file")
    parser.add_argument(
        "--out", type=str, default="-", help="Output JSON file path or '-' for stdout"
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON (indent=2)"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress parser logs to stdout"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    save_path = Path(args.save_path)
    if not save_path.exists():
        raise SystemExit(f"Save file not found: {save_path}")

    import logging as _logging

    _logging.basicConfig(level=_logging.ERROR if args.quiet else _logging.INFO)

    parser = OniSaveParser()
    result = parser.parse_save_file(save_path)
    if not result.success or result.save_game is None:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": result.error_message,
                    "warnings": result.warnings,
                },
                indent=2 if args.pretty else None,
            )
        )
        raise SystemExit(1)

    extractor = SaveFileDataExtractor()
    doc: Dict[str, Any] = extractor.extract(result.save_game, result.entities)

    out_path = args.out
    indent = 2 if args.pretty else None
    if out_path == "-":
        print(json.dumps(doc, indent=indent, sort_keys=False))
    else:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(doc, indent=indent, sort_keys=False))
        print(f"Wrote {out_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
