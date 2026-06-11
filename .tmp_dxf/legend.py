# -*- coding: utf-8 -*-
import ezdxf, sys
from ezdxf import bbox
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

# scan bottom-left of S7 sheet for legend
x0, y0, x1, y1 = -4838000, -4700000+0, 0, 0  # placeholder
REG = (-4838000, -469000, -4806000, -455000)
print("=== entities in S7 bottom-left region ===")
for e in msp:
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
    except Exception: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if not (REG[0] <= cx <= REG[2] and REG[1] <= cy <= REG[3]): continue
    t = e.dxftype()
    extra = ""
    if t == "TEXT": extra = e.dxf.text
    elif t == "MTEXT": extra = e.plain_text().replace("\n", "\\n")
    elif t == "INSERT": extra = e.dxf.name
    elif t == "HATCH": extra = f"pat={e.dxf.pattern_name}"
    w = ext.extmax.x-ext.extmin.x; h = ext.extmax.y-ext.extmin.y
    print(f"  {t} layer={e.dxf.layer} c=({cx:.0f},{cy:.0f}) size={w:.0f}x{h:.0f} {extra}")

VIEWS = {
    "S7_legend": (-4838000, -469000, -4806000, -455000),
    "S7_zone_wide": (-4733000, -437000, -4716000, -423000),
}
for name, (a, b, c, d) in VIEWS.items():
    w = c-a; h = d-b
    fig = plt.figure(figsize=(22, 22*h/w), dpi=120)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(a, c); ax.set_ylim(b, d)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{name}.png")
    plt.close(fig)
    print(name, "done")
