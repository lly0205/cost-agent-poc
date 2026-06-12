# -*- coding: utf-8 -*-
# render each IN-enclosure hole cluster with context; extract axis grid in S7
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
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572

# ---- axis grid: find axis bubble labels in S7 ----
import collections
cand = collections.Counter()
axes = []
for e in msp.query("TEXT"):
    t = e.dxf.text.strip()
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if X0 <= x <= X1 and SY0 <= y <= SY1:
        import re
        if re.fullmatch(r"\d{1,2}|[A-Z]", t):
            cand[e.dxf.layer] += 1
            axes.append((t, x, y, e.dxf.layer))
print("axis-label layer counts:", dict(cand))
# print numeric labels sorted by x (cols) and letters by y (rows)
nums = sorted([a for a in axes if a[0].isdigit()], key=lambda a: a[1])
lets = sorted([a for a in axes if a[0].isalpha()], key=lambda a: a[2])
print("\nnumeric axes (sorted x):")
for t, x, y, l in nums: print(f"  {t}: x={x:.0f} y={y:.0f} [{l}]")
print("\nletter axes (sorted y):")
for t, x, y, l in lets: print(f"  {t}: x={x:.0f} y={y:.0f} [{l}]")

HOLES = {
    "inA_37x92": (-4743741, -450382, 3.69, 9.16),
    "inB_37x80": (-4789644, -408882, 3.72, 7.96),
    "inC_38x72": (-4789591, -451567, 3.81, 7.19),
    "inD_27x35": (-4793066, -447332, 2.66, 3.46),
    "inE_18x15": (-4786666, -405432, 1.76, 1.46),
    "inF_14x17": (-4771566, -405532, 1.36, 1.66),
    "inG_19x09": (-4746816, -454657, 1.86, 0.91),
    "inH_09x19": (-4712716, -415307, 0.86, 1.91),
    "inI_21x07": (-4803316, -454823, 2.06, 0.68),
    "inJ_06x25": (-4779066, -453732, 0.56, 2.46),
    "inK_12x08": (-4820766, -453882, 1.16, 0.76),
    "inL_15x06": (-4792566, -404982, 1.46, 0.56),
    "inM_06x12": (-4728391, -454582, 0.61, 1.16),
}
ctx = RenderContext(doc)
for name, (cx, cy, w, h) in HOLES.items():
    m = max(w, h)*1000*1.2 + 2500
    a, b, c, d = cx-m, cy-m, cx+m, cy+m
    fig = plt.figure(figsize=(14, 14), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=Configuration(min_lineweight=0.05)).draw_layout(msp, finalize=True)
    ax.set_xlim(a, c); ax.set_ylim(b, d)
    fig.savefig(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\H_{name}.png")
    plt.close(fig)
    print(name, "rendered")
