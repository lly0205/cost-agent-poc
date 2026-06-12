# -*- coding: utf-8 -*-
# Task5: rebuild wall segments in S5 with thickness, type label, axis positions
import ezdxf, sys, collections, math, re, pickle
from shapely.geometry import LineString, Point
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S5 = (-307472, -223372)

# wall lines
Hl, Vl = [], []
for e in msp.query("LINE"):
    if e.dxf.layer != "砼墙": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    if not (X0 <= x1 <= X1 and S5[0] <= y1 <= S5[1]): continue
    if abs(y1-y2) < 1: Hl.append((y1, min(x1,x2), max(x1,x2)))
    elif abs(x1-x2) < 1: Vl.append((x1, min(y1,y2), max(y1,y2)))
print("H lines:", len(Hl), "V lines:", len(Vl))

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
Hm = merge_colinear(Hl); Vm = merge_colinear(Vl)

def pair(items):
    items = sorted(items)
    used = set(); pairs = []
    for i in range(len(items)):
        ci,a0,a1 = items[i]
        for j in range(i+1, len(items)):
            cj,b0,b1 = items[j]
            w = cj-ci
            if w > 650: break
            if w < 180: continue
            ov0, ov1 = max(a0,b0), min(a1,b1)
            if ov1-ov0 > 1000:
                pairs.append(((ci+cj)/2, w, ov0, ov1))
    return pairs
hp = pair(Hm); vp = pair(Vm)

# type labels (0-layer DWQ/SCQ texts in S5)
labels = []
for e in msp.query("TEXT"):
    t = e.dxf.text.strip()
    if re.fullmatch(r"(DWQ|SCQ)\d", t):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and S5[0] <= y <= S5[1]:
            labels.append((x, y, t))
print("type labels:", len(labels))

# axis grid in S5: TEXT + INSERT attribs
axes = []
for e in msp.query("TEXT"):
    t = e.dxf.text.strip()
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if X0 <= x <= X1 and S5[0] <= y <= S5[1] and re.fullmatch(r"\d{1,2}|[A-Z]", t):
        axes.append((t, x, y, e.dxf.layer))
for e in msp.query("INSERT"):
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if not (X0-3000 <= x <= X1+3000 and S5[0] <= y <= S5[1]): continue
    for a in e.attribs:
        t = a.dxf.text.strip()
        if re.fullmatch(r"\d{1,2}|[A-Z]", t):
            axes.append((t, x, y, "ATTR:"+e.dxf.name))
print("axis label candidates:", len(axes))
nums = sorted([a for a in axes if a[0].isdigit()], key=lambda a: a[1])
lets = sorted([a for a in axes if a[0].isalpha()], key=lambda a: a[2])
# cluster duplicates (top/bottom bubbles)
def uniq(arr, key):
    seen = {}
    for a in arr:
        k = a[0]
        if k not in seen: seen[k] = a
    return seen
NU = {}
for t, x, y, l in nums: NU.setdefault(t, []).append(x)
LU = {}
for t, x, y, l in lets: LU.setdefault(t, []).append(y)
NUX = {k: sum(v)/len(v) for k, v in NU.items()}
LUY = {k: sum(v)/len(v) for k, v in LU.items()}
print("num axes:", {k: round(v) for k, v in sorted(NUX.items(), key=lambda kv: kv[1])})
print("let axes:", {k: round(v) for k, v in sorted(LUY.items(), key=lambda kv: kv[1])})
def ax_of_x(x):
    best = min(NUX.items(), key=lambda kv: abs(kv[1]-x))
    return f"{best[0]}{'' if abs(best[1]-x)<300 else f'{(x-best[1])/1000:+.1f}m'}"
def ax_of_y(y):
    best = min(LUY.items(), key=lambda kv: abs(kv[1]-y))
    return f"{best[0]}{'' if abs(best[1]-y)<300 else f'{(y-best[1])/1000:+.1f}m'}"

print("\n=== H wall segments (run E-W) ===")
for c, w, a0, a1 in sorted(hp, key=lambda p: p[0]):
    if a1-a0 < 1500: continue
    lab, bd = None, 1e18
    mx, my = (a0+a1)/2, c
    for lx, ly, t in labels:
        d = (lx-mx)**2 + (ly-my)**2
        if d < bd: bd, lab = d, t
    print(f"y={c:.0f} ({ax_of_y(c)})  x {a0:.0f}..{a1:.0f} ({ax_of_x(a0)}~{ax_of_x(a1)})  L={(a1-a0)/1000:.2f}m t={w:.0f}  type={lab} (label_d={math.sqrt(bd)/1000:.1f}m)")
print("\n=== V wall segments (run N-S) ===")
for c, w, a0, a1 in sorted(vp, key=lambda p: p[0]):
    if a1-a0 < 1500: continue
    lab, bd = None, 1e18
    mx, my = c, (a0+a1)/2
    for lx, ly, t in labels:
        d = (lx-mx)**2 + (ly-my)**2
        if d < bd: bd, lab = d, t
    print(f"x={c:.0f} ({ax_of_x(c)})  y {a0:.0f}..{a1:.0f} ({ax_of_y(a0)}~{ax_of_y(a1)})  L={(a1-a0)/1000:.2f}m t={w:.0f}  type={lab} (label_d={math.sqrt(bd)/1000:.1f}m)")
