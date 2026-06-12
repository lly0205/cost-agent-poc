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
  "S3_NW": (-4823500, -90000, -4793000, -65500),   # NW shallow incl -5.200 star
  "S3_SW": (-4823500, -120000, -4793000, -95000),  # SW shallow incl BPB1 star
}
ctx = RenderContext(doc)
for name, (a, b, c, d) in VIEWS.items():
    w = c-a; h = d-b
    fig = plt.figure(figsize=(26, 26*h/w), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(a, c); ax.set_ylim(b, d)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{name}.png")
    plt.close(fig)
    print(name, "done")
