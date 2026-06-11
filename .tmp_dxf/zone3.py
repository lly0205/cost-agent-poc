# -*- coding: utf-8 -*-
import ezdxf, sys, collections, pickle
from shapely.geometry import Polygon, Point
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S1": (36225, 120325), "S3": (-139272, -55172), "S5": (-307472, -223372), "S6": (-391572, -307472)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1: return n
    return None

with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)   # S5 coords
enc3 = translate(enc5, yoff=BANDS["S3"][0]-BANDS["S5"][0])

hatch = None
for e in msp.query("HATCH"):
    if e.dxf.layer == "看线":
        for p in e.paths:
            if hasattr(p, "vertices"):
                pts = [(v[0], v[1]) for v in p.vertices]
                if len(pts) >= 3:
                    poly = Polygon(pts)
                    c = poly.centroid
                    if X0 <= c.x <= X1 and band(c.y) == "S3" and poly.area/1e6 > 1000:
                        hatch = poly

# classify caps polygons 3-way and group by nearest label
ctpos = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "承台集中标注" and e.dxf.text.startswith("CT"):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S3":
            ctpos.append((x, y, e.dxf.text))

res = collections.Counter()
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S3":
            p = Point(cx, cy)
            zone = "DEEP" if hatch.contains(p) else ("SHALLOW" if enc3.contains(p) else "PERIM")
            best, bd = None, 1e18
            for tx, ty, name in ctpos:
                d = (tx-cx)**2+(ty-cy)**2
                if d < bd: bd, best = d, name
            res[(best, zone)] += 1
print("cap polygon zones:")
tot = collections.Counter()
for k in sorted(res, key=str):
    print(" ", k, res[k])
    tot[k[1]] += res[k]
print(tot)
