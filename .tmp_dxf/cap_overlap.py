# -*- coding: utf-8 -*-
# v4 修正B：承台与筏板(围合区)重叠面积精确计算
# 重叠体积 = Σ area(承台多边形 ∩ 围合区) × 0.6 (筏板厚600,承台高均>=800)
import ezdxf, sys, math, pickle, collections
from shapely.geometry import Polygon, Point
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S3 = (-139272, -55172)
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423)}
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc3 = translate(enc5, xoff=ANCH["S3"][0]-ANCH["S5"][0], yoff=ANCH["S3"][1]-ANCH["S5"][1])
print(f"enclosure area = {enc3.area/1e6:.1f} m2")

# labels
ctpos = []
for e in msp.query("TEXT"):
    if e.dxf.layer == "承台集中标注" and e.dxf.text.startswith("CT"):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if X0 <= x <= X1 and S3[0] <= y <= S3[1]:
            ctpos.append((x, y, e.dxf.text.split()[0]))

caps = []
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer == "承台基础":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
        if X0 <= cx <= X1 and S3[0] <= cy <= S3[1]:
            caps.append(Polygon(pts))

# assign nearest label (<=4m), else unlabeled
rows = []
for cp in caps:
    c = cp.centroid
    best, bd = None, 1e18
    for tx, ty, name in ctpos:
        d = (tx-c.x)**2 + (ty-c.y)**2
        if d < bd: bd, best = d, name
    name = best if math.sqrt(bd) <= 4000 else "UNLABELED"
    ov = cp.intersection(enc3).area/1e6
    rows.append((name, cp.area/1e6, ov, c.x, c.y))

AXX = {1:-4821395,2:-4812995,3:-4804595,4:-4796195,5:-4787795,6:-4779395,7:-4770995,
       8:-4762595,9:-4754195,10:-4745795,11:-4737395,12:-4728995,13:-4720595,14:-4712195}
AXY = {"A":-117787,"B":-108187,"C":-98587,"D":-86587,"E":-76987,"F":-67387}

agg = collections.defaultdict(lambda: [0, 0.0, 0.0, 0, 0.0])  # n, plan_area, overlap_area, n_partial, area_full
for name, a, ov, x, y in rows:
    g = agg[name]
    g[0] += 1; g[1] += a; g[2] += ov
    if 0.005*a < ov < 0.995*a: g[3] += 1
print(f"\n{'type':10s} {'n':>3s} {'plan_area':>10s} {'overlap':>10s} {'n_partial':>9s}")
totN = totA = totOv = 0
for name in sorted(agg):
    n, a, ov, npart, _ = agg[name]
    print(f"{name:10s} {n:3d} {a:10.2f} {ov:10.2f} {npart:9d}")
    totN += n; totA += a; totOv += ov
print(f"{'TOTAL':10s} {totN:3d} {totA:10.2f} {totOv:10.2f}")

# per-type avg area (check vs detail dims)
print("\nper-type single-cap plan areas (unique):")
seen = collections.defaultdict(set)
for name, a, ov, x, y in rows:
    seen[name].add(round(a, 2))
for name in sorted(seen):
    print(f"  {name}: {sorted(seen[name])}")

# unlabeled positions
print("\nUNLABELED caps:")
for name, a, ov, x, y in rows:
    if name == "UNLABELED":
        bx = min(AXX.items(), key=lambda kv: abs(kv[1]-x))
        by = min(AXY.items(), key=lambda kv: abs(kv[1]-y))
        print(f"  {bx[0]}轴{(x-bx[1])/1000:+.1f} × {by[0]}轴{(y-by[1])/1000:+.1f} area={a:.2f} overlap={ov:.2f}")

# overlap excluding unlabeled
ovL = sum(ov for name, a, ov, x, y in rows if name != "UNLABELED")
aL  = sum(a for name, a, ov, x, y in rows if name != "UNLABELED")
nin = sum(1 for name, a, ov, x, y in rows if name != "UNLABELED" and ov > 0.005*a)
print(f"\n[有编号108台] 总底面积={aL:.2f} m2, 与筏板重叠面积={ovL:.2f} m2 (涉及{nin}台)")
print(f"重叠扣减体积 = {ovL:.2f} × 0.6 = {ovL*0.6:.1f} m3")
ovU = sum(ov for name, a, ov, x, y in rows if name == "UNLABELED")
print(f"[无编号3台] 重叠面积={ovU:.2f} m2 (若计入再扣 {ovU*0.6:.1f} m3)")
