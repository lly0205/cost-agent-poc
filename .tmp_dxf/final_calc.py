# -*- coding: utf-8 -*-
# FINAL assembly: walls by zone, raft sub-areas, band volumes, totals
import ezdxf, sys, collections, math, re, pickle
from shapely.geometry import LineString, Point, Polygon, box
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S5B = (-307472, -223372); S3B = (-139272, -55172)
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423)}
def tr(g, s, d): return translate(g, xoff=ANCH[d][0]-ANCH[s][0], yoff=ANCH[d][1]-ANCH[s][1])
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc3 = tr(enc5, "S5", "S3")

deep3 = None
for e in msp.query("HATCH"):
    if e.dxf.layer != "看线": continue
    for p in e.paths:
        if hasattr(p, "vertices") and len(p.vertices) >= 3:
            pts = [(v[0], v[1]) for v in p.vertices]
            poly = Polygon(pts)
            c = poly.centroid
            if X0 <= c.x <= X1 and S3B[0] <= c.y <= S3B[1] and poly.area/1e6 > 1000:
                deep3 = poly
deep5 = tr(deep3, "S3", "S5")
deep_in = deep3.intersection(enc3)
print(f"enc area={enc3.area/1e6:.1f} deep_hatch={deep3.area/1e6:.1f} deep∩enc={deep_in.area/1e6:.1f} shallow={(enc3.area-deep_in.area)/1e6:.1f}")
# 水池(-5.2)区: bounded by axis1 wall inner, D row, F row, x=-4813890 (S5 coords)
tank5 = box(-4828140, -250923, -4814040, -231723)  # rough inner box
tank_in = tank5.intersection(enc5)
print(f"水池(-5.200)区 approx area={tank_in.area/1e6:.1f} m2")

# ---------------- WALLS ----------------
Hl, Vl = [], []
for e in msp.query("LINE"):
    if e.dxf.layer != "砼墙": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    if not (X0 <= x1 <= X1 and S5B[0] <= y1 <= S5B[1]): continue
    if abs(y1-y2) < 1: Hl.append((y1, min(x1,x2), max(x1,x2)))
    elif abs(x1-x2) < 1: Vl.append((x1, min(y1,y2), max(y1,y2)))
def merge_colinear(items):
    d = collections.defaultdict(list)
    for c, a0, a1 in items: d[round(c,0)].append((a0,a1))
    out = []
    for c, segs in d.items():
        segs.sort(); m=[]
        for a0,a1 in segs:
            if m and a0 <= m[-1][1]+150: m[-1][1]=max(m[-1][1],a1)
            else: m.append([a0,a1])
        for a0,a1 in m: out.append((c,a0,a1))
    return out
def pair(items):
    items = sorted(items); pairs = []
    for i in range(len(items)):
        ci,a0,a1 = items[i]
        for j in range(i+1, len(items)):
            cj,b0,b1 = items[j]
            w = cj-ci
            if w > 650: break
            if w < 180: continue
            ov0, ov1 = max(a0,b0), min(a1,b1)
            if ov1-ov0 > 1000: pairs.append(((ci+cj)/2, w, ov0, ov1))
    return pairs
hp = pair(merge_colinear(Hl)); vp = pair(merge_colinear(Vl))
labels = []
for e in msp.query("TEXT"):
    t = e.dxf.text.strip()
    if re.fullmatch(r"(DWQ|SCQ)\d", t):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and S5B[0] <= y <= S5B[1]: labels.append((x, y, t))
NUX = {'1': -4828140, '2': -4819740, '3': -4811340, '4': -4802940, '5': -4794540, '6': -4786140,
       '7': -4777740, '8': -4769340, '9': -4760940, '10': -4752540, '11': -4744140, '12': -4735740,
       '13': -4727340, '14': -4718940}
