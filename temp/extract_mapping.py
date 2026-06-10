# -*- coding: utf-8 -*-
"""器具表/图例映射 + 设备INSERT全量 + 关键图块渲染PNG"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import ezdxf
from ezdxf import bbox as ezbbox

PATH = r"C:\Users\Windows 11\Desktop\机电\阳山卫生间大样\2~4层给排水_布局1.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

print("=== 器具表区域 TEL_TEXT (x>1100) ===")
rows = []
for e in msp.query('TEXT'):
    p = e.dxf.insert
    if 1100 < p.x < 1400 and 640 < p.y < 800:
        rows.append((p.y, p.x, e.dxf.text.strip(), e.dxf.layer))
for y, x, s, lay in sorted(rows, key=lambda r: (-r[0], r[1])):
    print(f"  y={y:.0f} x={x:.0f} [{lay}] '{s}'")

print("\n=== 图例区全部实体 (1240<x<1300, 770<y<950) ===")
for e in msp:
    try:
        if e.dxftype() == "INSERT":
            p = e.dxf.insert
            if 1200 < p.x < 1300 and 760 < p.y < 950:
                print(f"  INSERT {e.dxf.name} ({p.x:.0f},{p.y:.0f}) layer={e.dxf.layer}")
    except Exception:
        pass

print("\n=== P-PDRN-EQPM / P-DOMW-EQPM / OTHER / VPIP 全量 INSERT ===")
for e in msp.query('INSERT'):
    if e.dxf.layer.startswith("P-") or e.dxf.layer == "0_J给水_市政_PJ":
        p = e.dxf.insert
        print(f"  {e.dxf.name}\t{e.dxf.layer}\t({p.x:.0f},{p.y:.0f})\trot={e.dxf.rotation:.0f}")

print("\n=== 洁具 INSERT 实际落位 bbox（virtual entities） ===")
targets = ("gdshwdeh","$lvtry$00000200","$lvtry$00000179","$lvtry$00000219","$lvtry$00000191","_LV5","无障碍洗脸盆","A$C177467FC","TOILET","M_E6","M_E8")
for e in msp.query('INSERT'):
    if e.dxf.name in targets:
        try:
            bb = ezbbox.extents(e.virtual_entities(), fast=True)
            if bb.has_data:
                cx = (bb.extmin.x + bb.extmax.x)/2; cy = (bb.extmin.y + bb.extmax.y)/2
                print(f"  {e.dxf.name}\tlayer={e.dxf.layer}\tcenter=({cx:.0f},{cy:.0f})\tsize={bb.size.x:.1f}x{bb.size.y:.1f}")
        except Exception as ex:
            print(f"  {e.dxf.name} ERR {ex}")
