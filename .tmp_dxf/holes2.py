# -*- coding: utf-8 -*-
import ezdxf, sys, math, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union, polygonize
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572

# collect 板洞边线 lines and polylines
hv, diag = [], []
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    if not (X0 <= x1 <= X1 and SY0 <= y1 <= SY1): continue
    if abs(y1-y2) < 1 or abs(x1-x2) < 1:
        hv.append(LineString([(x1, y1), (x2, y2)]))
    else:
        diag.append(LineString([(x1, y1), (x2, y2)]))
pl_cnt = 0
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer != "板洞边线": continue
    pts = [(p[0], p[1]) for p in e.get_points("xy")]
    cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
    if not (X0 <= cx <= X1 and SY0 <= cy <= SY1): continue
    pl_cnt += 1
    # split into segments
    closed = e.closed
    seq = pts + ([pts[0]] if closed else [])
    for a, b in zip(seq, seq[1:]):
        if abs(a[1]-b[1]) < 1 or abs(a[0]-b[0]) < 1:
            hv.append(LineString([a, b]))
        else:
            diag.append(LineString([a, b]))
print(f"H/V segs: {len(hv)}, diagonal segs: {len(diag)}, polylines: {pl_cnt}")

# build rectangles from H/V lines
merged = unary_union(hv)
polys = list(polygonize(merged))
print(f"closed rects from H/V: {len(polys)}")
rects = []
for p in polys:
    b = p.bounds
    w = (b[2]-b[0])/1000; h = (b[3]-b[1])/1000
    # diagonals intersecting this rect
    nd = sum(1 for d in diag if d.length > 200 and p.buffer(50).contains(d.centroid))
    rects.append((b, w, h, p.area/1e6, nd))
for b, w, h, a, nd in sorted(rects, key=lambda r: -r[3]):
    print(f"  rect c=({(b[0]+b[2])/2:.0f},{(b[1]+b[3])/2:.0f}) {w:.2f}x{h:.2f}m area={a:.2f}m2 diagonals={nd}")

# diagonal-only marks (zigzags over panels): group leftover diagonals not in any rect
loose = [d for d in diag if not any(Polygon([(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]).buffer(100).contains(d.centroid) for b,_,_,_,_ in rects)]
u = unary_union([d.buffer(10) for d in loose]) if loose else None
if u is not None:
    gs = list(u.geoms) if u.geom_type == "MultiPolygon" else [u]
    print(f"\nloose diagonal clusters (zigzag panel marks): {len(gs)}")
    for g in gs:
        b = g.bounds
        print(f"  c=({(b[0]+b[2])/2:.0f},{(b[1]+b[3])/2:.0f}) bbox {(b[2]-b[0])/1000:.1f}x{(b[3]-b[1])/1000:.1f}m")

# render note5+note6 legend crops at high zoom
VIEWS = {
    "S7_note5": (-4754300, -467500, -4745800, -466700),
    "S7_note6": (-4754300, -468300, -4749500, -467500),
}
for name, (a, b, c, d) in VIEWS.items():
    w = c-a; h = d-b
    fig = plt.figure(figsize=(24, 24*h/w), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(a, c); ax.set_ylim(b, d)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{name}.png")
    plt.close(fig)
    print(name, "done")
