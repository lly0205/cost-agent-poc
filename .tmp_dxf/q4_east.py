# -*- coding: utf-8 -*-
# Q4 final check: raw read of every 板洞边线 segment in S7 east zone (axes 12.5~14+, C-1~D+4.5)
import ezdxf, sys, math, pickle
from shapely.geometry import Point
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

# S7 sheet anchor offsets (from S5 grid)
dx = -4711816 - (-4718640)   # +6824
dy = -404432 - (-231423)     # -173009
NUX = {k: v + dx for k, v in {'12': -4735740, '13': -4727340, '14': -4718940}.items()}
LUY = {k: v + dy for k, v in {'B': -272523, 'C': -262923, 'D': -250923, 'E': -241323}.items()}
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc = translate(enc5, xoff=dx, yoff=dy)

def axx(x):
    k, v = min(NUX.items(), key=lambda kv: abs(kv[1] - x)); o = (x - v) / 1000
    return k if abs(o) < 0.05 else f"{k}{o:+.2f}"
def axy(y):
    k, v = min(LUY.items(), key=lambda kv: abs(kv[1] - y)); o = (y - v) / 1000
    return k if abs(o) < 0.05 else f"{k}{o:+.2f}"

# window: x 12.3轴 ~ 14轴+5m, y C轴-6m ~ D轴+6m
WX0, WX1 = NUX['12'] - 2000, NUX['14'] + 6000
WY0, WY1 = LUY['C'] - 6000, LUY['D'] + 6000
segs = []
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    if not (WX0 <= cx <= WX1 and WY0 <= cy <= WY1): continue
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
    segs.append((x1, y1, x2, y2, cx, cy, ang))
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer != "板洞边线": continue
    pts = list(e.get_points("xy"))
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    if WX0 <= cx <= WX1 and WY0 <= cy <= WY1:
        print("LWPOLYLINE in window:", [(round(p[0]), round(p[1])) for p in pts])

print(f"window X[{WX0:.0f},{WX1:.0f}] Y[{WY0:.0f},{WY1:.0f}]  -> {len(segs)} LINE segs on 板洞边线")
print(f"axis ref: 13={NUX['13']:.0f} 14={NUX['14']:.0f} C={LUY['C']:.0f} D={LUY['D']:.0f}")
segs.sort(key=lambda s: (s[5], s[4]))
for i, (x1, y1, x2, y2, cx, cy, ang) in enumerate(segs):
    L = math.hypot(x2 - x1, y2 - y1) / 1000
    kind = "ORTH" if (ang < 2 or ang > 178 or 88 < ang < 92) else "DIAG"
    print(f"[{i:02d}] {kind} ang={ang:6.1f} L={L:6.2f}m  ({x1:.0f},{y1:.0f})->({x2:.0f},{y2:.0f})  "
          f"start@({axx(x1)},{axy(y1)}) end@({axx(x2)},{axy(y2)}) ctr@({axx(cx)},{axy(cy)})")

# pair diagonals: X (same center) vs bent (shared endpoint)
diags = [s for s in segs if not (s[6] < 2 or s[6] > 178 or 88 < s[6] < 92)]
used = [False] * len(diags)
print("\n--- pairing of diagonals ---")
for i in range(len(diags)):
    if used[i]: continue
    for j in range(i + 1, len(diags)):
        if used[j]: continue
        si, sj = diags[i], diags[j]
        same_ctr = abs(si[4] - sj[4]) < 200 and abs(si[5] - sj[5]) < 200
        share = any(abs(si[a] - sj[b]) < 80 and abs(si[a+1] - sj[b+1]) < 80
                    for a in (0, 2) for b in (0, 2))
        if same_ctr or share:
            xs = [si[0], si[2], sj[0], sj[2]]; ys = [si[1], si[3], sj[1], sj[3]]
            a, b, c, d = min(xs), min(ys), max(xs), max(ys)
            w, h = (c - a) / 1000, (d - b) / 1000
            ins = enc.buffer(800).contains(Point((a + c) / 2, (b + d) / 2))
            tag = "X形(交叉于中心,临时)" if same_ctr and not share else "折线(共端点,永久)"
            if same_ctr and share: tag = "AMBIG"
            print(f"{tag}: bbox X:{axx(a)}~{axx(c)} Y:{axy(b)}~{axy(d)}  {w:.2f}x{h:.2f}={w*h:.2f}m2  "
                  f"{'界内' if ins else '界外(板区边界外)'}  rawX[{a:.0f},{c:.0f}] rawY[{b:.0f},{d:.0f}]")
            used[i] = used[j] = True
            break
