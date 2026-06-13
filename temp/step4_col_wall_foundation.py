#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入分析：
1. 找真正的柱名称文字（KZ、GBZ、QZ、AZ、FBZ等）
2. 提取砼墙图层的LINE实体坐标（挡土墙/外墙）
3. 找筏板真实面积（可能在HATCH或其他图层中）
4. 分析柱与墙的空间关系（附墙柱识别）
"""
import sys, time, math

dxf_path = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
out_path = r"D:\cc-connect\cost-agent-poc\temp\col_wall_result.txt"

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
    n = len(pts)
    if n < 3: return 0
    area = 0
    for i in range(n):
        j = (i+1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    return abs(area) / 2

def parse_lwpolyline_verts(lines, start, end_limit):
    """解析LWPOLYLINE返回顶点列表"""
    vertices = []
    layer = ""
    flags = 0
    i = start + 1
    cur_x = None
    while i < end_limit - 1:
        code = lines[i].strip()
        val = lines[i+1].strip() if i+1 < end_limit else ""
        if code == "0":
            break
        try:
            gc = int(code)
        except:
            i += 2
            continue
        if gc == 8: layer = val
        elif gc == 70: flags = int(val) if val else 0
        elif gc == 10: cur_x = float(val)
        elif gc == 20:
            if cur_x is not None:
                vertices.append((cur_x, float(val)))
                cur_x = None
        i += 2
    return vertices, layer, flags

# ============ 全文本扫描：找柱名称 ============
w("\n=== 全局文本扫描：找柱编号（KZ/GBZ/QZ/AZ/FBZ/TZ/附墙）===")
col_name_texts = []
all_texts_by_layer = {}

i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e:
        etype = lines[i+1].strip()
        if etype in ("TEXT", "MTEXT"):
            layer = ""
            text_val = ""
            x, y = 0.0, 0.0
            for j in range(i+2, min(i+60, e)):
                if lines[j].strip() == "0":
                    break
                try:
                    gc = int(lines[j].strip())
                    val = lines[j+1].strip() if j+1 < e else ""
                    if gc == 8: layer = val
                    elif gc == 1: text_val = val
                    elif gc == 3: text_val = text_val + val  # MTEXT continuation
                    elif gc == 10: x = float(val)
                    elif gc == 20: y = float(val)
                except:
                    pass

            # 只看有柱相关内容的文本
            tu = text_val.upper()
            if any(k in tu for k in ['KZ','GBZ','QZ','AZ','FBZ','TZ','柱','附墙','WALL']):
                col_name_texts.append({'layer': layer, 'text': text_val, 'x': x, 'y': y})

            # 统计所有文本图层
            if layer not in all_texts_by_layer:
                all_texts_by_layer[layer] = []
            all_texts_by_layer[layer].append({'text': text_val, 'x': x, 'y': y})
    i += 1

w(f"找到含柱名关键字文本: {len(col_name_texts)} 个")
for t in col_name_texts[:50]:
    w(f"  [{t['layer']}] '{t['text']}' @ ({t['x']:.0f},{t['y']:.0f})")

# ============ 分析 柱表文字 的实际内容 ============
w("\n=== 柱表文字内容（前100个）===")
for t in all_texts_by_layer.get('柱表文字', [])[:100]:
    w(f"  '{t['text']}' @ ({t['x']:.0f},{t['y']:.0f})")

# ============ 分析 柱原位标注 内容 ============
w("\n=== 柱原位标注内容（全部）===")
for t in all_texts_by_layer.get('柱原位标注', []):
    w(f"  '{t['text']}' @ ({t['x']:.0f},{t['y']:.0f})")

# ============ 分析 PUB_TEXT 内容（通常含截面信息）===
w("\n=== PUB_TEXT 内容（前50个）===")
for t in all_texts_by_layer.get('PUB_TEXT', [])[:50]:
    w(f"  '{t['text']}' @ ({t['x']:.0f},{t['y']:.0f})")

# ============ 提取砼墙LINE坐标 ============
w("\n=== 砼墙图层LINE实体（前30个）===")
wall_lines = []
i = s
count = 0
while i < e - 1 and count < 200:
    if lines[i].strip() == "0" and i+1 < e:
        etype = lines[i+1].strip()
        if etype == "LINE":
            layer = ""
            x1,y1,x2,y2 = 0,0,0,0
            for j in range(i+2, min(i+40, e)):
                if lines[j].strip() == "0":
                    break
                try:
                    gc = int(lines[j].strip())
                    val = lines[j+1].strip() if j+1 < e else ""
                    if gc == 8: layer = val
                    elif gc == 10: x1 = float(val)
                    elif gc == 20: y1 = float(val)
                    elif gc == 11: x2 = float(val)
                    elif gc == 21: y2 = float(val)
                except:
                    pass
            if layer == "砼墙":
                wall_lines.append({'x1':x1,'y1':y1,'x2':x2,'y2':y2,'len':math.sqrt((x2-x1)**2+(y2-y1)**2)})
                count += 1
    i += 1

w(f"砼墙LINE实体（前200个）: {len(wall_lines)}个")
for wl in wall_lines[:30]:
    w(f"  ({wl['x1']:.0f},{wl['y1']:.0f}) -> ({wl['x2']:.0f},{wl['y2']:.0f})  长={wl['len']:.0f}mm")

# ============ 砼墙坐标范围 ============
if wall_lines:
    all_x = [wl['x1'] for wl in wall_lines] + [wl['x2'] for wl in wall_lines]
    all_y = [wl['y1'] for wl in wall_lines] + [wl['y2'] for wl in wall_lines]
    w(f"\n砼墙X范围: {min(all_x):.0f} ~ {max(all_x):.0f}  跨度={max(all_x)-min(all_x):.0f}mm")
    w(f"砼墙Y范围: {min(all_y):.0f} ~ {max(all_y):.0f}  跨度={max(all_y)-min(all_y):.0f}mm")

# ============ 统计COLU坐标范围 ============
w("\n=== COLU柱坐标范围 ===")
colu_polys = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LWPOLYLINE":
        layer = ""
        for j in range(i+2, min(i+20, e)):
            if lines[j].strip() == "0": break
            if lines[j].strip() == "8" and j+1 < e:
                layer = lines[j+1].strip(); break
        if layer == "COLU":
            verts, _, _ = parse_lwpolyline_verts(lines, i+1, e)
            if len(verts) >= 3:
                xs = [v[0] for v in verts]
                ys = [v[1] for v in verts]
                colu_polys.append({
                    'cx': (max(xs)+min(xs))/2, 'cy': (max(ys)+min(ys))/2,
                    'w': max(xs)-min(xs), 'h': max(ys)-min(ys),
                    'minx': min(xs), 'maxx': max(xs),
                    'miny': min(ys), 'maxy': max(ys)
                })
    i += 1

if colu_polys:
    all_cx = [c['cx'] for c in colu_polys]
    all_cy = [c['cy'] for c in colu_polys]
    w(f"COLU柱中心X范围: {min(all_cx):.0f} ~ {max(all_cx):.0f}")
    w(f"COLU柱中心Y范围: {min(all_cy):.0f} ~ {max(all_cy):.0f}")

# ============ 找大面积HATCH（筏板面积候选）============
w("\n=== 全图HATCH实体面积统计 ===")
# HATCH实体含有边界路径，组码91=路径数，组码92=路径类型，组码93=顶点数
# 路径中组码10/20是顶点
# 也可能用组码47（面积）直接给出
hatch_areas = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "HATCH":
        layer = ""
        area_val = None
        boundary_pts = []
        cur_x = None
        in_boundary = False
        in_polyline_path = False
        for j in range(i+2, min(i+2000, e)):
            if lines[j].strip() == "0": break
            try:
                gc = int(lines[j].strip())
                val = lines[j+1].strip() if j+1 < e else ""
                if gc == 8: layer = val
                # 面积直接给出（47=pixel size，42=elevation，97=source obj count）
                # HATCH的面积通常在路径中计算
                # 边界路径：92=边界类型，93=顶点数
                if gc == 92: in_polyline_path = True
                if gc == 93 and in_polyline_path:
                    pass  # vertex count
                if gc == 10 and in_polyline_path:
                    cur_x = float(val)
                if gc == 20 and in_polyline_path and cur_x is not None:
                    boundary_pts.append((cur_x, float(val)))
                    cur_x = None
                # 面积字段（某些软件输出）
                if gc == 42: area_val = float(val)
            except:
                pass

        if len(boundary_pts) >= 3:
            area = polygon_area(boundary_pts)
            hatch_areas.append({'layer': layer, 'area_mm2': area, 'area_m2': area/1e6, 'n_pts': len(boundary_pts)})
        elif area_val is not None:
            hatch_areas.append({'layer': layer, 'area_mm2': area_val, 'area_m2': area_val/1e6, 'n_pts': 0})
    i += 1

w(f"全图HATCH实体数（含边界计算）: {len(hatch_areas)}")
for ha in sorted(hatch_areas, key=lambda x: -x['area_m2'])[:30]:
    w(f"  图层[{ha['layer']}] 面积={ha['area_m2']:.2f}m² (n_pts={ha['n_pts']})")

# ============ 找"施工图板区边界"或其他大面积LWPOLYLINE ============
w("\n=== 找大面积LWPOLYLINE（>100m²）===")
large_polys = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LWPOLYLINE":
        verts, layer, flags = parse_lwpolyline_verts(lines, i+1, e)
        if len(verts) >= 3:
            area = polygon_area(verts)
            area_m2 = area / 1e6
            if area_m2 > 100:
                xs = [v[0] for v in verts]
                ys = [v[1] for v in verts]
                large_polys.append({
                    'layer': layer, 'area_m2': area_m2,
                    'n_verts': len(verts),
                    'xrange': (min(xs), max(xs)),
                    'yrange': (min(ys), max(ys))
                })
    i += 1

w(f"找到大面积LWPOLYLINE: {len(large_polys)}个")
for p in sorted(large_polys, key=lambda x: -x['area_m2'])[:30]:
    w(f"  图层[{p['layer']}] 面积={p['area_m2']:.2f}m²  n_verts={p['n_verts']}")
    w(f"    X: {p['xrange'][0]:.0f} ~ {p['xrange'][1]:.0f}")
    w(f"    Y: {p['yrange'][0]:.0f} ~ {p['yrange'][1]:.0f}")

# ============ 保存 ============
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(results))
w(f"\n结果已保存到: {out_path}")
print("Done.")
