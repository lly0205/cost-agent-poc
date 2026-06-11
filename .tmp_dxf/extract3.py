# -*- coding: utf-8 -*-
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

# 1. layer "4" entities in all bands
print("=== layer '4' entities by band ===")
cnt = collections.Counter()
big = []
for e in msp:
    if e.dxf.layer != "4": continue
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
    except Exception: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if not (X0 <= cx <= X1): continue
    b = band(cy)
    cnt[(b, e.dxftype())] += 1
    w = ext.extmax.x-ext.extmin.x; h = ext.extmax.y-ext.extmin.y
    if max(w, h) > 2000 and e.dxftype() in ("LWPOLYLINE", "LINE", "HATCH"):
        big.append((b, e.dxftype(), cx, cy, w, h))
print(dict(cnt))
for r in sorted(big):
    print(f"  {r[0]} {r[1]} c=({r[2]:.0f},{r[3]:.0f}) size={r[4]:.0f}x{r[5]:.0f}")

# 2. all DWQ/SCQ labels in S5
print("\n=== DWQ/SCQ labels in S5 ===")
import re
for e in msp.query("TEXT"):
    t = e.dxf.text.strip()
    if re.match(r"^(DWQ|SCQ)", t):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S5":
            print(f"  {t}: ({x:.0f},{y:.0f}) layer={e.dxf.layer}")

# 3. DIMENSION values in S4 (detail dims)
print("\n=== S4 DIMENSIONs (measurement) ===")
dims = []
for e in msp.query("DIMENSION"):
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
    except Exception: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if not (X0 <= cx <= X1 and band(cy) == "S4"): continue
    try:
        m = e.get_measurement()
    except Exception:
        m = None
    txt = e.dxf.text
    dims.append((cx, cy, m, txt))
for cx, cy, m, txt in sorted(dims, key=lambda d: (-d[1], d[0])):
    if isinstance(m, (int, float)):
        print(f"  ({cx:.0f},{cy:.0f}) meas={m:.0f} text='{txt}'")
    else:
        print(f"  ({cx:.0f},{cy:.0f}) meas={m} text='{txt}'")
