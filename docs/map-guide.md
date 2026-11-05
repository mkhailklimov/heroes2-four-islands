# Four Islands: map guide

**File:** [`FOURISL.MX2`](../FOURISL.MX2). XL (144×144), 4 players, Heroes of Might and Magic II: The Price of Loyalty / Gold (original game).
**Status:** first generated sketch, not yet tested in the game. Polish it in the original editor.
**Preview:** [`preview.png`](../preview.png), schematic only:

| Colour | Meaning |
|---|---|
| Background | Type of ground |
| Magenta | Towns |
| Yellow | Heroes |
| Orange | Prisons |
| Red | Monsters |
| Black | Mines |
| Cyan | Whirlpools and Magellan's Maps |
| White | Other objects |

The full list of objects with coordinates is in [objects.md](objects.md). It is regenerated with the map.

## Story

On day 1 every player sees this message (it is also the scenario description):

> The Blue Sea was home to peaceful lands: six free countries lived and prospered. But the central island has fallen to an invading dragon horde. Conquer the central island, or the dragons will crush you!

## Idea

Four factions each start on their own corner island. No land path leads off an island. To leave, you take the neutral port village, upgrade it to a castle and build a shipyard. Each island lacks a mine for its own level-6 resource. That resource comes from the windmill, the market, or the centre island. The centre island has two neutral castles, the missing mines and a dragon fortress.

## Players

| Colour | Faction | Corner | Ground | Village | Port village |
|---|---|---|---|---|---|
| Red | Warlock | NW | Lava | Ashkeep | Cinderport |
| Blue | Knight | NE | Snow | Frostmere | Icehaven |
| Green | Sorceress | SW | Grass | Greenvale | Bluebay |
| Yellow | Wizard | SE | Dirt (clay) | Claytower | Saltgate |

- **Victory and loss:** defeat everybody / lose everything.
- **Player slots:** all 4 can be human or computer.
- **Starting hero:** no extra starting hero is added. Each player's hero is placed on the map in front of the village.

## Each corner island

| Feature | Details |
|---|---|
| Starting village | Owned by the player. Town, not castle, but upgradable to a castle. |
| Starting hero | Faction hero with a small army: Warlock 14 Centaurs + 5 Gargoyles; Knight 25 Peasants + 6 Archers; Sorceress 15 Sprites + 6 Dwarves; Wizard 12 Halflings + 4 Boars. |
| Free dwellings | Warlock: Cave + Goblin Hut; Knight: Peasant Hut + Archer House; Sorceress: Tree House + Dwarf Cottage; Wizard: Halfling Hole + Dwarf Cottage. |
| Mines | Sawmill, ore mine, gold mine (8 Ogres), two "foreign" rare mines (10 Wolves, 6 Griffins). |
| Windmill + water wheel | The windmill is the random chance at your own rare resource. |
| Visitable buildings | 1 Witch Hut, 1 Gazebo, 1 Tree of Knowledge, 2 Obelisks. HoMM2 has no "academy", so the Tree of Knowledge (a free level) stands in for it. Gazebo and Tree are drawn for grass/dirt, so on snow and lava they stand on a small dirt patch. |
| Treasure | 4 wood piles, 4 ore piles, 1 gold pile, 3 treasure chests, 1 treasure-class artifact. |
| Prison | Super-hero, guarded by 6 Trolls (see below). |
| Port village | Neutral, on the coast facing the centre, with a garrison of 12 Orcs/Swordsmen + 10 Elves. Water lies directly below its entrance, so a shipyard can be built once it is a castle. |
| Road guard | 6 Minotaurs (Warlock) or 6 Cavalry between the village and the port. |

### Rare resources

| Faction | Needs (level 6) | Mines on island | No mine for |
|---|---|---|---|
| Warlock | Sulfur | Gems, Mercury | Sulfur, Crystal |
| Knight | Crystal | Sulfur, Gems | Crystal, Mercury |
| Sorceress | Mercury | Crystal, Sulfur | Mercury, Gems |
| Wizard | Gems | Crystal, Mercury | Gems, Sulfur |

