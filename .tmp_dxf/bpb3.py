# -*- coding: utf-8 -*-
# all 基础集中标注 texts in S3 + all layer-0 plate labels
import ezdxf, sys
sys.stdout.reconfigure(encoding='utf-8')
PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()
X0, X1 = -4840000, -4691000
S3 = (-139272, -55172)
print("=== 基础集中标注 texts in S3 ===")
for e in msp.query("TEXT MTEXT"):
    if e.dxf.layer != "基础集中标注": continue
    t = (e.dxf.text if e.dxftype()=="TEXT" else e.text).strip()
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if X0 <= x <= X1 and S3[0] <= y <= S3[1]:
        print(f"  ({x:.0f},{y:.0f}) rot={getattr(e.dxf,'rotation',0):.0f} {t[:100]}")
print("\n=== FB/BPB/底板-like labels any layer in S3 ===")
import re
for e in msp.query("TEXT MTEXT"):
    t = (e.dxf.text if e.dxftype()=="TEXT" else e.text).strip()
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if X0 <= x <= X1 and S3[0] <= y <= S3[1]:
        if re.match(r"^(FB|BPB|DB|ZB|WB)\d", t) or "h=" in t[:12]:
            print(f"  ({x:.0f},{y:.0f}) [{e.dxf.layer}] {t[:100]}")
