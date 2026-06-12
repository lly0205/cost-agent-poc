# -*- coding: utf-8 -*-
# Task1: rigorous pile count on S2 (pile layout plan)
import ezdxf, sys, collections
from ezdxf import bbox
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
        if y0 <= y <= y1: return n
    return None

# 1) all pile-symbol INSERTs in S2 with positions
piles = []
for e in msp.query("INSERT"):
    if e.dxf.name != "sdfsdfsdfsfdsf": continue
    ext = bbox.extents([e], fast=True)
    if not ext.has_data: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if X0 <= cx <= X1 and band(cy) == "S2":
        piles.append((cx, cy))
print("raw pile INSERTs in S2:", len(piles))

# 2) dedupe within 100mm
piles.sort()
ded = []
for p in piles:
    if any(abs(p[0]-q[0]) < 100 and abs(p[1]-q[1]) < 100 for q in ded):
        continue
    ded.append(p)
print("after dedupe:", len(ded))

# 3) extent of pile cloud — find outliers (legend symbols sit far from building)
xs = sorted(p[0] for p in ded); ys = sorted(p[1] for p in ded)
print(f"x range {xs[0]:.0f}..{xs[-1]:.0f}, y range {ys[0]:.0f}..{ys[-1]:.0f}")
# median bounding: use 5th..95th percentile core then flag points >15m outside
import statistics
def pct(v, q): return v[int(q*(len(v)-1))]
cx0, cx1 = pct(xs, 0.05), pct(xs, 0.95)
cy0, cy1 = pct(ys, 0.05), pct(ys, 0.95)
out = [p for p in ded if p[0] < cx0-20000 or p[0] > cx1+20000 or p[1] < cy0-20000 or p[1] > cy1+20000]
print("possible legend/outlier piles:", len(out))
for p in out: print("   outlier at", round(p[0]), round(p[1]))

# 4) also check: any pile drawn directly on layer 桩 (not via INSERT) in S2
direct = collections.Counter()
dpos = []
for e in msp.query("LWPOLYLINE CIRCLE LINE"):
    if e.dxf.layer != "桩": continue
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
        cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    except Exception:
        continue
    if X0 <= cx <= X1 and band(cy) == "S2":
        direct[e.dxftype()] += 1
        if e.dxftype() == "LWPOLYLINE": dpos.append((cx, cy))
print("direct entities on layer 桩 in S2:", dict(direct))
# are direct polylines coincident with INSERT piles?
extra = [p for p in dpos if not any(abs(p[0]-q[0]) < 300 and abs(p[1]-q[1]) < 300 for q in ded)]
print("direct 桩-layer polylines NOT coincident with INSERT piles:", len(extra))
for p in extra[:20]: print("   extra at", round(p[0]), round(p[1]))

# 5) total-count notes in S2 text
for e in msp.query("TEXT MTEXT"):
    x = e.dxf.insert.x if e.dxftype()=="TEXT" else e.dxf.insert.x
    y = e.dxf.insert.y
    if not (X0 <= x <= X1 and band(y) == "S2"): continue
    t = e.dxf.text if e.dxftype()=="TEXT" else e.text
    if any(k in t for k in ("根", "共", "桩数", "总数")):
        print("NOTE:", t.strip()[:120])
