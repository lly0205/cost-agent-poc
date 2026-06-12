# -*- coding: utf-8 -*-
# Task2: classify 板洞边线 clusters in S7 vs basement enclosure; nearest labels
import ezdxf, sys, pickle, collections
from shapely.geometry import LineString, Polygon, Point, MultiPoint
from shapely.ops import unary_union, polygonize
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423), "S7": (-4711816, -404432)}
def tr(g, s, d): return translate(g, xoff=ANCH[d][0]-ANCH[s][0], yoff=ANCH[d][1]-ANCH[s][1])

with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc7 = tr(enc5, "S5", "S7")
print("enclosure in S7 bounds:", [round(v) for v in enc7.bounds], "area m2:", round(enc7.area/1e6,1))

# all 板洞边线 segments in S7
segs = []
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    if X0 <= x1 <= X1 and SY0 <= y1 <= SY1:
        segs.append(LineString([(x1, y1), (x2, y2)]))
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer != "板洞边线": continue
    pts = [(p[0], p[1]) for p in e.get_points("xy")]
    cx = sum(p[0] for p in pts)/len(pts)
    if not (X0 <= cx <= X1): continue
    if not (SY0 <= pts[0][1] <= SY1): continue
    seq = pts + ([pts[0]] if e.closed else [])
    for a, b in zip(seq, seq[1:]):
        segs.append(LineString([a, b]))
print("segs:", len(segs))

# cluster all segs together
u = unary_union([s.buffer(30) for s in segs])
gs = list(u.geoms) if u.geom_type == "MultiPolygon" else [u]
print("clusters:", len(gs))

# texts in S7 plan for labeling
texts = []
for e in msp.query("TEXT MTEXT"):
    t = (e.dxf.text if e.dxftype()=="TEXT" else e.text).strip()
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if X0 <= x <= X1 and SY0 <= y <= SY1 and t:
        texts.append((x, y, e.dxf.layer, t))

rows = []
for g in gs:
    b = g.bounds
    cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2
    w, h = (b[2]-b[0])/1000, (b[3]-b[1])/1000
    nseg = sum(1 for s in segs if g.contains(s.centroid))
    inside = enc7.buffer(500).contains(Point(cx, cy))
    # nearest 3 texts
    near = sorted(texts, key=lambda t: (t[0]-cx)**2+(t[1]-cy)**2)[:3]
    lab = " | ".join(f"{t[3][:18]}" for t in near)
    rows.append((inside, -w*h, cx, cy, w, h, nseg, lab))
rows.sort()
print("\nIN = inside basement enclosure")
for inside, _, cx, cy, w, h, nseg, lab in rows:
    print(f"{'IN ' if inside else 'OUT'} c=({cx:.0f},{cy:.0f}) {w:.2f}x{h:.2f}m segs={nseg}  near: {lab}")
