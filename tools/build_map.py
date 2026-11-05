"""Generate FOURISL.MX2 - "Four Islands", an XL (144x144) 4-player map for
Heroes of Might and Magic II: The Price of Loyalty.

usage: python3 build_map.py [output.mx2] [objects.md]
"""
import math
import random
import struct
import sys
from collections import deque

from editor import Map, CAT, BY_ID, MO, K, G2T, ACTION
from terrain import Terrain, WATER, GRASS, SNOW, SWAMP, LAVA, DESERT, DIRT, START

N = 144
SEED = 20261105
rng = random.Random(SEED)

# ---------------------------------------------------------------- catalogue
MINE_BASE = {GRASS: 30, SNOW: 41, SWAMP: 52, LAVA: 63, DESERT: 74, DIRT: 87}
ORE, SULFUR, CRYSTAL, GEMS, GOLD = range(5)
SAWMILL = {GRASS: 789, SNOW: 556, SWAMP: 789, LAVA: 618, DESERT: 661, DIRT: 774}
ALCH_LAB = {SNOW: 552}
ALCH_LAB_ANY = 770
WINDMILL = {GRASS: 509, SNOW: 548, DIRT: 707, LAVA: 707, SWAMP: 509, DESERT: 707}
WATER_WHEEL = {SNOW: 554}
WATER_WHEEL_ANY = 775
PEASANT_HUT, ARCHER_HOUSE, DWARF_COTTAGE, TREE_HOUSE, HALFLING_HOLE_DIRT, CAVE_SNOW, GOBLIN_HUT = 746, 510, 512, 760, 701, 516, 511
JAIL = 798
WITCH_HUT = 558
WHIRLPOOL, MAGELLAN, FLOTSAM, SEA_CHEST, SURVIVOR, BUOY, LIGHTHOUSE = 457, 448, 447, 445, 451, 456, 773
OBS_TOWER = 787
HUT_OF_MAGI, EYE_OF_MAGI = BY_ID[K["OVERLAY_HUT_OF_MAGI_SITE"]], BY_ID[K["OVERLAY_EYE_OF_MAGI_SITE"]]
RES = {"wood": 825, "mercury": 826, "ore": 827, "sulfur": 828, "crystal": 829, "gems": 830, "gold": 831}
RANDOM_RES, CHEST = 833, 834
ART_TREASURE, ART_MINOR, ART_MAJOR = 337, 338, 339
MONSTER0 = 148
HERO0 = 357
RANDOM_MON = {"weak": 215, "medium": 216, "strong": 217, "very_strong": 218}

# MP2 monster ids (0-based)
M = dict(peasant=0, archer=1, pikeman=3, swordsman=5, cavalry=7, goblin=11, orc=12, wolf=14, ogre=15, troll=17,
         cyclops=19, sprite=20, dwarf=21, elf=23, druid=25, unicorn=27, phoenix=28, centaur=29, gargoyle=30, griffin=31,
         minotaur=32, hydra=34, green_dragon=35, red_dragon=36, black_dragon=37, halfling=38, boar=39, iron_golem=40,
         roc=42, mage=43, giant=45, titan=46, skeleton=47, zombie=48, mummy=50, vampire=52, lich=54, bone_dragon=56,
         rogue=57, nomad=58, ghost=59, genie=60, medusa=61, earth_el=62, air_el=63, fire_el=64, water_el=65)
# factions / colors
KNIGHT, BARBARIAN, SORCERESS, WARLOCK, WIZARD, NECRO = range(6)
BLUE, GREEN, RED, YELLOW = range(4)
NEUTRAL = 6
# MP2 secondary skills (0-based) and levels
PATHFINDING, ARCHERY, LOGISTICS, SCOUTING, DIPLOMACY, NAVIGATION, LEADERSHIP, WISDOM, MYSTICISM, LUCK, BALLISTICS, EAGLE_EYE = range(12)
EXPERT = 3


def town_type(color, faction, castle):
    return BY_ID[K["OVERLAY_TOWN_FIRST"] + color * 12 + faction * 2 + (0 if castle else 1)]


