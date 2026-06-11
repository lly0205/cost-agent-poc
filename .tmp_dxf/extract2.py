# -*- coding: utf-8 -*-
import ezdxf, sys, re, collections, math, pickle
from ezdxf import bbox
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from shapely.affinity import translate
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
        if y0 <= y <= y1: return n
    return None

# ========== A. axis bubbles in S3: number + position ==========
print("=== A. axis bubbles (S3) ===")
ax_s3 = []
for e in msp.query("INSERT"):
    if e.dxf.name == "_AXISO":
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
        cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
        if not (X0 <= cx <= X1): continue
        b = band(cy)
        if b != "S3": continue
        num = None
        for a in e.attribs:
            num = a.dxf.text
        ax_s3.append((num, cx, cy))
xa = sorted([(n, x) for n, x, y in ax_s3 if y < -120000 or y > -62000], key=lambda t: t[1])
# horizontal axes (letters) on left/right side, vertical axes (numbers) top/bottom
# classify: bubbles near left edge -> letter axes (horizontal grid lines); near bottom/top -> number axes
xs = [x for _, x, _ in ax_s3]; ys = [y for _, _, y in ax_s3]
for n, x, y in sorted(ax_s3, key=lambda t: (t[2], t[1])):
    print(f"  {n}: ({x:.0f}, {y:.0f})")

# ========== B. expansion band (膨胀加强带) in S3 ==========
print("\n=== B. entities near 膨胀加强带 labels ===")
LBL = [(-4828879, -90228), (-4828879, -90634)]
for e in msp:
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
    except Exception:
        continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    for lx, ly in LBL:
        if abs(cx-lx) < 4000 and abs(cy-ly) < 4000:
            t = e.dxftype()
            extra = e.dxf.text if t == "TEXT" else (e.dxf.name if t == "INSERT" else "")
            w = ext.extmax.x-ext.extmin.x; h = ext.extmax.y-ext.extmin.y
            print(f"  {t} layer={e.dxf.layer} c=({cx:.0f},{cy:.0f}) size={w:.0f}x{h:.0f} {extra}")
            break

# layer "4" entities in S3 (label layer) - the band lines may live on layer 4
print("\n--- layer '4' entities in S3 ---")
cnt4 = collections.Counter()
items4 = []
for e in msp:
    if e.dxf.layer != "4": continue
    try:
        ext = bbox.extents([e], fast=True)
        if not ext.has_data: continue
    except Exception: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if X0 <= cx <= X1 and band(cy) == "S3":
        t = e.dxftype()
        cnt4[t] += 1
        w = ext.extmax.x-ext.extmin.x; h = ext.extmax.y-ext.extmin.y
        items4.append((t, cx, cy, w, h, e))
print("  count:", dict(cnt4))
for t, cx, cy, w, h, e in items4:
    if t in ("LINE", "LWPOLYLINE") and max(w, h) > 2000:
        print(f"  {t} c=({cx:.0f},{cy:.0f}) size={w:.0f}x{h:.0f}")

# ========== C. sumps (集水坑) in S3: size + nearest JSK + zone ==========
print("\n=== C. sumps in S3 ===")
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
hatch3 = None
for e in msp.query("HATCH"):
    if e.dxf.layer == "看线":
        for p in e.paths:
            if hasattr(p, "vertices"):
                pts = [(v[0], v[1]) for v in p.vertices]
                if len(pts) >= 3:
                    poly = Polygon(pts)
                    c = poly.centroid
                    if X0 <= c.x <= X1 and band(c.y) == "S3" and poly.area/1e6 > 1000:
                        hatch3 = poly
JSK = [(-4801299,-68626),(-4733793,-78111),(-4795649,-81126),(-4801299,-97726),(-4787170,-113507),(-4801487,-117094)]
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer != "集水坑": continue
    pts = [(p[0], p[1]) for p in e.get_points("xy")]
    cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
    if not (X0 <= cx <= X1 and band(cy) == "S3"): continue
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    w = max(xs)-min(xs); h = max(ys)-min(ys)
    poly = Polygon(pts)
    zone = "DEEP(-6.5)" if hatch3.buffer(300).contains(Point(cx, cy)) else "SHALLOW(-4.8)"
    dj = min(math.hypot(cx-jx, cy-jy) for jx, jy in JSK)
    print(f"  pit c=({cx:.0f},{cy:.0f}) bbox={w:.0f}x{h:.0f} area={poly.area/1e6:.2f}m2 perim={poly.length/1000:.2f}m zone={zone} nearestJSK={dj:.0f}mm")

