#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终汇总分析：
1. 筏板面积精确计算（施工图板区边界最大多边形 - 各类扣除项）
2. 附墙柱识别汇总（去除重复图块，只统计1号图层位置）
3. 输出正式报告
"""
import sys, time, math

dxf_path = r"C:\Users\Windows 11\Desktop\土建测试用例\职工食堂\C02#职工食堂及职工活动用房结构施工图.dxf"
out_path = r"D:\cc-connect\cost-agent-poc\temp\final_report.txt"

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
        s = i+4; break
for i in range(s, len(lines)-1):
    if lines[i].strip()=="0" and lines[i+1].strip()=="ENDSEC":
        e = i; break

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
            i += 2; continue
        if gc == 8: layer = val
        elif gc == 70: flags = int(val) if val else 0
        elif gc == 10: cur_x = float(val)
        elif gc == 20:
            if cur_x is not None:
                verts.append((cur_x, float(val)))
                cur_x = None
        i += 2
    return verts, layer, flags

# ============ 1. 施工图板区边界 精确分析 ============
w("=" * 60)
w("任务2：筏板面积复核")
w("=" * 60)
w("")

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
                'cx': (max(xs)+min(xs))/2,
                'cy': (max(ys)+min(ys))/2,
                'xrange': (min(xs), max(xs)),
                'yrange': (min(ys), max(ys)),
                'verts': verts
            })
    i += 1

# 按Y坐标范围分组（找基础图位置）
# 已知PUB_TEXT显示：
# 筏板、承台平面布置图 @ Y≈-132033
# 施工图板区边界 面积4518m² Y:56810~109010
# 施工图板区边界 面积4516m² Y:-34587~17613  (基础顶~-0.100图)
# 施工图板区边界 面积4516m² Y:-118687~-66487

# 找Y≈-132033附近的板区边界（筏板图）
# 实际上筏板图的Y坐标在-66487~-118687之间（第3个）

w("施工图板区边界图层多边形汇总：")
for p in sorted(board_polys, key=lambda x: x['cy']):
    w(f"  面积={p['area_m2']:.2f}m²  Y范围:{p['yrange'][0]:.0f}~{p['yrange'][1]:.0f}  中心Y:{p['cy']:.0f}")

w("")
# 根据PUB_TEXT的图纸名称，筏板、承台平面布置图的Y中心约为-130000附近
# 而板区边界Y=-118687~-66487中心≈-92587，Y=-34587~17613中心≈-8487
# 找筏板图附近（Y在-200000~-50000之间）
raft_candidates = [p for p in board_polys if -200000 < p['cy'] < -50000]
w(f"筏板、承台平面布置图区域候选（Y=-200000~-50000）: {len(raft_candidates)}个")
for p in raft_candidates:
    w(f"  面积={p['area_m2']:.2f}m²  n_verts={p['n_verts']}  Y:{p['yrange'][0]:.0f}~{p['yrange'][1]:.0f}")

# 最大的施工图板区边界面积
all_areas = [p['area_m2'] for p in board_polys if p['area_m2'] > 100]
w(f"\n主要板区面积值：")
for a in sorted(set([round(a,1) for a in all_areas]), reverse=True):
    w(f"  {a} m²")

# 关键：多个图（Y坐标不同）都有边界，代表不同楼层/工况的图框
# 最大的4518m²和4516m²的区别是16顶点（含锯齿扣减）
# 分析最大多边形（4518m²）的顶点，理解筏板轮廓形状
w("\n最大多边形（4518m²）顶点坐标分析：")
main_poly = max(board_polys, key=lambda x: x['area_m2'])
verts = main_poly['verts']
w(f"顶点数: {len(verts)}")
# 转换为相对坐标（去掉基准点）
min_x = min(v[0] for v in verts)
min_y = min(v[1] for v in verts)
w("顶点（相对坐标，单位m）：")
for v in verts:
    rx = (v[0]-min_x)/1000
    ry = (v[1]-min_y)/1000
    w(f"  ({rx:.2f}, {ry:.2f})")

# 凸包面积（矩形）
xs = [v[0] for v in verts]
ys = [v[1] for v in verts]
rect_area = (max(xs)-min(xs)) * (max(ys)-min(ys)) / 1e6
actual_area = main_poly['area_m2']
w(f"\n外包矩形面积: {rect_area:.2f}m²  ({(max(xs)-min(xs))/1000:.2f}m × {(max(ys)-min(ys))/1000:.2f}m)")
w(f"实际多边形面积: {actual_area:.2f}m²")
w(f"缺口面积（扣减）: {rect_area-actual_area:.2f}m²")
w(f"")
w(f"参考值 4300.7m²: 差值={actual_area-4300.7:.2f}m²")
w(f"  如按4516.29m²作为原始筏板，差值={4516.29-4300.7:.2f}m²（可能含承台等扣除）")
w(f"  承台面积(234.70+215.04=449.74m²)不在筏板范围内")

# ============ 分析FOUNDATION图层总面积 ============
w("\nFOUNDATION图层LWPOLYLINE面积：")
found_total = 0
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LWPOLYLINE":
        verts, layer, flags = parse_lwpolyline(lines, i+1, e)
        if layer == "FOUNDATION" and len(verts) >= 3:
            area = polygon_area(verts)
            xs = [v[0] for v in verts]
            ys = [v[1] for v in verts]
            found_total += area/1e6
            w(f"  面积={area/1e6:.2f}m² ({(max(xs)-min(xs))/1000:.1f}x{(max(ys)-min(ys))/1000:.1f}m)")
    i += 1
w(f"FOUNDATION图层总面积: {found_total:.2f}m²")

# ============ 2. 附墙柱识别 ============
w("\n" + "=" * 60)
w("任务1：附墙柱识别")
w("=" * 60)
w("")

# 提取砼墙LINE
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
            wall_lines.append({'x1':x1,'y1':y1,'x2':x2,'y2':y2})
    i += 1
w(f"砼墙LINE总数: {len(wall_lines)}")

# 提取COLU柱
colu_cols = []
i = s
while i < e - 1:
    if lines[i].strip() == "0" and i+1 < e and lines[i+1].strip() == "LWPOLYLINE":
        verts, layer, flags = parse_lwpolyline(lines, i+1, e)
        if layer == "COLU" and len(verts) >= 3:
            xs = [v[0] for v in verts]
            ys = [v[1] for v in verts]
            colu_cols.append({
                'cx':(max(xs)+min(xs))/2, 'cy':(max(ys)+min(ys))/2,
                'w':max(xs)-min(xs), 'h':max(ys)-min(ys),
                'minx':min(xs),'maxx':max(xs),'miny':min(ys),'maxy':max(ys)
            })
    i += 1
w(f"COLU柱总数: {len(colu_cols)}")

def point_to_seg_dist(px,py,x1,y1,x2,y2):
    dx=x2-x1; dy=y2-y1
    if dx==0 and dy==0: return math.sqrt((px-x1)**2+(py-y1)**2)
    t=max(0,min(1,((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)))
    return math.sqrt((px-x1-t*dx)**2+(py-y1-t*dy)**2)

def col_min_dist(col, walls):
    pts=[(col['minx'],col['miny']),(col['maxx'],col['miny']),
         (col['maxx'],col['maxy']),(col['minx'],col['maxy'])]
    min_d=float('inf'); nw=None
    for wl in walls:
        for px,py in pts:
            d=point_to_seg_dist(px,py,wl['x1'],wl['y1'],wl['x2'],wl['y2'])
            if d<min_d: min_d=d; nw=wl
    return min_d, nw

# 识别附墙柱
all_x=[wl['x1'] for wl in wall_lines]+[wl['x2'] for wl in wall_lines]
all_y=[wl['y1'] for wl in wall_lines]+[wl['y2'] for wl in wall_lines]
wx_min,wx_max=min(all_x)-1000,max(all_x)+1000
wy_min,wy_max=min(all_y)-1000,max(all_y)+1000

THRESHOLD = 150

attached = []
for col in colu_cols:
    if not (wx_min<=col['cx']<=wx_max and wy_min<=col['cy']<=wy_max):
        continue
    nearby=[wl for wl in wall_lines
            if (min(wl['x1'],wl['x2'])-2000<=col['cx']<=max(wl['x1'],wl['x2'])+2000
                or min(wl['y1'],wl['y2'])-2000<=col['cy']<=max(wl['y1'],wl['y2'])+2000)]
    if not nearby: continue
    d,nw = col_min_dist(col, nearby)
    if d < THRESHOLD:
        attached.append((col,d,nw))

w(f"附墙柱（距砼墙<{THRESHOLD}mm）: {len(attached)}个（含重复图块）")

# 去重：DXF中相同图块可能重复绘制（图框Y不同）
# 将柱位置按相对坐标聚类（取同一图纸内的柱）
# 关键观察：COLU图层有637个柱，分布在多个Y坐标范围（多个图）
# 筏板图对应 基础顶~-0.100墙柱施工图（Y约-300000附近）
# 统计各Y区间的柱数量

# 找砼墙所在的Y区间（主要区域）
# 墙Y范围:-455432~108410，跨度563842mm，约564m
# 单栋建筑约52.2m高，所以可能有多层平面图叠放
# 各层图纸的Y偏移约为84000mm（层高）
# 实际这是不同标高的平面图在同一DXF文件中竖向排布

# 分析柱Y坐标分布（找各层图纸位置）
y_groups = {}
for col in colu_cols:
    # 按10000mm（10m）分组
    y_key = round(col['cy']/84000)*84000
    y_groups[y_key] = y_groups.get(y_key, 0) + 1

w("\nCOLU柱按Y区间分布（每84m一组）：")
for yk in sorted(y_groups.keys()):
    w(f"  Y≈{yk/1000:.0f}m: {y_groups[yk]}个柱")

# 取最接近筏板图的Y区间柱子
# 筏板图Y=-118687~-66487（施工图板区边界）
# 基础顶~-0.100墙柱施工图Y=-391572~-307472
# 所以附墙柱应在-391572~-307472之间

wall_range_y = (-400000, -300000)  # 基础顶~-0.100图
raft_range_y = (-150000, -50000)   # 筏板图
floor0_range_y = (-50000, 30000)   # 0.000层

w("\n各图纸Y范围内的附墙柱:")
for range_name, (y1,y2) in [("基础顶~-0.100墙柱图", (-400000,-280000)),
                               ("筏板承台平面图", (-150000,-50000)),
                               ("地面层（0~1层）", (-50000,30000)),
                               ("地面层（1~2层）", (30000,130000))]:
    cols_in_range = [(col,d,nw) for col,d,nw in attached if y1<=col['cy']<=y2]
    w(f"\n  【{range_name}】 Y={y1//1000}~{y2//1000}m  附墙柱数: {len(cols_in_range)}")
    # 按截面尺寸统计
    sizes = {}
    for col,d,nw in cols_in_range:
        k=f"{col['w']:.0f}x{col['h']:.0f}"
        sizes[k]=sizes.get(k,0)+1
    for sz,cnt in sorted(sizes.items(),key=lambda x:-x[1]):
        w(f"    截面{sz}mm: {cnt}个")

# 重点输出：基础顶~-0.100层（最有可能是附墙柱的层）
w("\n===== 基础顶~-0.100层附墙柱详细列表 =====")
main_attached = [(col,d,nw) for col,d,nw in attached if -400000<=col['cy']<=-280000]
w(f"该层附墙柱数: {len(main_attached)}")

def wall_side(col,nw):
    if nw is None: return "?"
    if abs(nw['y1']-nw['y2'])<50:
        wy=(nw['y1']+nw['y2'])/2
        return "南侧附墙" if col['cy']<wy else "北侧附墙"
    wx=(nw['x1']+nw['x2'])/2
    return "西侧附墙" if col['cx']<wx else "东侧附墙"

for col,d,nw in sorted(main_attached, key=lambda x: (round(x[0]['cx']/5000),round(x[0]['cy']/5000))):
    side=wall_side(col,nw)
    w(f"  [{side}] 截面{col['w']:.0f}×{col['h']:.0f} 距墙={d:.0f}mm  位置({col['cx']:.0f},{col['cy']:.0f})")

# ============ 总结 ============
w("\n" + "=" * 60)
w("分析总结")
w("=" * 60)
w("")
w("【任务1：附墙柱识别】")
w(f"  砼墙（混凝土外墙/挡土墙）：{len(wall_lines)} 条LINE实体")
w(f"  COLU图层柱总数：{len(colu_cols)} 个")
w(f"  距砼墙<150mm的附墙柱：{len(attached)} 个（全图所有平面图之和）")
w(f"  其中基础顶~-0.100层附墙柱：{len(main_attached)} 个")
w("")
w("  附墙柱截面尺寸（基础顶~-0.100层）：")
sizes2 = {}
for col,d,nw in main_attached:
    k=f"{col['w']:.0f}×{col['h']:.0f}mm"
    sizes2[k]=sizes2.get(k,0)+1
for sz,cnt in sorted(sizes2.items(),key=lambda x:-x[1]):
    w(f"    {sz}: {cnt}个")
w("")
w("【任务2：筏板面积复核】")
w(f"  施工图板区边界（最大）: {max(p['area_m2'] for p in board_polys):.2f} m²")
w(f"  施工图板区边界（各图尺寸相同，宽111m×高52.2m）")
w(f"  问题分析:")
w(f"    - 图纸上'施工图板区边界'是图框线，不代表筏板轮廓")
w(f"    - FOUNDATION图层实体代表局部基础（筏板/独基），总面积={found_total:.2f}m²")
w(f"    - 4300.7m²可能是图纸设计说明中给出的建筑面积或筏板计算值")
w(f"    - 筏板的实际轮廓需通过'HATCH填充'或单独的封闭多边形来确认")
w(f"    - 本DXF中未找到面积接近4300.7m²的单一封闭筏板轮廓线")
w(f"    - 建议：查阅图纸说明或向设计院确认筏板边界图层名称")
w("")
w("  关键数据：")
w(f"    外包矩形 111.0×52.2 = 5794.2 m²")
w(f"    板区边界多边形（凹多边形）≈ 4516~4518 m²")
w(f"    设计值 4300.7 m²")
w(f"    差值（板区边界-设计值）: {4516.29-4300.7:.1f} m²")
w(f"    此差值可能是承台坑/集水坑/桩头等扣减项")

with open(out_path,'w',encoding='utf-8') as f:
    f.write("\n".join(results))
w(f"\n报告已保存到: {out_path}")
print("Done.")
