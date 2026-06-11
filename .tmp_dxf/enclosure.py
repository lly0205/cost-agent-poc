# -*- coding: utf-8 -*-
import ezdxf, sys, collections, math
from shapely.geometry import LineString, Polygon, Point, MultiLineString
from shapely.ops import unary_union, polygonize
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S5 = (-307472, -223372)

wl = []
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙" and X0 <= e.dxf.start.x <= X1 and S5[0] <= e.dxf.start.y <= S5[1]:
        wl.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))

# centerline pairing (same as before)
H = [l for l in wl if abs(l[0][1]-l[1][1]) < 1]
V = [l for l in wl if abs(l[0][0]-l[1][0]) < 1]
def pair_lines(items_raw, horiz):
    items = []
    for (p1, p2) in items_raw:
        if horiz: items.append((p1[1], min(p1[0], p2[0]), max(p1[0], p2[0])))
        else: items.append((p1[0], min(p1[1], p2[1]), max(p1[1], p2[1])))
    items.sort()
    out = []
    for i in range(len(items)):
        ci, a0, a1 = items[i]
        for j in range(i+1, len(items)):
            cj, b0, b1 = items[j]
            w = cj-ci
            if w > 600: break
            if w < 100: continue
            ov0, ov1 = max(a0, b0), min(a1, b1)
            if ov1-ov0 > 500:
                out.append(((ci+cj)/2, round(w, -1), ov0, ov1))
    return out
def dedupe(strips):
    d = collections.defaultdict(list)
    for c, w, a0, a1 in strips:
        d[(round(c, -1), w)].append((a0, a1))
    out = []
    for (c, w), segs in d.items():
        segs.sort(); m = []
        for a0, a1 in segs:
            if m and a0 <= m[-1][1]+50: m[-1][1] = max(m[-1][1], a1)
            else: m.append([a0, a1])
        for a0, a1 in m: out.append((c, w, a0, a1))
    return out
wh = dedupe(pair_lines(H, True))
wv = dedupe(pair_lines(V, False))

EXT = 400
segs = []
for c, w, a0, a1 in wh:
    segs.append(LineString([(a0-EXT, c), (a1+EXT, c)]))
for c, w, a0, a1 in wv:
    segs.append(LineString([(c, a0-EXT), (c, a1+EXT)]))
merged = unary_union(segs)
polys = sorted(polygonize(merged), key=lambda p: -p.area)
print("polygons found:", len(polys))
for p in polys[:8]:
    b = [round(v/1000, 1) for v in p.bounds]
    print(f"  area={p.area/1e6:.1f} m2 perim={p.length/1000:.1f} m bbox={b}")

if polys:
    import pickle
    enc = unary_union([p for p in polys if p.area/1e6 > 50])
    with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "wb") as f:
        pickle.dump(enc, f)
    print("enclosure union area:", enc.area/1e6, "m2")
