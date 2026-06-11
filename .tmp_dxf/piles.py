# -*- coding: utf-8 -*-
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -55172, 28928  # S2 band

inv = collections.Counter()
ins = collections.Counter()
for e in msp:
    t = e.dxftype()
    try:
        if t == "INSERT":
            x, y = e.dxf.insert.x, e.dxf.insert.y
        elif t in ("LINE",):
            x, y = e.dxf.start.x, e.dxf.start.y
        elif t in ("CIRCLE", "ARC"):
            x, y = e.dxf.center.x, e.dxf.center.y
        elif t == "LWPOLYLINE":
            p = e.get_points("xy")[0]; x, y = p[0], p[1]
        elif t in ("TEXT", "MTEXT"):
            x, y = e.dxf.insert.x, e.dxf.insert.y
        elif t == "HATCH":
            # use first path vertex
            v = None
            for p in e.paths:
                if hasattr(p, "vertices") and len(p.vertices):
                    v = p.vertices[0]; break
            if v is None: continue
            x, y = v[0], v[1]
        else:
            continue
    except Exception:
        continue
    if not (X0 <= x <= X1 and SY0 <= y <= SY1):
        continue
    inv[(t, e.dxf.layer)] += 1
    if t == "INSERT":
        ins[e.dxf.name] += 1

print("=== S2 entity inventory (type, layer) ===")
for k, v in sorted(inv.items(), key=lambda kv: -kv[1]):
    print(f"  {k}: {v}")
print("\n=== S2 INSERT block names ===")
for k, v in sorted(ins.items(), key=lambda kv: -kv[1]):
    print(f"  {k}: {v}")
