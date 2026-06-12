# -*- coding: utf-8 -*-
# find ALL sheet titles across entire modelspace
import ezdxf, sys
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
rows = []
for e in msp.query("TEXT"):
    lay = e.dxf.layer
    t = e.dxf.text.strip()
    if lay in ("S_PLAN_TOPC", "PUB_TEXT", "TEXT", "图块", "需要设计单位填写内容"):
        if any(s in t for s in ("平面", "配筋图", "布置图", "施工图", "详图", "说明", "大样")) and len(t) < 40:
            rows.append((e.dxf.insert.x, e.dxf.insert.y, lay, t, e.dxf.height))
rows.sort(key=lambda r: (round(r[0]/50000), -r[1]))
for x, y, lay, t, h in rows:
    if h > 300:  # sheet titles are big text
        print(f"({x:.0f},{y:.0f}) h={h:.0f} [{lay}] {t}")
