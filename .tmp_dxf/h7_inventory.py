# -*- coding: utf-8 -*-
# S7 sheet entity inventory: find ALL hole-candidate representations
import ezdxf, sys, collections, pickle
from shapely.geometry import Point
from shapely.affinity import translate
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572
ANCH = {"S3": (-4711895, -67087), "S5": (-4718640, -231423), "S7": (-4711816, -404432)}
with open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\enclosure.pkl", "rb") as f:
    enc5 = pickle.load(f)
enc7 = translate(enc5, xoff=ANCH["S7"][0]-ANCH["S5"][0], yoff=ANCH["S7"][1]-ANCH["S5"][1])

cnt = collections.Counter()
for e in msp:
    try:
        if e.dxf.dxftype == "LINE":
            x, y = e.dxf.start.x, e.dxf.start.y
        elif e.dxf.dxftype in ("TEXT", "MTEXT", "INSERT"):
            x, y = e.dxf.insert.x, e.dxf.insert.y
        elif e.dxf.dxftype == "CIRCLE":
            x, y = e.dxf.center.x, e.dxf.center.y
        elif e.dxf.dxftype == "LWPOLYLINE":
            pts = list(e.get_points("xy"))
            x = sum(p[0] for p in pts)/len(pts); y = sum(p[1] for p in pts)/len(pts)
        elif e.dxf.dxftype == "HATCH":
            paths = [p for p in e.paths if hasattr(p, "vertices")]
            if not paths: continue
            vs = [v for p in paths for v in p.vertices]
            x = sum(v[0] for v in vs)/len(vs); y = sum(v[1] for v in vs)/len(vs)
        else:
            continue
    except Exception:
        continue
    if X0 <= x <= X1 and SY0 <= y <= SY1:
        inside = enc7.buffer(500).contains(Point(x, y))
        cnt[(e.dxf.dxftype, e.dxf.layer, inside)] += 1

print("=== S7 band entity inventory (type, layer, inside_enclosure): count ===")
for k in sorted(cnt, key=str):
    print(f"  {k[0]:<11} {k[1]:<22} {'IN ' if k[2] else 'OUT'}  {cnt[k]}")

# texts mentioning 洞/留/JD/后浇 in S7
print("\n=== S7 texts containing 洞/留/补/浇/井 (inside enclosure or near) ===")
for e in msp.query("TEXT MTEXT"):
    try:
        t = e.dxf.text if e.dxf.dxftype == "TEXT" else e.text
    except Exception:
        continue
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if X0 <= x <= X1 and SY0 <= y <= SY1:
        if any(c in t for c in ("洞", "留", "浇", "井", "封")):
            ins = "IN " if enc7.buffer(500).contains(Point(x, y)) else "OUT"
            print(f"  {ins} ({x:.0f},{y:.0f}) [{e.dxf.layer}] {t.strip()[:60]}")
