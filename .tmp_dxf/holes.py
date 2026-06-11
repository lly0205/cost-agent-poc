# -*- coding: utf-8 -*-
import ezdxf, sys, collections
from ezdxf import bbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

# legend symbols sit left of note texts 5 & 6:
# note5: (-4753570, -467105) "5. [sym] 填充部分板顶h-0.500"  + (-4747555,-467067) "[sym2] 填充部分板顶h-0.050"
# note6: (-4753575, -467873) "6. [sym] 楼板开洞..."
regions = {
    "note5_sym1": (-4754000, -467500, -4752000, -466800),
    "note5_sym2": (-4748600, -467500, -4746500, -466800),
    "note6_sym":  (-4754200, -468300, -4752200, -467600),
}
for name, (x0, y0, x1, y1) in regions.items():
    print(f"\n=== {name} region ===")
    for e in msp:
        try:
            ext = bbox.extents([e], fast=True)
            if not ext.has_data: continue
        except Exception:
            continue
        cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
        if not (x0 <= cx <= x1 and y0 <= cy <= y1): continue
        t = e.dxftype()
        extra = ""
        if t == "INSERT": extra = e.dxf.name
        if t == "TEXT": extra = e.dxf.text
        if t == "HATCH": extra = f"pat={e.dxf.pattern_name}"
        w = ext.extmax.x-ext.extmin.x; h = ext.extmax.y-ext.extmin.y
        print(f"  {t} layer={e.dxf.layer} size={w:.0f}x{h:.0f} {extra}")

# inventory all hatches in S7 band by pattern + layer
X0, X1 = -4840000, -4691000
SY0, SY1 = -475672, -391572
hv = collections.Counter()
hl = []
for e in msp.query("HATCH"):
    ext = bbox.extents([e], fast=True)
    if not ext.has_data: continue
    cx = (ext.extmin.x+ext.extmax.x)/2; cy = (ext.extmin.y+ext.extmax.y)/2
    if not (X0 <= cx <= X1 and SY0 <= cy <= SY1): continue
    w = ext.extmax.x-ext.extmin.x; h = ext.extmax.y-ext.extmin.y
    hv[(e.dxf.layer, e.dxf.pattern_name)] += 1
    hl.append((e.dxf.layer, e.dxf.pattern_name, cx, cy, w, h))
print("\n=== S7 hatches (layer, pattern): count ===")
for k, v in sorted(hv.items(), key=lambda kv: -kv[1]):
    print(f"  {k}: {v}")
print("\n=== S7 hatch list ===")
for r in sorted(hl, key=lambda r: (r[0], r[1])):
    print(f"  {r[0]} {r[1]} c=({r[2]:.0f},{r[3]:.0f}) {r[4]:.0f}x{r[5]:.0f}")

# 板洞边线 lines clusters (from previous run) - re-list with positions
from shapely.geometry import LineString
from shapely.ops import unary_union
op = []
for e in msp.query("LINE"):
    if e.dxf.layer == "板洞边线" and X0 <= e.dxf.start.x <= X1 and SY0 <= e.dxf.start.y <= SY1:
        op.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
mp = unary_union([l.buffer(10) for l in op])
gs = list(mp.geoms) if mp.geom_type == "MultiPolygon" else [mp]
print(f"\n=== 板洞边线 clusters: {len(gs)} ===")
for g in gs:
    b = g.bounds
    print(f"  c=({(b[0]+b[2])/2:.0f},{(b[1]+b[3])/2:.0f}) bbox {(b[2]-b[0])/1000:.2f} x {(b[3]-b[1])/1000:.2f} m")
# also check other layers containing 洞
print("\n=== layers with 洞 in name ===")
for layer in doc.layers:
    if "洞" in layer.dxf.name:
        print(" ", layer.dxf.name)
