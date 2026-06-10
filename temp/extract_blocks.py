# -*- coding: utf-8 -*-
"""1) DIMENSION 验证比例 2) 洁具/设备 INSERT 位置 3) 图块几何特征 4) 图例区映射 5) 配件高度表"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import ezdxf
from collections import Counter

PATH = r"C:\Users\Windows 11\Desktop\机电\阳山卫生间大样\2~4层给排水_布局1.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

print("=== DIMENSION (AXIS) 验证比例 ===")
for e in msp.query('DIMENSION'):
    try:
        m = e.dxf.actual_measurement if e.dxf.hasattr('actual_measurement') else None
        p1 = e.dxf.defpoint2 if e.dxf.hasattr('defpoint2') else None
        p2 = e.dxf.defpoint3 if e.dxf.hasattr('defpoint3') else None
        d = None
        if p1 and p2:
            d = ((p2.x-p1.x)**2+(p2.y-p1.y)**2)**0.5
        print(f"  layer={e.dxf.layer} text='{e.dxf.text}' measured={m} geo_dist={d:.1f}" if d else f"  layer={e.dxf.layer} text='{e.dxf.text}' measured={m}")
    except Exception as ex:
        print("  err", ex)

print("\n=== 洁具类 INSERT 位置 ===")
for e in msp.query('INSERT'):
    if e.dxf.layer in ("TOLIET","LVTRY","_MPFIXTURE","FURNITURE") or "lvtry" in e.dxf.name.lower() or e.dxf.name in ("gdshwdeh","无障碍洗脸盆","_LV5","TOILET"):
        p = e.dxf.insert
        print(f"  {e.dxf.name}  layer={e.dxf.layer}  ({p.x:.0f},{p.y:.0f}) rot={e.dxf.rotation:.0f} sx={e.dxf.xscale:.2f}")

print("\n=== 给排水设备 INSERT 位置 ===")
for e in msp.query('INSERT'):
    if e.dxf.layer.startswith("P-") or e.dxf.layer in ("0_J给水_市政_PJ",):
        p = e.dxf.insert
        print(f"  {e.dxf.name}  layer={e.dxf.layer}  ({p.x:.0f},{p.y:.0f}) rot={e.dxf.rotation:.0f}")

print("\n=== 图块几何特征（识别用） ===")
names = set()
for e in msp.query('INSERT'):
    names.add(e.dxf.name)
for n in sorted(names):
    if n not in doc.blocks:
        continue
    blk = doc.blocks.get(n)
    tc = Counter(x.dxftype() for x in blk)
    # bbox
    xs, ys = [], []
    for x in blk:
        try:
            if x.dxftype() == "LINE":
                xs += [x.dxf.start.x, x.dxf.end.x]; ys += [x.dxf.start.y, x.dxf.end.y]
            elif x.dxftype() == "LWPOLYLINE":
                for px, py in x.get_points("xy"):
                    xs.append(px); ys.append(py)
            elif x.dxftype() in ("CIRCLE","ARC"):
                xs += [x.dxf.center.x - x.dxf.radius, x.dxf.center.x + x.dxf.radius]
                ys += [x.dxf.center.y - x.dxf.radius, x.dxf.center.y + x.dxf.radius]
        except Exception:
            pass
    bb = f"bbox {max(xs)-min(xs):.1f} x {max(ys)-min(ys):.1f}" if xs else "no-geom"
    print(f"  {n}: {dict(tc)} {bb}")

print("\n=== 图例区文字+附近实体（layer 0 / PL 区域） ===")
legend_texts = []
for e in msp.query('TEXT[layer=="0"]'):
    p = e.dxf.insert
    legend_texts.append((e.dxf.text.strip(), p.x, p.y))
    print(f"  text '{e.dxf.text.strip()}' ({p.x:.0f},{p.y:.0f})")
print("--- layer 0 INSERTs ---")
for e in msp.query('INSERT[layer=="0"]'):
    p = e.dxf.insert
    print(f"  block {e.dxf.name} ({p.x:.0f},{p.y:.0f})")
print("--- 图例线段 (layer 0, LINE/LWPOLYLINE/CIRCLE/ARC) ---")
for e in msp.query('LINE[layer=="0"] LWPOLYLINE[layer=="0"] CIRCLE[layer=="0"] ARC[layer=="0"]'):
    if e.dxftype()=="LINE":
        print(f"  LINE ({e.dxf.start.x:.0f},{e.dxf.start.y:.0f})->({e.dxf.end.x:.0f},{e.dxf.end.y:.0f})")
    elif e.dxftype()=="LWPOLYLINE":
        pts=e.get_points("xy"); print(f"  LWPL {[(round(a),round(b)) for a,b in pts]} w={e.dxf.const_width if e.dxf.hasattr('const_width') else 0}")
    else:
        print(f"  {e.dxftype()} c=({e.dxf.center.x:.0f},{e.dxf.center.y:.0f}) r={e.dxf.radius:.1f}")

print("\n=== 配件高度表（TEL_TEXT 数字+器具名 位置） ===")
for e in msp.query('TEXT[layer=="TEL_TEXT"]'):
    s = e.dxf.text.strip()
    if s in ("蹲便器","洗脸盆","小便器","坐便器","污水盆","地漏","淋浴器","清扫口","卫生器具名称","给水配件距楼面高度（mm）","留洞尺寸（mm）","预留洞中心距墙距离（mm）","100","150","180","200","250","320","450","680","800","1000","1300") or s.startswith("Φ"):
        p = e.dxf.insert
        print(f"  '{s}' ({p.x:.0f},{p.y:.0f})")
