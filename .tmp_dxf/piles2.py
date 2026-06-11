# -*- coding: utf-8 -*-
import ezdxf, sys, collections
from ezdxf import bbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -55172, 28928  # S2 band

inv = collections.Counter()
samples = {}
for e in msp:
    t = e.dxftype()
    if t in ("LINE","LWPOLYLINE","TEXT","MTEXT","INSERT","CIRCLE","ARC","HATCH"):
        continue  # already inventoried
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
        cx = (ext.extmin.x + ext.extmax.x)/2
        cy = (ext.extmin.y + ext.extmax.y)/2
    except Exception:
        continue
    if X0 <= cx <= X1 and SY0 <= cy <= SY1:
        key = (t, e.dxf.layer)
        inv[key] += 1
        if key not in samples:
            samples[key] = (cx, cy, ext.extmax.x-ext.extmin.x, ext.extmax.y-ext.extmin.y)

print("=== S2 other entity types ===")
for k, v in sorted(inv.items(), key=lambda kv: -kv[1]):
    s = samples[k]
    print(f"  {k}: {v}  sample c=({s[0]:.0f},{s[1]:.0f}) size={s[2]:.0f}x{s[3]:.0f}")

# also: COLU polygons in S2 - check size distribution (are they 500x500 piles?)
sizes = collections.Counter()
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "COLU":
        pts = e.get_points("xy")
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
        if X0 <= cx <= X1 and SY0 <= cy <= SY1:
            sizes[(round(max(xs)-min(xs),-1), round(max(ys)-min(ys),-1))] += 1
print("\n=== S2 COLU polygon bbox sizes ===")
for k, v in sorted(sizes.items(), key=lambda kv: -kv[1]):
    print(f"  {k}: {v}")
