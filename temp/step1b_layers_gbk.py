#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1b: 用GBK编码列出DXF文件的所有图层名
"""
import sys, time

dxf_path = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"

print(f"开始读取文件(GBK)...")
t0 = time.time()

try:
    with open(dxf_path, 'r', encoding='gbk', errors='replace') as f:
        lines = f.readlines()
except Exception as ex:
    # fallback utf-8
    with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

t1 = time.time()
print(f"总行数: {len(lines)}，耗时: {t1-t0:.1f}s")

# 找ENTITIES区段
s, e = 0, len(lines)
for i in range(len(lines)-3):
    if (lines[i].strip()=="0" and lines[i+1].strip()=="SECTION"
            and lines[i+2].strip()=="2" and lines[i+3].strip()=="ENTITIES"):
        s = i+4
        break

for i in range(s, len(lines)-1):
    if lines[i].strip()=="0" and lines[i+1].strip()=="ENDSEC":
        e = i
        break

print(f"ENTITIES区段: 行{s} ~ 行{e}")

# 提取所有图层名
layers = set()
for i in range(s, e-1):
    if lines[i].strip() == "8":
        layers.add(lines[i+1].strip())

print(f"\n共找到 {len(layers)} 个图层：")
for l in sorted(layers):
    print(f"  [{l}]")

# TABLES中的图层
print("\n===== TABLES图层 =====")
table_layers = set()
in_layer_table = False
for i in range(len(lines)-3):
    if lines[i].strip()=="0" and lines[i+1].strip()=="TABLE":
        if lines[i+2].strip()=="2" and lines[i+3].strip()=="LAYER":
            in_layer_table = True
    if in_layer_table:
        if lines[i].strip()=="0" and lines[i+1].strip()=="ENDTAB":
            in_layer_table = False
        if lines[i].strip()=="2" and in_layer_table:
            val = lines[i+1].strip()
            if val not in ("LAYER","TABLE"):
                table_layers.add(val)

print(f"TABLES图层数: {len(table_layers)}")
for l in sorted(table_layers):
    print(f"  [{l}]")

print("\nDone.")
