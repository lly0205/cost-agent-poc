# -*- coding: utf-8 -*-
"""DXF 总览：图层、实体分布、图块 INSERT、文字标注"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import ezdxf
from collections import Counter, defaultdict

PATH = r"C:\Users\Windows 11\Desktop\机电\阳山卫生间大样\2~4层给排水_布局1.dxf"
doc = ezdxf.readfile(PATH)
print("DXF version:", doc.dxfversion)
print("Layouts:", [l for l in doc.layout_names()])

for space_name, space in [("MODEL", doc.modelspace())] + [(n, doc.layout(n)) for n in doc.layout_names() if n != "Model"]:
    ents = list(space)
    if not ents:
        print(f"\n=== {space_name}: empty ===")
        continue
    print(f"\n=== {space_name}: {len(ents)} entities ===")
    layer_type = Counter()
    for e in ents:
        layer_type[(e.dxf.layer, e.dxftype())] += 1
    by_layer = defaultdict(list)
    for (lay, typ), n in layer_type.items():
        by_layer[lay].append((typ, n))
    for lay in sorted(by_layer):
        items = ", ".join(f"{t}:{n}" for t, n in sorted(by_layer[lay]))
        print(f"  [{lay}] {items}")

# INSERT block names in modelspace
msp = doc.modelspace()
print("\n=== INSERT blocks (modelspace) ===")
ins = Counter()
for e in msp.query("INSERT"):
    ins[(e.dxf.name, e.dxf.layer)] += 1
for (name, lay), n in sorted(ins.items(), key=lambda x: -x[1]):
    print(f"  {name}  layer={lay}  x{n}")

# Text contents
print("\n=== TEXT/MTEXT contents (modelspace) ===")
txt = Counter()
for e in msp.query("TEXT MTEXT"):
    s = e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()
    s = s.strip()
    if s:
        txt[(s, e.dxf.layer)] += 1
for (s, lay), n in sorted(txt.items()):
    print(f"  '{s}'  layer={lay}  x{n}")
