# -*- coding: utf-8 -*-
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

SHEETS = [
    ("S1", 36225, 120325), ("S2", -55172, 28928), ("S3", -139272, -55172),
    ("S4", -223372, -139272), ("S5", -307472, -223372),
    ("S6", -391572, -307472), ("S7", -475672, -391572),
]
X0, X1 = -4840000, -4691000

def ref(e):
    t = e.dxftype()
    try:
        if t in ("TEXT", "MTEXT", "INSERT"):
            return e.dxf.insert
        if t == "CIRCLE":
            return e.dxf.center
        if t == "LINE":
            return e.dxf.start
        if t == "LWPOLYLINE":
            p = e.get_points()[0]
            class P: x, y = p[0], p[1]
            return P
        if t == "DIMENSION":
            return e.dxf.defpoint
        if t in ("ARC",):
            return e.dxf.center
        if t == "HATCH":
            return None
    except Exception:
        return None
    return None

cnt = collections.Counter()
for e in msp:
    p = ref(e)
    if p is None or not (X0 <= p.x <= X1):
        continue
    for n, y0, y1 in SHEETS:
        if y0 <= p.y <= y1:
            cnt[(n, e.dxf.layer, e.dxftype())] += 1
            break

cur = None
for (s, layer, t), v in sorted(cnt.items()):
    if s != cur:
        print(f"\n===== {s} =====")
        cur = s
    print(f"{layer} / {t}: {v}")
