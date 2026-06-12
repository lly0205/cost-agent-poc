# -*- coding: utf-8 -*-
# Task3/4/6: band net lengths in raft & top slab; deep-zone interior boundary; BPB1
import ezdxf, sys, pickle
from shapely.geometry import Polygon, Point, LineString
from shapely.affinity import translate
from ezdxf import bbox as ebbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S3": (-139272, -55172), "S5": (-307472, -223372), "S7": (-475672, -391572)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1: return n
    return None
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423), "S7": (-4711816, -404432)}
def tr(g, s, d): return translate(g, xoff=ANCH[d][0]-ANCH[s][0], yoff=ANCH[d][1]-ANCH[s][1])

with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc3 = tr(enc5, "S5", "S3")
print("enc3 bounds:", [round(v) for v in enc3.bounds], "area:", round(enc3.area/1e6,1))

# band hatch polygons (layer 4, ANSI37) in S3
bands = []
for e in msp.query("HATCH"):
    if e.dxf.layer != "4" or e.dxf.pattern_name != "ANSI37": continue
    for p in e.paths:
        if hasattr(p, "vertices") and len(p.vertices) >= 3:
            pts = [(v[0], v[1]) for v in p.vertices]
            poly = Polygon(pts)
            c = poly.centroid
            if X0 <= c.x <= X1 and band(c.y) == "S3":
                bands.append(poly)
print("band polys:", len(bands))
for i, bp in enumerate(bands):
    b = bp.bounds
    clip = bp.intersection(enc3)
    horiz = (b[2]-b[0]) > (b[3]-b[1])
    L_full = max(b[2]-b[0], b[3]-b[1])/1000
    Wd = min(b[2]-b[0], b[3]-b[1])/1000
    # net length = clipped area / width
    L_net = clip.area/1e6/Wd
    print(f"band{i}: {'H' if horiz else 'V'} c=({(b[0]+b[2])/2:.0f},{(b[1]+b[3])/2:.0f}) w={Wd:.2f}m full={L_full:.2f}m net_in_raft={L_net:.2f}m")

# deep zone polygon (看线 ANSI31)
deep = None
for e in msp.query("HATCH"):
    if e.dxf.layer != "看线": continue
    for p in e.paths:
        if hasattr(p, "vertices") and len(p.vertices) >= 3:
            pts = [(v[0], v[1]) for v in p.vertices]
            poly = Polygon(pts)
            c = poly.centroid
            if X0 <= c.x <= X1 and band(c.y) == "S3" and poly.area/1e6 > 1000:
                deep = poly
print("\ndeep zone area m2:", round(deep.area/1e6, 1), "perimeter m:", round(deep.exterior.length/1000, 1))
# interior boundary = deep boundary not on enclosure edge
edge = deep.exterior
inner = edge.difference(enc3.exterior.buffer(400))
print("deep boundary inside raft (step line) length m:", round(inner.length/1000, 1))
# segments detail
geoms = list(inner.geoms) if inner.geom_type == "MultiLineString" else [inner]
for g in geoms:
    b = g.bounds
    print(f"  step seg: ({b[0]:.0f},{b[1]:.0f})-({b[2]:.0f},{b[3]:.0f}) len={g.length/1000:.1f}m")

# BPB1 texts anywhere
print("\nBPB1 texts:")
for e in msp.query("TEXT MTEXT"):
    t = (e.dxf.text if e.dxftype()=="TEXT" else e.text)
    if "BPB" in t.upper():
        x, y = e.dxf.insert.x, e.dxf.insert.y
        print(f"  {band(y)} ({x:.0f},{y:.0f}) layer={e.dxf.layer} rot={getattr(e.dxf,'rotation',0):.0f}: {t.strip()[:80]}")
