# MP2 / MX2 file format (as written by the original editor)

These notes come from the original editor's `SaveMap` in [homm2-decomp](https://github.com/sushi-shi/homm2-decomp) (CC0), and are checked against a real map. All values are little-endian. `.MX2` (Price of Loyalty) and `.MP2` share this layout.

## File layout

| Part | Size | Notes |
|---|---|---|
| Header (`SMapHeader`) | 420 | See below. |
| Width, height | u32 + u32 | |
| Cells | 20 × w × h | Row by row, y from the top. |
| Extra count | u32 | Number of overlay extras. Extra 0 is unused. |
| Overlay extras | 15 × count | Free extras have `nextIndex = 0xFFFF`. |
| Towns | 72 × 3 | (x, y, faction \| 0x80 if castle). An empty slot is `FF FF 00`. |
| Mines | 144 × 3 | (x, y, type). An empty slot is `FF FF FF`. |
| Obelisk count | u8 | At least 1. |
| Rumour / time-event indices | u16 each | `header[418]` + `header[419]` entries. |
| Map-extra count | **i32** | `N + 1`. Index 0 unused. fheroes2 reads this as byte pairs until `00 00`. |
| Map-extra records 1..N | u16 size + data each | Towns, heroes, prisons, signs, events… |
| Next object link | u32 | |

Mine types:

| Type | Meaning |
|---|---|
| 0 | Sawmill |
| 1 | Mercury (alchemist lab) |
| 2 | Ore (= EXTRAOVR resource marker index + 2) |
| 3 | Sulfur |
| 4 | Crystal |
| 5 | Gems |
| 6 | Gold |
| 100 | Lighthouse |
| 101 | Dragon city |
| 103 | Abandoned mine |

## Header (420 bytes)

| Offset | Field |
|---|---|
| 0 | Magic `5C 00 00 00` |
| 4 | Difficulty (u16) |
| 6 / 7 | Width / height (u8) |
| 8–13 | Colour enabled (blue, green, red, yellow, orange, purple) |
| 14–19 | Can be human |
| 20–25 | Can be computer |
| 26 | Player count |
| 27 / 28 | Min / max human |
| 29 | Victory condition |
| 30 | Computer can also win |
| 31 | Allow normal victory |
| 32 | Victory value (u16) |
| 34 | Loss condition |
| 35 | Loss value (u16) |
| 37 | No starting hero |
| 38–43 | Race per colour: 0 Knight, 1 Barbarian, 2 Sorceress, 3 Warlock, 4 Wizard, 5 Necromancer, 0xFF none |
| 56 | Town name index |
| 57 | Name file on save |
| 58 | Name[60] |
| 118 | Description[300] |
| 418 | Rumour count |
| 419 | Time event count |

## Cell (20 bytes)

| Offset | Field |
|---|---|
| 0 | Ground image index (u16, GROUND32.TIL) |
| 2 | Object bits: bit 0 animated, bit 1 road, bits 2–7 tileset |
| 3 | Object image index (0xFF none) |
| 4 | Object data (u16), see below |
| 6 | Overlay bits: bit 0 animated, bit 1 draw on top, bits 2–7 tileset |
| 7 | Overlay image index |
| 8 | Flags: 1 flip V, 2 flip H, 4 shore, 0x10 shore corner |
| 9 | Trigger (MapObjectType, \| 0x80 = action object) |
| 10 | Overlay extra index (u16) |
| 12 | Object link (u32) |
| 16 | Overlay link (u32) |

Object data bits:

| Bits | Meaning |
|---|---|
| 0 | Ground layer |
| 1 | Shadow |
| 2 | Drawn as overlay |
| 3–15 | Metadata |

The metadata depends on the object:

| Object | Metadata |
|---|---|
| Town, hero, prison, sign, event | Map-extra record index |
| Monster | Count |
| Expansion sites | Site kind |

Ground image ranges in GROUND32.TIL:

