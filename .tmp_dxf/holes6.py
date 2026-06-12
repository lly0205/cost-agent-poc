# -*- coding: utf-8 -*-
# final hole quantification: hull area per IN-enclosure cluster + axis refs
import ezdxf, sys, pickle
from shapely.geometry import LineString, Polygon, Point, MultiPoint
from shapely.ops import unary_union
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423), "S7": (-4711816, -404432)}
def tr(g, s, d): return translate(g, xoff=ANCH[d][0]-ANCH[s][0], yoff=ANCH[d][1]-ANCH[s][1])
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc7 = tr(enc5, "S5", "S7")

# axes from S5 (walls1 results) shifted to S7
NUX5 = {'1': -4828140, '2': -4819740, '3': -4811340, '4': -4802940, '5': -4794540, '6': -4786140,
        '7': -4777740, '8': -4769340, '9': -4760940, '10': -4752540, '11': -4744140, '12': -4735740,
        '13': -4727340, '14': -4718940}
LUY5 = {'A': -282123, 'B': -272523, 'C': -262923, 'D': -250923, 'E': -241323, 'F': -231723}
dx = ANCH["S7"][0]-ANCH["S5"][0]; dy = ANCH["S7"][1]-ANCH["S5"][1]
NUX = {k: v+dx for k, v in NUX5.items()}
LUY = {k: v+dy for k, v in LUY5.items()}
def axx(x):
    k, v = min(NUX.items(), key=lambda kv: abs(kv[1]-x))
    o = (x-v)/1000
    return k if abs(o) < 0.35 else f"{k}{o:+.1f}"
def axy(y):
    k, v = min(LUY.items(), key=lambda kv: abs(kv[1]-y))
    o = (y-v)/1000
    return k if abs(o) < 0.35 else f"{k}{o:+.1f}"

segs = []
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    if X0 <= x1 <= X1 and SY0 <= y1 <= SY1:
        segs.append(LineString([(x1, y1), (x2, y2)]))
u = unary_union([s.buffer(30) for s in segs])
gs = list(u.geoms) if u.geom_type == "MultiPolygon" else [u]
tot_perm = tot_temp = 0.0
peri_perm = peri_temp = 0.0
print("holes INSIDE basement enclosure:")
rows = []
for g in gs:
    b = g.bounds
    cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2
    if not enc7.buffer(500).contains(Point(cx, cy)): continue
    pts = []
    for s in segs:
        if g.contains(s.centroid):
            pts += list(s.coords)
    hull = MultiPoint(pts).convex_hull
    A = hull.area/1e6
    P = hull.length/1000
    w, h = (b[2]-b[0])/1000, (b[3]-b[1])/1000
    rows.append((-A, cx, cy, w, h, A, P, b))
rows.sort()
for _, cx, cy, w, h, A, P, bb in rows:
    cls = "PERM(楼梯/坡道等)" if A > 5 else ("TEMP(注4设备井)" if A > 0.3 else "small(<=0.3 不扣)")
    if A > 5: tot_perm += A; peri_perm += P
    elif A > 0.3: tot_temp += A; peri_temp += P
    print(f"  {w:.2f}x{h:.2f}m hull={A:.2f}m2 peri={P:.2f}m at X:{axx(bb[0])}~{axx(bb[2])} Y:{axy(bb[1])}~{axy(bb[3])}  {cls}")
print(f"\nPERM total {tot_perm:.2f} m2, peri {peri_perm:.1f} m")
print(f"TEMP total {tot_temp:.2f} m2, peri {peri_temp:.1f} m")
print(f"deduct ALL>0.3: {tot_perm+tot_temp:.2f} m2 -> slab vol deduct = {(tot_perm+tot_temp)*0.18:.2f} m3")
