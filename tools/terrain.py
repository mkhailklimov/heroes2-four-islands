"""Terrain painting with proper transition images.

Port of the terrain-transition logic from the fheroes2 editor
(src/fheroes2/maps/map_format_helper.cpp, GPL-2.0) to Python.
Ground image indices refer to GROUND32.TIL of the original game.
"""
import random

WATER, GRASS, SNOW, SWAMP, LAVA, DESERT, DIRT, WASTELAND, BEACH = range(9)
START = [0, 30, 92, 146, 208, 262, 321, 361, 415]
MAX_IMAGE = 432

TL, T, TR, R, BR, B, BL, L, C = 0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80, 0x100
TOP_ROW = TL | T | TR
BOTTOM_ROW = BL | B | BR
CENTER_ROW = L | C | R
ALL = TOP_ROW | BOTTOM_ROW | CENTER_ROW
NEIGH = [(TL, -1, -1), (T, 0, -1), (TR, 1, -1), (R, 1, 0), (BR, 1, 1), (B, 0, 1), (BL, -1, 1), (L, -1, 0)]


def ground_of(idx):
    for g in range(8, -1, -1):
        if idx >= START[g]:
            return g
    return WATER


def is_transition(idx):
    g = ground_of(idx)
    if g in (WATER, DIRT):
        return idx < 16 + START[g]
    if g == BEACH:
        return False
    return idx < 38 + START[g]


def random_index(g, rng, embedded=True):
    if g == WATER:
        return rng.randrange(3) + 16 + START[g]
    if embedded and rng.randrange(6) == 0:
        n = {GRASS: 15, SWAMP: 15, SNOW: 7, WASTELAND: 7, LAVA: 7, DESERT: 12, DIRT: 15, BEACH: 8}[g]
        base = {DIRT: 24, BEACH: 8}.get(g, 46)
        return rng.randrange(n) + base + START[g]
    off = rng.randrange(7)
    if g == DIRT:
        return off + 16 + START[g]
    if g == BEACH:
        return off + START[g]
    return off + 38 + START[g]


def has(v, bits):
    return (v & bits) == bits


def hasno(v, bits):
    return (v & bits) == 0


