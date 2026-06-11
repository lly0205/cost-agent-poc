# -*- coding: utf-8 -*-
import ezdxf, sys, re, collections, pickle, math
from shapely.geometry import Polygon, Point, LineString
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
    for n, (y0, y1) in BANDS.items():
        if y0 <= y <= y1: return n
    return None

with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc3 = translate(enc5, yoff=BANDS["S3"][0]-BANDS["S5"][0])
enc6 = translate(enc5, yoff=BANDS["S6"][0]-BANDS["S5"][0])

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
hatch5 = translate(hatch3, yoff=BANDS["S5"][0]-BANDS["S3"][0])
hatch6 = translate(hatch3, yoff=BANDS["S6"][0]-BANDS["S3"][0])
shallow_area = enc3.area - enc3.intersection(hatch3).area
print(f"raft zones: deep={hatch3.area/1e6:.1f} m2, shallow={shallow_area/1e6:.1f} m2, enclosure={enc3.area/1e6:.1f} m2, enc perim={enc3.length/1000:.1f} m, deep perim={hatch3.length/1000:.1f} m")
shared = hatch3.exterior.intersection(enc3.buffer(-500)).length/1000
print(f"deep/shallow internal step length approx: {shared:.1f} m")

SEC = {"KZ1":(500,500),"KZ2":(400,400),"KZ3":(500,500),"KZ4":(500,500),"KZ5":(600,500),
"KZ6":(500,500),"KZ7":(500,600),"KZ8":(500,500),"KZ9":(400,400),"KZ10":(500,500),
"KZ11":(500,500),"KZ12":(600,600),"KZ13":(500,500),"KZ14":(600,600),"KZ15":(600,600),
"KZ16":(500,500),"KZ17":(500,600),"KZ18":(500,500),"KZ19":(700,700),"KZ20":(600,700),
"KZ21":(700,600),"KZ22":(500,600),"KZ23":(600,700),"KZ24":(500,500),"KZ25":(400,500),
"KZ26":(500,500),"KZ27":(500,600),"KZ28":(600,600),"KZ29":(600,650),"KZ30":(500,500),
"KZ31":(600,700),"KZ32":(600,600),"KZ33":(600,600),"KZ34":(700,700),"KZ35":(600,600),
"KZ36":(550,500),"KZ37":(500,600),"KZ38":(650,600),"KZ39":(550,600),"KZ40":(550,500),
"KZ41":(600,700),"KZ42":(500,600),"KZ43":(600,650),"KZ44":(600,600),"KZ45":(600,700),
"KZ46":(500,500),"KZ47":(600,700),"KZ48":(600,600),"KZ49":(600,600),"KZ50":(500,600)}

# ---- columns 3-way ----
cols = collections.Counter()
for e in msp.query("TEXT"):
    if e.dxf.layer == "柱集中标注":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S5":
            name = re.sub(r"\(.*\)", "", e.dxf.text).strip()
            p = Point(x, y)
            zone = "DEEP" if hatch5.contains(p) else ("SHALLOW" if enc5.contains(p) else "PERIM")
            cols[(name, zone)] += 1
HZ = {"DEEP": 6.22, "SHALLOW": 4.52, "PERIM": 0.22}
vol = collections.defaultdict(float); fw = collections.defaultdict(float)
cnt = collections.Counter()
det = collections.defaultdict(list)
for (name, zone), n in cols.items():
    b, h = SEC.get(name, (550, 550))
    vol[zone] += n * b/1000 * h/1000 * HZ[zone]
    fw[zone] += n * 2*(b+h)/1000 * HZ[zone]
    cnt[zone] += n
    det[zone].append(f"{name} {b}x{h} x{n}")
print("\n=== columns ===")
for z in ("DEEP", "SHALLOW", "PERIM"):
    print(f"{z}: n={cnt[z]} H={HZ[z]} vol={vol[z]:.2f} m3 formwork={fw[z]:.1f} m2")
    print("   ", "; ".join(sorted(det[z])))

# ---- beams ----
def pair_lines(items_raw, horiz):
    items = []
    for (p1, p2) in items_raw:
        if horiz: items.append((p1[1], min(p1[0], p2[0]), max(p1[0], p2[0])))
        else: items.append((p1[0], min(p1[1], p2[1]), max(p1[1], p2[1])))
    items.sort()
    out = []
    for i in range(len(items)):
        ci, a0, a1 = items[i]
        for j in range(i+1, len(items)):
            cj, b0, b1 = items[j]
            w = cj-ci
            if w > 600: break
            if w < 100: continue
            ov0, ov1 = max(a0, b0), min(a1, b1)
            if ov1-ov0 > 600:
                out.append(((ci+cj)/2, round(w,-1), ov0, ov1))
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

SY = BANDS["S6"]
Hl, Vl = [], []
for e in msp.query("LINE"):
    if e.dxf.layer in ("BEAM", "BEAM_CON"):
        x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
        if not (X0 <= x1 <= X1 and SY[0] <= y1 <= SY[1]): continue
        if abs(y1-y2) < 1: Hl.append(((x1, y1), (x2, y2)))
        elif abs(x1-x2) < 1: Vl.append(((x1, y1), (x2, y2)))
hs = dedupe(pair_lines(Hl, True)); vs = dedupe(pair_lines(Vl, False))

