# -*- coding: utf-8 -*-
# find expansion-band geometry: sample entities near band label & in band-cross view
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

def sample(a, b, c, d, title):
    cnt = collections.Counter()
    for e in msp.query("LINE"):
        x1, y1 = e.dxf.start.x, e.dxf.start.y
        if a <= x1 <= c and b <= y1 <= d:
            cnt[("LINE", e.dxf.layer, e.dxf.linetype if hasattr(e.dxf,'linetype') else "")] += 1
    for e in msp.query("LWPOLYLINE"):
        try:
            p0 = e.get_points("xy")[0]
        except Exception: continue
        if a <= p0[0] <= c and b <= p0[1] <= d:
            cnt[("LWPOLYLINE", e.dxf.layer, "")] += 1
    for e in msp.query("HATCH"):
        try:
            sp = e.seeds[0] if e.seeds else None
        except Exception: sp = None
        el = e.dxf.elevation if hasattr(e.dxf, 'elevation') else None
        # use path vertex
        for p in e.paths:
            if hasattr(p, "vertices") and len(p.vertices):
                vx, vy = p.vertices[0][0], p.vertices[0][1]
                if a <= vx <= c and b <= vy <= d:
                    cnt[("HATCH", e.dxf.layer, e.dxf.pattern_name)] += 1
                break
    print(f"--- {title} ---")
    for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
        print("  ", k, v)

# near the 膨胀加强带 labels (left edge of S3 plan)
sample(-4832000, -92500, -4824000, -88500, "near labels (-4828879,-90634/-90228)")
# band cross region from trans.py
sample(-4787000, -97000, -4777000, -88000, "band cross region")
