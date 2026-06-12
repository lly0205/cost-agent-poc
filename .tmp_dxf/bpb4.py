# -*- coding: utf-8 -*-
# whole-S3 render with overlays + markers
import ezdxf, sys, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration
from shapely.geometry import Polygon
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423)}
def tr(g, s, d): return translate(g, xoff=ANCH[d][0]-ANCH[s][0], yoff=ANCH[d][1]-ANCH[s][1])
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc3 = tr(enc5, "S5", "S3")
X0, X1 = -4840000, -4691000
deep = None
for e in msp.query("HATCH"):
    if e.dxf.layer != "看线": continue
    for p in e.paths:
        if hasattr(p, "vertices") and len(p.vertices) >= 3:
            pts = [(v[0], v[1]) for v in p.vertices]
            poly = Polygon(pts)
            c = poly.centroid
            if X0 <= c.x <= X1 and -139272 <= c.y <= -55172 and poly.area/1e6 > 1000:
                deep = poly
a, b, c, d = -4824000, -120500, -4708000, -60000
w = c-a; h = d-b
fig = plt.figure(figsize=(34, 34*h/w), dpi=110)
ax = fig.add_axes([0, 0, 1, 1])
ctx = RenderContext(doc)
backend = MatplotlibBackend(ax)
Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
xs, ys = zip(*enc3.exterior.coords); ax.plot(xs, ys, color="yellow", lw=2.5, zorder=11)
xs, ys = zip(*deep.exterior.coords); ax.plot(xs, ys, color="orange", lw=2.5, zorder=11)
ax.plot([-4806788], [-102435], marker="*", color="red", ms=25, zorder=12)   # BPB1
ax.plot([-4808235], [-78140], marker="*", color="cyan", ms=25, zorder=12)   # -5.200
ax.set_xlim(a, c); ax.set_ylim(b, d)
fig.savefig(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\S3_overview2.png")
plt.close(fig)
print("done")
