# -*- coding: utf-8 -*-
import ezdxf, sys, collections, math, re
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

# ---------- A. pile polylines in S1 ----------
piles = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "桩":
        pts = e.get_points("xy")
        x = sum(p[0] for p in pts) / len(pts); y = sum(p[1] for p in pts) / len(pts)
        if X0 <= x <= X1 and band(y) == "S1":
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            piles.append((x, y, max(xs)-min(xs), max(ys)-min(ys), len(pts), e.closed))
print("=== 桩 polylines in S1:", len(piles))
sizes = collections.Counter((round(p[2], -1), round(p[3], -1), p[4], p[5]) for p in piles)
for k, v in sizes.most_common(10):
    print("  size(dx,dy,nverts,closed):", k, "x", v)
# cluster piles by center within 600mm
cl = []
for x, y, *_ in piles:
    for c in cl:
        if abs(c[0]-x) < 300 and abs(c[1]-y) < 300:
            c[2] += 1
            break
    else:
        cl.append([x, y, 1])
print("  pile clusters:", len(cl))

# ---------- B. CT labels tally (S3) ----------
ct = collections.Counter()
ctpos = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "承台集中标注":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S3" and e.dxf.text.startswith("CT"):
            ct[e.dxf.text] += 1
            ctpos.append((x, y, e.dxf.text))
print("\n=== CT label tally (S3):")
tot = 0
for k in sorted(ct):
    print(f"  {k}: {ct[k]}")
    tot += ct[k]
print("  total CT labels:", tot)

# ---------- C. 承台基础 bbox in S3, matched to nearest CT label ----------
caps = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = e.get_points("xy")
        x = sum(p[0] for p in pts)/len(pts); y = sum(p[1] for p in pts)/len(pts)
        if X0 <= x <= X1 and band(y) == "S3":
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            caps.append((x, y, max(xs)-min(xs), max(ys)-min(ys), len(pts)))
print("\n=== 承台基础 polylines in S3:", len(caps))
match = collections.defaultdict(collections.Counter)
for x, y, dx, dy, nv in caps:
    best, bd = None, 1e9
    for tx, ty, name in ctpos:
        d = math.hypot(tx-x, ty-y)
        if d < bd:
            bd, best = d, name
    if best:
        match[best][(round(dx, -1), round(dy, -1))] += 1
for name in sorted(match):
    print(f"  {name}: {dict(match[name])}")

# ---------- D. 柱集中标注 tally on plan (S5) ----------
kz = collections.Counter()
for e in msp.query("TEXT"):
    if e.dxf.layer == "柱集中标注":
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and band(y) == "S5":
            kz[re.sub(r"\(.*\)", "", e.dxf.text)] += 1
print("\n=== 柱集中标注 tally (plan S5): total", sum(kz.values()))
for k in sorted(kz, key=lambda s: int(re.sub(r"\D", "", s) or 0)):
    print(f"  {k}: {kz[k]}")

# ---------- E. 柱尺寸标注 DIMENSION values in S5 (column table sections) ----------
dims = []
for e in msp.query("DIMENSION"):
    if e.dxf.layer == "柱尺寸标注":
        p = e.dxf.defpoint
        if X0 <= p.x <= X1 and band(p.y) == "S5":
            try:
                m = e.get_measurement()
            except Exception:
                m = None
            dims.append((p.x, p.y, round(m) if isinstance(m, float) else m))
print("\n=== 柱尺寸标注 dims in S5:", len(dims))
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\col_dims.txt", "w", encoding="utf-8") as f:
    for x, y, m in sorted(dims, key=lambda r: (-r[1], r[0])):
        f.write(f"{x:.0f}\t{y:.0f}\t{m}\n")

# 柱截面轮廓 bbox in S5 (table section sketches)
secs = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "柱截面轮廓":
        pts = e.get_points("xy")
        x = sum(p[0] for p in pts)/len(pts); y = sum(p[1] for p in pts)/len(pts)
        if X0 <= x <= X1 and band(y) == "S5":
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            secs.append((x, y, round(max(xs)-min(xs)), round(max(ys)-min(ys))))
print("=== 柱截面轮廓 bbox in S5:", len(secs))
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\col_secs.txt", "w", encoding="utf-8") as f:
    for x, y, dx, dy in sorted(secs, key=lambda r: (-r[1], r[0])):
        f.write(f"{x:.0f}\t{y:.0f}\t{dx}\t{dy}\n")
