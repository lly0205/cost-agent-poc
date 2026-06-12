# -*- coding: utf-8 -*-
# S7 slab boundary polygons + net slab area with new hole classification
import ezdxf, sys, math, pickle
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S1": (36225, 120325), "S3": (-139272, -55172), "S5": (-307472, -223372),
         "S6": (-391572, -307472), "S7": (-475672, -391572)}
def band(y):
    for n, (a, b) in BANDS.items():
        if a <= y <= b: return n
    return None

print("=== 施工图板区边界 LWPOLYLINE by band ===")
polys7 = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer != "施工图板区边界": continue
    pts = [(p[0], p[1]) for p in e.get_points("xy")]
    cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
    if not (X0 <= cx <= X1): continue
    b = band(cy)
    try:
        pg = Polygon(pts)
        a = pg.area/1e6
    except Exception:
        a = -1
    print(f"  band={b} cy={cy:.0f} closed={e.closed} npts={len(pts)} area={a:.1f} m2 perim={pg.length/1000:.1f} m")
    if b == "S3" and e.closed:
        # translate S3 -> S7 using anchors
        ANCH = {"S3": (-4711895, -67087), "S7": (-4711816, -404432)}
        pg7 = translate(pg, xoff=ANCH["S7"][0]-ANCH["S3"][0], yoff=ANCH["S7"][1]-ANCH["S3"][1])
        polys7.append(("S3->S7", pg7))

# net slab calc using S7 boundary
for bnd, pg in polys7[:1]:
    print(f"\n=== using {bnd} boundary: gross={pg.area/1e6:.1f} m2 ===")
    dy = 0
    # recompute marks quickly
    diags = []
    SY0, SY1 = BANDS["S7"]
    for e in msp.query("LINE"):
        if e.dxf.layer != "板洞边线": continue
        x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
        cx, cy = (x1+x2)/2, (y1+y2)/2
        if not (X0 <= cx <= X1 and SY0 <= cy <= SY1): continue
        ang = math.degrees(math.atan2(y2-y1, x2-x1)) % 180
        if ang < 2 or ang > 178 or 88 < ang < 92: continue
        diags.append([(x1, y1), (x2, y2), cx, cy])
    used = [False]*len(diags)
    def close(p, q, tol=80): return abs(p[0]-q[0]) < tol and abs(p[1]-q[1]) < tol
    Xs, bents = [], []
    for i in range(len(diags)):
        if used[i]: continue
        for j in range(i+1, len(diags)):
            if used[j]: continue
            if abs(diags[j][2]-diags[i][2]) < 200 and abs(diags[j][3]-diags[i][3]) < 200:
                xs = [diags[i][0][0], diags[i][1][0], diags[j][0][0], diags[j][1][0]]
                ys = [diags[i][0][1], diags[i][1][1], diags[j][0][1], diags[j][1][1]]
                Xs.append(box(min(xs), min(ys), max(xs), max(ys))); used[i] = used[j] = True; break
        if used[i]: continue
        for j in range(i+1, len(diags)):
            if used[j]: continue
            if any(close(diags[i][a], diags[j][b2]) for a in (0, 1) for b2 in (0, 1)):
                xs = [diags[i][0][0], diags[i][1][0], diags[j][0][0], diags[j][1][0]]
                ys = [diags[i][0][1], diags[i][1][1], diags[j][0][1], diags[j][1][1]]
                bents.append(box(min(xs), min(ys), max(xs), max(ys))); used[i] = used[j] = True; break
    pgs = pg
    print("  -- permanent holes vs boundary --")
    ap = at = 0.0
    for nm, lst in (("PERM", bents), ("TEMP", Xs)):
        n_in = n_part = n_out = 0
        for h in lst:
            ia = h.intersection(pgs).area/1e6
            fa = h.area/1e6
            if ia > 0.99*fa: n_in += 1
            elif ia > 0.01*fa: n_part += 1
            else: n_out += 1
            if nm == "PERM": ap += ia
            else: at += ia
            if ia > 0.01*fa and ia < 0.99*fa:
                b = h.bounds
                print(f"    {nm} partial: full={fa:.1f} clip={ia:.1f} bbox=({(b[2]-b[0])/1000:.1f}x{(b[3]-b[1])/1000:.1f})")
        print(f"  {nm}: fully_in={n_in} partial={n_part} outside={n_out}")
    print(f"  perm clipped total={ap:.2f} m2; temp clipped total={at:.2f} m2")
    print(f"  net slab = {pg.area/1e6:.1f} - {ap:.1f} - {at:.1f} = {pg.area/1e6-ap-at:.1f} m2")
    # also: how much of boundary is outside basement enclosure
    enc7 = translate(enc5, xoff=ANCH["S7"][0]-(-4718640), yoff=ANCH["S7"][1]-(-231423)) if False else None
