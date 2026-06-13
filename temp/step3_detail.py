#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入分析DXF：
1. 解析COLU图层LWPOLYLINE（柱截面轮廓）
2. 解析"砼墙"图层（挡土墙/外墙）
3. 解析FOUNDATION图层（筏板轮廓）
4. 解析"柱截面轮廓"图层
5. 分析筏板面积（通过计算LWPOLYLINE包围面积）
"""
import sys, time, math

dxf_path = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
out_path = r"D:\cc-connect\cost-agent-poc\temp\detail_result.txt"

print("读取文件...")
t0 = time.time()
with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
t1 = time.time()
print(f"总行数: {len(lines)}，耗时: {t1-t0:.1f}s")

results = []
def w(msg):
    results.append(str(msg))
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

def polygon_area(pts):
    """Shoelace公式计算多边形面积"""
    n = len(pts)
    if n < 3:
        return 0
    area = 0
    for i in range(n):
        j = (i+1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    return abs(area) / 2

def parse_lwpolyline(lines, start, end):
    """
    解析LWPOLYLINE实体，返回顶点列表和属性
    start: 实体类型行（"LWPOLYLINE"所在行）
    """
    props = {}
    vertices = []
    i = start + 1
    cur_x = None
    while i < end - 1:
        code = lines[i].strip()
        val = lines[i+1].strip() if i+1 < end else ""
        if code == "0":
            break
        try:
            gc = int(code)
        except:
            i += 2
            continue

        if gc == 8:
            props['layer'] = val
        elif gc == 90:
            props['vertex_count'] = int(val) if val else 0
        elif gc == 70:
            props['flags'] = int(val) if val else 0  # 1=closed
        elif gc == 10:
            cur_x = float(val)
        elif gc == 20:
            if cur_x is not None:
                vertices.append((cur_x, float(val)))
                cur_x = None
        elif gc == 43:
            props['width'] = float(val) if val else 0

        i += 2

    props['vertices'] = vertices
    return props

# ============ 扫描感兴趣的图层实体 ============
target_layers = {'COLU', '柱截面轮廓', '砼墙', 'FOUNDATION', 'HATCH', 'E-hatch  250'}
# 注：FOUNDATION只有少量LWPOLYLINE，应该就是筏板边界

entities_by_layer = {l: [] for l in target_layers}

i = s
ent_count = 0
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e:
        etype = lines[i+1].strip()
        if etype in ("LWPOLYLINE", "LINE", "POLYLINE", "HATCH"):
            # 找图层
            layer = ""
            for j in range(i+2, min(i+20, e)):
                if lines[j].strip() == "0":
                    break
                if lines[j].strip() == "8" and j+1 < e:
                    layer = lines[j+1].strip()
                    break

            if layer in target_layers:
                if etype == "LWPOLYLINE":
                    props = parse_lwpolyline(lines, i+1, e)
                    props['etype'] = etype
                    props['start_line'] = i
                    entities_by_layer[layer].append(props)
                else:
                    ent = {'etype': etype, 'layer': layer, 'start_line': i}
                    for j in range(i+2, min(i+100, e)):
                        if lines[j].strip() == "0":
                            break
                        try:
                            gc = int(lines[j].strip())
                            val = lines[j+1].strip() if j+1 < e else ""
                            ent[gc] = val
                        except:
                            pass
                    entities_by_layer[layer].append(ent)
    i += 1

for layer, ents in entities_by_layer.items():
    w(f"图层[{layer}]: {len(ents)}个实体")

# ============ 分析COLU图层柱子 ============
w("\n=== COLU图层柱子分析 ===")
colu_polys = entities_by_layer.get('COLU', [])
col_info = []
for p in colu_polys:
    if p.get('etype') != 'LWPOLYLINE':
        continue
    verts = p.get('vertices', [])
    if len(verts) < 3:
        continue
    area = polygon_area(verts)
    # 计算边界框（bbox）
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    w_dim = max(xs) - min(xs)  # 宽
    h_dim = max(ys) - min(ys)  # 高
    cx = (max(xs)+min(xs))/2
    cy = (max(ys)+min(ys))/2
    col_info.append({
        'cx': cx, 'cy': cy,
        'width': round(w_dim),
        'height': round(h_dim),
        'area': area,
        'n_verts': len(verts)
    })

w(f"COLU图层共 {len(col_info)} 个柱截面")
# 按截面尺寸分组
size_groups = {}
for c in col_info:
    key = f"{c['width']}x{c['height']}"
    size_groups[key] = size_groups.get(key, 0) + 1
w("截面尺寸分布（单位mm）：")
for k, cnt in sorted(size_groups.items(), key=lambda x: -x[1]):
    w(f"  {k}: {cnt}个")

# 打印前20个柱位置（mm坐标）
w("\n前20个柱位置（中心坐标mm）：")
for c in col_info[:20]:
    w(f"  中心({c['cx']:.0f},{c['cy']:.0f}) 截面{c['width']}x{c['height']}")

# ============ 分析"柱截面轮廓"图层 ============
w("\n=== 柱截面轮廓图层分析 ===")
csec_polys = entities_by_layer.get('柱截面轮廓', [])
w(f"柱截面轮廓图层: {len(csec_polys)} 个实体")
csec_info = []
for p in csec_polys:
    if p.get('etype') != 'LWPOLYLINE':
        continue
    verts = p.get('vertices', [])
    if len(verts) < 3:
        continue
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    w_dim = max(xs) - min(xs)
    h_dim = max(ys) - min(ys)
    cx = (max(xs)+min(xs))/2
    cy = (max(ys)+min(ys))/2
    csec_info.append({'cx': cx, 'cy': cy, 'width': round(w_dim), 'height': round(h_dim)})

w("柱截面尺寸分布：")
csec_size_groups = {}
for c in csec_info:
    key = f"{c['width']}x{c['height']}"
    csec_size_groups[key] = csec_size_groups.get(key, 0) + 1
for k, cnt in sorted(csec_size_groups.items(), key=lambda x: -x[1]):
    w(f"  {k}: {cnt}个")

for c in csec_info[:20]:
    w(f"  中心({c['cx']:.0f},{c['cy']:.0f}) 截面{c['width']}x{c['height']}")

# ============ 分析"砼墙"图层 ============
w("\n=== 砼墙图层分析 ===")
wall_ents = entities_by_layer.get('砼墙', [])
w(f"砼墙图层: {len(wall_ents)} 个实体")
for ent in wall_ents[:10]:
    w(f"  {ent.get('etype')} layer={ent.get('layer')} keys={list(ent.keys())[:10]}")

# ============ 分析FOUNDATION图层 ============
w("\n=== FOUNDATION图层分析（筏板）===")
found_ents = entities_by_layer.get('FOUNDATION', [])
w(f"FOUNDATION图层: {len(found_ents)} 个实体")
total_foundation_area = 0
for ent in found_ents:
    w(f"  etype={ent.get('etype')} n_verts={len(ent.get('vertices', []))} layer={ent.get('layer')}")
    verts = ent.get('vertices', [])
    if len(verts) >= 3:
        area = polygon_area(verts)
        area_m2 = area / 1e6  # mm² -> m²
        w(f"    面积: {area:.0f} mm² = {area_m2:.2f} m²")
        total_foundation_area += area_m2
        # 打印顶点
        for v in verts[:5]:
            w(f"    顶点: ({v[0]:.1f}, {v[1]:.1f})")
        if len(verts) > 5:
            w(f"    ... 共{len(verts)}个顶点")

w(f"FOUNDATION图层总面积: {total_foundation_area:.2f} m²")

# ============ 也检查HATCH图层 ============
w("\n=== HATCH图层分析 ===")
hatch_ents = entities_by_layer.get('HATCH', [])
w(f"HATCH图层: {len(hatch_ents)} 个实体")
for ent in hatch_ents[:3]:
    w(f"  {ent}")

# ============ 分析TEXT实体找柱标注信息 ============
w("\n=== 分析柱标注文字（柱集中标注/柱原位标注）===")
text_layers = {'柱集中标注', '柱原位标注', '柱表文字'}
text_entities = []

i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e:
        etype = lines[i+1].strip()
        if etype in ("TEXT", "MTEXT", "ATTDEF"):
            layer = ""
            text_val = ""
            x, y = 0, 0
            for j in range(i+2, min(i+50, e)):
                if lines[j].strip() == "0":
                    break
                try:
                    gc = int(lines[j].strip())
                    val = lines[j+1].strip() if j+1 < e else ""
                    if gc == 8: layer = val
                    elif gc == 1: text_val = val
                    elif gc == 10: x = float(val)
                    elif gc == 20: y = float(val)
                except:
                    pass
            if layer in text_layers:
                text_entities.append({'layer': layer, 'text': text_val, 'x': x, 'y': y})
    i += 1

w(f"柱标注文字实体数: {len(text_entities)}")
# 打印含KZ/GBZ/附墙柱的文字
kz_texts = [t for t in text_entities if any(k in t['text'].upper() for k in ['KZ','GBZ','FBZ','AZ','QZ','附'])]
w(f"含KZ/GBZ/附等关键字文字: {len(kz_texts)}")
for t in kz_texts[:30]:
    w(f"  [{t['layer']}] '{t['text']}' @ ({t['x']:.0f},{t['y']:.0f})")

# 打印全部集中标注
w("\n全部柱集中标注：")
for t in [t for t in text_entities if t['layer']=='柱集中标注']:
    w(f"  '{t['text']}' @ ({t['x']:.0f},{t['y']:.0f})")

# ============ 保存结果 ============
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(results))
w(f"\n结果已保存到: {out_path}")
print("Done.")
