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
    "hole_2x06": (-4805500, -456500, -4801000, -453000),
    "hole_62x11": (-4729000, -456500, -4719000, -452500),
    "hole_05x24": (-4780500, -455500, -4777500, -452000),
    "hole_18x09": (-4748500, -456000, -4745000, -453200),
    "hole_37x71": (-4792500, -456000, -4786500, -447500),
}
for name, (a, b, c, d) in VIEWS.items():
    w = c-a; h = d-b
    fig = plt.figure(figsize=(18, 18*h/w), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(a, c); ax.set_ylim(b, d)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{name}.png")
    plt.close(fig)
    print(name, "done")
