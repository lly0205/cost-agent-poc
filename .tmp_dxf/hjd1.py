# -*- coding: utf-8 -*-
# Task3: find 后浇带 texts and candidate layers across all sheets
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S1": (36225, 120325), "S2": (-55172, 28928), "S3": (-139272, -55172),
         "S4": (-223372, -139272), "S5": (-307472, -223372),
         "S6": (-391572, -307472), "S7": (-475672, -391572), "GEN": (120325, 400000)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1: return n
    return None

# texts containing 后浇
for e in msp.query("TEXT MTEXT"):
    t = e.dxf.text if e.dxftype()=="TEXT" else e.text
    if "后浇" in t:
        x, y = e.dxf.insert.x, e.dxf.insert.y
        print(f"{band(y)}\t({x:.0f},{y:.0f})\tlayer={e.dxf.layer}\trot={getattr(e.dxf,'rotation',0):.0f}\t{t.strip()[:100]}")

# layers with 后浇/HJD in name
print("\nlayers:")
for l in doc.layers:
    if "后浇" in l.dxf.name or "HJD" in l.dxf.name.upper() or "JC" in l.dxf.name.upper():
        print(" ", l.dxf.name)
