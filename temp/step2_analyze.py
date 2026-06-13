#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析DXF文件：
1. 列出所有图层名（UTF-8读取，输出到文件）
2. 分析COLU/WALL等图层的实体
3. 分析FOUNDATION图层（筏板）
"""
import sys, time, json, math

dxf_path = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
out_path = r"D:\cc-connect\cost-agent-poc\temp\analysis_result.txt"

print(f"读取文件...")
t0 = time.time()
with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
t1 = time.time()
print(f"总行数: {len(lines)}，耗时: {t1-t0:.1f}s")

results = []

def w(msg):
    results.append(msg)
    print(msg)

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

w(f"ENTITIES区段: 行{s} ~ 行{e}")

# 提取所有图层名
layers = set()
for i in range(s, e-1):
    if lines[i].strip() == "8":
        layers.add(lines[i+1].strip())

w(f"\n=== 所有图层（{len(layers)}个）===")
for l in sorted(layers):
    w(f"  {l}")

# ============ 解析实体函数 ============
def parse_entity(lines, start):
    """从start行开始，解析一个实体，返回(entity_type, props_dict, end_line)"""
    etype = lines[start].strip()
    props = {'_type': etype}
    i = start + 1
    while i < len(lines) - 1:
        code = lines[i].strip()
        val = lines[i+1].strip() if i+1 < len(lines) else ""
        # 到了下一个实体
        if code == "0":
            return etype, props, i
        try:
            code_int = int(code)
        except:
            i += 2
            continue
        props[code_int] = val
        i += 2
    return etype, props, i

# ============ 找柱相关图层的实体 ============
w("\n=== 柱相关图层分析 ===")
col_layers = [l for l in layers if any(k in l.upper() for k in ["COLU","KZ","GBZ","柱","ZHU"])]
w(f"柱相关图层: {col_layers}")

# ============ 找挡土墙/外墙相关图层 ============
wall_layers = [l for l in layers if any(k in l.upper() for k in ["WALL","DWQ","SCQ","外墙","挡土","WQ"])]
w(f"墙相关图层: {wall_layers}")

# ============ 找筏板/底板相关图层 ============
foundation_layers = [l for l in layers if any(k in l for k in ["FOUNDATION","筏板","底板","S4","SLAB","FLOOR"])]
w(f"基础/筏板相关图层: {foundation_layers}")

# ============ 扫描ENTITIES段，提取各类实体 ============
w("\n=== 扫描实体 ===")

# 先统计各图层的实体类型分布
layer_entity_count = {}  # layer -> {etype: count}
colu_entities = []   # 柱图层实体
wall_entities = []   # 墙图层实体
foundation_entities = []  # 基础图层实体
hatch_entities = []  # HATCH实体（填充，用于面积计算）

i = s
while i < e - 1:
    code = lines[i].strip()
    if code == "0" and i+1 < e:
        etype = lines[i+1].strip()
        if etype in ("SECTION", "ENDSEC", "EOF"):
            i += 2
            continue

        # 找图层
        layer = ""
        for j in range(i+2, min(i+40, e)):
            if lines[j].strip() == "8" and j+1 < e:
                layer = lines[j+1].strip()
                break
            if lines[j].strip() == "0":  # 下一个实体开始
                break

        # 统计
        if layer not in layer_entity_count:
            layer_entity_count[layer] = {}
        layer_entity_count[layer][etype] = layer_entity_count[layer].get(etype, 0) + 1

        # 收集柱实体
        if layer in col_layers and etype in ("INSERT","LWPOLYLINE","POLYLINE","SOLID","HATCH"):
            # 收集此实体的关键属性
            ent = {'type': etype, 'layer': layer, 'line': i}
            for j in range(i+2, min(i+80, e)):
                if lines[j].strip() == "0":
                    break
                try:
                    gc = int(lines[j].strip())
                    val = lines[j+1].strip() if j+1 < e else ""
                    if gc in (10,11,12,20,21,22,30,40,41,42,43,44,50,2):
                        ent[gc] = val
                except:
                    pass
            colu_entities.append(ent)

        # 收集墙实体
        if layer in wall_layers:
            ent = {'type': etype, 'layer': layer, 'line': i}
            for j in range(i+2, min(i+60, e)):
                if lines[j].strip() == "0":
                    break
                try:
                    gc = int(lines[j].strip())
                    val = lines[j+1].strip() if j+1 < e else ""
                    if gc in (10,11,12,20,21,22,30,40,41,2):
                        ent[gc] = val
                except:
                    pass
            wall_entities.append(ent)

        # 收集基础/筏板HATCH实体（用于面积计算）
        if layer in foundation_layers and etype == "HATCH":
            ent = {'type': etype, 'layer': layer, 'line': i}
            hatch_entities.append(ent)

        # 收集所有HATCH（包括FOUNDATION图层）
        if etype == "HATCH" and layer == "FOUNDATION":
            ent = {'type': etype, 'layer': layer, 'line': i, 'props': {}}
            for j in range(i+2, min(i+200, e)):
                if lines[j].strip() == "0":
                    break
                try:
                    gc = int(lines[j].strip())
                    val = lines[j+1].strip() if j+1 < e else ""
                    ent['props'][gc] = val
                except:
                    pass
            foundation_entities.append(ent)

    i += 1

w(f"柱实体数: {len(colu_entities)}")
w(f"墙实体数: {len(wall_entities)}")
w(f"FOUNDATION HATCH数: {len(foundation_entities)}")

# ============ 各图层实体类型统计 ============
w("\n=== 各图层实体类型统计（柱/墙/基础相关）===")
interest_layers = set(col_layers + wall_layers + foundation_layers)
for layer in sorted(interest_layers):
    if layer in layer_entity_count:
        w(f"  图层[{layer}]: {layer_entity_count[layer]}")

# ============ 打印前几个柱实体 ============
w("\n=== 柱实体样本（前10个）===")
for ent in colu_entities[:10]:
    w(f"  {ent}")

# ============ 打印前几个墙实体 ============
w("\n=== 墙实体样本（前10个）===")
for ent in wall_entities[:10]:
    w(f"  {ent}")

# ============ FOUNDATION HATCH属性 ============
w("\n=== FOUNDATION HATCH样本（前3个）===")
for ent in foundation_entities[:3]:
    w(f"  props: {ent['props']}")

# ============ 保存结果 ============
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(results))
w(f"\n结果已保存到: {out_path}")

print("\nDone.")
