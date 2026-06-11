# -*- coding: utf-8 -*-
import ezdxf, sys
from ezdxf import bbox
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

for e in msp.query("INSERT"):
    if e.dxf.name in ("图框1", "A0"):
        try:
            ext = bbox.extents(e.virtual_entities(), fast=True)
            print(f"{e.dxf.name}\tinsert=({e.dxf.insert.x:.0f},{e.dxf.insert.y:.0f})\tscale={e.dxf.xscale:.1f}\tbbox=({ext.extmin.x:.0f},{ext.extmin.y:.0f})-({ext.extmax.x:.0f},{ext.extmax.y:.0f})")
        except Exception as ex:
            print(f"{e.dxf.name}\tinsert=({e.dxf.insert.x:.0f},{e.dxf.insert.y:.0f})\terr={ex}")
