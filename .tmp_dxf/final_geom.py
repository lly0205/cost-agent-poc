# -*- coding: utf-8 -*-
import ezdxf, sys, math, re, collections
from shapely.geometry import LineString, Polygon, Point, MultiLineString
from shapely.ops import unary_union, polygonize
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

# ============ 1. basement wall centerlines (S5) ============
wl = []
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙" and X0 <= e.dxf.start.x <= X1 and band(e.dxf.start.y) == "S5":
        wl.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))

H = [l for l in wl if abs(l[0][1]-l[1][1]) < 1]
V = [l for l in wl if abs(l[0][0]-l[1][0]) < 1]

def pair_lines(lines, horiz):
    # returns centerline segments (c, w, a0, a1)
    items = []
    for (p1, p2) in lines:
        if horiz:
            items.append((p1[1], min(p1[0], p2[0]), max(p1[0], p2[0])))
        else:
            items.append((p1[0], min(p1[1], p2[1]), max(p1[1], p2[1])))
    items.sort()
    used = [False]*len(items)
    out = []
    for i in range(len(items)):
        ci, a0, a1 = items[i]
        for j in range(i+1, len(items)):
            cj, b0, b1 = items[j]
            w = cj - ci
            if w > 600: break
            if w < 100: continue
            ov0, ov1 = max(a0, b0), min(a1, b1)
            if ov1-ov0 > 500:
                out.append(((ci+cj)/2, round(w, -1), ov0, ov1))
    return out

wh = pair_lines(H, True)
wv = pair_lines(V, False)
# merge duplicates
def dedupe(strips):
    d = collections.defaultdict(list)
    for c, w, a0, a1 in strips:
        d[(round(c, -1), w)].append((a0, a1))
    out = []
    for (c, w), segs in d.items():
        segs.sort()
        m = []
        for a0, a1 in segs:
            if m and a0 <= m[-1][1]+50: m[-1][1] = max(m[-1][1], a1)
            else: m.append([a0, a1])
        for a0, a1 in m:
            out.append((c, w, a0, a1))
    return out
wh, wv = dedupe(wh), dedupe(wv)
wt = collections.Counter()
wall_lines = []
for c, w, a0, a1 in wh:
    wt[w] += (a1-a0)/1000
    wall_lines.append(LineString([(a0, c), (a1, c)]))
for c, w, a0, a1 in wv:
    wt[w] += (a1-a0)/1000
    wall_lines.append(LineString([(c, a0), (c, a1)]))
print("=== wall centerline length by thickness (m):", {k: round(v,1) for k,v in wt.items()})
print("total centerline:", round(sum(wt.values()),1), "m")

# wall DWQ label matching
labels = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "0" and X0 <= e.dxf.insert.x <= X1 and band(e.dxf.insert.y) == "S5":
        if re.match(r"^(DWQ\d|SCQ\d)$", e.dxf.text.strip()):
            labels.append((e.dxf.insert.x, e.dxf.insert.y, e.dxf.text.strip()))
lab_len = collections.Counter()
for c, w, a0, a1 in wh + wv:
    horiz = (c, w, a0, a1) in wh
    mid = ((a0+a1)/2, c) if horiz else (c, (a0+a1)/2)
    best, bd = None, 1e18
    for lx, ly, lt in labels:
        d = (lx-mid[0])**2 + (ly-mid[1])**2
        if d < bd: bd, best = d, lt
    lab_len[(best, w)] += (a1-a0)/1000
print("=== wall length by (label, thickness):")
for k in sorted(lab_len, key=str):
    print(f"  {k}: {lab_len[k]:.1f} m")

# basement polygon via buffered union holes
buf = unary_union([l.buffer(250, cap_style=2) for l in wall_lines])
polys = list(buf.geoms) if buf.geom_type == "MultiPolygon" else [buf]
big = max(polys, key=lambda p: p.area)
outer = Polygon(big.exterior)
print(f"=== basement outer-face area approx: {outer.area/1e6:.0f} m2 (incl wall buffer)")
holes = [Polygon(r) for r in big.interiors]
holes_area = sum(h.area for h in holes)
print(f"    interior holes: {len(holes)}, area {holes_area/1e6:.0f} m2")
basement = outer  # zone polygon for in/out tests

# ============ 2. footprint polygon (S3 施工图板区边界) ============
fp = None
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "施工图板区边界":
        pts = e.get_points("xy")
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S3":
            fp = Polygon([(p[0], p[1]) for p in pts])
print(f"=== footprint: area {fp.area/1e6:.1f} m2, perim {fp.length/1000:.1f} m")
# move basement polygon offset: S5 vs S3 sheets are stacked: same x, y offset = -307472-(-139272)
dy_53 = 0
# basement coords are in S5; footprint in S3. shift basement up by (S3 band - S5 band)
shift = (BANDS["S3"][0] - BANDS["S5"][0])
from shapely.affinity import translate
basement_s3 = translate(basement, yoff=shift)
print(f"    basement zone area (outer): {basement_s3.area/1e6:.0f} m2; share of footprint: {basement_s3.intersection(fp).area/fp.area*100:.0f}%")

# ============ 3. caps per type: polygon area/perimeter + zone ============
ctpos = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "承台集中标注" and e.dxf.text.startswith("CT"):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S3":
            ctpos.append((x, y, e.dxf.text))