# ========== D. deep-zone hatch boundary ==========
print("\n=== D. deep zone (hatch3) ===")
print(f"  area={hatch3.area/1e6:.1f} m2, perim={hatch3.length/1000:.1f} m")
b = hatch3.bounds
print(f"  bounds x:[{b[0]:.0f},{b[2]:.0f}] y:[{b[1]:.0f},{b[3]:.0f}]")
# boundary segments list (long ones)
coords = list(hatch3.exterior.coords)
print("  exterior vertices:")
for p in coords:
    print(f"    ({p[0]:.0f},{p[1]:.0f})")

# ========== E. walls in S5 with segment detail ==========
print("\n=== E. wall segments (S5) ===")
wl = []
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙" and X0 <= e.dxf.start.x <= X1 and band(e.dxf.start.y) == "S5":
        wl.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
H = [l for l in wl if abs(l[0][1]-l[1][1]) < 1]
V = [l for l in wl if abs(l[0][0]-l[1][0]) < 1]
def pair_lines(lines, horiz):
    items = []
    for (p1, p2) in lines:
        if horiz: items.append((p1[1], min(p1[0], p2[0]), max(p1[0], p2[0])))
        else: items.append((p1[0], min(p1[1], p2[1]), max(p1[1], p2[1])))
    items.sort(); out = []
    for i in range(len(items)):
        ci, a0, a1 = items[i]
        for j in range(i+1, len(items)):
            cj, b0, b1 = items[j]
            w = cj-ci
            if w > 600: break
            if w < 100: continue
            ov0, ov1 = max(a0, b0), min(a1, b1)
            if ov1-ov0 > 500: out.append(((ci+cj)/2, round(w,-1), ov0, ov1))
    return out
def dedupe(strips):
    d = collections.defaultdict(list)
    for c, w, a0, a1 in strips:
        d[(round(c,-1), w)].append((a0, a1))
    out = []
    for (c, w), segs in d.items():
        segs.sort(); m = []
        for a0, a1 in segs:
            if m and a0 <= m[-1][1]+50: m[-1][1] = max(m[-1][1], a1)
            else: m.append([a0, a1])
        for a0, a1 in m: out.append((c, w, a0, a1))
    return out
wh = dedupe(pair_lines(H, True)); wv = dedupe(pair_lines(V, False))
labels = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "0" and X0 <= e.dxf.insert.x <= X1 and band(e.dxf.insert.y) == "S5":
        if re.match(r"^(DWQ\d|SCQ\d)$", e.dxf.text.strip()):
            labels.append((e.dxf.insert.x, e.dxf.insert.y, e.dxf.text.strip()))
hatch5 = translate(hatch3, yoff=BANDS["S5"][0]-BANDS["S3"][0])  # approx; refine with anchors
# anchors from boq_calc3: S3 (-4711895,-67087)  S5 (-4718640,-231423)
dx = -4718640 - (-4711895); dy = -231423 - (-67087)
hatch5 = translate(hatch3, xoff=dx, yoff=dy)
print("  segments: orient center width from..to len(m) label zone")
for strips, horiz in ((wh, True), (wv, False)):
    for c, w, a0, a1 in sorted(strips, key=lambda s: -(s[3]-s[2])):
        L = (a1-a0)/1000
        if L < 0.8: continue
        mid = ((a0+a1)/2, c) if horiz else (c, (a0+a1)/2)
        best, bd = None, 1e18
        for lx, ly, lt in labels:
            d = (lx-mid[0])**2 + (ly-mid[1])**2
            if d < bd: bd, best = d, lt
        zone = "DEEP" if hatch5.buffer(500).contains(Point(mid)) else "SHALLOW"
        o = "H" if horiz else "V"
        print(f"  {o} c={c:.0f} w={w:.0f} [{a0:.0f}..{a1:.0f}] L={L:.1f}m {best} d={math.sqrt(bd):.0f} {zone}")
