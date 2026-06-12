# -*- coding: utf-8 -*-
# per-line detail of 板洞边线 in S7; pair diagonals into X; singles = single-diagonal holes
import ezdxf, sys, math, pickle
from shapely.geometry import Point
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
NUX5 = {'1': -4828140, '2': -4819740, '3': -4811340, '4': -4802940, '5': -4794540, '6': -4786140,
        '7': -4777740, '8': -4769340, '9': -4760940, '10': -4752540, '11': -4744140, '12': -4735740,
        '13': -4727340, '14': -4718940}
LUY5 = {'A': -282123, 'B': -272523, 'C': -262923, 'D': -250923, 'E': -241323, 'F': -231723}
dx = ANCH["S7"][0]-ANCH["S5"][0]; dy = ANCH["S7"][1]-ANCH["S5"][1]
NUX = {k: v+dx for k, v in NUX5.items()}
LUY = {k: v+dy for k, v in LUY5.items()}
def axx(x):
    k, v = min(NUX.items(), key=lambda kv: abs(kv[1]-x)); o = (x-v)/1000
    return k if abs(o) < 0.35 else f"{k}{o:+.1f}"
def axy(y):
    k, v = min(LUY.items(), key=lambda kv: abs(kv[1]-y)); o = (y-v)/1000
    return k if abs(o) < 0.35 else f"{k}{o:+.1f}"

lines = []
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    cx, cy = (x1+x2)/2, (y1+y2)/2
    if X0 <= cx <= X1 and SY0 <= cy <= SY1:
        L = math.hypot(x2-x1, y2-y1)
        ang = math.degrees(math.atan2(y2-y1, x2-x1)) % 180
        kind = "H" if ang < 2 or ang > 178 else ("V" if 88 < ang < 92 else "DIAG")
        bw, bh = abs(x2-x1), abs(y2-y1)
        ins = enc7.buffer(800).contains(Point(cx, cy))
        lines.append((cx, cy, L, ang, kind, bw, bh, ins))

# pair diagonals sharing same bbox center (X pairs)
used = [False]*len(lines)
marks = []
for i, (cx, cy, L, ang, kind, bw, bh, ins) in enumerate(lines):
    if used[i] or kind != "DIAG": continue
    mate = None
    for j in range(i+1, len(lines)):
        if used[j] or lines[j][4] != "DIAG": continue
        cx2, cy2 = lines[j][0], lines[j][1]
        if abs(cx2-cx) < 200 and abs(cy2-cy) < 200 and abs(lines[j][5]-bw) < 300 and abs(lines[j][6]-bh) < 300:
            mate = j; break
    if mate is not None:
        used[i] = used[mate] = True
        marks.append(("X", cx, cy, bw, bh, ins))
    else:
        used[i] = True
        marks.append(("single", cx, cy, bw, bh, ins))
for i, (cx, cy, L, ang, kind, bw, bh, ins) in enumerate(lines):
    if not used[i] and kind != "DIAG":
        marks.append((kind+"-line", cx, cy, bw, bh, ins))

print(f"total lines={len(lines)}  DIAG={sum(1 for l in lines if l[4]=='DIAG')}  H={sum(1 for l in lines if l[4]=='H')}  V={sum(1 for l in lines if l[4]=='V')}")
print(f"\nmarks ({len(marks)}): type, bbox WxH m, pos, in_enclosure")
nin = {"X":0, "single":0}
for t, cx, cy, bw, bh, ins in sorted(marks, key=lambda m: (m[0], -m[3]*m[4])):
    a = bw*bh/1e6/2 if t == "single" else bw*bh/1e6
    print(f"  {'IN ' if ins else 'OUT'} {t:<7} {bw/1000:.2f}x{bh/1000:.2f}m rectA={bw*bh/1e6:.2f} at X:{axx(cx)} Y:{axy(cy)}")
    if ins and t in nin: nin[t] += 1
print(f"\nIN-enclosure: X={nin['X']} single={nin['single']}")
