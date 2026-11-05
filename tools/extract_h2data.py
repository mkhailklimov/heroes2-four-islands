"""Extract the original HoMM2 editor's object catalogue and ground tables
from the homm2-decomp sources (https://github.com/sushi-shi/homm2-decomp, CC0)
into h2data.json. Text parsing only; nothing from the decomp is executed.

usage: python3 extract_h2data.py <path-to-homm2-decomp>
"""
import json
import ast
import operator

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.BitOr: operator.or_,
        ast.LShift: operator.lshift, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}


def safe_eval(expr, env):
    """Evaluate a C constant expression (numbers, known names, + - * | << / %, lists) without executing code."""
    expr = expr.replace("/", "//")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, int):
            return n.value
        if isinstance(n, ast.Name):
            return env[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.List):
            return [ev(e) for e in n.elts]
        raise ValueError("unsupported expression: " + ast.dump(n))

    return ev(ast.parse(expr.strip(), mode="eval"))

import re
import sys

root = sys.argv[1]


def read(p):
    return open(f"{root}/{p}", encoding="utf-8", errors="replace").read()


def parse_enum_block(text, begin_pat):
    m = re.search(begin_pat + r"(.*?)H2_ENUM_[A-Z_]*END", text, re.S)
    body = re.sub(r"//.*", "", m.group(1))
    out = {}
    for line in body.split(","):
        line = line.strip()
        if "=" not in line:
            continue
        k, v = [s.strip() for s in line.split("=", 1)]
        out[k] = v
    return out


def resolve(d, extra=None):
    env = dict(extra or {})
    res = {}
    for _ in range(10):
        for k, v in d.items():
            if k in res:
                continue
            expr = re.sub(r"\bIDX\(([^)]*)\)", r"(\1)", v)
            try:
                res[k] = int(safe_eval(expr, {**env, **res}))
            except (KeyError, ValueError, SyntaxError):
                pass
    return res


kb = read("include/SOURCE/kbTypes.h")
mapobj = resolve(parse_enum_block(kb, r"H2_ENUM_CLASS_BEGIN_SPLIT\(MapObjectType, i16\)"))
cell_h = read("include/EDITOR/mapcell.h")
tileset = resolve(parse_enum_block(cell_h, r"H2_ENUM_CLASS_BEGIN_SPLIT\(TilesetId, u8\)"))
ov_h = read("include/EDITOR/OVERLAY.h")
consts = {}
for blk in re.findall(r"H2_ENUM_BEGIN\(\w+\)(.*?)H2_ENUM_END", ov_h, re.S):
    body = re.sub(r"//.*", "", blk)
    for line in body.split(","):
        if "=" in line:
            k, v = [s.strip() for s in line.split("=", 1)]
            consts[k] = v
consts = resolve(consts)
ov_cpp = read("src/EDITOR/OVERLAY.cpp")
for k, v in re.findall(r"(OVERLAY_[A-Z_]+)\s*=\s*(-?\d+)", ov_cpp):
    consts.setdefault(k, int(v))
trig = {"MAP_TRIGGER_ACTION_FLAG": 0x80}

env = {**mapobj, **tileset, **consts, **trig}

# ---- object catalogue
src = read("src/EDITOR/EDITMGR.cpp")
start = src.index("overlayType gOverlayTypes[OVERLAY_TYPE_COUNT] = {")
end = src.index("\n};", start)
body = src[start + len("overlayType gOverlayTypes[OVERLAY_TYPE_COUNT] = {"):end]
body = re.sub(r"//.*", "", body)
body = re.sub(r"\bIDX\(([^)]*)\)", r"(\1)", body)
pyexpr = "[" + body.replace("{", "[").replace("}", "]") + "]"
types = safe_eval(pyexpr, env)
fields = ["id", "group", "ordinal", "tileset", "category", "frequency", "animationFrames", "occupied", "terrainMask",
          "groundMask", "overlayRows", "shadowRows", "animatedRows", "resourceRows", "color", "flags", "entranceRows",
          "groundLayer", "trigger", "width", "frameNumbering"]
cat = []
for t in types:
    assert len(t) == len(fields), (len(t), t)
    cat.append(dict(zip(fields, t)))
assert len(cat) == consts["OVERLAY_TYPE_COUNT"], len(cat)

W, H = 8, 6


def grid_has(grid, x, y):
    bit = (W - x - 1) + (H - y - 1) * W
    if bit < 32:
        return (grid[1] >> bit) & 1 == 1
    return (grid[0] >> (bit - 32)) & 1 == 1


# FillInOverlayTiles
cur = -1
base = 0
first = 0
for t in cat:
    width = 0
    if t["tileset"] != cur:
        base = 0
    cur = t["tileset"]
    if t["frameNumbering"] == consts["OVERLAY_FRAMES_SHARED"]:
        base = first
    if t["frameNumbering"] == consts["OVERLAY_FRAMES_OWN"]:
        base = 0
    nxt = base
    first = base
    frames = []
    for gy in range(H):
        for gx in range(W):
            if grid_has(t["occupied"], gx, gy):
                width = max(width, W - gx)
                frames.append(nxt)
                if grid_has(t["animatedRows"], gx, gy):
                    nxt += t["animationFrames"] + 1
                    base += t["animationFrames"] + 1
                else:
                    nxt += 1
                    base += 1
            else:
                frames.append(255)
    t["frames"] = frames
    t["width"] = width
    for g in ["occupied", "overlayRows", "shadowRows", "animatedRows", "resourceRows", "entranceRows"]:
        t[g] = [[1 if grid_has(t[g], x, y) else 0 for x in range(W)] for y in range(H)]

# ---- ground tables
kbcpp = read("src/SOURCE/KB.cpp")
macros = {}


def expand(text):
    std = re.search(r"#define GROUND_SHAPE_STANDARD_FRAME_SET(.*?)\n\n", kbcpp, re.S).group(1)
    std = std.replace("\\\n", " ")
    text = text.replace("GROUND_SHAPE_STANDARD_FRAME_SET", std)
    for _ in range(8):
        text = re.sub(r"GROUND_REPEAT_(\d+)\(([^()]*)\)", lambda m: ",".join([m.group(2)] * int(m.group(1))), text)
    return text


def table(name):
    m = re.search(name + r"\[GROUND_TILE_IMAGE_COUNT\] = \{(.*?)\};", kbcpp, re.S)
    t = expand(re.sub(r"//.*", "", m.group(1)))
    tenv = {k: int(v) for k, v in re.findall(r"(TERRAIN_[A-Z]+)\s*=\s*(-?\d+)", kb)}
    tenv["GROUND_SHAPE_VARIED"] = 0x80
    vals = [int(safe_eval(s, tenv)) for s in t.split(",") if s.strip()]
    assert len(vals) == 432, (name, len(vals))
    return vals


data = {
    "mapobj": mapobj,
    "tileset": tileset,
    "consts": consts,
    "catalogue": cat,
    "groundToTerrain": table("giGroundToTerrain"),
    "groundShape": table("giGroundShape"),
}
json.dump(data, open(__file__.rsplit("/", 1)[0] + "/h2data.json", "w"))
print("types", len(cat), "mapobj", len(mapobj), "tilesets", len(tileset))
