# -*- coding: utf-8 -*-
# refine: band rects clipped; step line = deep edge far from enclosure edge; BPB1 render
import ezdxf, sys, pickle, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration
from shapely.geometry import Polygon, LineString, box, Point
from shapely.affinity import translate
from ezdxf import bbox as ebbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S3": (-139272, -55172), "S7": (-475672, -391572)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1: return n
    return None
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423), "S7": (-4711816, -404432)}
def tr(g, s, d): return translate(g, xoff=ANCH[d][0]-ANCH[s][0], yoff=ANCH[d][1]-ANCH[s][1])
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc3 = tr(enc5, "S5", "S3"); enc7 = tr(enc5, "S5", "S7")

# band rects via ezdxf bbox of the 3 ANSI37 hatches
rects = []
for e in msp.query("HATCH"):
    if e.dxf.layer != "4" or e.dxf.pattern_name != "ANSI37": continue
    ext = ebbox.extents([e], fast=True)
    if not ext.has_data: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if X0 <= cx <= X1 and band(cy) == "S3":
        rects.append(box(ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y))
print("band rects:", len(rects))
for i, r in enumerate(rects):
    b = r.bounds
    horiz = (b[2]-b[0]) > (b[3]-b[1])
    Wd = min(b[2]-b[0], b[3]-b[1])/1000
    clip3 = r.intersection(enc3)
    r7 = tr(r, "S3", "S7")
    clip7 = r7.intersection(enc7)
    print(f"band{i} {'H' if horiz else 'V'} c=({(b[0]+b[2])/2:.0f},{(b[1]+b[3])/2:.0f}) w={Wd:.2f} "
          f"L_raft={clip3.area/1e6/Wd:.2f}m L_topslab={clip7.area/1e6/Wd:.2f}m fullL={max(b[2]-b[0],b[3]-b[1])/1000:.2f}")

# deep zone & step edges
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
co = list(deep.exterior.coords)
print("\ndeep zone vertices:", len(co))
total = 0
for a, b2 in zip(co, co[1:]):
    seg = LineString([a, b2])
    if seg.length < 10: continue
    mid = seg.interpolate(0.5, normalized=True)
    dist = enc3.exterior.distance(mid)
    tag = "STEP" if dist > 1200 else "edge"
    if tag == "STEP": total += seg.length
    print(f"  {tag} ({a[0]:.0f},{a[1]:.0f})->({b2[0]:.0f},{b2[1]:.0f}) L={seg.length/1000:.2f}m dist_to_wall={dist/1000:.2f}m")
print("STEP total length:", round(total/1000, 1), "m")

# render BPB1 vicinity
cx, cy = -4806788, -102435
m = 9000
fig = plt.figure(figsize=(16, 16), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ctx = RenderContext(doc)
backend = MatplotlibBackend(ax)
Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
ax.set_xlim(cx-m, cx+m); ax.set_ylim(cy-m, cy+m)
fig.savefig(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\S3_BPB1.png")
plt.close(fig)
print("BPB1 rendered")
