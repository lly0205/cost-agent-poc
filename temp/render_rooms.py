# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

PATH = r"C:\Users\Windows 11\Desktop\机电\阳山卫生间大样\2~4层给排水_布局1.dxf"
OUT = r"D:\cc-connect\cost-agent-poc\temp"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

crops = {
    "room_chashui":  ((-462, -412), (818, 882)),
    "room_wuzhangai":((-468, -408), (688, 822)),
    "room_nanwei":   ((-428, -328), (688, 822)),
    "room_nvwei":    ((-465, -328), (628, 695)),
}
for name, (xl, yl) in crops.items():
    fig = plt.figure(figsize=(12, 12 * (yl[1]-yl[0]) / (xl[1]-xl[0])))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend).draw_layout(msp, finalize=False)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(*xl); ax.set_ylim(*yl)
    ax.axis("off")
    fig.savefig(OUT + f"\\{name}.png", dpi=130, facecolor="black")
    plt.close(fig)
    print("saved", name)
