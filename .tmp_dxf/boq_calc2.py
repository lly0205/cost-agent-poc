# -*- coding: utf-8 -*-
import ezdxf, sys, re, collections, pickle
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

# exact wall-bbox anchors (xmax, ymax) per sheet
ANCH = {"S1": (-4711895, 108410), "S3": (-4711895, -67087), "S5": (-4718640, -231423),
        "S6": (-4711895, -322585), "S7": (-4711816, -404432)}
def tr(geom, src, dst):
    return translate(geom, xoff=ANCH[dst][0]-ANCH[src][0], yoff=ANCH[dst][1]-ANCH[src][1])

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
hatch5 = tr(hatch3, "S3", "S5")
enc3 = tr(enc5, "S5", "S3")
enc6 = tr(enc5, "S5", "S6")
hatch6 = tr(hatch3, "S3", "S6")
print(f"deep={hatch3.area/1e6:.1f} shallow={enc3.area/1e6 - enc3.intersection(hatch3).area/1e6:.1f} enclosure={enc3.area/1e6:.1f}")

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

cols = collections.Counter()
for e in msp.query("TEXT"):
    if e.dxf.layer == "柱集中标注":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S5":
            name = re.sub(r"\(.*\)", "", e.dxf.text).strip()
            p = Point(x, y)
            zone = "DEEP" if hatch5.buffer(500).contains(p) else ("SHALLOW" if enc5.buffer(500).contains(p) else "PERIM")
            cols[(name, zone)] += 1
HZ = {"DEEP": 6.22, "SHALLOW": 4.52, "PERIM": 0.22}
print("\n=== columns ===")
for z in ("DEEP", "SHALLOW", "PERIM"):
    n = v = f = 0
    names = []
    for (nm, zz), c in sorted(cols.items()):
        if zz != z: continue
        b, h = SEC.get(nm, (550, 550))
        n += c; v += c*b/1000*h/1000*HZ[z]; f += c*2*(b+h)/1000*HZ[z]
        names.append(f"{nm}({b}x{h})x{c}")
    print(f"{z}: n={n} H={HZ[z]} vol={v:.2f} formwork={f:.1f}")
    print("   ", "; ".join(names))

# caps 3-way recheck
ctpos = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "承台集中标注" and e.dxf.text.startswith("CT"):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S3":
            ctpos.append((x, y, e.dxf.text))
capz = collections.Counter()
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S3":
            p = Point(cx, cy)
            zone = "DEEP" if hatch3.buffer(500).contains(p) else ("SHALLOW" if enc3.buffer(500).contains(p) else "PERIM")
            best, bd = None, 1e18
            for tx, ty, name in ctpos:
                d = (tx-cx)**2+(ty-cy)**2
                if d < bd: bd, best = d, name
            capz[(best, zone)] += 1
print("\n=== caps zones ===")
tot = collections.Counter()
for k in sorted(capz, key=str):
    tot[k[1]] += capz[k]
    print("  ", k, capz[k])
print(" ", dict(tot))

# beams
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

colpolys = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "COLU":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S6":
            try: colpolys.append(Polygon(pts).buffer(0))
            except Exception: pass
colu = unary_union(colpolys)

marks = []
name2sec = {}
for e in msp.query("TEXT"):
    if e.dxf.layer == "梁名称编号":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S6":
            t = e.dxf.text.strip()
            parts = t.split()
            if len(parts) > 1:
                name2sec[parts[0]] = parts[1]
            marks.append((x, y, round(e.dxf.rotation) % 180, t))
# fill missing sections
marks2 = []
for x, y, r, t in marks:
    parts = t.split()
    sec = parts[1] if len(parts) > 1 else name2sec.get(parts[0])
    marks2.append((x, y, r, parts[0], sec))
nosec = [m[3] for m in marks2 if not m[4]]
print("\nbeam marks w/o any section:", set(nosec))

agg = collections.defaultdict(lambda: [0.0, 0.0])
for strips, horiz in ((hs, True), (vs, False)):
    for c, w, a0, a1 in strips:
        ls = LineString([(a0, c), (a1, c)]) if horiz else LineString([(c, a0), (c, a1)])
        net = ls.difference(colu)
        Lin = net.intersection(enc6).length/1000
        Lout = net.length/1000 - Lin
        best, bd = None, 1e18
        for x, y, r, nm, sec in marks2:
            if ((r == 0) != horiz) or not sec: continue
            if int(sec.split("x")[0]) != w: continue
            if horiz: d = abs(y-c)*2 + (0 if a0-2000 <= x <= a1+2000 else min(abs(x-a0), abs(x-a1)))
            else: d = abs(x-c)*2 + (0 if a0-2000 <= y <= a1+2000 else min(abs(y-a0), abs(y-a1)))
            if d < bd: bd, best = d, (nm, sec)
        if best:
            typ = "KL" if best[0].startswith("KL") else ("WKL" if best[0].startswith("WKL") else "L")
            agg[(typ, best[1])][0] += Lin
            agg[(typ, best[1])][1] += Lout
        else:
            agg[("UNK", f"{int(w)}x700?")][0] += Lin
            agg[("UNK", f"{int(w)}x700?")][1] += Lout

print("\n=== beam NET length & volume by (type, section) ===")
ti = to = vin = vout = vrib = fsi = fso = bbot = 0
for k in sorted(agg, key=str):
    Lin, Lout = agg[k]
    b, h = (int(re.sub(r"\D", "", v) or 0) for v in k[1].split("x"))
    vi = Lin*b/1000*h/1000; vo = Lout*b/1000*h/1000
    print(f"  {k[0]} {k[1]}: in={Lin:.1f}m/{vi:.1f}m3  out={Lout:.1f}m/{vo:.1f}m3")
    ti += Lin; to += Lout; vin += vi; vout += vo
    vrib += Lin*b/1000*(h-180)/1000
    fsi += 2*(h-180)/1000*Lin; fso += 2*h/1000*Lout; bbot += b/1000*Lin
print(f"TOTALS: len in={ti:.1f} out={to:.1f}; vol full in={vin:.1f} out={vout:.1f}; rib in={vrib:.1f}")
print(f"formwork: in sides(h-180)={fsi:.1f} m2, beam bottoms in={bbot:.1f} m2, out 2sides={fso:.1f} m2")

# slab zone split (footprint poly S3 -> S7)
fp3 = None
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "施工图板区边界":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and band(cy) == "S3":
            fp3 = Polygon(pts)
in_a = fp3.intersection(enc3).area/1e6
print(f"\nfootprint={fp3.area/1e6:.1f} m2; over basement={in_a:.1f}; outside={fp3.area/1e6-in_a:.1f}")
