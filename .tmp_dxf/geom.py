# -*- coding: utf-8 -*-
import ezdxf, sys, math, collections
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
BANDS = {"S1": (36225, 120325), "S2": (-55172, 28928), "S3": (-139272, -55172),
         "S4": (-223372, -139272), "S5": (-307472, -223372),
         "S6": (-391572, -307472), "S7": (-475672, -391572)}
def band(y):
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1:
            return n
    return None

def poly_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i][0], pts[i][1]
        x2, y2 = pts[(i+1) % len(pts)][0], pts[(i+1) % len(pts)][1]
        a += x1*y2 - x2*y1
    return abs(a) / 2

def perim(pts, closed=True):
    p = 0.0
    n = len(pts)
    rng = range(n) if closed else range(n-1)
    for i in rng:
        x1, y1 = pts[i][0], pts[i][1]
        x2, y2 = pts[(i+1) % n][0], pts[(i+1) % n][1]
        p += math.hypot(x2-x1, y2-y1)
    return p

print("=== 施工图板区边界 / 看线 / 立剖外轮廓线 polylines ===")
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer in ("施工图板区边界", "看线", "立剖外轮廓线"):
        pts = e.get_points("xy")
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        b = band(cy) if X0 <= cx <= X1 else None
        if b:
            print(f"{b}\t{e.dxf.layer}\tnpts={len(pts)}\tclosed={e.closed}\tarea={poly_area(pts)/1e6:.1f}m2\tperim={perim(pts, e.closed)/1000:.1f}m")

print("\n=== 集水坑 polylines (S2/S3) ===")
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "集水坑":
        pts = e.get_points("xy")
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        b = band(cy) if X0 <= cx <= X1 else None
        if b:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            print(f"{b}\tnpts={len(pts)}\tclosed={e.closed}\tdx={max(xs)-min(xs):.0f}\tdy={max(ys)-min(ys):.0f}\tarea={poly_area(pts)/1e6:.2f}m2")

print("\n=== 砼墙 lines summary per sheet ===")
walls = collections.defaultdict(list)
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙":
        x, y = e.dxf.start.x, e.dxf.start.y
        b = band(y) if X0 <= x <= X1 else None
        if b:
            walls[b].append((e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y))
for b, ls in sorted(walls.items()):
    tot = sum(math.hypot(x2-x1, y2-y1) for x1, y1, x2, y2 in ls)
    print(f"{b}: {len(ls)} lines, total len={tot/1000:.1f}m")

# wall thickness distribution in S5: pair parallel lines
ls = walls.get("S5", [])
H = [l for l in ls if abs(l[1]-l[3]) < 1]   # horizontal
V = [l for l in ls if abs(l[0]-l[2]) < 1]   # vertical
print(f"S5 walls: H={len(H)} V={len(V)} other={len(ls)-len(H)-len(V)}")
thick = collections.Counter()
for i, a in enumerate(H):
    ax0, ax1 = sorted((a[0], a[2]))
    for bln in H[i+1:]:
        bx0, bx1 = sorted((bln[0], bln[2]))
        dy = abs(a[1]-bln[1])
        ov = min(ax1, bx1) - max(ax0, bx0)
        if 100 <= dy <= 800 and ov > 1000:
            thick[round(dy, -1)] += 1
for v in V:
    pass
print("H-pair dy distribution:", dict(thick.most_common(10)))

# wall centerline length estimate: total/2 per orientation
totH = sum(abs(l[0]-l[2]) for l in H)
totV = sum(abs(l[1]-l[3]) for l in V)
print(f"S5 wall line len: H={totH/1000:.1f}m V={totV/1000:.1f}m sum={(totH+totV)/1000:.1f}m -> centerline approx {(totH+totV)/2000:.1f}m")

print("\n=== S5 wall bbox (extent of basement zone) ===")
if ls:
    xs = [l[0] for l in ls] + [l[2] for l in ls]
    ys = [l[1] for l in ls] + [l[3] for l in ls]
    print(f"x: {min(xs):.0f}..{max(xs):.0f} ({(max(xs)-min(xs))/1000:.1f}m)  y: {min(ys):.0f}..{max(ys):.0f} ({(max(ys)-min(ys))/1000:.1f}m)")

print("\n=== AXIS extent S6 (whole building grid) ===")
ax = [e for e in msp.query("LINE") if e.dxf.layer == "AXIS" and X0 <= e.dxf.start.x <= X1 and band(e.dxf.start.y) == "S6"]
xs = []; ys = []
for e in ax:
    xs += [e.dxf.start.x, e.dxf.end.x]; ys += [e.dxf.start.y, e.dxf.end.y]
if xs:
    print(f"x span {(max(xs)-min(xs))/1000:.1f}m, y span {(max(ys)-min(ys))/1000:.1f}m")

print("\n=== DIM texts in S4 detail zone (DWQ walls y<-190000) ===")
def dim_text(e):
    blk = e.get_geometry_block()
    if blk:
        for ve in blk:
            if ve.dxftype() == "TEXT":
                return ve.dxf.text
            if ve.dxftype() == "MTEXT":
                return ve.plain_text()
    return ""
rows = []
for e in msp.query("DIMENSION"):
    p = e.dxf.defpoint
    if X0 <= p.x <= X1 and band(p.y) == "S4" and p.y < -190000:
        rows.append((p.x, p.y, e.dxf.layer, dim_text(e)))
rows.sort(key=lambda r: (-r[1], r[0]))
for x, y, l, t in rows:
    print(f"{x:.0f}\t{y:.0f}\t{l}\t{t}")