def town_record(owner, faction, castle, name, army=None, buildings=None):
    b = bytearray(70)
    b[0] = owner if owner < 6 else 0xFF
    if buildings is not None:
        b[1] = 1
        struct.pack_into("<HH", b, 2, buildings[0], buildings[1])
        b[6] = buildings[2]
    if army:
        b[7] = 1
        for i in range(5):
            mt, cnt = army[i] if i < len(army) else (0xFF, 0)
            b[8 + i] = mt
            struct.pack_into("<h", b, 13 + 2 * i, cnt)
    else:
        for i in range(5):
            b[8 + i] = 0xFF
    b[23] = 0
    b[24] = 1
    nm = name.encode("ascii")[:12]
    b[25:25 + len(nm)] = nm
    b[38] = faction
    b[39] = 1 if castle else 0
    b[40] = 0  # building a castle is allowed
    return b


def hero_record(owner, army=None, name=None, skills=None, jail_class=None, exp=0):
    b = bytearray(76)
    b[0] = owner if owner is not None else 0
    if army:
        b[1] = 1
    for i in range(5):
        mt, cnt = army[i] if army and i < len(army) else (0xFF, 0)
        b[2 + i] = mt & 0xFF
        struct.pack_into("<h", b, 7 + 2 * i, cnt)
    b[17], b[18] = 0, 0
    b[19], b[20], b[21], b[22] = 0xFF, 0xFF, 0xFF, 0
    struct.pack_into("<i", b, 23, exp)
    for i in range(8):
        b[28 + i] = 0xFF
        b[36 + i] = 0
    if skills:
        b[27] = 1
        for i, (s, lvl) in enumerate(skills):
            b[28 + i] = s
            b[36 + i] = lvl
    if name:
        b[45] = 1
        nm = name.encode("ascii")[:12]
        b[46:46 + len(nm)] = nm
    if jail_class is not None:
        b[60] = jail_class
    return b


# ---------------------------------------------------------------- terrain
def blob(cx, cy, r, seed, amp=0.18):
    """Return a function telling whether (x, y) is inside a noisy round island."""
    g = random.Random(seed)
    waves = [(g.randint(2, 5), g.uniform(0, 2 * math.pi), g.uniform(0.3, 1.0)) for _ in range(4)]
    norm = sum(w[2] for w in waves)

    def inside(x, y):
        dx, dy = x - cx, y - cy
        a = math.atan2(dy, dx)
        k = sum(w * math.sin(f * a + p) for f, p, w in waves) / norm
        return math.hypot(dx * 1.0, dy * 1.0) <= r * (1 + amp * k)
    return inside


def build_ground():
    g = [WATER] * (N * N)
    # NW island shape, mirrored to the other corners (with a different noise seed for small deviations)
    corners = [  # (centre, faction terrain, seed)
        ((24, 24), LAVA, 11),      # Warlock - NW
        ((119, 24), SNOW, 12),     # Knight  - NE
        ((24, 119), GRASS, 13),    # Sorceress - SW
        ((119, 119), DIRT, 14),    # Wizard  - SE
    ]
    for (cx, cy), terr, seed in corners:
        f = blob(cx, cy, 18.5, seed, amp=0.10)
        for y in range(N):
            for x in range(N):
                if f(x, y):
                    g[y * N + x] = terr
    # southern islands: a harbour bay cut in from the side facing the centre, so the port village
    # (its shipyard needs water just south of the entrance) looks at the centre instead of the map edge
    for cx, cy, sx in ((24, 119, 1), (119, 119, -1)):
        for y in range(cy - 7, cy - 4):
            for d in range(9, 26):
                g[y * N + cx + sx * d] = WATER
    fc = blob(72, 72, 21.5, 21, amp=0.10)
    for y in range(N):
        for x in range(N):
            if fc(x, y):
                g[y * N + x] = SWAMP if x < 72 else DESERT
    # dirt plateau under the boss castle
    for y in range(66, 79):
        for x in range(65, 80):
            if math.hypot(x - 72, (y - 72) * 1.2) <= 6.5:
                g[y * N + x] = DIRT
    return g


