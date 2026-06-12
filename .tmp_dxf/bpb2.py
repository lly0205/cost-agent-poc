# -*- coding: utf-8 -*-
# find BPB1 boundary: entities near label; elevation texts in S3
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S3 = (-139272, -55172)

# elevation-like texts in S3 plan
print("=== elevation texts in S3 plan ===")
for e in msp.query("TEXT MTEXT"):
    t = (e.dxf.text if e.dxftype()=="TEXT" else e.text).strip()
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if X0 <= x <= X1 and S3[0] <= y <= S3[1]:
        if any(k in t for k in ("标高", "-4.8", "-5.2", "-6.5", "-5.4", "-7.1", "泵", "BPB", "板顶")):
            print(f"  ({x:.0f},{y:.0f}) [{e.dxf.layer}] {t[:90]}")

# entity layers near BPB1 label
print("\n=== entities within 8m of BPB1 label ===")
LX, LY, R = -4806788, -102435, 8000
cnt = collections.Counter()
for e in msp.query("LINE LWPOLYLINE ARC CIRCLE"):
    try:
        if e.dxftype() == "LINE":
            x, y = e.dxf.start.x, e.dxf.start.y
        elif e.dxftype() == "LWPOLYLINE":
            p = e.get_points("xy")[0]; x, y = p[0], p[1]
        else:
            x, y = e.dxf.center.x, e.dxf.center.y
    except Exception: continue
    if abs(x-LX) < R and abs(y-LY) < R:
        cnt[(e.dxftype(), e.dxf.layer)] += 1
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print("  ", k, v)
