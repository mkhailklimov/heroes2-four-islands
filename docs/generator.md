# Map generator

The map is generated, not hand-made, so it can be rebuilt after any rule change. Python 3 only; no game files are needed.

```
cd tools
python3 build_map.py ../FOURISL.MX2 ../docs/objects.md   # map + object list
python3 preview.py ../FOURISL.MX2 ../preview.png          # schematic preview
python3 mp2read.py ../FOURISL.MX2                         # read the file back (sanity check)
```

The output is deterministic (`SEED` in `build_map.py`). Change the seed to get different noise and placement.

## Files

| File | Purpose |
|---|---|
| `tools/build_map.py` | The map itself: island shapes, players, objects, armies, header. Start here to change content. |
| `tools/editor.py` | Re-implementation of the original editor's `PlaceOverlay` (object placement, town shadow/ground/flags, resource markers), coast triggers and `SaveMap`. |
| `tools/terrain.py` | Ground transition images (port of the fheroes2 editor's terrain logic, GPL-2.0). |
| `tools/h2data.json` | Object catalogue and ground tables from the original editor. |
| `tools/extract_h2data.py` | Rebuilds `h2data.json` from a homm2-decomp checkout by parsing its source text (nothing is executed). |
| `tools/mp2read.py` | Independent reader (fheroes2-style), used to check the output. |
| `tools/mp2_enums.json` | Object/ICN names for `mp2read.py`. |
| `tools/preview.py` | Renders `preview.png`. |

## How `build_map.py` works

1. **Ground.**
   - Four noisy round islands (radius about 18.5) in the corners, each with its faction's ground.
   - A centre island (radius about 21.5): swamp west, desert east, a dirt plateau in the middle.
   - Harbour bays on the southern islands.
   - `smooth()` removes one-tile spikes so every tile gets a valid transition image. `Terrain.finalize()` then picks the images.
2. **Islands.** For each entry in `ISLANDS`, objects are placed at mirrored offsets from the island centre with `local()`. The asymmetries are flags on the entry: `jail_shift`, `extra_chest`, `second_windmill`, `weak_port`, `extra_ore_mine`, `gold_piles`.
3. **Placement.**
   - `Builder.place()` searches outward in a spiral from the wanted spot for a free tile that fits the terrain mask.
   - It reserves the object's tiles and the 3 tiles in front of its entrance, so nothing blocks a door.
   - Guards go diagonally in front of what they guard.
4. **Port village.** It goes on the coastal spot closest to the map centre where the land around it is solid and the 3 water tiles at y + 2 allow a shipyard.
5. **Centre and sea.** These use fixed coordinates; see the code.
6. **Decoration.** Sparse trees, rocks and mountains, kept away from action objects.
7. **Checks.**
   - `check_reachability()` walks the land from each hero and from the centre island's shore. Every action object must be reachable.
   - The script prints any issues and the number of ground-transition fallbacks. Both should be empty or 0.

## Changing things

| To change | Edit |
|---|---|
| Armies, names, skills, dwellings, rare mines | The `ISLANDS` list |
| Centre castles, mines, guards, boss | The "central island" block in `build()` |
| Victory/loss, players, description | `header()` |
| Object type ids | Catalogue constants at the top (positions in `h2data.json["catalogue"]`) |

After a change, rebuild and look at the preview and at [objects.md](objects.md).
