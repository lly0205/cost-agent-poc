# -*- coding: utf-8 -*-
import ezdxf, sys
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S1": (36225, 120325), "S2": (-55172, 28928), "S3": (-139272, -55172),
         "S5": (-307472, -223372), "S6": (-391572, -307472), "S7": (-475672, -391572)}
import collections
bb = {}
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙":
        x, y = e.dxf.start.x, e.dxf.start.y
        if X0 <= x <= X1:
            for n, (y0, y1) in BANDS.items():
                if y0 <= y <= y1:
                    b = bb.setdefault(n, [1e18, 1e18, -1e18, -1e18])
                    for px, py in ((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)):
                        b[0] = min(b[0], px); b[1] = min(b[1], py)
                        b[2] = max(b[2], px); b[3] = max(b[3], py)
for n in sorted(bb):
    b = bb[n]
    print(f"{n}: x {b[0]:.0f}..{b[2]:.0f}  y {b[1]:.0f}..{b[3]:.0f}  (w={b[2]-b[0]:.0f}, h={b[3]-b[1]:.0f})")
