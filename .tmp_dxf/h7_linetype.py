# -*- coding: utf-8 -*-
# classify 板洞边线 lines by linetype/color/lineweight; also scan WHOLE drawing for other hole layers
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572

print("=== 板洞边线 lines in S7: (linetype, color, ltscale) ===")
cnt = collections.Counter()
for e in msp.query("LINE"):
    if e.dxf.layer != "板洞边线": continue
    x1, y1 = e.dxf.start.x, e.dxf.start.y
    if X0 <= x1 <= X1 and SY0 <= y1 <= SY1:
        cnt[(e.dxf.linetype, e.dxf.color, round(e.dxf.ltscale,1))] += 1
for k, v in sorted(cnt.items(), key=str):
    print("  ", k, v)

# layer table defaults
print("\n=== layer table: hole/void related layers in entire doc ===")
for layer in doc.layers:
    n = layer.dxf.name
    if any(s in n for s in ("洞", "井", "留", "HOLE", "OPEN", "VOID")):
        print(f"  layer={n} color={layer.dxf.color} linetype={layer.dxf.linetype}")

# whole-doc: which layers contain 洞-named entities; count per band
BANDS = {"S1": (36225, 120325), "S3": (-139272, -55172), "S5": (-307472, -223372),
         "S6": (-391572, -307472), "S7": (-475672, -391572)}
def band(y):
    for nm, (a, b) in BANDS.items():
        if a <= y <= b: return nm
    return f"Y{int(y/1000)}k"
print("\n=== whole-doc entity count on 洞/井 layers by band ===")
c2 = collections.Counter()
for e in msp:
    lay = e.dxf.layer
    if not any(s in lay for s in ("洞", "井", "留")): continue
    try:
        if e.dxf.dxftype == "LINE": x, y = e.dxf.start.x, e.dxf.start.y
        elif e.dxf.dxftype in ("TEXT", "MTEXT", "INSERT"): x, y = e.dxf.insert.x, e.dxf.insert.y
        elif e.dxf.dxftype == "CIRCLE": x, y = e.dxf.center.x, e.dxf.center.y
        elif e.dxf.dxftype == "LWPOLYLINE":
            pts = list(e.get_points("xy")); x = sum(p[0] for p in pts)/len(pts); y = sum(p[1] for p in pts)/len(pts)
        else: continue
    except Exception: continue
    c2[(lay, e.dxf.dxftype, band(y), X0 <= x <= X1)] += 1
for k, v in sorted(c2.items(), key=str):
    print("  ", k, v)

# also: any TEXT in whole doc containing 后浇 or 临时 or 封堵
print("\n=== whole-doc TEXT containing 后浇/临时/封堵/预留 ===")
for e in msp.query("TEXT MTEXT"):
    try: t = e.dxf.text if e.dxf.dxftype == "TEXT" else e.text
    except Exception: continue
    if any(s in t for s in ("后浇", "临时", "封堵", "预留")):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        print(f"  [{band(y)} x_in={X0<=x<=X1}] ({x:.0f},{y:.0f}) [{e.dxf.layer}] {t.strip()[:70]}")
