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
    # S3 west transition at deep-zone edge x=-4796095 (axis 4), y mid C~D
    "S3_trans_west": (-4800000, -98000, -4790000, -88000),
    # S3 north transition y=-76087 between axes 9-11
    "S3_trans_north": (-4750000, -80000, -4738000, -72000),
    # S3 expansion band vertical #1 crossing horizontal band
    "S3_band_cross": (-4787000, -97000, -4777000, -88000),
}
for name, (a, b, c, d) in VIEWS.items():
    w = c-a; h = d-b
    fig = plt.figure(figsize=(20, 20*h/w), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(a, c); ax.set_ylim(b, d)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{name}.png")
    plt.close(fig)
    print(name, "done")
