# -*- coding: utf-8 -*-
# inspect NUM-layer inserts & 板洞边线 clusters in S7 (in & out of enclosure)
import ezdxf, sys, collections, pickle
from ezdxf import bbox
from shapely.geometry import LineString, Point, MultiPoint
from shapely.ops import unary_union
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572
ANCH = {"S5": (-4718640, -231423), "S7": (-4711816, -404432)}
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc7 = translate(enc5, xoff=ANCH["S7"][0]-ANCH["S5"][0], yoff=ANCH["S7"][1]-ANCH["S5"][1])

# axes (S7)
NUX5 = {'1': -4828140, '2': -4819740, '3': -4811340, '4': -4802940, '5': -4794540, '6': -4786140,
        '7': -4777740, '8': -4769340, '9': -4760940, '10': -4752540, '11': -4744140, '12': -4735740,
        '13': -4727340, '14': -4718940}
LUY5 = {'A': -282123, 'B': -272523, 'C': -262923, 'D': -250923, 'E': -241323, 'F': -231723}
dx = ANCH["S7"][0]-ANCH["S5"][0]; dy = ANCH["S7"][1]-ANCH["S5"][1]
NUX = {k: v+dx for k, v in NUX5.items()}
LUY = {k: v+dy for k, v in LUY5.items()}
def axx(x):
    k, v = min(NUX.items(), key=lambda kv: abs(kv[1]-x)); o = (x-v)/1000
    return k if abs(o) < 0.35 else f"{k}{o:+.1f}"
def axy(y):
    k, v = min(LUY.items(), key=lambda kv: abs(kv[1]-y)); o = (y-v)/1000
    return k if abs(o) < 0.35 else f"{k}{o:+.1f}"

print("=== NUM-layer INSERTs in S7 ===")
num_pts = []
names = collections.Counter()
for e in msp.query("INSERT"):
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if not (X0 <= x <= X1 and SY0 <= y <= SY1): continue
    if e.dxf.layer != "NUM": continue
    ext = bbox.extents([e], fast=True)
    cx, cy = ((ext.extmin.x+ext.extmax.x)/2, (ext.extmin.y+ext.extmax.y)/2) if ext.has_data else (x, y)
    w = (ext.extmax.x-ext.extmin.x) if ext.has_data else 0
    h = (ext.extmax.y-ext.extmin.y) if ext.has_data else 0
    ins = enc7.buffer(500).contains(Point(cx, cy))
    names[e.dxf.name] += 1
    num_pts.append((cx, cy, e.dxf.name))
    # attribs
    att = []
    if e.attribs:
        att = [f"{a.dxf.tag}={a.dxf.text}" for a in e.attribs]
    print(f"  {'IN ' if ins else 'OUT'} blk={e.dxf.name} bbox_c=({cx:.0f},{cy:.0f}) {w:.0f}x{h:.0f} at X:{axx(cx)} Y:{axy(cy)} {att}")
print("block name counts:", dict(names))

# block definition contents
for nm in names:
    blk = doc.blocks.get(nm)
    print(f"\n=== block '{nm}' definition ===")
    tc = collections.Counter()
    for be in blk:
        tc[(be.dxf.dxftype, be.dxf.layer)] += 1
        if be.dxf.dxftype in ("TEXT", "MTEXT", "ATTDEF"):
            try: print("   text:", be.dxf.text)
            except Exception: pass
    print("   ", dict(tc))

# NUM-layer LINEs (leaders?)
print("\n=== NUM-layer LINEs in S7 (count, sample endpoints) ===")
nl = []
for e in msp.query("LINE"):
    if e.dxf.layer != "NUM": continue
    x1, y1 = e.dxf.start.x, e.dxf.start.y
    if X0 <= x1 <= X1 and SY0 <= y1 <= SY1:
        nl.append((x1, y1, e.dxf.end.x, e.dxf.end.y))
print("count:", len(nl))
for s in nl[:8]: print("  ", [f"{v:.0f}" for v in s])

# 板洞边线 clusters OUT of enclosure (excluding legend/无板区?)
print("\n=== 板洞边线 clusters (ALL in S7, in/out flag) ===")
segs = []
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    if X0 <= min(x1,x2) and max(x1,x2) <= X1 and SY0 <= min(y1,y2) and max(y1,y2) <= SY1:
        segs.append(LineString([(x1, y1), (x2, y2)]))
u = unary_union([s.buffer(30) for s in segs])
gs = list(u.geoms) if u.geom_type == "MultiPolygon" else [u]
for g in sorted(gs, key=lambda g: -g.area):
    b = g.bounds
    cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2
    ins = enc7.buffer(500).contains(Point(cx, cy))
    n = sum(1 for s in segs if g.contains(s.centroid))
    pts = [c for s in segs if g.contains(s.centroid) for c in s.coords]
    A = MultiPoint(pts).convex_hull.area/1e6 if pts else 0
    # nearest NUM insert
    nd, nn = 1e18, None
    for px, py, pn in num_pts:
        d = (px-cx)**2+(py-cy)**2
        if d < nd: nd, nn = d, pn
    print(f"  {'IN ' if ins else 'OUT'} {(b[2]-b[0])/1000:.2f}x{(b[3]-b[1])/1000:.2f}m A={A:.2f} nlines={n} at X:{axx(cx)} Y:{axy(cy)} nearestNUM={nn}@{nd**0.5/1000:.1f}m")
