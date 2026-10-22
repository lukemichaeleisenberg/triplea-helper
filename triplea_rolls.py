"""Roll random territories for house rules from a TripleA save (.tsvg).

Produces the four rolls that seed a round's house-rule board changes.
The physical actions they trigger (sacrificing a unit to build a minor
factory, placing partisan units) are done by the players afterward — this
only reports *where*. Alliance membership is read from the save's
AllianceTracker, so it works on any map that defines Axis/Allies.

Rolls, in order:

1. Infrastructure — Axis:   re-roll until an Axis territory.
2. Infrastructure — Allied: re-roll until an Allied territory.
3. Partisans — Axis:  partisans behind enemy lines — re-roll until an
   Allied, neutral, or pro-Allied territory.
4. Partisans — Allied: partisans behind enemy lines — re-roll until an
   Axis, neutral, or pro-Axis territory.

Territory classification (from the AllianceTracker):

- Axis / Allies  — power whose alliance is Axis / Allies. Dutch count
  as Allied.
- Pro-Axis / Pro-Allies — the map's pro-aligned neutral pseudo-powers
  (Neutral_Axis / Neutral_Allies).
- Neutral — strict neutrals and anything else unaligned.
- Mongolians are excluded from every pool.

Shared by the CLI (triplea-helper.py) and the web API (api/roll.py).
"""

import gzip
import random
from collections import defaultdict

import javaobj.v2 as javaobj

ROLLS = [
    ("Infrastructure", "Axis", ["Axis"]),
    ("Infrastructure", "Allied", ["Allies"]),
    ("Partisans", "Axis", ["Allies", "Neutral", "Pro-Allies"]),
    ("Partisans", "Allied", ["Axis", "Neutral", "Pro-Axis"]),
]


class SaveParseError(Exception):
    """The file isn't a TripleA save this parser understands."""


def fields(inst):
    """Flatten a JavaInstance's per-class field maps into one dict."""
    out = {}
    for _, field_map in inst.field_data.items():
        for field, value in field_map.items():
            out[field.name] = value
    return out


def player_alliances(game_data):
    """Decode the Guava ImmutableListMultimap inside AllianceTracker.

    Guava writes it via writeObject as alternating key/value entries
    interleaved with count block data, so pair up the non-BlockData
    items: GamePlayer, alliance-name string, repeat.
    """
    multimap = fields(fields(game_data)["alliances"])["alliances"]
    items = next(iter(multimap.annotations.values()))
    seq = [x for x in items if type(x).__name__ != "BlockData"]
    return {
        str(fields(seq[i])["name"]): str(seq[i + 1])
        for i in range(0, len(seq), 2)
    }


def classify(owner, alliance):
    """Bucket a territory's owner into a house-rule pool, or None to skip."""
    side = alliance.get(owner)
    if owner == "Mongolians" or side == "Mongolians":
        return None  # too complicated — left out of the house rules
    if owner == "Dutch" or side == "Dutch":
        return "Allies"  # Dutch count as Allied
    if side in ("Axis", "Allies"):
        return side
    if side == "Neutral_Axis":
        return "Pro-Axis"
    if side == "Neutral_Allies":
        return "Pro-Allies"
    return "Neutral"  # Neutral_True and any other unaligned owner


def roll(rng, pools, groups):
    """Pick a territory uniformly across the given pools; return (name, owner)."""
    candidates = [entry for g in groups for entry in pools[g]]
    return rng.choice(candidates)


def roll_save(fileobj, rng=None):
    """Parse a .tsvg file object and return the game info and four rolls.

    Returns a dict: {"game", "round", "rolls": [{"kind", "side",
    "territory", "owner"}, ...]}. Raises SaveParseError if the stream
    can't be read as a TripleA save.
    """
    rng = rng or random.Random()

    try:
        with gzip.GzipFile(fileobj=fileobj, mode="rb") as f:
            stream = javaobj.load(f)
        game_data = next(
            item for item in stream
            if hasattr(item, "field_data")
            and any(cd.name.endswith("GameData") for cd in item.field_data)
        )
        gd = fields(game_data)
        seq = fields(gd["sequence"])
        alliance = player_alliances(game_data)
        territories = fields(gd["map"])["territories"]
    except Exception as e:
        raise SaveParseError(f"Could not read TripleA save: {e}") from e

    pools = defaultdict(list)
    for territory in territories:
        tf = fields(territory)
        if tf["water"]:
            continue
        owner = str(fields(tf["owner"])["name"])
        group = classify(owner, alliance)
        if group:
            pools[group].append((str(tf["name"]), owner))

    rolls = []
    for kind, side, groups in ROLLS:
        name, owner = roll(rng, pools, groups)
        rolls.append({"kind": kind, "side": side, "territory": name, "owner": owner})

    return {"game": str(gd["gameName"]), "round": seq.get("round"), "rolls": rolls}
