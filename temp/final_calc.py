# -*- coding: utf-8 -*-
"""最终算量：平面图管段长度按最近管径标注赋径，汇总（1单位=50mm）"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import ezdxf
from collections import defaultdict

PATH = r"C:\Users\Windows 11\Desktop\机电\阳山卫生间大样\2~4层给排水_布局1.dxf"
SC = 0.05  # 1 unit = 50mm = 0.05m
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

def seg_len(pts):
    return sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))

def collect(layer, region, width_max=0.5):
    """plan-view polylines (w=0) in region (xmin,xmax)"""
    segs = []
    for e in msp.query(f'LWPOLYLINE[layer=="{layer}"]'):
        w = e.dxf.const_width if e.dxf.hasattr("const_width") else 0
        if w > width_max:
            continue
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) < 2:
            continue
        xs = [p[0] for p in pts]
        if not (region[0] <= min(xs) and max(xs) <= region[1]):
            continue
        mid = ((pts[0][0]+pts[-1][0])/2, (pts[0][1]+pts[-1][1])/2)
        segs.append((pts, seg_len(pts), mid))
    return segs

def texts(layer, region):
    out = []
    for e in msp.query(f'TEXT[layer=="{layer}"]'):
        p = e.dxf.insert
        if region[0] <= p.x <= region[1] and 600 < p.y < 900:
            out.append((e.dxf.text.strip(), (p.x, p.y)))
    return out

def assign(segs, dntexts, sysname):
    sums = defaultdict(float)
    print(f"\n=== {sysname} 平面管段赋径明细 ===")
    for pts, L, mid in segs:
        # nearest DN text to segment midpoint AND endpoints
        best, bestd = None, 1e9
        for s, tp in dntexts:
            for ref in [mid, pts[0], pts[-1]]:
                d = math.dist(ref, tp)
                if d < bestd:
                    bestd, best = d, s
        Lm = L * SC
        conf = "HIGH" if bestd*50 < 500 else ("MED" if bestd*50 < 1500 else "LOW")
        print(f"  ({pts[0][0]:.0f},{pts[0][1]:.0f})->({pts[-1][0]:.0f},{pts[-1][1]:.0f}) L={Lm:.2f}m -> {best} (d={bestd*0.05:.2f}m {conf})")
        sums[best] += Lm
    print(f"--- {sysname} 汇总 ---")
    for dn in sorted(sums):
        print(f"  {dn}: {sums[dn]:.2f} m")
    print(f"  总计: {sum(sums.values()):.2f} m")
    return sums

# 给水平面图: x in [-460,-330]
js = collect("P-DOMW", (-460, -330))
js_t = texts("P-DOMW-PDMT", (-460, -330))
assign(js, js_t, "给水(P-DOMW)")

# 排水平面图: x in [200,335]
ps = collect("P-PDRN", (200, 335))
ps_t = texts("P-PDRN-PDMT", (200, 335))
assign(ps, ps_t, "排水(P-PDRN)")

# 通气平面: x in [200,335]
tq = collect("P-PGAS", (200, 335))
tq_t = texts("P-PGAS-PDMT", (200, 335)) or [("DN50", (275, 800))]
assign(tq, tq_t, "通气(P-PGAS)")
