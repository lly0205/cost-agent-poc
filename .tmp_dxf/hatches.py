# -*- coding: utf-8 -*-
import ezdxf, sys
from shapely.geometry import Polygon
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
        if y0 <= y <= y1:
            return n
    return None

for e in msp.query("HATCH"):
    paths = e.paths
    polys = []
    for p in paths:
        pts = []
        if hasattr(p, "vertices"):
            pts = [(v[0], v[1]) for v in p.vertices]
        elif hasattr(p, "edges"):
            for edge in p.edges:
                if hasattr(edge, "start"):
                    pts.append((edge.start[0], edge.start[1]))
        if len(pts) >= 3:
            polys.append(Polygon(pts))
    if not polys:
        continue
    big = max(polys, key=lambda q: q.area)
    c = big.centroid
    b = band(c.y) if X0 <= c.x <= X1 else None
    if b and big.area/1e6 > 5:
        print(f"{b}\tlayer={e.dxf.layer}\tpattern={e.dxf.pattern_name}\tnpaths={len(paths)}\tarea={big.area/1e6:.1f} m2\tperim={big.length/1000:.1f} m\tbbox={[round(v/1000,1) for v in big.bounds]}")
