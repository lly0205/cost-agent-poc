# -*- coding: utf-8 -*-
# list HATCH strips (expansion bands) in S3, S5, S7 plan areas
import ezdxf, sys
from ezdxf import bbox as ebbox
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
for e in msp.query("HATCH"):
    try:
        ext = ebbox.extents([e], fast=True)
    except Exception:
        continue
    if not ext.has_data: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if not (X0 <= cx <= X1): continue
    bn = band(cy)
    if bn not in ("S3", "S5", "S6", "S7"): continue
    w = (ext.extmax.x-ext.extmin.x)/1000; h = (ext.extmax.y-ext.extmin.y)/1000
    # strips: long & thin OR any sizable hatch — print all with area filters
    if max(w, h) < 3: continue
    print(f"{bn}\tlayer={e.dxf.layer}\tpat={e.dxf.pattern_name}\tc=({cx:.0f},{cy:.0f})\t{w:.2f}x{h:.2f}m\tpaths={len(e.paths)}")