class Terrain:
    def __init__(self, size, seed=1):
        self.n = size
        self.rng = random.Random(seed)
        self.idx = [0] * (size * size)
        self.flags = [0] * (size * size)
        self.no_embedded = set()  # tiles where embedded terrain decorations are not allowed (objects/roads)

    def fill(self, grounds):
        """grounds: list of ground ids per tile."""
        for i, g in enumerate(grounds):
            self.idx[i] = random_index(g, self.rng, embedded=False)
            self.flags[i] = 0

    def ground(self, i):
        return ground_of(self.idx[i])

    def gdir(self, i, g):
        n = self.n
        x, y = i % n, i // n
        d = C if self.ground(i) == g else 0
        for bit, dx, dy in NEIGH:
            xx = min(n - 1, max(0, x + dx))
            yy = min(n - 1, max(0, y + dy))
            if self.ground(yy * n + xx) == g:
                d |= bit
        return d

    def set(self, i, image, hflip, vflip):
        self.flags[i] = (1 if vflip else 0) + (2 if hflip else 0)
        self.idx[i] = image

    def r3(self):
        return self.rng.randrange(3)

    def boundaries(self, gd, bd, i, off):
        s = self.set
        if gd == ALL:
            return True
        if gd == (TR | T | BOTTOM_ROW | CENTER_ROW):
            s(i, off + 12 + (0 if hasno(bd, TL) else 16) + self.r3(), True, False); return True
        if gd == (TL | T | BOTTOM_ROW | CENTER_ROW):
            s(i, off + 12 + (0 if hasno(bd, TR) else 16) + self.r3(), False, False); return True
        if gd == (BL | B | TOP_ROW | CENTER_ROW):
            s(i, off + 12 + (0 if hasno(bd, BR) else 16) + self.r3(), False, True); return True
        if gd == (BR | B | TOP_ROW | CENTER_ROW):
            s(i, off + 12 + (0 if hasno(bd, BL) else 16) + self.r3(), True, True); return True
        notwater = self.ground(i) != WATER
        if has(gd, L | T | B) and (notwater or has(gd, TL | BL)):
            if has(bd, R):
                s(i, off + 24 + self.r3(), False, False); return True
            if hasno(gd, R):
                if has(bd, TR): s(i, off + 35, False, False)
                elif has(bd, BR): s(i, off + 35, False, True)
                else: s(i, off + 8 + self.r3(), False, False)
                return True
        if has(gd, R | T | B) and (notwater or has(gd, TR | BR)):
            if has(bd, L):
                s(i, off + 24 + self.r3(), True, False); return True
            if hasno(gd, L):
                if has(bd, TL): s(i, off + 35, True, False)
                elif has(bd, BL): s(i, off + 35, True, True)
                else: s(i, off + 8 + self.r3(), True, False)
                return True
        if has(gd, B | L | R) and (notwater or has(gd, BL | BR)):
            if has(bd, T):
                s(i, off + 16 + self.r3(), False, False); return True
            if hasno(gd, T):
                if has(bd, TR): s(i, off + 34, False, False)
                elif has(bd, TL): s(i, off + 34, True, False)
                else: s(i, off + self.r3(), False, False)
                return True
        if has(gd, T | L | R) and (notwater or has(gd, TL | TR)):
            if has(bd, B):
                s(i, off + 16 + self.r3(), False, True); return True
            if hasno(gd, B):
                if has(bd, BR): s(i, off + 34, False, True)
                elif has(bd, BL): s(i, off + 34, True, True)
                else: s(i, off + self.r3(), False, True)
                return True
        if has(gd, R | BR | B):
            if has(bd, T | L) or has(bd, T | BL) or has(bd, TR | L):
                s(i, off + 20 + self.r3(), True, False); return True
            if hasno(gd, T | L):
                if has(bd, T): s(i, off + 36, True, False)
                elif has(bd, L): s(i, off + 37, True, False)
                elif has(bd, TR): s(i, off + 33, True, False)
                elif has(bd, BL): s(i, off + 32, True, False)
                else: s(i, off + 4 + self.r3(), True, False)
                return True
        if has(gd, L | BL | B):
            if has(bd, T | R) or has(bd, T | BR) or has(bd, TL | R):
                s(i, off + 20 + self.r3(), False, False); return True
            if hasno(gd, T | R):
                if has(bd, T): s(i, off + 36, False, False)
                elif has(bd, R): s(i, off + 37, False, False)
                elif has(bd, TL): s(i, off + 33, False, False)
                elif has(bd, BR): s(i, off + 32, False, False)
                else: s(i, off + 4 + self.r3(), False, False)
                return True
        if has(gd, T | TL | L):
            if has(bd, R | B) or has(bd, R | BL) or has(bd, TR | B):
                s(i, off + 20 + self.r3(), False, True); return True
            if hasno(gd, R | B):
                if has(bd, B): s(i, off + 36, False, True)
                elif has(bd, R): s(i, off + 37, False, True)
                elif has(bd, BL): s(i, off + 33, False, True)
                elif has(bd, TR): s(i, off + 32, False, True)
                else: s(i, off + 4 + self.r3(), False, True)
                return True
        if has(gd, T | TR | R):
            if has(bd, L | B) or has(bd, L | BR) or has(bd, TL | B):
                s(i, off + 20 + self.r3(), True, True); return True
            if hasno(gd, L | B):
                if has(bd, B): s(i, off + 36, True, True)
                elif has(bd, L): s(i, off + 37, True, True)
                elif has(bd, BR): s(i, off + 33, True, True)
                elif has(bd, TL): s(i, off + 32, True, True)
                else: s(i, off + 4 + self.r3(), True, True)
                return True
        if has(gd, T | R | B | L):
            g = self.ground(i)
            if g != WATER:
                s(i, random_index(g, self.rng, i not in self.no_embedded), False, False)
                return True
        return False

    def update_tile(self, i):
        g = self.ground(i)
        if g == BEACH:
            return True
        if g == DIRT:
            gd = ALL - (self.gdir(i, WATER) | self.gdir(i, BEACH))
        else:
            gd = self.gdir(i, g) | C
        if gd == ALL:
            if is_transition(self.idx[i]):
                self.set(i, random_index(g, self.rng, i not in self.no_embedded), False, False)
            return True
        if g in (WATER, DIRT):
            return self.boundaries(gd, 0, i, START[g])
        bd = self.gdir(i, WATER) | self.gdir(i, BEACH)
        return self.boundaries(gd, bd, i, START[g])

    def around(self, i):
        n = self.n
        x, y = i % n, i // n
        out = []
        for _, dx, dy in NEIGH:
            if 0 <= x + dx < n and 0 <= y + dy < n:
                out.append((y + dy) * n + x + dx)
        return out

    def update_area(self, tiles, fill_ground=None, depth=0):
        failed = []
        for i in tiles:
            if self.update_tile(i):
                continue
            g0 = self.ground(i)
            cands = []
            if fill_ground is not None and g0 != fill_ground:
                cands.append(fill_ground)
            water = g0 == WATER
            for j in self.around(i):
                gj = self.ground(j)
                if gj != g0 and gj not in cands:
                    cands.append(gj)
                water = water or gj == WATER
            last = BEACH if water else DIRT
            if last not in cands:
                cands.append(last)
            ok = False
            for ng in cands:
                self.set(i, random_index(ng, self.rng, False), False, False)
                if not self.update_tile(i):
                    continue
                if depth < 6:
                    for j in self.around(i):
                        if not self.update_tile(j):
                            self.update_area([j], fill_ground, depth + 1)
                ok = True
                break
            if not ok:
                self.set(i, random_index(g0, self.rng, False), False, False)
                failed.append(i)
        return failed

    def finalize(self):
        all_tiles = list(range(self.n * self.n))
        failed = self.update_area(all_tiles)
        # second pass to settle neighbours changed by the fallback logic
        failed = self.update_area(all_tiles)
        return failed
