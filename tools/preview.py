"""Render a schematic minimap PNG of an MP2/MX2 map (terrain colors + object markers)."""
import sys
from PIL import Image, ImageDraw
import mp2read
from terrain import ground_of

COL = [(40, 80, 170), (70, 150, 60), (230, 235, 245), (70, 95, 70), (90, 50, 40),
       (220, 200, 120), (150, 110, 70), (170, 160, 130), (235, 220, 160)]
MARK = {"OBJ_CASTLE": (255, 0, 255), "OBJ_HERO": (255, 255, 0), "OBJ_JAIL": (255, 128, 0),
        "OBJ_MINE": (0, 0, 0), "OBJ_SAWMILL": (0, 0, 0), "OBJ_ALCHEMIST_LAB": (0, 0, 0),
        "OBJ_MONSTER": (255, 0, 0), "OBJ_WHIRLPOOL": (0, 255, 255), "OBJ_MAGELLANS_MAPS": (0, 255, 255)}
m = mp2read.read(sys.argv[1])
w, h, S = m["w"], m["h"], int(sys.argv[3]) if len(sys.argv) > 3 else 5
img = Image.new("RGB", (w * S, h * S))
d = ImageDraw.Draw(img)
for i, t in enumerate(m["tiles"]):
    x, y = i % w, i // w
    c = COL[ground_of(t["terr"])]
    name = mp2read.OBJ.get(t["otype"], "")
    if "TREES" in name: c = (20, 90, 30)
    if "MOUNTAINS" in name or "ROCK" in name: c = (100, 100, 100)
    if name.startswith("OBJ_NON_ACTION"): c = tuple(v // 2 for v in c)
    d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=c)
    mk = MARK.get(name)
    if mk is None and name.startswith("OBJ_") and not name.startswith("OBJ_NON") and name not in ("OBJ_NONE", "OBJ_COAST", "OBJ_TREES", "OBJ_MOUNTAINS", "OBJ_ROCK"):
        mk = (255, 255, 255)
    if mk:
        d.ellipse([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=mk)
img.save(sys.argv[2])
