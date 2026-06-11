# -*- coding: utf-8 -*-
import ezdxf, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

PATH = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
doc = ezdxf.readfile(PATH)
msp = doc.modelspace()

print("=== LAYOUTS ===")
for name in doc.layout_names():
    print(name)

print("\n=== LAYERS (count of entities in msp) ===")
layer_count = collections.Counter()
type_count = collections.Counter()
for e in msp:
    layer_count[e.dxf.layer] += 1
    type_count[e.dxftype()] += 1
for k, v in layer_count.most_common(60):
    print(f"{k}: {v}")
print("\n=== ENTITY TYPES ===")
for k, v in type_count.most_common():
    print(f"{k}: {v}")

print("\n=== TEXT/MTEXT count ===")
texts = [e for e in msp if e.dxftype() in ("TEXT", "MTEXT")]
print(len(texts))
