# -*- coding: utf-8 -*-
# render S2 with the 355 counted pile positions marked
import ezdxf, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf import bbox
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY = (-55172, 28928)
piles = []
for e in msp.query("INSERT"):
    if e.dxf.name != "sdfsdfsdfsfdsf": continue
    ext = bbox.extents([e], fast=True)
    if not ext.has_data: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if X0 <= cx <= X1 and SY[0] <= cy <= SY[1]:
        piles.append((cx, cy))
print("piles:", len(piles))
a, b, c, d = X0, SY[0], X1, SY[1]
w = c-a; h = d-b
fig = plt.figure(figsize=(30, 30*h/w), dpi=110)
ax = fig.add_axes([0, 0, 1, 1])
ctx = RenderContext(doc)
backend = MatplotlibBackend(ax)
Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
ax.scatter([p[0] for p in piles], [p[1] for p in piles], s=14, facecolors='none', edgecolors='red', linewidths=0.8, zorder=10)
ax.set_xlim(a, c); ax.set_ylim(b, d)
fig.savefig(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\S2_pile_marked.png")
plt.close(fig)
print("saved")