LUY = {'A': -282123, 'B': -272523, 'C': -262923, 'D': -250923, 'E': -241323, 'F': -231723}
def axx(x):
    k, v = min(NUX.items(), key=lambda kv: abs(kv[1]-x)); o=(x-v)/1000
    return k if abs(o)<0.35 else f"{k}{o:+.1f}"
def axy(y):
    k, v = min(LUY.items(), key=lambda kv: abs(kv[1]-y)); o=(y-v)/1000
    return k if abs(o)<0.35 else f"{k}{o:+.1f}"

segs = []
for (c, w, a0, a1) in hp:
    if a1-a0 < 1200: continue
    segs.append(("H", c, w, a0, a1))
for (c, w, a0, a1) in vp:
    if a1-a0 < 1200: continue
    segs.append(("V", c, w, a0, a1))
groups = collections.defaultdict(lambda: [0.0, 0.0, 0.0, []])  # key=(类别,t,H): L, vol, fw
det = []
for o, c, w, a0, a1 in segs:
    mid = Point(((a0+a1)/2, c) if o=="H" else (c, (a0+a1)/2))
    lab, bd = None, 1e18
    for lx, ly, t in labels:
        d = (lx-mid.x)**2+(ly-mid.y)**2
        if d < bd: bd, lab = d, t
    is_deep = deep5.buffer(800).intersects(mid.buffer(10))
    L = (a1-a0)/1000; t = w/1000
    if lab.startswith("SCQ"):
        cat = "SCQ1水池墙"; H = 4.70
    elif is_deep:
        cat = "挡土墙-深区"; H = 6.40
    else:
        cat = "挡土墙-浅区"; H = 4.70
    g = groups[(cat, round(t,2), H)]
    g[0] += L; g[1] += L*t*H; g[2] += 2*L*H
    if o == "H":
        pos = f"{axy(c)}轴 {axx(a0)}~{axx(a1)}"
    else:
        pos = f"{axx(c)}轴 {axy(a0)}~{axy(a1)}"
    g[3].append(f"{pos} L={L:.2f}")
    det.append((cat, pos, L, t, H, lab, math.sqrt(bd)/1000))
print("\n=== wall segments detail ===")
for cat, pos, L, t, H, lab, ld in sorted(det):
    print(f"  {cat}\t{pos}\tL={L:.2f}\tt={t:.2f}\tH={H}\t标签{lab}({ld:.1f}m)")
print("\n=== wall groups ===")
TV = TF = 0
for (cat, t, H), (L, V, F, lst) in sorted(groups.items()):
    print(f"{cat} t={t} H={H}: L={L:.2f}m vol={V:.1f}m3 fw双面={F:.1f}m2  ({len(lst)}段)")
    TV += V; TF += F
print(f"WALL TOTksię vol={TV:.1f} fw={TF:.1f}")

# ---- band crossings with walls (外墙加强带) ----
# V bands at S3 x=-4782595,-4741595 -> S5 -4789340,-4748340; H band S3 y=-92587 -> S5 -256923
print("\n=== expansion band wall crossings ===")
crossings = []
for o, c, w, a0, a1 in segs:
    t = w/1000
    for bx in (-4789340, -4748340):
        if o == "H" and a0-100 <= bx <= a1+100:
            mid = Point(bx, c)
            H = 6.40 if deep5.buffer(800).intersects(mid.buffer(10)) else 4.70
            crossings.append((f"H墙 y={axy(c)} @x={axx(bx)}", t, H))
    by = -256923
    if o == "V" and a0-100 <= by <= a1+100:
        mid = Point(c, by)
        H = 6.40 if deep5.buffer(800).intersects(mid.buffer(10)) else 4.70
        crossings.append((f"V墙 x={axx(c)} @y={axy(by)}", t, H))
vb = 0
for nm, t, H in crossings:
    v = 2.0*t*H
    vb += v
    print(f"  {nm} t={t} H={H} vol={v:.2f}")
print(f"外墙加强带合计 {vb:.2f} m3")
