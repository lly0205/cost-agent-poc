# -*- coding: utf-8 -*-
import ezdxf, sys
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

out = open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\all_texts.txt", "w", encoding="utf-8")
rows = []
for e in msp:
    t = e.dxftype()
    if t == "TEXT":
        txt = e.dxf.text
        x, y = e.dxf.insert.x, e.dxf.insert.y
        h = e.dxf.height
    elif t == "MTEXT":
        txt = e.plain_text().replace("\n", "\\n")
        x, y = e.dxf.insert.x, e.dxf.insert.y
        h = e.dxf.char_height
    else:
        continue
    rows.append((x, y, e.dxf.layer, h, txt))

rows.sort(key=lambda r: (-r[1], r[0]))
for x, y, layer, h, txt in rows:
    out.write(f"{x:.0f}\t{y:.0f}\t{layer}\t{h:.0f}\t{txt}\n")
out.close()
print("rows:", len(rows))

# also dump INSERT block names with text-like attribs
import collections
bc = collections.Counter()
for e in msp.query("INSERT"):
    bc[e.dxf.name] += 1
print("\n=== top blocks ===")
for k, v in bc.most_common(40):
    print(k, v)
