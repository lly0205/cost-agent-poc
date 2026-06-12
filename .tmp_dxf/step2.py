# -*- coding: utf-8 -*-
# measure parallel lines near the step boundary x=-4796095 in S3, and dims nearby
import ezdxf, sys, collections
from ezdxf import bbox as ebbox
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
# vertical lines with x in [-4799500,-4793500], y overlapping [-104087,-77287]
xs = collections.Counter()
for e in msp.query("LINE"):
    x1, y1, x2, y2 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
    if abs(x1-x2) < 1 and -4799500 <= x1 <= -4793000:
        ov = min(max(y1,y2), -77287) - max(min(y1,y2), -104087)
        if ov > 3000:
            xs[(round(x1), e.dxf.layer)] += 1
for k, v in sorted(xs.items()):
    print("V line x=%d layer=%s n=%d" % (k[0], k[1], v))
# dims near the step (S3 area around x -4799k..-4790k)
for e in msp.query("DIMENSION"):
    try:
        ext = ebbox.extents([e], fast=True)
        if not ext.has_data: continue
        cx=(ext.extmin.x+ext.extmax.x)/2; cy=(ext.extmin.y+ext.extmax.y)/2
    except Exception: continue
    if -4801000 <= cx <= -4790000 and -106000 <= cy <= -75000:
        m = e.dxf.actual_measurement if e.dxf.hasattr("actual_measurement") else -1
        print(f"DIM ({cx:.0f},{cy:.0f}) meas={m:.0f} text='{e.dxf.text}'")
