# -*- coding: utf-8 -*-
import ezdxf, sys, math, re, collections
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -391572, -307472  # S6

# ---- collect beam edge lines ----
H, V, SK = [], [], []
for e in msp.query("LINE"):
    if e.dxf.layer in ("BEAM", "BEAM_CON"):
        x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
        if not (X0 <= x1 <= X1 and SY0 <= y1 <= SY1):
            continue
        if abs(y1-y2) < 1:
            H.append((min(x1, x2), max(x1, x2), y1, e.dxf.layer))
        elif abs(x1-x2) < 1:
            V.append((min(y1, y2), max(y1, y2), x1, e.dxf.layer))
        else:
            SK.append((x1, y1, x2, y2, e.dxf.layer))
print(f"H={len(H)} V={len(V)} skew={len(SK)}")
sk_len = sum(math.hypot(x2-x1, y2-y1) for x1, y1, x2, y2, _ in SK)
print(f"skew total len={sk_len/1000:.1f}m")

# ---- merge collinear segments on same coordinate ----
def merge(segs):
    # segs: list of (a0,a1) on same line; merge overlapping/adjacent (<50)
    segs = sorted(segs)
    out = []
    for a0, a1 in segs:
        if out and a0 <= out[-1][1] + 50:
            out[-1][1] = max(out[-1][1], a1)
        else:
            out.append([a0, a1])
    return out

# group H by y
from collections import defaultdict
Hy = defaultdict(list)
for a0, a1, y, lay in H:
    Hy[round(y)].append((a0, a1))
Hys = sorted(Hy)
# cluster y keys within 2mm
ykeys = []
for y in Hys:
    if ykeys and y - ykeys[-1][-1] <= 2:
        ykeys[-1].append(y)
    else:
        ykeys.append([y])
Hlines = []  # (y, [(a0,a1),...])
for grp in ykeys:
    segs = []
    for y in grp:
        segs += Hy[y]
    Hlines.append((sum(grp)/len(grp), merge(segs)))

Vx = defaultdict(list)
for a0, a1, x, lay in V:
    Vx[round(x)].append((a0, a1))
Vxs = sorted(Vx)
xkeys = []
for x in Vxs:
    if xkeys and x - xkeys[-1][-1] <= 2:
        xkeys[-1].append(x)
    else:
        xkeys.append([x])
Vlines = []
for grp in xkeys:
    segs = []
    for x in grp:
        segs += Vx[x]
    Vlines.append((sum(grp)/len(grp), merge(segs)))

# ---- pair edge lines into beam strips ----
def pair(lines):
    """lines: [(coord, [[a0,a1],...])]; returns beam strips (center, width, a0, a1)"""
    strips = []
    used = set()
    n = len(lines)
    for i in range(n):
        ci, segi = lines[i]
        for j in range(i+1, n):
            cj, segj = lines[j]
            w = cj - ci
            if w > 600:
                break
            if w < 100:
                continue
            for (a0, a1) in segi:
                for (b0, b1) in segj:
                    ov0, ov1 = max(a0, b0), min(a1, b1)
                    if ov1 - ov0 > 600:
                        strips.append((round((ci+cj)/2, 1), round(w), ov0, ov1))
    return strips

Hstrips = pair(Hlines)   # horizontal beams: (ycenter, width, x0, x1)
Vstrips = pair(Vlines)   # vertical beams: (xcenter, width, y0, y1)
print(f"H strips={len(Hstrips)} V strips={len(Vstrips)}")

# dedupe overlapping strips on same center (keep longest spans, merge)
def dedupe(strips):
    d = defaultdict(list)
    for c, w, a0, a1 in strips:
        d[(round(c, -1), w)].append((a0, a1))
    out = []
    for (c, w), segs in d.items():
        for a0, a1 in merge(segs):
            out.append((c, w, a0, a1))
    return out

Hstrips = dedupe(Hstrips)
Vstrips = dedupe(Vstrips)
print(f"after dedupe: H={len(Hstrips)} V={len(Vstrips)}")
wdist = collections.Counter()
for c, w, a0, a1 in Hstrips + Vstrips:
    wdist[w] += round((a1-a0)/1000, 1)
print("width -> total gross length(m):")
for w in sorted(wdist):
    print(f"  {w}: {wdist[w]:.1f}")

# ---- beam marks ----
marks = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "梁名称编号":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and SY0 <= y <= SY1:
            m = re.match(r"^(W?KL|L)(\d+)\((\d+)[A-Za-z]?\)\s*(\d+)?x?(\d+)?", e.dxf.text)
            if m:
                marks.append((x, y, round(e.dxf.rotation), e.dxf.text.strip()))
print(f"\nmarks={len(marks)}")
uniq = {}
for x, y, r, t in marks:
    name = t.split()[0]
    sec = t.split()[1] if len(t.split()) > 1 else None
    if name not in uniq or (uniq[name] is None and sec):
        uniq[name] = sec
print("unique beam marks:", len(uniq))
nosec = [k for k, v in uniq.items() if not v]
print("marks without section:", nosec)
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\beam_marks.txt", "w", encoding="utf-8") as f:
    for k in sorted(uniq, key=lambda s: (s[0], int(re.sub(r'\D', '', s.split('(')[0])))):
        f.write(f"{k}\t{uniq[k]}\n")

# ---- match strips to marks (same orientation, nearest) ----
# horizontal strip -> marks with rotation 0; vertical -> rotation 90
def match(strips, horiz):
    res = []
    for c, w, a0, a1 in strips:
        best, bd = None, 1e9
        for x, y, r, t in marks:
            isH = (r % 180) == 0
            if isH != horiz:
                continue
            if horiz:
                d = abs(y - c) + (0 if a0 - 3000 <= x <= a1 + 3000 else min(abs(x-a0), abs(x-a1)))
            else:
                d = abs(x - c) + (0 if a0 - 3000 <= y <= a1 + 3000 else min(abs(y-a0), abs(y-a1)))
            if d < bd:
                bd, best = d, t
        res.append((c, w, a0, a1, best, round(bd)))
    return res

HM = match(Hstrips, True)
VM = match(Vstrips, False)
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\beam_strips.txt", "w", encoding="utf-8") as f:
    for c, w, a0, a1, t, d in HM:
        f.write(f"H\t{c:.0f}\t{w}\t{a0:.0f}\t{a1:.0f}\tlen={(a1-a0)/1000:.2f}\t{t}\td={d}\n")
    for c, w, a0, a1, t, d in VM:
        f.write(f"V\t{c:.0f}\t{w}\t{a0:.0f}\t{a1:.0f}\tlen={(a1-a0)/1000:.2f}\t{t}\td={d}\n")

# aggregate by section parsed from matched mark
agg = defaultdict(float)
bad = 0.0
for c, w, a0, a1, t, d in HM + VM:
    L = (a1-a0)/1000
    sec = None
    if t and len(t.split()) > 1:
        sec = t.split()[1]
    if sec:
        agg[(t.split()[0][:2].rstrip('0123456789'), sec)] += L
    else:
        bad += L
print("\n=== aggregated gross length by (type, section) ===")
for k in sorted(agg):
    print(f"  {k}: {agg[k]:.1f} m")
print(f"unmatched-section length: {bad:.1f} m")
