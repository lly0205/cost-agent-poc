# -*- coding: utf-8 -*-
import ezdxf, sys, collections
from ezdxf.math import OCS
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

n = 0
for e in msp.query("INSERT"):
    if e.dxf.name == "sdfsdfsdfsfdsf" and n < 5:
        ocs = e.ocs()
        wcs = ocs.to_wcs(e.dxf.insert)
        print("extrusion=", tuple(e.dxf.extrusion), "insert=", tuple(e.dxf.insert), "wcs=", (round(wcs.x), round(wcs.y)), "scale=", e.dxf.xscale, "rot=", e.dxf.rotation)
        n += 1

# x distribution of all entity insert/start points
xs = []
for e in msp:
    p = None
    t = e.dxftype()
    try:
        if t in ("TEXT", "MTEXT", "INSERT", "CIRCLE"):
            p = e.dxf.insert if t != "CIRCLE" else e.dxf.center
        elif t == "LINE":
            p = e.dxf.start
        elif t == "LWPOLYLINE":
            p = e.get_points()[0]
            p = type("P", (), {"x": p[0], "y": p[1]})()
    except Exception:
        continue
    if p is not None:
        xs.append(p.x)
import statistics
xs.sort()
print("min/max x:", round(xs[0]), round(xs[-1]))
hist = collections.Counter(int(x // 100000) * 100000 for x in xs)
for k in sorted(hist):
    print(k, hist[k])
