# -*- coding: utf-8 -*-
import ezdxf, sys
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

SHEETS = [
    ("S1_基础布置图", 36225, 120325),
    ("S2_桩平面布置图", -55172, 28928),
    ("S3_筏板承台平面布置图", -139272, -55172),
    ("S4_基础详图", -223372, -139272),
    ("S5_墙柱施工图", -307472, -223372),
    ("S6_梁配筋图", -391572, -307472),
    ("S7_板配筋图", -475672, -391572),
]

data = {n: [] for n, _, _ in SHEETS}
for e in msp:
    t = e.dxftype()
    if t == "TEXT":
        txt, x, y = e.dxf.text, e.dxf.insert.x, e.dxf.insert.y
    elif t == "MTEXT":
        txt, x, y = e.plain_text().replace("\n", "\\n"), e.dxf.insert.x, e.dxf.insert.y
    else:
        continue
    if not (-4840000 <= x <= -4691000):
        continue
    for n, y0, y1 in SHEETS:
        if y0 <= y <= y1:
            data[n].append((x, y, e.dxf.layer, txt))
            break

for n, rows in data.items():
    rows.sort(key=lambda r: (-r[1], r[0]))
    with open(rf"D:\cc-connect\cost-agent-poc\.tmp_dxf\{n}.txt", "w", encoding="utf-8") as f:
        for x, y, layer, txt in rows:
            f.write(f"{x:.0f}\t{y:.0f}\t{layer}\t{txt}\n")
    print(n, len(rows))
