"""A minimal re-implementation of the original HoMM2 (Price of Loyalty) map
editor's object placement and save logic, following the homm2-decomp
sources (CC0): PlaceOverlay, UpdateTriggers/SetCoast and SaveMap.
Object data comes from h2data.json (see extract_h2data.py).
"""
import json
import os
import random
import struct

from terrain import Terrain, WATER, ground_of

D = json.load(open(os.path.join(os.path.dirname(__file__), "h2data.json")))
CAT = D["catalogue"]
BY_ID = {t["id"]: i for i, t in enumerate(CAT)}
MO = D["mapobj"]
TS = D["tileset"]
K = D["consts"]
G2T = D["groundToTerrain"]
GSHAPE = D["groundShape"]
ACTION = 0x80
NONE = 0xFF

# editor ground shapes
SH_PLAIN, SH_N, SH_NE, SH_E, SH_NE_IN = 0, 1, 2, 3, 4
SH_N_ALT, SH_E_ALT = 16, 17
SH_DECOR = (18, 19, 20, 21)


def new_part():
    return None


class Cell:
    __slots__ = ("terrain", "flags", "obj", "ovl", "trigger", "meta", "extras")

    def __init__(self):
        self.terrain = 0
        self.flags = 0
        self.obj = None  # dict(ts, idx, anim, ground, shadow, odraw, link)
        self.ovl = None  # dict(ts, idx, anim, top, link)
        self.trigger = 0
        self.meta = 0
        self.extras = []  # list of [obj, ovl]