# columns footprints in S6 for crossing deduction
colpolys = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "COLU":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S6":
            try: colpolys.append(Polygon(pts).buffer(0))
            except Exception: pass
colu = unary_union(colpolys)
print(f"\ncolumns in S6: {len(colpolys)}")

marks = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "梁名称编号":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S6":
            marks.append((x, y, round(e.dxf.rotation) % 180, e.dxf.text.strip()))
def msec(t):
    p = t.split()
    return p[1] if len(p) > 1 else None

agg = collections.defaultdict(lambda: [0.0, 0.0])  # (KL/L, sec) -> [in, out] net len
unmatched = [0.0, 0.0]
for strips, horiz in ((hs, True), (vs, False)):
    for c, w, a0, a1 in strips:
        ls = LineString([(a0, c), (a1, c)]) if horiz else LineString([(c, a0), (c, a1)])
        net = ls.difference(colu)
        Lin = net.intersection(enc6).length/1000
        Lout = net.length/1000 - Lin
        best, bd = None, 1e18
        for x, y, r, t in marks:
            if ((r == 0) != horiz): continue
            sec = msec(t)
            if sec and int(sec.split("x")[0]) != w: continue
            if horiz: d = abs(y-c)*2 + (0 if a0-2000 <= x <= a1+2000 else min(abs(x-a0), abs(x-a1)))
            else: d = abs(x-c)*2 + (0 if a0-2000 <= y <= a1+2000 else min(abs(y-a0), abs(y-a1)))
            if d < bd: bd, best = d, t
        if best and bd < 30000:
            typ = "KL" if best.startswith("KL") else ("WKL" if best.startswith("WKL") else "L")
            key = (typ, msec(best))
            agg[key][0] += Lin; agg[key][1] += Lout
        else:
            sec = f"{w}x?"
            agg[("UNK", sec)][0] += Lin; agg[("UNK", sec)][1] += Lout
print("\n=== beam NET length by (type, section): [in_enclosure, outside] m ===")
ti = to = vin = vout = vrib = 0
for k in sorted(agg, key=str):
    Lin, Lout = agg[k]
    print(f"  {k[0]} {k[1]}: in={Lin:.1f} out={Lout:.1f}")
    ti += Lin; to += Lout
    try:
        b, h = (int(v) for v in k[1].split("x"))
        vin += Lin * b/1000 * h/1000
        vout += Lout * b/1000 * h/1000
        vrib += Lin * b/1000 * (h-180)/1000
    except Exception:
        pass
print(f"totals: net len in={ti:.1f} m out={to:.1f} m")
print(f"volume full-section: in={vin:.1f} m3 out={vout:.1f} m3 ; rib(in, h-180)={vrib:.1f} m3")

# formwork beams: in => rib sides 2*(h-180)*L ; out (基础梁) => 2*h*L
fw_in = fw_out = bot_in = 0
for k, (Lin, Lout) in agg.items():
    try:
        b, h = (int(v) for v in k[1].split("x"))
    except Exception:
        continue
    fw_in += 2 * (h-180)/1000 * Lin
    fw_out += 2 * h/1000 * Lout
    bot_in += b/1000 * Lin
print(f"formwork: in rib sides={fw_in:.1f} m2 (+beam bottoms {bot_in:.1f} m2), out 2 sides={fw_out:.1f} m2")

# ---- slab openings S7 ----
SY7 = BANDS["S7"]
op = []
for e in msp.query("LINE"):
    if e.dxf.layer == "板洞边线" and X0 <= e.dxf.start.x <= X1 and SY7[0] <= e.dxf.start.y <= SY7[1]:
        op.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
mp = unary_union([l.buffer(10) for l in op])
gs = list(mp.geoms) if mp.geom_type == "MultiPolygon" else [mp]
tot_open = 0
print(f"\n=== slab openings: {len(gs)} clusters ===")
for g in gs:
    b = g.bounds
    a = (b[2]-b[0])*(b[3]-b[1])/1e6
    if a > 0.09:
        tot_open += a
        print(f"  {(b[2]-b[0])/1000:.2f} x {(b[3]-b[1])/1000:.2f} = {a:.2f} m2")
print(f"total openings: {tot_open:.1f} m2")

# wall length adjacency to hatch (S5): split heights
wlen_deep = collections.Counter(); wlen_shallow = collections.Counter()
wl = []
for e in msp.query("LINE"):
    if e.dxf.layer == "砼墙" and X0 <= e.dxf.start.x <= X1 and band(e.dxf.start.y) == "S5":
        wl.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
H = [l for l in wl if abs(l[0][1]-l[1][1]) < 1]; V = [l for l in wl if abs(l[0][0]-l[1][0]) < 1]
hb = hatch5.boundary
for strips, horiz in ((dedupe(pair_lines(H, True)), True), (dedupe(pair_lines(V, False)), False)):
    for c, w, a0, a1 in strips:
        ls = LineString([(a0, c), (a1, c)]) if horiz else LineString([(c, a0), (c, a1)])
        L = ls.length/1000
        if ls.distance(hb) < 600:
            wlen_deep[w] += L
        else:
            wlen_shallow[w] += L
print(f"\n=== walls near deep boundary: {dict(wlen_deep)} (h=6.4) ; others: {dict(wlen_shallow)} (h=4.7)")
