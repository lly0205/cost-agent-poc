# -*- coding: utf-8 -*-
import ezdxf, sys, re, collections
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

def dim_text(e):
    blk = e.get_geometry_block()
    vals = []
    if blk:
        for ve in blk:
            if ve.dxftype() in ("TEXT", "MTEXT"):
                t = ve.dxf.text if ve.dxftype() == "TEXT" else ve.plain_text()
                vals.append(t)
    return vals

rows = []
for e in msp.query("DIMENSION"):
    if e.dxf.layer == "柱尺寸标注":
        p = e.dxf.defpoint
        if -4840000 <= p.x <= -4691000 and -307472 <= p.y <= -223372:
            rows.append((p.x, p.y, "|".join(dim_text(e))))
rows.sort(key=lambda r: (-r[1], r[0]))
for x, y, t in rows:
    print(f"{x:.0f}\t{y:.0f}\t{t}")