def smooth(g, passes=4):
    """Remove 1-tile spikes and holes so every tile can get a proper transition image."""
    for _ in range(passes):
        changed = 0
        out = g[:]
        for y in range(N):
            for x in range(N):
                i = y * N + x
                cur = g[i]
                # each tile must belong to at least one 2x2 block of its own ground
                ok = False
                for ox in (-1, 0):
                    for oy in (-1, 0):
                        if all(0 <= x + ox + a < N and 0 <= y + oy + b < N and g[(y + oy + b) * N + x + ox + a] == cur
                               for a in (0, 1) for b in (0, 1)):
                            ok = True
                if not ok:
                    cnt = {}
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if (dx or dy) and 0 <= x + dx < N and 0 <= y + dy < N:
                                v = g[(y + dy) * N + x + dx]
                                cnt[v] = cnt.get(v, 0) + 1
                    out[i] = max(cnt, key=cnt.get)
                    changed += 1
        g = out
        if not changed:
            break
    return g


# ---------------------------------------------------------------- placement helpers
class Builder:
    def __init__(self):
        g = smooth(build_ground())
        self.ter = Terrain(N, seed=SEED)
        self.ter.fill(g)
        failed = self.ter.finalize()
        self.m = Map(N, seed=SEED)
        for i in range(N * N):
            self.m.cells[i].terrain = self.ter.idx[i]
            self.m.cells[i].flags = self.ter.flags[i]
        self.reserved = set()
        self.log = []
        self.failed_terrain = failed
        self.placed_objects = []

    def ground(self, x, y):
        return G2T[self.m.cell(x, y).terrain]

    def is_free(self, ti, ax, ay, margin=0):
        t = CAT[ti]
        for row in range(6):
            for col in range(8):
                if t["frames"][row * 8 + col] == 255:
                    continue
                x, y = ax - 7 + col, ay - 5 + row
                if not (1 <= x < N - 1 and 1 <= y < N - 1):
                    return False
                if t["shadowRows"][row][col] or t["overlayRows"][row][col]:
                    continue
                if (x, y) in self.reserved:
                    return False
        ents = [(ax - 7 + c, ay - 5 + r) for r in range(6) for c in range(8) if t["entranceRows"][r][c]]
        land = G2T[self.m.cell(ax, ay).terrain] != 0 if t["groundMask"] != 1 else True
        for ex, ey in ents:
            fx, fy = ex, ey + 1
            if not (0 <= fy < N) or (fx, fy) in self.reserved and self.front_of.get((fx, fy)) is None:
                return False
            if t["groundMask"] == 1:  # water objects need water around their front
                if G2T[self.m.cell(fx, fy).terrain] != 0:
                    return False
            else:
                if G2T[self.m.cell(fx, fy).terrain] == 0:
                    return False
        return land and self.m.can_place(ti, ax, ay)

    front_of = {}

    def place(self, ti, ax, ay, search=6, reserve_front=True, label=""):
        for r in range(search + 1):
            cands = [(ax + dx, ay + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
            rng.shuffle(cands)
            for x, y in cands:
                if self.is_free(ti, x, y):
                    cell = self.m.place(ti, x, y)
                    t = CAT[ti]
                    for row in range(6):
                        for col in range(8):
                            if t["frames"][row * 8 + col] != 255 and not t["shadowRows"][row][col] and not t["overlayRows"][row][col]:
                                self.reserved.add((x - 7 + col, y - 5 + row))
                    ents = [(x - 7 + c, y - 5 + rr) for rr in range(6) for c in range(8) if t["entranceRows"][rr][c]]
                    if reserve_front:
                        for ex, ey in ents:
                            for fx in (ex - 1, ex, ex + 1):
                                self.reserved.add((fx, ey + 1))
                                self.front_of[(fx, ey + 1)] = (ex, ey)
                    self.placed_objects.append((label or str(ti), x, y, ti, cell))
                    return cell, (x, y)
        raise RuntimeError(f"no room for {label or ti} near {ax},{ay}")

    def monster(self, mtype, count, ax, ay, search=3, label="guard"):
        cell, pos = self.place(MONSTER0 + mtype, ax, ay, search=search, reserve_front=False, label=label)
        cell.meta = count
        return pos

    def guard_front(self, pos, mtype, count, dx=1):
        """Put a guard diagonally in front of the entrance at `pos` (it blocks the approach)."""
        x, y = pos
        for cx, cy in ((x + dx, y + 1), (x - dx, y + 1), (x + 2 * dx, y + 1), (x, y + 2)):
            self.reserved.discard((cx, cy))
            try:
                cell, p = self.place(MONSTER0 + mtype, cx, cy, search=0, reserve_front=False, label="guard")
                cell.meta = count
                return p
            except RuntimeError:
                continue
        return self.monster(mtype, count, x, y + 2, search=3)


# ---------------------------------------------------------------- the map
ISLANDS = [
    # color, faction, ground, center, mirror (mx, my), missing lvl6 resource, two foreign rare mines, names
    dict(color=RED, faction=WARLOCK, ground=LAVA, c=(24, 24), m=(1, 1), port_side=1, rare=[GEMS, "mercury"],
         dw=[CAVE_SNOW, GOBLIN_HUT], town="Ashkeep", port="Cinderport", extra_ore_mine=True, gold_piles=0,
         jail=dict(name="Ironhide", skills=[(LEADERSHIP, EXPERT), (DIPLOMACY, EXPERT), (LOGISTICS, EXPERT), (PATHFINDING, EXPERT)]),
         army=[(M["centaur"], 14), (M["gargoyle"], 5)]),
    dict(color=BLUE, faction=KNIGHT, ground=SNOW, c=(119, 24), m=(-1, 1), port_side=1, rare=[SULFUR, GEMS],
         dw=[PEASANT_HUT, ARCHER_HOUSE], town="Frostmere", port="Icehaven", jail_shift=3, extra_chest=True,
         jail=dict(name="Bladeheart", skills=[(LEADERSHIP, EXPERT), (LUCK, EXPERT), (ARCHERY, EXPERT), (BALLISTICS, EXPERT)]),
         army=[(M["peasant"], 25), (M["archer"], 6)]),
    dict(color=GREEN, faction=SORCERESS, ground=GRASS, c=(24, 119), m=(1, -1), port_side=1, rare=[CRYSTAL, SULFUR],
         dw=[TREE_HOUSE, DWARF_COTTAGE], town="Greenvale", port="Bluebay", second_windmill=True,
         jail=dict(name="Starlight", skills=[(WISDOM, EXPERT), (MYSTICISM, EXPERT), (EAGLE_EYE, EXPERT), (LUCK, EXPERT)]),
         army=[(M["sprite"], 15), (M["dwarf"], 6)]),
    dict(color=YELLOW, faction=WIZARD, ground=DIRT, c=(119, 119), m=(-1, -1), port_side=1, rare=[CRYSTAL, "mercury"],
         dw=[HALFLING_HOLE_DIRT, DWARF_COTTAGE], town="Claytower", port="Saltgate", weak_port=True,
         jail=dict(name="Deepmind", skills=[(WISDOM, EXPERT), (MYSTICISM, EXPERT), (NAVIGATION, EXPERT), (SCOUTING, EXPERT)]),
         army=[(M["halfling"], 12), (M["boar"], 4)]),
]


def local(isl, dx, dy):
    cx, cy = isl["c"]
    mx, my = isl["m"]
    return cx + mx * dx, cy + my * dy


def build():
    b = Builder()
    m = b.m
    summary = {}

    # ---------- islands
    for k, isl in enumerate(ISLANDS):
        col, fac, gr = isl["color"], isl["faction"], isl["ground"]
        s = {}
        # player's inland village (town, can be upgraded to castle)
        cell, pos = b.place(town_type(col, fac, False), *local(isl, -2, -3), search=4, label="village")
        m.add_extra_record(cell, town_record(col, fac, False, isl["town"]))
        s["village"] = pos
        # starting hero right in front of the village
        hx, hy = pos[0], pos[1] + 1
        b.reserved.discard((hx, hy))
        hcell, hpos = b.place(HERO0 + col * 7 + fac, hx, hy, search=0, reserve_front=False, label="hero")
        m.add_extra_record(hcell, hero_record(col, army=isl["army"]))
        s["hero"] = hpos
        # free dwellings
        for j, dw in enumerate(isl["dw"]):
            _, p = b.place(dw, *local(isl, -9 + 18 * j, -9 + 3 * j), search=6, label="dwelling")
        # mines: sawmill, ore, gold, two foreign rare resources
        _, p = b.place(SAWMILL[gr], *local(isl, -10, 4), search=6, label="sawmill")
        _, p = b.place(MINE_BASE[gr] + ORE, *local(isl, 8, -11), search=6, label="ore mine")
        _, p = b.place(MINE_BASE[gr] + GOLD, *local(isl, 10, 6), search=6, label="gold mine")
        b.guard_front(p, M["ogre"], 8)
        for j, r in enumerate(isl["rare"]):
            ax, ay = local(isl, -13 + 10 * j, 12 - 2 * j)
            if r == "mercury":
                ti = ALCH_LAB.get(gr, ALCH_LAB_ANY)
            else:
                ti = MINE_BASE[gr] + r
            _, p = b.place(ti, ax, ay, search=7, label="rare mine")
            b.guard_front(p, M["wolf"] if j == 0 else M["griffin"], 10 if j == 0 else 6)
        # windmill (random rare resource every week) and water wheel
        _, p = b.place(WINDMILL[gr], *local(isl, 4, 9), search=6, label="windmill")
        if isl.get("second_windmill"):
            _, p = b.place(WINDMILL[gr], *local(isl, -5, 9), search=6, label="windmill 2")
        else:
            _, p = b.place(WATER_WHEEL.get(gr, WATER_WHEEL_ANY), *local(isl, -5, 9), search=6, label="water wheel")
        if isl.get("extra_ore_mine"):
            _, p = b.place(MINE_BASE[gr] + ORE, *local(isl, -14, -12), search=6, label="ore mine 2")
            b.guard_front(p, M["goblin"], 20)
        b.place(WITCH_HUT, *local(isl, 13, 1), search=6, label="witch hut")
        # wood/ore piles for the castle + other treasure
        for j in range(4):
            b.place(RES["wood"], *local(isl, -7 + 4 * j + rng.randint(-1, 1), 2 + rng.randint(-2, 1)), search=4, label="wood")
            b.place(RES["ore"], *local(isl, -5 + 4 * j + rng.randint(-1, 1), 6 + rng.randint(-1, 2)), search=4, label="ore")
        for j in range(isl.get("gold_piles", 1)):
            b.place(RES["gold"], *local(isl, 3, -7), search=4, label="gold")
        for j in range(4 if isl.get("extra_chest") else 3):
            b.place(CHEST, *local(isl, -12 + 9 * j - (j == 3) * 20, -13 + 4 * j - (j == 3) * 4), search=5, label="chest")
        b.place(ART_TREASURE, *local(isl, 12, -2), search=5, label="artifact")
        # prison with the super hero
        cell, p = b.place(JAIL, *local(isl, -13 - isl.get("jail_shift", 0), -5), search=6, label="jail")
        j = isl["jail"]
        m.add_extra_record(cell, hero_record(None, name=j["name"], skills=j["skills"], jail_class=fac))
        b.guard_front(p, M["troll"], 6)
        s["jail"] = p
        # coastal village (neutral, guarded), shipyard possible: water two rows below its entrance
        cx, cy = isl["c"]
        best = None
        for y in range(cy - 25, cy + 26):
            for x in range(cx - 25, cx + 26):
                if not (3 <= x < N - 3 and 3 <= y < N - 4):
                    continue
                if b.ground(x, y) == 0 or b.ground(x, y + 2) != 0:
                    continue
                # the coast must face the centre of the map horizontally
                score = abs(x - 72) + abs(y - 72)
                if any(b.ground(x + dx, y + 2) != 0 for dx in (-1, 0, 1)):
                    continue
                if any(b.ground(x + dx, y + 1) == 0 for dx in (-2, -1, 0, 1, 2)):
                    continue
                if any(b.ground(x + dx, y - dy) == 0 for dx in (-2, -1, 0, 1, 2) for dy in (0, 1, 2, 3)):
                    continue
                ti = town_type(NEUTRAL, fac, False)
                if not b.is_free(ti, x, y):
                    continue
                if best is None or score < best[0]:
                    best = (score, x, y)
        assert best, "no coastal spot for port village"
        cell, p = b.place(town_type(NEUTRAL, fac, False), best[1], best[2], search=0, reserve_front=False, label="port village")
        m.add_extra_record(cell, town_record(NEUTRAL, fac, False, isl["port"],
                                             army=[(M["swordsman"] if fac == KNIGHT else M["orc"], 8 if isl.get("weak_port") else 12),
                                                   (M["elf"], 6 if isl.get("weak_port") else 10)]))
        s["port"] = p
        # guard on the road from the village to the port
        b.monster(M["minotaur"] if fac == WARLOCK else M["cavalry"], 6, (pos[0] + p[0]) // 2, (pos[1] + p[1]) // 2 + 1, search=4)
        summary[isl["town"]] = s

    # ---------- central island
    # boss: neutral Warlock castle, no hero, 5 x 20 black dragons
    cell, boss = b.place(town_type(NEUTRAL, WARLOCK, True), 72, 72, search=2, label="boss castle")
    m.add_extra_record(cell, town_record(NEUTRAL, WARLOCK, True, "Dragonhold", army=[(M["black_dragon"], 20)] * 5))
    summary["boss"] = boss
    cell, barb = b.place(town_type(NEUTRAL, BARBARIAN, True), 57, 71, search=4, label="barbarian castle")
    m.add_extra_record(cell, town_record(NEUTRAL, BARBARIAN, True, "Orcrest",
                                         army=[(M["orc"], 30), (M["wolf"], 15), (M["ogre"], 10), (M["troll"], 6), (M["cyclops"], 3)]))
    cell, necr = b.place(town_type(NEUTRAL, NECRO, True), 88, 71, search=4, label="necromancer castle")
    m.add_extra_record(cell, town_record(NEUTRAL, NECRO, True, "Gravemoor",
                                         army=[(M["skeleton"], 40), (M["zombie"], 20), (M["mummy"], 10), (M["vampire"], 6), (M["lich"], 4)]))
    summary["barbarian"], summary["necro"] = barb, necr
    # two top artifacts next to the boss, behind strong guards
    for dx in (-6, 6):
        _, p = b.place(ART_MAJOR, 72 + dx, 76, search=3, label="boss artifact")
        b.monster(M["titan"] if dx < 0 else M["bone_dragon"], 6, p[0], p[1] + 1, search=2)
    # missing level-6 resources: 2 of each
    centre_mines = [
        (CRYSTAL, 62, 58), (CRYSTAL, 82, 88),
        ("mercury", 82, 58), ("mercury", 62, 88),
        (GEMS, 70, 55), (GEMS, 76, 90),
        (SULFUR, 76, 56), (SULFUR, 68, 90),
    ]
    guards = [M["green_dragon"], M["hydra"], M["giant"], M["genie"]]
    for j, (r, x, y) in enumerate(centre_mines):
        gr = b.ground(x, y)
        gr = gr if gr in (SWAMP, DESERT, DIRT) else (SWAMP if x < 72 else DESERT)
        ti = ALCH_LAB_ANY if r == "mercury" else MINE_BASE[gr] + r
        _, p = b.place(ti, x, y, search=6, label="centre mine")
        b.guard_front(p, guards[j % 4], 4 + (j % 3))
    for j in range(6):
        b.place(ART_MINOR if j % 2 else ART_MAJOR, 60 + 5 * j, 64 + (j % 2) * 15, search=5, label="artifact")
    for j in range(6):
        b.monster(rng.choice([M["red_dragon"], M["titan"], M["bone_dragon"]]), 3, 62 + 4 * j, 80 - (j % 2) * 16, search=4)

    # ---------- sea
    for x, y in ((22, 72), (121, 72)):
        b.place(WHIRLPOOL, x, y, search=6, reserve_front=False, label="whirlpool")
    for x, y in ((72, 16), (72, 128)):
        b.place(MAGELLAN, x, y, search=6, reserve_front=False, label="magellan maps")
    for x, y in ((48, 30), (96, 30), (48, 114), (96, 114)):
        b.place(SURVIVOR, x, y, search=6, reserve_front=False, label="survivor")
    sea_spots = [(x, y) for y in range(4, N - 4, 9) for x in range(4, N - 4, 9)]
    rng.shuffle(sea_spots)
    n_flot = n_chest = 0
    for x, y in sea_spots:
        if b.ground(x, y) != 0:
            continue
        # keep the lanes around whirlpools and maps free
        try:
            if n_flot < 22:
                b.place(FLOTSAM, x, y, search=2, reserve_front=False, label="flotsam"); n_flot += 1
            elif n_chest < 14:
                b.place(SEA_CHEST, x, y, search=2, reserve_front=False, label="sea chest"); n_chest += 1
        except RuntimeError:
            pass
    for x, y in ((60, 40), (84, 104), (40, 84), (104, 60)):
        try:
            b.place(BUOY, x, y, search=4, reserve_front=False, label="buoy")
        except RuntimeError:
            pass

    decorate(b)
    return b, summary


def decorate(b):
    """Sparse trees, rocks and mountains on land; keeps every action object reachable."""
    deco = {}
    for i, t in enumerate(CAT):
        if t["category"] != 0 or t["trigger"] & ACTION:
            continue
        name = {v: k for k, v in MO.items()}.get(t["trigger"], "")
        if name not in ("MAP_OBJECT_TREES", "MAP_OBJECT_MOUNTAINS", "MAP_OBJECT_ROCK"):
            continue
        if any(any(r) for r in t["entranceRows"]):
            continue
        for terr in range(1, 9):
            if (t["terrainMask"] >> terr) & 1 and t["terrainMask"] != 0xFFE:
                deco.setdefault(terr, []).append(i)
    tiles = [(x, y) for y in range(3, N - 3) for x in range(3, N - 3)]
    rng.shuffle(tiles)
    placed = 0
    for x, y in tiles:
        gr = b.ground(x, y)
        if gr == 0 or gr not in deco or rng.random() > 0.09:
            continue
        # stay away from action objects
        if any((x + dx, y + dy) in b.reserved for dx in range(-2, 3) for dy in range(-2, 3)):
            continue
        ti = rng.choice(deco[gr])
        if not b.is_free(ti, x, y):
            continue
        b.m.place(ti, x, y)
        t = CAT[ti]
        for row in range(6):
            for col in range(8):
                if t["frames"][row * 8 + col] != 255 and not t["shadowRows"][row][col] and not t["overlayRows"][row][col]:
                    b.reserved.add((x - 7 + col, y - 5 + row))
        placed += 1
    b.log.append(f"decorations: {placed}")


def blocked_cells(m):
    blk = set()
    for y in range(N):
        for x in range(N):
            c = m.cell(x, y)
            parts = [c.obj] + [e[0] for e in c.extras]
            if any(p is not None and not p["shadow"] and p["ts"] != 29 for p in parts):
                blk.add((x, y))
    return blk


def check_reachability(b, summary):
    """BFS on land: every action object on a player island must be reachable from the hero,
    and every action object on the central island from its shore (where boats land)."""
    m = b.m
    blk = blocked_cells(m)
    land = lambda x, y: 0 <= x < N and 0 <= y < N and G2T[m.cell(x, y).terrain] != 0
    issues = []

    def flood(starts):
        seen = set(starts)
        dq = deque(starts)
        while dq:
            x, y = dq.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in seen or not land(nx, ny) or (nx, ny) in blk:
                        continue
                    seen.add((nx, ny))
                    dq.append((nx, ny))
        return seen

    def audit(name, seen, cx, cy, r):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if not land(x, y):
                    continue
                c = m.cell(x, y)
                if c.trigger & ACTION and not any((x + dx, y + dy) in seen for dx in (-1, 0, 1) for dy in (0, 1)):
                    issues.append((name, x, y, {v: k for k, v in MO.items()}.get(c.trigger & 0x7F)))

    for isl in ISLANDS:
        audit(isl["town"], flood([summary[isl["town"]]["hero"]]), *isl["c"], 26)
    shore = [(x, y) for y in range(46, 99) for x in range(46, 99)
             if land(x, y) and (x, y) not in blk
             and any(not land(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    summary["centre landing tiles"] = len(shore)
    audit("centre", flood(shore), 72, 72, 26)
    return issues


def header():
    h = bytearray(420)
    h[0:4] = b"\x5c\x00\x00\x00"
    h[4] = 1  # normal
    h[6] = h[7] = N
    for i in range(4):
        h[8 + i] = 1
        h[14 + i] = 1
        h[20 + i] = 1
    h[26] = 4
    h[27] = 1
    h[28] = 4
    h[29] = 0   # victory: defeat everybody
    h[30] = 0
    h[31] = 1
    h[34] = 0   # loss: lose everything
    h[37] = 1   # no extra starting hero in the first town (heroes are placed on the map)
    races = {BLUE: KNIGHT, GREEN: SORCERESS, RED: WARLOCK, YELLOW: WIZARD}
    for c in range(6):
        h[38 + c] = races.get(c, 0xFF)
    h[57] = 0
    name = b"Four Islands"
    h[58:58 + len(name)] = name
    desc = (b"Four rival islands in the corners: Knights, Sorceresses, Wizards and Warlocks. "
            b"Upgrade your village, take the port, build a shipyard and sail for the central island, "
            b"where the missing mines and the dragon fortress await.")
    h[118:118 + len(desc)] = desc[:299]
    return bytes(h)


def write_object_list(b, path):
    """Write docs/objects.md: every placed object grouped by island, with its anchor tile."""
    regions = [(isl["town"] + f" ({['Knight', 'Barbarian', 'Sorceress', 'Warlock', 'Wizard', 'Necromancer'][isl['faction']]})", isl["c"])
               for isl in ISLANDS] + [("Centre island", (72, 72))]

    def region(x, y):
        name, (cx, cy) = min(regions, key=lambda r: math.hypot(x - r[1][0], y - r[1][1]))
        return name if b.ground(x, y) != 0 else "Sea"

    groups = {}
    mon = {v: k.replace("_", " ") for k, v in M.items()}
    mo = {v: k[len("MAP_OBJECT_"):].replace("_", " ").lower() for k, v in MO.items()}
    for lab, x, y, ti, cell in b.placed_objects:
        if MONSTER0 <= ti < MONSTER0 + 66:
            lab = f"{lab}: {cell.meta} x {mon.get(ti - MONSTER0, ti - MONSTER0)}"
        elif lab in ("dwelling", "rare mine", "centre mine", "ore mine", "ore mine 2", "gold mine", "windmill 2"):
            kind = mo.get(CAT[ti]["trigger"], "?")
            for base in MINE_BASE.values():
                if 0 <= ti - base < 5:
                    kind = ["ore", "sulfur", "crystal", "gems", "gold"][ti - base] + " mine"
            if kind == "alchemist lab":
                kind = "alchemist lab (mercury)"
            lab = f"dwelling: {kind}" if lab == "dwelling" else kind
        groups.setdefault(region(x, y), []).append((lab, x, y))
    out = ["# Object list", "",
           "Generated by `tools/build_map.py`; do not edit by hand. Coordinates are the object's anchor "
           "(its bottom-right tile, as in the editor), x from the left, y from the top, 0-based.", ""]
    for name, _ in regions + [("Sea", None)]:
        items = sorted(groups.get(name, []))
        if not items:
            continue
        out += [f"## {name}", "", "| Object | x | y |", "|---|---|---|"]
        out += [f"| {lab} | {x} | {y} |" for lab, x, y in items]
        out.append("")
    open(path, "w").write("\n".join(out))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "FOURISL.MX2"
    b, summary = build()
    issues = check_reachability(b, summary)
    size, towns, mines = b.m.save(out, header())
    print("written", out, size, "bytes; towns", towns, "mines", mines, "extras", len(b.m.extra_records) - 1)
    print("terrain transition fallbacks:", len(b.failed_terrain))
    print("\n".join(b.log))
    print("reachability issues:", issues)
    for k, v in summary.items():
        print(k, v)
    if len(sys.argv) > 2:
        write_object_list(b, sys.argv[2])
