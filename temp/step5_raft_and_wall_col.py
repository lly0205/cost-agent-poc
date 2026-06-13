#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重点分析：
1. 精确计算筏板面积（分析 施工图板区边界 / FOUNDATION 等图层的大面积多边形）
2. 提取所有砼墙LINE实体
3. 分析COLU柱是否紧贴砼墙（附墙柱识别）
4. 查找INSERT块（柱表通常用块表示）
5. 深入分析柱图层块名称
"""
import sys, time, math

dxf_path = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
out_path = r"D:\cc-connect\cost-agent-poc\temp\raft_walcol_result.txt"

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

def polygon_area(pts):
    n = len(pts)
    if n < 3: return 0
    area = 0
    for i in range(n):
        j = (i+1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    return abs(area) / 2

def parse_lwpolyline(lines, start, end_limit):
    verts = []
    layer = ""
    flags = 0
    i = start + 1
    cur_x = None
    while i < end_limit - 1:
        code = lines[i].strip()
        val = lines[i+1].strip() if i+1 < end_limit else ""
        if code == "0": break
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
                verts.append((cur_x, float(val)))
                cur_x = None
        i += 2
    return verts, layer, flags

# ============ 详细分析 施工图板区边界 图层多边形 ============
w("=== 施工图板区边界 图层多边形详细分析 ===")
board_polys = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LWPOLYLINE":
        verts, layer, flags = parse_lwpolyline(lines, i+1, e)
        if layer == "施工图板区边界" and len(verts) >= 3:
            area = polygon_area(verts)
            xs = [v[0] for v in verts]
            ys = [v[1] for v in verts]
            board_polys.append({
                'area_m2': area/1e6,
                'n_verts': len(verts),
                'xrange': (min(xs), max(xs)),
                'yrange': (min(ys), max(ys)),
                'verts': verts
            })
    i += 1

w(f"施工图板区边界多边形: {len(board_polys)}个")
for p in sorted(board_polys, key=lambda x: -x['area_m2']):
    w(f"  面积={p['area_m2']:.2f}m²  n_verts={p['n_verts']}")
    w(f"    X: {p['xrange'][0]:.0f} ~ {p['xrange'][1]:.0f}  宽={(p['xrange'][1]-p['xrange'][0])/1000:.2f}m")
    w(f"    Y: {p['yrange'][0]:.0f} ~ {p['yrange'][1]:.0f}  高={(p['yrange'][1]-p['yrange'][0])/1000:.2f}m")
    w(f"    顶点: {[(round(v[0]),round(v[1])) for v in p['verts']]}")

# ============ 所有大LWPOLYLINE ============
w("\n=== 所有大LWPOLYLINE（>200m²）的详细顶点 ===")
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LWPOLYLINE":
        verts, layer, flags = parse_lwpolyline(lines, i+1, e)
        if len(verts) >= 3:
            area = polygon_area(verts)
            if area/1e6 > 200 and layer not in ("BORDER",):
                xs = [v[0] for v in verts]
                ys = [v[1] for v in verts]
                w(f"  图层[{layer}] 面积={area/1e6:.2f}m²  n_verts={len(verts)}")
                w(f"    X: {min(xs):.0f}~{max(xs):.0f} 宽={(max(xs)-min(xs))/1000:.1f}m, Y: {min(ys):.0f}~{max(ys):.0f} 高={(max(ys)-min(ys))/1000:.1f}m")
    i += 1

# ============ 全部砼墙LINE提取（不限200个）============
w("\n=== 砼墙图层全部LINE实体 ===")
wall_lines = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LINE":
        layer = ""
        x1,y1,x2,y2 = 0,0,0,0
        for j in range(i+2, min(i+40, e)):
            if lines[j].strip() == "0": break
            try:
                gc = int(lines[j].strip())
                val = lines[j+1].strip() if j+1 < e else ""
                if gc == 8: layer = val
                elif gc == 10: x1 = float(val)
                elif gc == 20: y1 = float(val)
                elif gc == 11: x2 = float(val)
                elif gc == 21: y2 = float(val)
            except: pass
        if layer == "砼墙":
            wall_lines.append({'x1':x1,'y1':y1,'x2':x2,'y2':y2,
                                'len':math.sqrt((x2-x1)**2+(y2-y1)**2)})
    i += 1

w(f"砼墙LINE总数: {len(wall_lines)}")

# 找砼墙的X/Y坐标分布（边界）
all_x = [wl['x1'] for wl in wall_lines] + [wl['x2'] for wl in wall_lines]
all_y = [wl['y1'] for wl in wall_lines] + [wl['y2'] for wl in wall_lines]
w(f"砼墙坐标范围: X [{min(all_x):.0f}, {max(all_x):.0f}], Y [{min(all_y):.0f}, {max(all_y):.0f}]")

# 找砼墙最外边界线段（通常附墙柱在墙最外侧）
# 分析Y轴最大值的水平线（上边界）和Y轴最小值的水平线（下边界）
# 分析X轴最大值的垂直线（右边界）和X轴最小值的垂直线（左边界）
def is_horiz(wl, tol=10): return abs(wl['y1']-wl['y2']) < tol
def is_vert(wl, tol=10): return abs(wl['x1']-wl['x2']) < tol

# 最外圈线段坐标
max_y = max(all_y)
min_y = min(all_y)
max_x = max(all_x)
min_x = min(all_x)

top_lines = [wl for wl in wall_lines if is_horiz(wl) and abs(max(wl['y1'],wl['y2'])-max_y)<50]
bot_lines = [wl for wl in wall_lines if is_horiz(wl) and abs(min(wl['y1'],wl['y2'])-min_y)<50]
right_lines = [wl for wl in wall_lines if is_vert(wl) and abs(max(wl['x1'],wl['x2'])-max_x)<50]
left_lines = [wl for wl in wall_lines if is_vert(wl) and abs(min(wl['x1'],wl['x2'])-min_x)<50]

w(f"\n砼墙最上边界Y≈{max_y:.0f}的水平线: {len(top_lines)}条")
for wl in top_lines[:5]:
    w(f"  ({wl['x1']:.0f},{wl['y1']:.0f})->({wl['x2']:.0f},{wl['y2']:.0f}) L={wl['len']:.0f}")

w(f"砼墙最左边界X≈{min_x:.0f}的垂直线: {len(left_lines)}条")
for wl in left_lines[:5]:
    w(f"  ({wl['x1']:.0f},{wl['y1']:.0f})->({wl['x2']:.0f},{wl['y2']:.0f}) L={wl['len']:.0f}")

w(f"砼墙最右边界X≈{max_x:.0f}的垂直线: {len(right_lines)}条")
for wl in right_lines[:5]:
    w(f"  ({wl['x1']:.0f},{wl['y1']:.0f})->({wl['x2']:.0f},{wl['y2']:.0f}) L={wl['len']:.0f}")

# ============ 附墙柱识别 ============
w("\n=== 附墙柱识别 ===")
# 策略：COLU图层柱子中心点距离砼墙外边界线很近（<400mm即为附墙柱）

# 提取所有COLU柱
colu_cols = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LWPOLYLINE":
        verts, layer, flags = parse_lwpolyline(lines, i+1, e)
        if layer == "COLU" and len(verts) >= 3:
            xs = [v[0] for v in verts]
            ys = [v[1] for v in verts]
            cx = (max(xs)+min(xs))/2
            cy = (max(ys)+min(ys))/2
            w_dim = max(xs)-min(xs)
            h_dim = max(ys)-min(ys)
            colu_cols.append({
                'cx':cx, 'cy':cy, 'w':w_dim, 'h':h_dim,
                'minx':min(xs), 'maxx':max(xs),
                'miny':min(ys), 'maxy':max(ys)
            })
    i += 1

w(f"COLU柱总数: {len(colu_cols)}")

def point_to_segment_dist(px, py, x1, y1, x2, y2):
    """点到线段距离"""
    dx = x2-x1; dy = y2-y1
    if dx==0 and dy==0:
        return math.sqrt((px-x1)**2+(py-y1)**2)
    t = max(0,min(1, ((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)))
    nx = x1+t*dx; ny = y1+t*dy
    return math.sqrt((px-nx)**2+(py-ny)**2)

def col_to_wall_min_dist(col, wall_lines):
    """柱bbox边缘到最近墙线段的最小距离"""
    # 用柱的四个角点
    pts = [(col['minx'],col['miny']), (col['maxx'],col['miny']),
           (col['maxx'],col['maxy']), (col['minx'],col['maxy'])]
    min_d = float('inf')
    nearest = None
    for wl in wall_lines:
        for px,py in pts:
            d = point_to_segment_dist(px,py,wl['x1'],wl['y1'],wl['x2'],wl['y2'])
            if d < min_d:
                min_d = d
                nearest = wl
    return min_d, nearest

# 筛选：距任意砼墙线段<150mm的柱（附墙柱判定）
THRESHOLD = 150  # mm

# 先筛选Y坐标在砼墙范围内的柱
wall_y_min = min_y - 1000
wall_y_max = max_y + 1000
wall_x_min = min_x - 1000
wall_x_max = max_x + 1000

candidate_cols = [c for c in colu_cols
                  if wall_x_min <= c['cx'] <= wall_x_max
                  and wall_y_min <= c['cy'] <= wall_y_max]

w(f"在砼墙坐标范围内的柱: {len(candidate_cols)}个")

# 对候选柱计算到墙的最近距离
# 为加速，只用Y方向相近的墙线
attached_cols = []
for col in candidate_cols:
    # 预过滤：只用X或Y坐标相近的墙线（±2000mm）
    nearby_walls = [wl for wl in wall_lines
                    if (min(wl['x1'],wl['x2'])-2000 <= col['cx'] <= max(wl['x1'],wl['x2'])+2000
                        or min(wl['y1'],wl['y2'])-2000 <= col['cy'] <= max(wl['y1'],wl['y2'])+2000)]
    if not nearby_walls:
        continue
    d, nearest = col_to_wall_min_dist(col, nearby_walls)
    if d < THRESHOLD:
        # 判断附墙类型
        col['wall_dist'] = d
        col['nearest_wall'] = nearest
        # 判断附在哪一侧（上/下/左/右）
        side = ""
        if nearest:
            # 水平墙线
            if abs(nearest['y1']-nearest['y2']) < 50:
                wy = (nearest['y1']+nearest['y2'])/2
                if col['cy'] < wy:
                    side = "南侧附墙（柱在墙下方）"
                else:
                    side = "北侧附墙（柱在墙上方）"
            else:  # 垂直墙线
                wx = (nearest['x1']+nearest['x2'])/2
                if col['cx'] < wx:
                    side = "西侧附墙（柱在墙左侧）"
                else:
                    side = "东侧附墙（柱在墙右侧）"
        col['wall_side'] = side
        attached_cols.append(col)

w(f"\n附墙柱（距砼墙<{THRESHOLD}mm）: {len(attached_cols)}个")
for c in attached_cols:
    nw = c['nearest_wall']
    w(f"  柱中心({c['cx']:.0f},{c['cy']:.0f}) 截面{c['w']:.0f}x{c['h']:.0f} 距墙={c['wall_dist']:.0f}mm [{c['wall_side']}]")
    w(f"    最近墙线: ({nw['x1']:.0f},{nw['y1']:.0f})->({nw['x2']:.0f},{nw['y2']:.0f})")

# 也用更大阈值看看
w(f"\n附墙柱（距砼墙<300mm）：")
attached_300 = []
for col in candidate_cols:
    nearby_walls = [wl for wl in wall_lines
                    if (min(wl['x1'],wl['x2'])-2000 <= col['cx'] <= max(wl['x1'],wl['x2'])+2000
                        or min(wl['y1'],wl['y2'])-2000 <= col['cy'] <= max(wl['y1'],wl['y2'])+2000)]
    if not nearby_walls: continue
    d, nearest = col_to_wall_min_dist(col, nearby_walls)
    if d < 300:
        attached_300.append((col, d, nearest))

w(f"共 {len(attached_300)} 个（距墙<300mm）")
for col, d, nw in attached_300:
    w(f"  柱中心({col['cx']:.0f},{col['cy']:.0f}) 截面{col['w']:.0f}x{col['h']:.0f} 距墙={d:.0f}mm")

# ============ 查看INSERT块（柱名称）============
w("\n=== INSERT块信息（柱相关图层）===")
inserts = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "INSERT":
        layer = ""
        block_name = ""
        x, y = 0.0, 0.0
        for j in range(i+2, min(i+60, e)):
            if lines[j].strip() == "0": break
            try:
                gc = int(lines[j].strip())
                val = lines[j+1].strip() if j+1 < e else ""
                if gc == 8: layer = val
                elif gc == 2: block_name = val
                elif gc == 10: x = float(val)
                elif gc == 20: y = float(val)
            except: pass
        inserts.append({'layer':layer,'block':block_name,'x':x,'y':y})
    i += 1

w(f"全图INSERT块数: {len(inserts)}")
# 按图层统计
layer_blocks = {}
for ins in inserts:
    key = ins['layer']
    if key not in layer_blocks:
        layer_blocks[key] = {}
    layer_blocks[key][ins['block']] = layer_blocks[key].get(ins['block'],0)+1

for lyr, blocks in sorted(layer_blocks.items()):
    if any(k in lyr.upper() for k in ['COLU','KZ','GBZ','柱','WALL','挡']):
        w(f"  图层[{lyr}]: {blocks}")

# 打印柱/墙相关图层的所有INSERT
w("\nCOLU/柱 图层的INSERT（前20个）：")
for ins in inserts:
    if 'COLU' in ins['layer'].upper() or '柱' in ins['layer']:
        w(f"  [{ins['layer']}] block='{ins['block']}' @ ({ins['x']:.0f},{ins['y']:.0f})")
    if len([x for x in results if x.startswith('  [')]) > 20:
        break

# ============ 保存 ============
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(results))
w(f"\n结果已保存到: {out_path}")
print("Done.")
