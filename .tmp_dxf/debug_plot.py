# -*- coding: utf-8 -*-
import ezdxf, sys, collections, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S6 = (-391572, -307472); S5 = (-307472, -223372); S3 = (-139272, -55172)
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423), "S6": (-4711895, -322585)}
def tr(geom, src, dst):
    return translate(geom, xoff=ANCH[dst][0]-ANCH[src][0], yoff=ANCH[dst][1]-ANCH[src][1])

with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc6 = tr(enc5, "S5", "S6")

fig, ax = plt.subplots(figsize=(22, 11), dpi=100)
xs, ys = enc6.exterior.xy
ax.fill(xs, ys, alpha=0.15, color="green")
ax.plot(xs, ys, color="green", lw=1)

# walls S6
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙" and X0 <= e.dxf.start.x <= X1 and S6[0] <= e.dxf.start.y <= S6[1]:
        ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], color="black", lw=0.8)

# beams colored by in/out
enc_in = enc6.buffer(600)
for e in msp.query("LINE"):
    if e.dxf.layer in ("BEAM", "BEAM_CON"):
        x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
        if not (X0 <= x1 <= X1 and S6[0] <= y1 <= S6[1]): continue
        ls = LineString([(x1, y1), (x2, y2)])
        inside = ls.intersection(enc_in).length / max(ls.length, 1)
        ax.plot([x1, x2], [y1, y2], color=("blue" if inside > 0.5 else "red"), lw=0.6)

ax.set_aspect("equal")
fig.savefig(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\debug_beams.png", bbox_inches="tight")
print("saved")
