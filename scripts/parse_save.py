#!/usr/bin/env python3
from __future__ import annotations

"""
CLI: Parse an ONI .sav file and emit the extractor contract JSON.

Usage:
  python scripts/parse_save.py test_data/clone_laboratory.sav --out test_data/analysis_results/parse_results.json
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from src.oni_ai_agents.services.oni_save_parser import OniSaveParser
from src.oni_ai_agents.services.oni_save_parser.data_extractor import SaveFileDataExtractor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse ONI save and output JSON contract")
    parser.add_argument("save_path", type=str, help="Path to .sav file")
    parser.add_argument("--out", type=str, default="-", help="Output JSON file path or '-' for stdout")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    save_path = Path(args.save_path)
    if not save_path.exists():
        raise SystemExit(f"Save file not found: {save_path}")

    parser = OniSaveParser()
    result = parser.parse_save_file(save_path)
    if not result.success or result.save_game is None:
        raise SystemExit(f"Failed to parse save: {result.error_message}")

    extractor = SaveFileDataExtractor()
    doc: Dict[str, Any] = extractor.extract(result.save_game, result.entities)

    out_path = args.out
    if out_path == "-":
        print(json.dumps(doc, indent=args.indent, sort_keys=False))
    else:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(doc, indent=args.indent, sort_keys=False))
        print(f"Wrote {out_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