class Map:
    def __init__(self, size, seed=7):
        self.n = size
        self.cells = [Cell() for _ in range(size * size)]
        self.link = 0
        self.extra_records = [None]  # map-extra records (towns, heroes...), index 0 unused
        self.rng = random.Random(seed)

    def cell(self, x, y):
        return self.cells[y * self.n + x]

    def inside(self, x, y):
        return 0 <= x < self.n and 0 <= y < self.n

    def terrain_type(self, x, y):
        return G2T[self.cell(x, y).terrain]

    # ---- extra-chain helpers (fullMap::GetNewCellExtraObject / Overlay)
    def _extra_for_obj(self, c):
        for e in c.extras:
            if e[0] is None:
                return e
        e = [None, None]
        c.extras.append(e)
        return e

    def _extra_for_ovl(self, c):
        for e in c.extras:
            if e[1] is None:
                return e
        e = [None, None]
        c.extras.append(e)
        return e

    def push_cell_object(self, c):
        e = self._extra_for_obj(c)
        e[0] = c.obj
        c.obj = None
        c.trigger = MO["MAP_OBJECT_NONE"]

    def _plain_ground(self, idx):
        """ChooseGroundTile replacement: a non-varied tile of the same terrain and shape."""
        terr = G2T[idx]
        shape = GSHAPE[idx] & 0x7F
        cands = [i for i in range(432) if G2T[i] == terr and GSHAPE[i] == shape]
        return self.rng.choice(cands) if cands else idx

    # ---- placement check (simplified CanPlaceOverlay)
    def can_place(self, ti, ax, ay):
        t = CAT[ti]
        x0, y0 = ax - 7, ay - 5
        for row in range(6):
            for col in range(8):
                f = t["frames"][row * 8 + col]
                if f == NONE:
                    continue
                x, y = x0 + col, y0 + row
                if not self.inside(x, y):
                    return False
                c = self.cell(x, y)
                if t["shadowRows"][row][col] or t["overlayRows"][row][col]:
                    continue
                if c.obj is not None and not c.obj["shadow"]:
                    return False
                terr = G2T[c.terrain]
                if not (t["groundMask"] >> terr) & 1:
                    return False
        return True

    # ---- PlaceOverlay
    def place(self, ti, ax, ay, new_link=True, check=True):
        """Place catalogue entry `ti` (index into the catalogue) with its anchor on (ax, ay).
        Returns the map cell of the (last) entrance."""
        if new_link:
            self.link += 1
        if check and not self.can_place(ti, ax, ay):
            raise ValueError(f"cannot place type {ti} at {ax},{ay}")
        t = CAT[ti]
        x, y = ax - 7, ay - 5
        trig = t["trigger"]
        entrance_cell = None
        if t["category"] == 5:  # town
            if K["OVERLAY_TOWN_FIRST"] <= t["id"] <= K["OVERLAY_TOWN_LAST"]:
                shadow = (t["id"] - K["OVERLAY_TOWN_FIRST"]) % K["OVERLAY_TOWN_VARIANTS"] + K["OVERLAY_TOWN_SHADOWS"]
            else:
                shadow = (t["id"] - K["OVERLAY_RANDOM_TOWN_FIRST"]) % K["OVERLAY_TOWN_KINDS"] + K["OVERLAY_RANDOM_TOWN_SHADOWS"]
            ground = self.terrain_type(x + 5, y + 5) + K["OVERLAY_TOWN_GROUNDS"]
            self.place(BY_ID[shadow], ax, ay, new_link=False, check=False)
            self.place(BY_ID[ground], ax, ay, new_link=False, check=False)
        for row in range(6):
            for col in range(8):
                f = t["frames"][row * 8 + col]
                if f == NONE or not self.inside(x + col, y + row):
                    continue
                c = self.cell(x + col, y + row)
                occ_below = row < 5 and t["occupied"][row + 1][col]
                shadow_below = row < 5 and t["shadowRows"][row + 1][col]
                ent_below = row < 5 and t["entranceRows"][row + 1][col]
                anim = t["animatedRows"][row][col]
                is_ent = t["entranceRows"][row][col]
                if t["overlayRows"][row][col]:
                    top = (row < 4 and occ_below and (trig != MO["MAP_OBJECT_ROAD"] or not ent_below) and not shadow_below)
                    part = dict(ts=t["tileset"], idx=f, anim=anim, top=1 if top else 0, link=self.link)
                    if c.ovl is not None:
                        self._extra_for_ovl(c)[1] = part
                    else:
                        c.ovl = part
                else:
                    if c.obj is not None and is_ent and trig != MO["MAP_OBJECT_MINE"]:
                        self.push_cell_object(c)
                    shadow = t["shadowRows"][row][col]
                    odraw = (row < 5 and not t["groundLayer"] and not shadow and occ_below and not shadow_below)
                    part = dict(ts=t["tileset"], idx=f, anim=anim, ground=t["groundLayer"], shadow=shadow,
                                odraw=1 if odraw else 0, link=self.link)
                    if c.obj is not None:
                        self._extra_for_obj(c)[0] = part
                    else:
                        if GSHAPE[c.terrain] & 0x80:
                            c.terrain = self._plain_ground(c.terrain)
                        c.obj = part
                        c.trigger = MO["MAP_OBJECT_NONE"] if shadow else trig
                if is_ent and trig == MO["MAP_OBJECT_MINE"]:
                    c.trigger = MO["MAP_OBJECT_MINE"]
                if is_ent:
                    c.trigger |= ACTION
                    entrance_cell = c
                if is_ent and t["id"] == K.get("OVERLAY_HUT_OF_MAGI_SITE"):
                    c.meta = 2
                if is_ent and t["id"] == K.get("OVERLAY_EYE_OF_MAGI_SITE"):
                    c.meta = 3
                if t["resourceRows"][row][col]:
                    self._resource_marker(K["OVERLAY_RESOURCE_MARKERS"] + t["color"], x + col, y + row)
        if t["category"] == 5:
            self.place(BY_ID[K["OVERLAY_TOWN_FLAGS"] + t["color"] * 2], x + K["OVERLAY_LEFT_FLAG_X"] + 7,
                       y + K["OVERLAY_FLAG_Y"] + 5, new_link=False, check=False)
            self.place(BY_ID[K["OVERLAY_TOWN_FLAGS"] + 1 + t["color"] * 2], x + K["OVERLAY_RIGHT_FLAG_X"] + 7,
                       y + K["OVERLAY_FLAG_Y"] + 5, new_link=False, check=False)
        return entrance_cell

    def _resource_marker(self, marker_type, x, y):
        t = CAT[BY_ID[marker_type]]
        idx = t["frames"][47]
        c = self.cell(x, y)
        ts = TS["TILESET_EXTRAOVR"]
        part = dict(ts=ts, idx=idx, anim=0, ground=0, shadow=0, odraw=0, link=self.link)
        if c.obj is not None and c.obj["ts"] != ts:
            for e in c.extras:
                if e[0] is None or e[0]["ts"] == ts:
                    e[0] = part
                    return
            self._extra_for_obj(c)[0] = part
        else:
            c.obj = part

    def add_extra_record(self, cell, data):
        assert len(data) in (70, 76)
        cell.meta = len(self.extra_records)
        self.extra_records.append(bytes(data))

    # ---- UpdateTriggers: coasts and shore flags
    def can_be_coast(self, x, y):
        if not self.inside(x, y):
            return False
        c = self.cell(x, y)
        if c.trigger & ACTION or c.trigger in (MO["MAP_OBJECT_CASTLE"], MO["MAP_OBJECT_RANDOM_TOWN"], MO["MAP_OBJECT_RANDOM_CASTLE"]):
            return False
        if c.obj is not None:
            shadows_only = False
            if c.obj["shadow"]:
                shadows_only = all(e[0] is None or e[0]["shadow"] for e in c.extras)
            if not shadows_only:
                return False
        return True

    def _coast(self, x, y):
        if self.can_be_coast(x, y):
            self.cell(x, y).trigger = MO["MAP_OBJECT_COAST"]

    def set_coast(self, x, y):
        c = self.cell(x, y)
        if G2T[c.terrain] != 0:
            return
        sh = GSHAPE[c.terrain]
        fv, fh = c.flags & 1, c.flags & 2
        if sh in (SH_N, SH_N_ALT):
            self._coast(x, y + 1) if fv else self._coast(x, y - 1)
        elif sh == SH_NE:
            if fv and fh:
                self._coast(x, y + 1); self._coast(x - 1, y); self._coast(x - 1, y + 1)
            elif fh:
                self._coast(x, y - 1); self._coast(x - 1, y); self._coast(x - 1, y - 1)
            elif fv:
                self._coast(x, y + 1); self._coast(x + 1, y); self._coast(x + 1, y + 1)
            else:
                self._coast(x, y - 1); self._coast(x + 1, y); self._coast(x + 1, y - 1)
        elif sh in (SH_E, SH_E_ALT):
            self._coast(x - 1, y) if fh else self._coast(x + 1, y)
        elif sh == SH_NE_IN:
            if fv and fh:
                self._coast(x - 1, y + 1)
            elif fh:
                self._coast(x - 1, y - 1)
            elif fv:
                self._coast(x + 1, y + 1)
            else:
                self._coast(x + 1, y - 1)

    def update_triggers(self):
        n = self.n
        for c in self.cells:
            if c.trigger == MO["MAP_OBJECT_COAST"]:
                c.trigger = 0
        for y in range(n):
            for x in range(n):
                c = self.cell(x, y)
                if not (c.trigger & ACTION) and c.trigger not in (MO["MAP_OBJECT_CASTLE"], MO["MAP_OBJECT_RANDOM_TOWN"], MO["MAP_OBJECT_RANDOM_CASTLE"]):
                    self.set_coast(x, y)
                elif c.trigger == MO["MAP_OBJECT_BOAT"] | ACTION:
                    self.set_coast(x, y)
                sh = GSHAPE[c.terrain]
                water = G2T[c.terrain] == 0
                if water and sh in (SH_N, SH_N_ALT, SH_NE, SH_E_ALT, SH_E, SH_NE_IN):
                    c.flags |= 0x04
                else:
                    c.flags &= ~0x04
                if water and sh == SH_NE:
                    c.flags |= 0x10
                else:
                    c.flags &= ~0x10

    # ---- file writing (editManager::SaveMap)
    @staticmethod
    def _cell_bytes(c, extra_index):
        o, v = c.obj, c.ovl
        if o:
            b_obj = (o["anim"] & 1) | ((o["ts"] & 0x3F) << 2)
            b_idx = o["idx"]
            data = (o["ground"] & 1) | ((o["shadow"] & 1) << 1) | ((o["odraw"] & 1) << 2) | ((c.meta & 0x1FFF) << 3)
            l1 = o["link"]
        else:
            b_obj, b_idx, data, l1 = 0, NONE, (c.meta & 0x1FFF) << 3, 0
        if v:
            b_ovl = (v["anim"] & 1) | ((v["top"] & 1) << 1) | ((v["ts"] & 0x3F) << 2)
            b_oidx = v["idx"]
            l2 = v["link"]
        else:
            b_ovl, b_oidx, l2 = 0, NONE, 0
        return struct.pack("<HBBHBBBBHII", c.terrain, b_obj, b_idx, data, b_ovl, b_oidx, c.flags & 0xFF,
                           c.trigger & 0xFF, extra_index, l1, l2)

    @staticmethod
    def _extra_bytes(e, nxt):
        o, v = e
        if o:
            b1 = (o["anim"] & 1) | ((o["ts"] & 0x7F) << 1)
            bi = o["idx"]
            q = (o["ground"] & 1) | ((o["shadow"] & 1) << 1) | ((o["odraw"] & 1) << 2)
            l1 = o["link"]
        else:
            b1, bi, q, l1 = 0, NONE, 0, 0
        if v:
            b2 = (v["anim"] & 1) | ((v["top"] & 1) << 1) | ((v["ts"] & 0x3F) << 2)
            b2i = v["idx"]
            l2 = v["link"]
        else:
            b2, b2i, l2 = 0, NONE, 0
        return struct.pack("<HBBBBBII", nxt, b1, bi, q, b2, b2i, l1, l2)

    def save(self, path, header):
        self.update_triggers()
        n = self.n
        # extras pool: record 0 unused
        pool = [struct.pack("<HBBBBBII", 0, 0, NONE, 0, 0, NONE, 0, 0)]
        cell_bytes = []
        for c in self.cells:
            recs = [e for e in c.extras if e[0] is not None or e[1] is not None]
            first = len(pool) if recs else 0
            for k, e in enumerate(recs):
                nxt = len(pool) + 1 if k + 1 < len(recs) else 0
                pool.append(self._extra_bytes(e, nxt))
            cell_bytes.append(self._cell_bytes(c, first))
        # slack free records as the editor keeps them
        for _ in range(4):
            pool.append(struct.pack("<HBBBBBII", 0xFFFF, 0, NONE, 0, 0, NONE, 0, 0))
        out = bytearray(header)
        assert len(out) == 420
        out += struct.pack("<II", n, n)
        for cb in cell_bytes:
            out += cb
        out += struct.pack("<I", len(pool))
        for p in pool:
            out += p
        # towns
        towns = []
        mines = []
        obelisks = 0
        for y in range(n):
            for x in range(n):
                c = self.cell(x, y)
                tr = c.trigger
                if tr in (MO["MAP_OBJECT_RANDOM_CASTLE"] | ACTION, MO["MAP_OBJECT_RANDOM_TOWN"] | ACTION, MO["MAP_OBJECT_CASTLE"] | ACTION):
                    rec = self.extra_records[c.meta]
                    faction = rec[38]
                    is_castle = rec[39]
                    towns.append(bytes([x, y, (faction | (0x80 if is_castle else 0)) & 0xFF]))
                kinds = {"MAP_OBJECT_LIGHTHOUSE": 100, "MAP_OBJECT_ABANDONED_MINE": 103, "MAP_OBJECT_DRAGON_CITY": 101,
                         "MAP_OBJECT_RANDOM_MINE": 102}
                for name in ("MAP_OBJECT_DRAGON_CITY", "MAP_OBJECT_LIGHTHOUSE", "MAP_OBJECT_MINE", "MAP_OBJECT_SAWMILL",
                             "MAP_OBJECT_ALCHEMIST_LAB", "MAP_OBJECT_ABANDONED_MINE", "MAP_OBJECT_RANDOM_MINE"):
                    if tr == MO[name] | ACTION:
                        if name in kinds:
                            kind = kinds[name]
                        else:
                            kind = None
                            for e in c.extras:
                                if e[0] is not None and e[0]["ts"] == TS["TILESET_EXTRAOVR"]:
                                    kind = e[0]["idx"] + 2
                                    break
                            if kind is None:
                                kind = 0 if name == "MAP_OBJECT_SAWMILL" else 1
                        mines.append(bytes([x, y, kind]))
                if tr == MO["MAP_OBJECT_OBELISK"] | ACTION:
                    obelisks += 1
        assert len(towns) <= 72 and len(mines) <= 144, (len(towns), len(mines))
        for t in towns:
            out += t
        out += bytes([0xFF, 0xFF, 0x00]) * (72 - len(towns))
        for m in mines:
            out += m
        out += bytes([0xFF, 0xFF, 0xFF]) * (144 - len(mines))
        out += bytes([max(1, obelisks)])
        # rumour / time event indices: none (header counts are 0)
        out += struct.pack("<I", len(self.extra_records))  # i32 m_extraCount
        for rec in self.extra_records[1:]:
            out += struct.pack("<H", len(rec)) + rec
        out += struct.pack("<I", self.link)
        with open(path, "wb") as f:
            f.write(out)
        return len(out), len(towns), len(mines)
