# -*- coding: utf-8 -*-
import ezdxf, sys, collections, pickle
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S5 = (-307472, -223372)

wl = []
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙" and X0 <= e.dxf.start.x <= X1 and S5[0] <= e.dxf.start.y <= S5[1]:
        wl.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))

R = 1300
buf = unary_union([l.buffer(R) for l in wl])
polys = list(buf.geoms) if buf.geom_type == "MultiPolygon" else [buf]
big = max(polys, key=lambda p: p.area)
# fill holes -> outer region, then erode back
outer = Polygon(big.exterior).buffer(-R)
print(f"enclosure: area={outer.area/1e6:.1f} m2, perim={outer.length/1000:.1f} m")
print("bbox:", [round(v/1000, 1) for v in outer.bounds])
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "wb") as f:
    pickle.dump(outer, f)
# holes of big (interior open areas not walled)?
print("n interior rings of buffered union:", len(list(big.interiors)))
