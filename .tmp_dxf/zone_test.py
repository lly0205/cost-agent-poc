# -*- coding: utf-8 -*-
import ezdxf, sys, re, collections, math
from shapely.geometry import Polygon, Point, LineString
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S1": (36225, 120325), "S2": (-55172, 28928), "S3": (-139272, -55172),
         "S4": (-223372, -139272), "S5": (-307472, -223372),
         "S6": (-391572, -307472), "S7": (-475672, -391572)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1:
            return n
    return None

# hatch polygon in S3
hatch = None
for e in msp.query("HATCH"):
    if e.dxf.layer == "看线":
        for p in e.paths:
            pts = []
            if hasattr(p, "vertices"):
                pts = [(v[0], v[1]) for v in p.vertices]
            if len(pts) >= 3:
                poly = Polygon(pts)
                c = poly.centroid
                if X0 <= c.x <= X1 and band(c.y) == "S3" and poly.area/1e6 > 1000:
                    hatch = poly
print("hatch area", hatch.area/1e6)

# CT label groups in S3: CT text + nearest elevation text
ctt, elev = [], []
for e in msp.query("TEXT"):
    if e.dxf.layer == "承台集中标注":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S3":
            t = e.dxf.text
            if t.startswith("CT"):
                ctt.append((x, y, t))
            elif "标高" in t:
                elev.append((x, y, t))

res = collections.Counter()
for x, y, t in ctt:
    inside = hatch.contains(Point(x, y))
    # nearest elevation text within 600
    el = None
    for ex, ey, et in elev:
        if abs(ex-x) < 200 and 0 < y-ey < 600:
            el = et
            break
    res[(t, "IN" if inside else "OUT", el)] += 1
print("\nCT, zone, elevation_label, count:")
for k in sorted(res, key=str):
    print(" ", k, res[k])

# caps polygons inside hatch
caps_in = caps_out = 0
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S3":
            if hatch.contains(Point(cx, cy)): caps_in += 1
            else: caps_out += 1
print(f"\ncaps polygons: in hatch={caps_in}, out={caps_out}")

# columns (S5) inside hatch (shift hatch to S5 band)
sh = translate(hatch, yoff=BANDS["S5"][0]-BANDS["S3"][0])
cin = cout = 0
for e in msp.query("TEXT"):
    if e.dxf.layer == "柱集中标注":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S5":
            if sh.contains(Point(x, y)): cin += 1
            else: cout += 1
print(f"columns: in hatch={cin}, out={cout}")

# piles (S1) inside hatch
sh1 = translate(hatch, yoff=BANDS["S1"][0]-BANDS["S3"][0])
pin = pout = 0
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "桩":
        pts = e.get_points("xy")
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S1":
            if sh1.contains(Point(cx, cy)): pin += 1
            else: pout += 1
print(f"piles: in hatch={pin}, out={pout}")