| Ground | First index |
|---|---|
| Water | 0 |
| Grass | 30 |
| Snow | 92 |
| Swamp | 146 |
| Lava | 208 |
| Desert | 262 |
| Dirt | 321 |
| Wasteland | 361 |
| Beach | 415 |
| (end) | 432 |

## Overlay extra (15 bytes)

These are extra object or overlay layers stacked on a cell.

| Offset | Field |
|---|---|
| 0 | Next index (u16) |
| 2 | Bit 0 animated, bits 1–7 tileset |
| 3 | Object index |
| 4 | Bit 0 ground, bit 1 shadow, bit 2 overlay-draw |
| 5 | Overlay bits (as in the cell) |
| 6 | Overlay index |
| 7 | Object link (u32) |
| 11 | Overlay link (u32) |

## Town record (70 bytes)

| Offset | Field |
|---|---|
| 0 | Owner colour (0xFF neutral) |
| 1 | Custom buildings |
| 2–5 | Buildings (u16 common, u16 dwellings) |
| 6 | Mage guild |
| 7 | Custom army |
| 8–12 | Troop types (0-based monster id, 0xFF none) |
| 13–22 | Troop counts (i16) |
| 23 | Captain |
| 24 | Custom name |
| 25–37 | Name[13] |
| 38 | Faction |
| 39 | Is castle |
| 40 | Disallow castle |
| 41–69 | Zero |

## Hero / prison record (76 bytes)

| Offset | Field |
|---|---|
| 0 | Owner |
| 1 | Custom army |
| 2–6 | Troop types |
| 7–16 | Counts (i16) |
| 17 | Custom portrait |
| 18 | Portrait |
| 19–22 | Artifacts (0xFF none) |
| 23–26 | Experience (i32) |
| 27 | Custom skills |
| 28–35 | Secondary skill types (0xFF none) |
| 36–43 | Secondary skill levels (1 basic, 2 advanced, 3 expert) |
| 45 | Custom name |
| 46–58 | Name[13] |
| 59 | Patrol |
| 60 | Patrol radius, or the hero class for a prison |
| 61–75 | Zero |

Secondary skill ids:

| Id | Skill |
|---|---|
| 0 | Pathfinding |
| 1 | Archery |
| 2 | Logistics |
| 3 | Scouting |
| 4 | Diplomacy |
| 5 | Navigation |
| 6 | Leadership |
| 7 | Wisdom |
| 8 | Mysticism |
| 9 | Luck |
| 10 | Ballistics |
| 11 | Eagle Eye |
| 12 | Necromancy |
| 13 | Estates |

## Time event record (49 bytes + message)

The extra-record indices of time events are listed right after the obelisk count, as u16 values (`header[419]` of them). Fields come from `EventExtra` in the decomp's `gameTypes.h`. The game checks them in `game::CheckForTimeEvent`: an event fires on `firstDay`, and every `repeatInterval` days after it.

| Offset | Field |
|---|---|
| 0 | Is map event (0 for a time event) |
| 1–28 | Resources (7 × i32: wood, mercury, ore, sulfur, crystal, gems, gold; can be negative) |
| 29 | Artifact (i16, −1 none) |
| 31 | Applies to computer |
| 32 | Cancel after visit |
| 33 | First day (u16) |
| 35 | Repeat interval (u16, 0 = once) |
| 37 | Active |
| 38 / 40 | x / y (u16, unused for time events) |
| 42 | Applies to human |
| 43–48 | Colours it applies to |
| 49… | Message, zero-terminated |

## Object catalogue

The editor's `gOverlayTypes` table has 956 entries, extracted to `tools/h2data.json`. Each object sits on an 8×6 grid anchored at the bottom-right cell (7,5). The grid holds bit masks for:

- occupied, overlay, shadow, animated, resource-marker and entrance cells;
- allowed terrain and ground.

Image frames are numbered by `FillInOverlayTiles`. Shipyard rule: the game builds the boat on water at (entrance x − 1 … x + 1, entrance y + 2).
