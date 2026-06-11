# -*- coding: utf-8 -*-
import ezdxf, sys, collections
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

def sheet_of(x, y):
    if x < -4850000:
        return None
    for n, y0, y1 in SHEETS:
        if y0 <= y <= y1:
            return n
    return None

out = open(r"D:\cc-connect\cost-agent-poc\.tmp_dxf\inserts.txt", "w", encoding="utf-8")
cnt = collections.Counter()
for e in msp.query("INSERT"):
    x, y = e.dxf.insert.x, e.dxf.insert.y
    s = sheet_of(x, y)
    if s is None:
        continue
    attrs = []
    for a in e.attribs:
        attrs.append(f"{a.dxf.tag}={a.dxf.text}")
    # also texts inside block definition (first 5)
    vt = []
    if not attrs:
        try:
            for ve in e.virtual_entities():
                if ve.dxftype() == "TEXT":
                    vt.append(ve.dxf.text)
                elif ve.dxftype() == "MTEXT":
                    vt.append(ve.plain_text())
                if len(vt) >= 6:
                    break
        except Exception:
            pass
    cnt[(s, e.dxf.name)] += 1
    out.write(f"{s}\t{e.dxf.name}\t{x:.0f}\t{y:.0f}\t{'|'.join(attrs)}\t{'|'.join(vt)}\n")
out.close()

for (s, n), v in sorted(cnt.items()):
    print(s, n, v)
