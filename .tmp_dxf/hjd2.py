# -*- coding: utf-8 -*-
# find 膨胀加强带 texts in plan sheets and its geometry layer
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
BANDS = {"S1": (36225, 120325), "S2": (-55172, 28928), "S3": (-139272, -55172),
         "S4": (-223372, -139272), "S5": (-307472, -223372),
         "S6": (-391572, -307472), "S7": (-475672, -391572)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1: return n
    return None
X0, X1 = -4840000, -4691000
hits = []
for e in msp.query("TEXT MTEXT"):
    t = e.dxf.text if e.dxftype()=="TEXT" else e.text
    if ("膨胀" in t or "加强带" in t):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        inplan = "PLAN" if X0 <= x <= X1 else "NOTE"
        hits.append((inplan, band(y), x, y, e.dxf.layer, round(getattr(e.dxf,'rotation',0)), t.strip()[:90]))
for h in sorted(hits):
    print("\t".join(str(v) for v in h))
