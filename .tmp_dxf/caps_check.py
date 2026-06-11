# -*- coding: utf-8 -*-
import ezdxf, sys, math, collections
from ezdxf import bbox
from shapely.geometry import Polygon, Point
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S3 = (-139272, -55172)

# axis coordinates (S3)
AXX = {1:-4821395,2:-4812995,3:-4804595,4:-4796195,5:-4787795,6:-4779395,7:-4770995,
       8:-4762595,9:-4754195,10:-4745795,11:-4737395,12:-4728995,13:-4720595,14:-4712195}
AXY = {"A":-117787,"B":-108187,"C":-98587,"D":-86587,"E":-76987,"F":-67387}
def axpos(x, y):
    bx = min(AXX.items(), key=lambda kv: abs(kv[1]-x))
    by = min(AXY.items(), key=lambda kv: abs(kv[1]-y))
    return f"{bx[0]}{'%+d' % round((x-bx[1])/100)*0}/{by[0]}", f"近{bx[0]}轴({(x-bx[1])/1000:+.1f}m)×{by[0]}轴({(y-by[1])/1000:+.1f}m)"

# cap polygons + labels
ctpos = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "承台集中标注" and e.dxf.text.startswith("CT"):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and S3[0] <= y <= S3[1]:
            ctpos.append((x, y, e.dxf.text))
caps = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and S3[0] <= cy <= S3[1]:
            caps.append(Polygon(pts))
print("caps:", len(caps), "labels:", len(ctpos))

# piles in S3
piles = []
for e in msp.query("INSERT"):
    if e.dxf.name != "sdfsdfsdfsfdsf": continue
    ext = bbox.extents([e], fast=True)
    if not ext.has_data: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if X0 <= cx <= X1 and S3[0] <= cy <= S3[1]:
        piles.append(Point(cx, cy))
print("piles in S3:", len(piles))

# assign labels to caps; find unlabeled
assigned = collections.Counter()
unl = []
for cp in caps:
    c = cp.centroid
    best, bd = None, 1e18
    for tx, ty, name in ctpos:
        d = (tx-c.x)**2 + (ty-c.y)**2
        if d < bd: bd, best = d, name
    np_in = sum(1 for p in piles if cp.buffer(100).contains(p))
    if math.sqrt(bd) > 4000:
        unl.append((c.x, c.y, cp.area/1e6, cp.length/1000, np_in, math.sqrt(bd), best))
    else:
        assigned[(best, np_in)] += 1
print("\nassigned (type, piles_inside): count")
tot = 0
for k in sorted(assigned, key=str):
    print(f"  {k}: {assigned[k]}")
    tot += assigned[k]*k[1]
print("piles in labeled caps:", tot)
print("\nunlabeled caps:")
for x, y, a, p, np_in, d, near in unl:
    bx = min(AXX.items(), key=lambda kv: abs(kv[1]-x))
    by = min(AXY.items(), key=lambda kv: abs(kv[1]-y))
    print(f"  c=({x:.0f},{y:.0f}) {bx[0]}轴{(x-bx[1])/1000:+.1f}m × {by[0]}轴{(y-by[1])/1000:+.1f}m area={a:.2f}m2 perim={p:.2f}m piles={np_in} nearest={near}@{d:.0f}mm")
piles_in_caps = tot + sum(u[4] for u in unl)
print(f"\npiles inside any cap: {piles_in_caps}, loose piles: {len(piles)-piles_in_caps}")
# loose piles positions
incap = []
for p in piles:
    if not any(cp.buffer(100).contains(p) for cp in caps):
        bx = min(AXX.items(), key=lambda kv: abs(kv[1]-p.x))
        by = min(AXY.items(), key=lambda kv: abs(kv[1]-p.y))
        print(f"  loose pile ({p.x:.0f},{p.y:.0f}) {bx[0]}轴{(p.x-bx[1])/1000:+.1f}m × {by[0]}轴{(p.y-by[1])/1000:+.1f}m")
