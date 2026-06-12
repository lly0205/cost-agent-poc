# -*- coding: utf-8 -*-
import ezdxf, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
VIEWS = {
  "S4_step1": (-4772000, -180500, -4758000, -171500),
  "S4_step2": (-4747500, -180500, -4733500, -171500),
}
ctx = RenderContext(doc)
for name, (a, b, c, d) in VIEWS.items():
    w = c-a; h = d-b
    fig = plt.figure(figsize=(22, 22*h/w), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(a, c); ax.set_ylim(b, d)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{name}.png")
    plt.close(fig)
    print(name, "done")
# also dump DIMENSION measurements + texts in those windows
from ezdxf import bbox as ebbox
for name, (a, b, c, d) in VIEWS.items():
    print(f"--- {name} texts/dims ---")
    for e in msp.query("TEXT MTEXT"):
        t = (e.dxf.text if e.dxftype()=="TEXT" else e.text).strip()
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if a <= x <= c and b <= y <= d:
            print(f"  T ({x:.0f},{y:.0f}) [{e.dxf.layer}] {t[:70]}")
    for e in msp.query("DIMENSION"):
        try:
            ext = ebbox.extents([e], fast=True)
            if not ext.has_data: continue
            cx=(ext.extmin.x+ext.extmax.x)/2; cy=(ext.extmin.y+ext.extmax.y)/2
        except Exception: continue
        if a <= cx <= c and b <= cy <= d:
            m = e.dxf.actual_measurement if e.dxf.hasattr("actual_measurement") else -1
            print(f"  D ({cx:.0f},{cy:.0f}) meas={m:.0f} text='{e.dxf.text}'")
