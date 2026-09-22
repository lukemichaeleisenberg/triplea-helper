# triplea-helper

Utilities for reading TripleA save files (`.tsvg`) outside the game.

A `.tsvg` is a gzip-compressed Java serialization stream of TripleA's
`GameData` object. These scripts parse it generically with `javaobj-py3`,
so no TripleA install or JVM is required. Tested against engine build
2026-06.16 saves of Global 1940 Balanced Mod3.

## Setup

```sh
uv venv .venv
uv pip install -r requirements.txt --python .venv/bin/python
source .venv/bin/activate
```

Plain `python3 -m venv` also works, but not with Homebrew's
`python@3.14`, which has a broken `ensurepip` (venv creation fails).
`uv` provisions its own CPython and sidesteps that.

## Scripts

### triplea-helper.py

Rolls the four territories that seed a round's house-rule board changes.
The script only reports *where*; players carry out the physical actions
(sacrificing a unit to build a minor factory, placing partisans).

Rolls, in order:

1. **Infrastructure — Axis** — re-roll until an Axis territory.
2. **Infrastructure — Allied** — re-roll until an Allied territory.
3. **Partisans — Axis** — partisans behind enemy lines: re-roll until an
   Allied, neutral, or pro-Allied territory.
4. **Partisans — Allied** — partisans behind enemy lines: re-roll until an
   Axis, neutral, or pro-Axis territory.

Each roll is independent, so a territory can be picked more than once.
Each line names the territory and, in parentheses, the power that
currently owns it.

```sh
python triplea-helper.py path/to/save.tsvg
```

Territory classification (from the save's `AllianceTracker`):

- **Axis / Allies** — power whose alliance is `Axis` / `Allies`. The Dutch
  count as Allied.
- **Pro-Axis / Pro-Allies** — the map's pro-aligned neutral pseudo-powers
  (`Neutral_Axis` / `Neutral_Allies`).
- **Neutral** — strict neutrals and any other unaligned owner.
- The Mongolians are excluded from every pool.
- Land only, no sea zones.
- Ownership is current, not original — captured territory counts for
  its occupier.

## Notes

Field names (`map`, `territories`, `owner`, `water`, `alliances`) come
from TripleA internals, not a public API. A future engine refactor could
break parsing.
