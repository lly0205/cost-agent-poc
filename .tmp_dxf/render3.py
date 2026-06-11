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
    # legend / notes block of S7
    "S7_notes": (-4756000, -468800, -4742000, -461500),
    # small hole at axis area with 0.82x1.87
    "S7_hole_a": (-4715500, -417500, -4710000, -413000),
    # big diagonal zone
    "S7_zone_b": (-4729500, -435000, -4720000, -425000),
    # hole 1.32x1.62 + 1.72x1.42 region
    "S7_hole_c": (-4789500, -407000, -4784500, -403500),
}
for name, (x0, y0, x1, y1) in VIEWS.items():
    w = (x1-x0); h = (y1-y0)
    fig = plt.figure(figsize=(20, 20*h/w), dpi=120)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{name}.png")
    plt.close(fig)
    print(name, "done")
