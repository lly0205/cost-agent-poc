# -*- coding: utf-8 -*-
# render S7 with mark classification: X-pairs RED thick, singles CYAN; beams gray; walls green
import ezdxf, sys, math, pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572
ANCH = {"S5": (-4718640, -231423), "S7": (-4711816, -404432)}
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc7 = translate(enc5, xoff=ANCH["S7"][0]-ANCH["S5"][0], yoff=ANCH["S7"][1]-ANCH["S5"][1])

fig, ax = plt.subplots(figsize=(28, 16), dpi=110)
for e in msp.query("LINE"):
    lay = e.dxf.layer
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    cx, cy = (x1+x2)/2, (y1+y2)/2
    if not (X0 <= cx <= X1 and SY0 <= cy <= SY1): continue
    if lay in ("BEAM", "BEAM_CON"):
        ax.plot([x1, x2], [y1, y2], color="0.65", lw=0.3)
    elif lay == "砼墙":
        ax.plot([x1, x2], [y1, y2], color="green", lw=0.8)
    elif lay == "AXIS":
        ax.plot([x1, x2], [y1, y2], color="0.85", lw=0.3, ls=":")

# marks
lines = []
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    cx, cy = (x1+x2)/2, (y1+y2)/2
    if X0 <= cx <= X1 and SY0 <= cy <= SY1:
        ang = math.degrees(math.atan2(y2-y1, x2-x1)) % 180
        kind = "DIAG" if 2 <= ang <= 178 and not (88 < ang < 92) else "ORTH"
        lines.append((cx, cy, abs(x2-x1), abs(y2-y1), kind, (x1, y1, x2, y2)))
used = [False]*len(lines)
for i, (cx, cy, bw, bh, kind, seg) in enumerate(lines):
    if used[i] or kind != "DIAG": continue
    mate = None
    for j in range(i+1, len(lines)):
        if used[j] or lines[j][4] != "DIAG": continue
        if abs(lines[j][0]-cx) < 200 and abs(lines[j][1]-cy) < 200 and abs(lines[j][2]-bw) < 300 and abs(lines[j][3]-bh) < 300:
            mate = j; break
    if mate is not None:
        used[i] = used[mate] = True
        for k in (i, mate):
            s = lines[k][5]
            ax.plot([s[0], s[2]], [s[1], s[3]], color="red", lw=2.0)
    else:
        used[i] = True
        s = seg
        ax.plot([s[0], s[2]], [s[1], s[3]], color="deepskyblue", lw=1.0)
for i, (cx, cy, bw, bh, kind, seg) in enumerate(lines):
    if kind == "ORTH":
        s = seg
        ax.plot([s[0], s[2]], [s[1], s[3]], color="orange", lw=1.2)

bx, by = enc7.exterior.xy
ax.plot(bx, by, color="lime", lw=1.5, ls="--")
ax.set_aspect("equal"); ax.axis("off")
plt.tight_layout()
plt.savefig(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\S7_marks_class.png", facecolor="white")
print("saved")

# East zone closeup 13~14 / A~F
fig2, ax2 = plt.subplots(figsize=(14, 18), dpi=110)
EX0, EX1 = -4734000, -4709000
EY0, EY1 = -462000, -400000
for e in msp.query("LINE"):
    lay = e.dxf.layer
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    cx, cy = (x1+x2)/2, (y1+y2)/2
    if not (EX0 <= cx <= EX1 and EY0 <= cy <= EY1): continue
    col, lw = None, 0.4
    if lay in ("BEAM",): col, lw = "0.5", 0.5
    elif lay == "BEAM_CON": col, lw = "0.7", 0.4
    elif lay == "砼墙": col, lw = "green", 1.0
    elif lay == "板洞边线": col, lw = "red", 1.4
    if col: ax2.plot([x1, x2], [y1, y2], color=col, lw=lw)
for e in msp.query("TEXT"):
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if EX0 <= x <= EX1 and EY0 <= y <= EY1 and e.dxf.height > 200:
        ax2.text(x, y, e.dxf.text.strip(), fontsize=5, color="blue")
ax2.plot(bx, by, color="lime", lw=1.5, ls="--")
ax2.set_xlim(EX0, EX1); ax2.set_ylim(EY0, EY1)
ax2.set_aspect("equal"); ax2.axis("off")
plt.tight_layout()
plt.savefig(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\S7_east_zone.png", facecolor="white")
print("saved east")
