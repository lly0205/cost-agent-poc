# -*- coding: utf-8 -*-
# FINAL hole classification S7 (+S6 cross-check):
#   X mark  = 2 diagonals crossing at center  -> TEMPORARY (5 expected)
#   bent mark = 2 diagonals sharing an endpoint -> PERMANENT (40 expected)
import ezdxf, sys, math, pickle
from shapely.geometry import Point
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S6": (-391572, -307472), "S7": (-475672, -391572)}
ANCH = {"S5": (-4718640, -231423), "S6": (-4711895, -322585), "S7": (-4711816, -404432)}
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)

NUX5 = {'1': -4828140, '2': -4819740, '3': -4811340, '4': -4802940, '5': -4794540, '6': -4786140,
        '7': -4777740, '8': -4769340, '9': -4760940, '10': -4752540, '11': -4744140, '12': -4735740,
        '13': -4727340, '14': -4718940}
LUY5 = {'A': -282123, 'B': -272523, 'C': -262923, 'D': -250923, 'E': -241323, 'F': -231723}

def analyze(sheet):
    SY0, SY1 = BANDS[sheet]
    dx = ANCH[sheet][0]-ANCH["S5"][0]; dy = ANCH[sheet][1]-ANCH["S5"][1]
    enc = translate(enc5, xoff=dx, yoff=dy)
    NUX = {k: v+dx for k, v in NUX5.items()}; LUY = {k: v+dy for k, v in LUY5.items()}
    def axx(x):
        k, v = min(NUX.items(), key=lambda kv: abs(kv[1]-x)); o = (x-v)/1000
        return k if abs(o) < 0.35 else f"{k}{o:+.1f}"
    def axy(y):
        k, v = min(LUY.items(), key=lambda kv: abs(kv[1]-y)); o = (y-v)/1000
        return k if abs(o) < 0.35 else f"{k}{o:+.1f}"
    diags, orth = [], 0
    for e in msp.query("LINE"):
        if e.dxf.layer != "板洞边线": continue
        x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
        cx, cy = (x1+x2)/2, (y1+y2)/2
        if not (X0 <= cx <= X1 and SY0 <= cy <= SY1): continue
        ang = math.degrees(math.atan2(y2-y1, x2-x1)) % 180
        if ang < 2 or ang > 178 or 88 < ang < 92:
            orth += 1; continue
        diags.append([(x1, y1), (x2, y2), cx, cy])
    used = [False]*len(diags)
    Xs, bents, lone = [], [], []
    # 1) X pairs: same center, similar bbox
    for i in range(len(diags)):
        if used[i]: continue
        for j in range(i+1, len(diags)):
            if used[j]: continue
            if abs(diags[j][2]-diags[i][2]) < 200 and abs(diags[j][3]-diags[i][3]) < 200:
                xs = [diags[i][0][0], diags[i][1][0], diags[j][0][0], diags[j][1][0]]
                ys = [diags[i][0][1], diags[i][1][1], diags[j][0][1], diags[j][1][1]]
                Xs.append((min(xs), min(ys), max(xs), max(ys)))
                used[i] = used[j] = True
                break
    # 2) bent pairs: share an endpoint
    def close(p, q, tol=80): return abs(p[0]-q[0]) < tol and abs(p[1]-q[1]) < tol
    for i in range(len(diags)):
        if used[i]: continue
        for j in range(i+1, len(diags)):
            if used[j]: continue
            share = any(close(diags[i][a], diags[j][b]) for a in (0, 1) for b in (0, 1))
            if share:
                xs = [diags[i][0][0], diags[i][1][0], diags[j][0][0], diags[j][1][0]]
                ys = [diags[i][0][1], diags[i][1][1], diags[j][0][1], diags[j][1][1]]
                bents.append((min(xs), min(ys), max(xs), max(ys)))
                used[i] = used[j] = True
                break
        if not used[i]:
            used[i] = True
            xs = [diags[i][0][0], diags[i][1][0]]; ys = [diags[i][0][1], diags[i][1][1]]
            lone.append((min(xs), min(ys), max(xs), max(ys)))
    print(f"\n######## {sheet}: diag={len(diags)} orth_ticks={orth} -> X={len(Xs)} bent={len(bents)} lone={len(lone)}")
    for nm, lst in (("X(临时)", Xs), ("bent(永久)", bents), ("lone(未配对)", lone)):
        tot = tin = 0.0
        print(f"--- {nm}: {len(lst)} ---")
        for (a, b, c, d) in sorted(lst, key=lambda r: -(r[2]-r[0])*(r[3]-r[1])):
            w, h = (c-a)/1000, (d-b)/1000
            A = w*h
            cx, cy = (a+c)/2, (b+d)/2
            ins = enc.buffer(800).contains(Point(cx, cy))
            tot += A; tin += A if ins else 0
            print(f"  {'IN ' if ins else 'OUT'} {w:.2f}x{h:.2f}={A:.2f}m2  X:{axx(a)}~{axx(c)} Y:{axy(b)}~{axy(d)}")
        print(f"  subtotal {tot:.2f} m2 (inside-enc {tin:.2f})")
analyze("S7")
analyze("S6")