caps = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S3":
            caps.append(Polygon(pts))
capdata = collections.defaultdict(list)
for cp in caps:
    c = cp.centroid
    best, bd = None, 1e18
    for tx, ty, name in ctpos:
        d = (tx-c.x)**2 + (ty-c.y)**2
        if d < bd: bd, best = d, name
    capdata[best].append(cp)
print("\n=== caps: type, count, area(m2), perim(m), inside-basement count ===")
for name in sorted(capdata):
    cps = capdata[name]
    areas = [c.area/1e6 for c in cps]
    pers = [c.length/1000 for c in cps]
    inb = sum(1 for c in cps if basement.contains(translate(c.centroid, yoff=-shift)) is False and basement_s3.contains(c.centroid))
    print(f"  {name}: n={len(cps)} area={sum(areas)/len(areas):.2f} perim={sum(pers)/len(pers):.2f} in_basement={inb}")

# ============ 4. columns zone (S5 柱集中标注) ============
kzin, kzout = collections.Counter(), collections.Counter()
for e in msp.query("TEXT"):
    if e.dxf.layer == "柱集中标注":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S5":
            name = re.sub(r"\(.*\)", "", e.dxf.text)
            if basement.contains(Point(x, y)) or basement.distance(Point(x, y)) < 1500:
                kzin[name] += 1
            else:
                kzout[name] += 1
print(f"\n=== columns: inside basement {sum(kzin.values())}, outside {sum(kzout.values())}")
print("  outside:", dict(kzout))

# ============ 5. beams zone split (S6) ============
shift65 = BANDS["S6"][0] - BANDS["S5"][0]
basement_s6 = translate(basement, yoff=shift65)
# reuse beam strips quickly
def get_beam_strips():
    SY0, SY1 = BANDS["S6"]
    Hl, Vl = [], []
    for e in msp.query("LINE"):
        if e.dxf.layer in ("BEAM", "BEAM_CON"):
            x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
            if not (X0 <= x1 <= X1 and SY0 <= y1 <= SY1): continue
            if abs(y1-y2) < 1: Hl.append(((x1, y1), (x2, y2)))
            elif abs(x1-x2) < 1: Vl.append(((x1, y1), (x2, y2)))
    hs = dedupe(pair_lines(Hl, True))
    vs = dedupe(pair_lines(Vl, False))
    return hs, vs
hs, vs = get_beam_strips()
marks = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "梁名称编号":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S6":
            marks.append((x, y, round(e.dxf.rotation) % 180, e.dxf.text.strip()))

def msec(t):
    p = t.split()
    return p[1] if len(p) > 1 else None

agg = collections.defaultdict(lambda: [0.0, 0.0])  # (type,sec) -> [len_in, len_out]
unm = [0.0, 0.0]
for strips, horiz in ((hs, True), (vs, False)):
    for c, w, a0, a1 in strips:
        ls = LineString([(a0, c), (a1, c)]) if horiz else LineString([(c, a0), (c, a1)])
        Lin = ls.intersection(basement_s6).length/1000
        Lout = ls.length/1000 - Lin
        # match mark: same orientation AND same width
        best, bd = None, 1e18
        for x, y, r, t in marks:
            isH = (r == 0)
            if isH != horiz: continue
            sec = msec(t)
            if sec and int(sec.split("x")[0]) != w: continue
            if horiz:
                d = abs(y-c)*2 + (0 if a0-2000 <= x <= a1+2000 else min(abs(x-a0), abs(x-a1)))
            else:
                d = abs(x-c)*2 + (0 if a0-2000 <= y <= a1+2000 else min(abs(y-a0), abs(y-a1)))
            if d < bd: bd, best = d, t
        if best and bd < 25000:
            typ = "KL" if best.startswith("KL") else ("WKL" if best.startswith("WKL") else "L")
            agg[(typ, msec(best))][0] += Lin
            agg[(typ, msec(best))][1] += Lout
        else:
            unm[0] += Lin; unm[1] += Lout
print("\n=== beam gross length by (type, section): [in_basement, outside] m ===")
ti = to = 0
for k in sorted(agg, key=str):
    print(f"  {k}: in={agg[k][0]:.1f} out={agg[k][1]:.1f}")
    ti += agg[k][0]; to += agg[k][1]
print(f"  matched totals: in={ti:.1f} out={to:.1f}; unmatched: in={unm[0]:.1f} out={unm[1]:.1f}")

# ============ 6. slab openings S7 ============
SY0, SY1 = BANDS["S7"]
op = []
for e in msp.query("LINE"):
    if e.dxf.layer == "板洞边线" and X0 <= e.dxf.start.x <= X1 and SY0 <= e.dxf.start.y <= SY1:
        op.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
mp = unary_union([l.buffer(10) for l in op])
gs = list(mp.geoms) if mp.geom_type == "MultiPolygon" else [mp]
print(f"\n=== slab openings (S7 板洞边线): {len(op)} lines, {len(gs)} clusters")
tot_open = 0
for g in gs:
    b = g.bounds
    a = (b[2]-b[0])*(b[3]-b[1])/1e6
    tot_open += a
    print(f"  bbox {(b[2]-b[0])/1000:.1f} x {(b[3]-b[1])/1000:.1f} m ~= {a:.1f} m2")
print(f"  total approx opening area: {tot_open:.1f} m2")
