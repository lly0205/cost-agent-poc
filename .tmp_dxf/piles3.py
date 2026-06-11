# -*- coding: utf-8 -*-
import ezdxf, sys, collections
from ezdxf import bbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -55172, 28928

# pick first cap polyline in S2
cap = None
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = e.get_points("xy")
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and SY0 <= cy <= SY1:
            cap = (cx, cy)
            break
print("cap centroid:", cap)
cx, cy = cap
W = 2500
found = collections.Counter()
det = []
for e in msp:
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
    except Exception:
        continue
    if ext.extmax.x < cx-W or ext.extmin.x > cx+W: continue
    if ext.extmax.y < cy-W or ext.extmin.y > cy+W: continue
    t = e.dxftype()
    found[(t, e.dxf.layer)] += 1
    sz = (ext.extmax.x-ext.extmin.x, ext.extmax.y-ext.extmin.y)
    extra = ""
    if t == "INSERT": extra = e.dxf.name
    if t in ("TEXT",): extra = e.dxf.text
    det.append((t, e.dxf.layer, f"{sz[0]:.0f}x{sz[1]:.0f}", extra))

print("\n=== entities near cap ===")
for d in det:
    print(" ", d)