### Prison super-heroes

All 4 skills are at Expert level. They belong to the hero and can't be passed on. Army is empty and experience is 0.

| Island | Hero | Skills |
|---|---|---|
| Warlock | Ironhide | Leadership, Diplomacy, Logistics, Pathfinding |
| Knight | Bladeheart | Leadership, Luck, Archery, Ballistics |
| Sorceress | Starlight | Wisdom, Mysticism, Eagle Eye, Luck |
| Wizard | Deepmind | Wisdom, Mysticism, Navigation, Scouting |

### Small asymmetries

- **Knight:** prison 3 tiles further from the village, but +1 treasure chest.
- **Sorceress:** a second windmill instead of the water wheel.
- **Wizard:** weaker port garrison (8 + 6).
- **Warlock:** an extra ore mine (20 Goblins), but no gold pile.
- **Southern islands:** a harbour bay cut into the side facing the centre, because a shipyard needs water directly below the town.
- **Island shapes:** each island has slightly different noisy outlines.

## Centre island

- **Terrain:** west half swamp, east half desert, dirt plateau in the middle.
- **Orcrest:** neutral Barbarian castle (west). Garrison 30 Orcs, 15 Wolves, 10 Ogres, 6 Trolls, 3 Cyclopes.
- **Gravemoor:** neutral Necromancer castle (east). Garrison 40 Skeletons, 20 Zombies, 10 Mummies, 6 Vampires, 4 Liches.
- **Dragonhold** (72,72): neutral Warlock castle with no hero and **5 × 20 Black Dragons**. The garrison does not regrow, so losses stay.
- **Ring of volcanoes** around Dragonhold, on lava ground. There are two gates only: **north, guarded by 100 Red Dragons**, and **south, guarded by 100 Green Dragons**. The generator checks that the ring has no other way in.
- **Inside the ring:** Dragonhold, 2 major artifacts behind 6 Titans and 6 Bone Dragons, a Gazebo and a Tree of Knowledge.
- **Outside the ring:** 1 Witch Hut and 2 Obelisks (one in the swamp, one in the desert).
- **Missing resources:** 2 mines each of crystal, mercury (alchemist lab), gems and sulfur. They are guarded by Green Dragons, Hydras, Giants and Genies (4–6 each).
- **Other artifacts:** 6 more (major and minor), plus 6 roaming stacks of 3 Red Dragons, Titans or Bone Dragons.

## Weekly dragon raids

The original game cannot create monsters during play: a timed event can only show a message and give or take resources. So the weekly hordes are dragon **raids**. They hit the 4 players only, never the neutral castles.

| Day | Raid | Loss |
|---|---|---|
| 8, 29, 50… | Green dragons | 5 wood, 5 ore, 1000 gold |
| 15, 36, 57… | Red dragons | 5 wood, 5 ore, 2 of each rare resource, 2000 gold |
| 22, 43, 64… | Black dragons | 10 wood, 10 ore, 3 of each rare resource, 3000 gold |

The cycle repeats every 3 weeks. Raids can't stop when the centre falls, because events have no conditions.

## Sea

- **Whirlpools:** west (22,72) and east (121,72). They are the only two on the map, so they lead to each other.
- **Magellan's Maps:** north (72,16) and south (72,128). They reveal the whole sea, in place of the plan's Hut of Magi with Eyes of Magi.
- **Other objects:** 4 shipwreck survivors (artifact), 22 flotsam, sea chests and 4 buoys.

## Known limitations and open points

- **Untested:** the map hasn't been loaded in the game yet.
- **Warlock ground:** lava. The original request said snow, which is still to be confirmed.
- **Bottles:** none yet. They need a message text, which the generator doesn't write.
- **Decoration:** sparse, and some placements may look odd. Polishing in the editor is expected.
- **Weekly raids:** a stand-in for weekly dragon spawns, which the engine can't do. The alternative under discussion is a 5th computer player owning Dragonhold.
- **Coordinates:** [objects.md](objects.md) gives anchors (the bottom-right tile of each object), not entrances.
