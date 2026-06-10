# -*- coding: utf-8 -*-
"""提取视图标题位置、各层实体坐标范围、INSERT位置"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import ezdxf
from collections import defaultdict

PATH = r"C:\Users\Windows 11\Desktop\机电\阳山卫生间大样\2~4层给排水_布局1.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

print("=== 视图标题位置 ===")
for e in msp.query("TEXT"):
    s = e.dxf.text.strip()
    if ('平面图' in s or '系统图' in s or '大样图' in s or s in ('PLAN',)) and e.dxf.layer in ('平面文字','图层3'):
        p = e.dxf.insert
        print(f"  '{s}'  layer={e.dxf.layer}  pos=({p.x:.0f}, {p.y:.0f})")

print("\n=== 各管线层 LWPOLYLINE 概况（坐标范围/线宽/长度） ===")
for layname in ("P-DOMW", "P-PDRN", "P-PGAS"):
    print(f"\n--- {layname} ---")
    for e in msp.query(f'LWPOLYLINE[layer=="{layname}"]'):
        pts = e.get_points("xy")
        if len(pts) < 2:
            continue
        L = 0.0
        for i in range(len(pts)-1):
            L += ((pts[i+1][0]-pts[i][0])**2 + (pts[i+1][1]-pts[i][1])**2)**0.5
        w = e.dxf.const_width if e.dxf.hasattr("const_width") else 0
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        print(f"  w={w:.0f} len={L:.0f} npts={len(pts)} x[{min(xs):.0f},{max(xs):.0f}] y[{min(ys):.0f},{max(ys):.0f}]")

print("\n=== P-DOMW 层 LINE ===")
for e in msp.query('LINE[layer=="P-DOMW"]'):
    a, b = e.dxf.start, e.dxf.end
    L = ((b.x-a.x)**2+(b.y-a.y)**2)**0.5
    print(f"  len={L:.0f} ({a.x:.0f},{a.y:.0f})->({b.x:.0f},{b.y:.0f})")

print("\n=== 管径标注位置 ===")
for layname in ("P-DOMW-PDMT", "P-PDRN-PDMT", "P-PGAS-PDMT"):
    print(f"--- {layname} ---")
    for e in msp.query(f'TEXT[layer=="{layname}"]'):
        p = e.dxf.insert
        print(f"  {e.dxf.text.strip()}  ({p.x:.0f},{p.y:.0f}) rot={e.dxf.rotation:.0f}")
