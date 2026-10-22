#!/usr/bin/env python3
"""Roll random territories for house rules from a TripleA save (.tsvg).

See triplea_rolls.py for the rules and territory classification.

Usage:
    python triplea-helper.py CareService_Italy_R24.tsvg
"""

import argparse
import sys

from triplea_rolls import roll_save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("savefile")
    args = parser.parse_args()

    with open(args.savefile, "rb") as f:
        result = roll_save(f)

    print(f"Game: {result['game']} | Round: {result['round']}\n", file=sys.stderr)
    for r in result["rolls"]:
        label = f"{r['kind']:<14} — {r['side'] + ':':<8}"
        print(f"{label}{r['territory']}, (Current owner: {r['owner']})")


if __name__ == "__main__":
    main()
