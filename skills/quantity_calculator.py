"""
工程量自动计算工具函数库
适用于 GB50854-2013 房屋建筑与装饰工程计量规范

可直接脚本化的计算部分：
- 钢筋理论重量
- 门窗洞口扣减
- 土方/垫层/基础等体积面积计算
- 构件净高计算（含Rule 1板厚扣除）
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# 钢筋理论重量表（kg/m），常用规格
# ─────────────────────────────────────────────

REBAR_UNIT_WEIGHT: dict[int, float] = {
    6:  0.222,
    8:  0.395,
    10: 0.617,
    12: 0.888,
    14: 1.208,
    16: 1.578,
    18: 1.998,
    20: 2.466,
    22: 2.984,
    25: 3.853,
    28: 4.834,
    32: 6.313,
    36: 7.990,
    40: 9.865,
}


def rebar_weight(diameter_mm: int, length_m: float) -> float:
    """计算钢筋重量 (kg)。diameter_mm 为公称直径（mm），length_m 为计算长度（m）。"""
    unit = REBAR_UNIT_WEIGHT.get(diameter_mm)
    if unit is None:
        # 通用公式：ρ=0.00617*d²  (kg/m，d in mm)
        unit = 0.00617 * diameter_mm ** 2
    return round(unit * length_m, 4)


def rebar_weight_tons(diameter_mm: int, length_m: float) -> float:
    """计算钢筋重量 (t)。"""
    return round(rebar_weight(diameter_mm, length_m) / 1000, 6)


# ─────────────────────────────────────────────
# 门窗洞口数据结构与扣减计算
# ─────────────────────────────────────────────

@dataclass
class DoorWindowOpening:
    """单个门窗洞口数据（来源：图纸门窗表）"""
    code: str           # 门窗编号，如 M1、C2
    width_mm: float     # 洞口宽度（mm）
    height_mm: float    # 洞口高度（mm）
    count: int = 1      # 数量
    wall_thickness_mm: float = 200.0  # 所在墙厚（mm），用于体积扣减

    @property
    def area_m2(self) -> float:
        """单个洞口面积（㎡）"""
        return round((self.width_mm / 1000) * (self.height_mm / 1000), 4)

    @property
    def total_area_m2(self) -> float:
        """该编号所有洞口总面积（㎡）"""
        return round(self.area_m2 * self.count, 4)

    @property
    def volume_m3(self) -> float:
        """单个洞口体积（m³），用于砌体扣减"""
        return round(self.area_m2 * (self.wall_thickness_mm / 1000), 4)

    @property
    def total_volume_m3(self) -> float:
        """该编号所有洞口总体积（m³）"""
        return round(self.volume_m3 * self.count, 4)


def deduct_openings_area(openings: list[DoorWindowOpening], min_area_m2: float = 0.3) -> dict:
    """
    计算门窗洞口面积扣减汇总。
    min_area_m2：单个面积小于此值的不扣（默认0.3㎡）。
    返回：{编号: {area_m2, count, total_deduct_m2}}
    """
    result = {}
    total = 0.0
    for op in openings:
        if op.area_m2 <= min_area_m2:
            continue
        deduct = op.total_area_m2
        result[op.code] = {
            "width_mm": op.width_mm,
            "height_mm": op.height_mm,
            "area_m2": op.area_m2,
            "count": op.count,
            "total_deduct_m2": deduct,
        }
        total += deduct
    result["__total_deduct_m2__"] = round(total, 4)
    return result


def deduct_openings_volume(openings: list[DoorWindowOpening], min_area_m2: float = 0.3) -> dict:
    """
    计算门窗洞口体积扣减汇总（用于砌体墙体积计算）。
    返回：{编号: {volume_m3, count, total_deduct_m3}}
    """
    result = {}
    total = 0.0
    for op in openings:
        if op.area_m2 <= min_area_m2:
            continue
        deduct = op.total_volume_m3
        result[op.code] = {
            "width_mm": op.width_mm,
            "height_mm": op.height_mm,
            "wall_thickness_mm": op.wall_thickness_mm,
            "volume_m3": op.volume_m3,
            "count": op.count,
            "total_deduct_m3": deduct,
        }
        total += deduct
    result["__total_deduct_m3__"] = round(total, 4)
    return result


# ─────────────────────────────────────────────
# 柱净高计算（Rule 1 + 造价师确认的3种情形）
# ─────────────────────────────────────────────
#
# 有梁板：柱基面 → 上层楼板上表面，然后Rule 1扣板厚
#         净高 = 层高 - 上层板厚
# 无梁板：柱基面 → 柱帽下表面
#         净高 = 层高 - 柱帽高度（Rule 1不适用，已止于柱帽底）
# 框架柱：柱基面 → 柱顶全高，然后Rule 1扣板厚
#         净高 = 层高 - 板厚（与有梁板相同）
#
# 构造柱：嵌接墙体马牙槎体积并入；净高计算同上

COLUMN_TYPE_BEAMED = "有梁板"    # 有梁板体系
COLUMN_TYPE_FLAT   = "无梁板"    # 无梁板体系（需传入柱帽高度）
COLUMN_TYPE_FRAME  = "框架柱"    # 框架柱（同有梁板，别名）


def column_net_height(
    floor_height_mm: float,
    slab_thickness_mm: float,
    column_type: str = COLUMN_TYPE_BEAMED,
    cap_height_mm: float = 0.0,
) -> float:
    """
    柱净高（m）。
    column_type: '有梁板'/'框架柱' → 净高 = 层高 - 板厚（Rule 1）
                 '无梁板'         → 净高 = 层高 - 柱帽高度
    """
    if column_type == COLUMN_TYPE_FLAT:
        if cap_height_mm <= 0:
            raise ValueError("无梁板柱型必须传入 cap_height_mm（柱帽高度）")
        net = (floor_height_mm - cap_height_mm) / 1000
    else:
        net = (floor_height_mm - slab_thickness_mm) / 1000
    return round(net, 4)


def column_volume(
    section_width_mm: float,
    section_height_mm: float,
    floor_height_mm: float,
    slab_thickness_mm: float,
    column_type: str = COLUMN_TYPE_BEAMED,
    cap_height_mm: float = 0.0,
    embedded_wall_volume_m3: float = 0.0,
) -> dict:
    """
    柱工程量（m³）。
    column_type: COLUMN_TYPE_BEAMED/'框架柱' → Rule 1扣板厚
                 COLUMN_TYPE_FLAT            → 扣柱帽高度，需传入 cap_height_mm
    embedded_wall_volume_m3: 构造柱嵌接墙体马牙槎体积，并入总量
    """
    net_h = column_net_height(floor_height_mm, slab_thickness_mm, column_type, cap_height_mm)
    section_m2 = (section_width_mm / 1000) * (section_height_mm / 1000)
    body_vol = round(section_m2 * net_h, 4)
    total_vol = round(body_vol + embedded_wall_volume_m3, 4)

    deduct_label = f"板厚{slab_thickness_mm}mm" if column_type != COLUMN_TYPE_FLAT else f"柱帽{cap_height_mm}mm"
    return {
        "column_type": column_type,
        "section_width_mm": section_width_mm,
        "section_height_mm": section_height_mm,
        "floor_height_mm": floor_height_mm,
        "deduct_mm": cap_height_mm if column_type == COLUMN_TYPE_FLAT else slab_thickness_mm,
        "deduct_label": deduct_label,
        "net_height_m": net_h,
        "body_volume_m3": body_vol,
        "embedded_wall_m3": embedded_wall_volume_m3,
        "total_volume_m3": total_vol,
        "formula": (
            f"{section_width_mm/1000:.3f}×{section_height_mm/1000:.3f}"
            f"×({floor_height_mm}-{cap_height_mm if column_type==COLUMN_TYPE_FLAT else slab_thickness_mm})/1000"
            f"{'+ '+str(embedded_wall_volume_m3) if embedded_wall_volume_m3 else ''}"
            f" = {total_vol} m³"
        ),
    }


# ─────────────────────────────────────────────
# 土方计算
# ─────────────────────────────────────────────

def earthwork_trench(base_width_m: float, base_length_m: float, depth_m: float) -> dict:
    """挖沟槽土方（基础垫层底面积 × 挖土深度）"""
    area = round(base_width_m * base_length_m, 4)
    vol = round(area * depth_m, 4)
    return {
        "base_width_m": base_width_m,
        "base_length_m": base_length_m,
        "depth_m": depth_m,
        "base_area_m2": area,
        "volume_m3": vol,
        "formula": f"{base_width_m}×{base_length_m}×{depth_m} = {vol} m³",
    }


def earthwork_pit(base_width_m: float, base_length_m: float, depth_m: float) -> dict:
    """挖基坑土方（同沟槽计算逻辑）"""
    return earthwork_trench(base_width_m, base_length_m, depth_m)


def backfill_foundation(excavation_vol_m3: float, buried_structure_vol_m3: float) -> dict:
    """基础回填 = 挖方体积 - 自然地坪以下埋设的基础（含垫层）体积"""
    backfill = round(excavation_vol_m3 - buried_structure_vol_m3, 4)
    return {
        "excavation_vol_m3": excavation_vol_m3,
        "buried_structure_vol_m3": buried_structure_vol_m3,
        "backfill_vol_m3": max(backfill, 0),
        "formula": f"{excavation_vol_m3} - {buried_structure_vol_m3} = {backfill} m³",
    }


# ─────────────────────────────────────────────
# 砌体墙工程量计算
# ─────────────────────────────────────────────

def masonry_wall_volume(
    length_m: float,
    height_m: float,
    thickness_m: float,
    openings: Optional[list[DoorWindowOpening]] = None,
    embedded_rc_vol_m3: float = 0.0,
) -> dict:
    """
    砌体墙工程量（m³）。
    Rule 2：必须扣除所有门窗洞口体积，尺寸来自门窗表。
    同时扣除嵌入墙内的钢筋混凝土柱梁圈梁等体积。
    """
    gross_vol = round(length_m * height_m * thickness_m, 4)
    deduct_openings = 0.0
    opening_detail = {}

    if openings:
        deduct_info = deduct_openings_volume(openings)
        deduct_openings = deduct_info.get("__total_deduct_m3__", 0.0)
        opening_detail = {k: v for k, v in deduct_info.items() if not k.startswith("__")}

    net_vol = round(gross_vol - deduct_openings - embedded_rc_vol_m3, 4)

    return {
        "length_m": length_m,
        "height_m": height_m,
        "thickness_m": thickness_m,
        "gross_volume_m3": gross_vol,
        "deduct_openings_m3": deduct_openings,
        "deduct_rc_m3": embedded_rc_vol_m3,
        "net_volume_m3": max(net_vol, 0),
        "opening_detail": opening_detail,
        "formula": (
            f"{length_m}×{height_m}×{thickness_m}"
            f"{' - '+str(deduct_openings) if deduct_openings else ''}"
            f"{' - '+str(embedded_rc_vol_m3) if embedded_rc_vol_m3 else ''}"
            f" = {max(net_vol, 0)} m³"
        ),
    }


# ─────────────────────────────────────────────
# 面积类（通用）
# ─────────────────────────────────────────────

def rectangle_area(length_m: float, width_m: float) -> float:
    """矩形面积（㎡）"""
    return round(length_m * width_m, 4)


def slope_area(horizontal_area_m2: float, slope_ratio: float) -> float:
    """
    斜屋面/坡屋面面积（㎡）。
    slope_ratio = tan(θ)，水平投影面积 × √(1 + slope²)
    """
    return round(horizontal_area_m2 * math.sqrt(1 + slope_ratio ** 2), 4)


# ─────────────────────────────────────────────
# 清单编码查找（关键字匹配）
# ─────────────────────────────────────────────

_CODE_INDEX: dict[str, str] = {
    "平整场地": "010101001",
    "挖一般土方": "010101002",
    "挖沟槽土方": "010101003",
    "挖基坑土方": "010101004",
    "回填方": "010103001",
    "余方弃置": "010103002",
    "垫层": "010501001",          # 混凝土垫层（优先）
    "砌筑垫层": "010404001",
    "带形基础": "010501002",
    "独立基础": "010501003",
    "满堂基础": "010501004",
    "桩承台基础": "010501005",
    "矩形柱": "010502001",
    "框架柱": "010502001",
    "构造柱": "010502002",
    "基础梁": "010503001",
    "矩形梁": "010503002",
    "圈梁": "010503004",
    "过梁": "010503005",
    "有梁板": "010505001",
    "无梁板": "010505002",
    "平板": "010505003",
    "楼梯": "010506001",
    "直形楼梯": "010506001",
    "砖基础": "010401001",
    "实心砖墙": "010401003",
    "多孔砖墙": "010401004",
    "空心砖墙": "010401005",
    "填充墙": "010401008",
    "砌块墙": "010402001",
    "木质门": "010801001",
    "木门": "010801001",
    "金属门": "010802001",
    "塑钢门": "010802001",
    "防火门": "010802003",
    "金属窗": "010807001",
    "塑钢窗": "010807001",
    "断桥铝窗": "010807001",
    "屋面卷材防水": "010902001",
    "屋面防水": "010902001",
    "墙面抹灰": "011201001",
    "天棚抹灰": "011301001",
    "吊顶": "011302001",
    "现浇构件钢筋": "010515001",
    "钢筋": "010515001",
    "综合脚手架": "011701001",
    "模板": "011702001",
    "垂直运输": "011703001",
}


def lookup_boq_code(keyword: str) -> Optional[str]:
    """根据关键字查找清单编码。精确匹配 → 关键字包含匹配。"""
    if keyword in _CODE_INDEX:
        return _CODE_INDEX[keyword]
    for k, v in _CODE_INDEX.items():
        if keyword in k or k in keyword:
            return v
    return None


# ─────────────────────────────────────────────
# CLI 入口（直接运行时演示）
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 钢筋重量示例 ===")
    print(f"φ16, 长度 5.8m: {rebar_weight(16, 5.8)} kg")
    print(f"φ25, 长度 12.3m: {rebar_weight_tons(25, 12.3)} t")

    print("\n=== 柱工程量（3种情形）===")
    # 情形1：有梁板（Rule 1 扣板厚）
    col1 = column_volume(600, 600, 3600, 120, column_type="有梁板")
    print(f"有梁板: 净高={col1['net_height_m']}m  公式={col1['formula']}")

    # 情形2：无梁板（扣柱帽高度）
    col2 = column_volume(600, 600, 3600, 0, column_type="无梁板", cap_height_mm=300)
    print(f"无梁板: 净高={col2['net_height_m']}m  公式={col2['formula']}")

    # 情形3：构造柱（有梁板体系，嵌接墙体并入）
    col3 = column_volume(240, 240, 3600, 120, column_type="有梁板", embedded_wall_volume_m3=0.05)
    print(f"构造柱: 净高={col3['net_height_m']}m  总量={col3['total_volume_m3']}m³  公式={col3['formula']}")

    print("\n=== 门窗洞口扣减示例（Rule 2）===")
    openings = [
        DoorWindowOpening("M1", 1000, 2100, count=3, wall_thickness_mm=240),
        DoorWindowOpening("C1", 1500, 1500, count=6, wall_thickness_mm=240),
        DoorWindowOpening("C2", 600, 600, count=2, wall_thickness_mm=240),   # ≤0.3㎡不扣
    ]
    deduct = deduct_openings_volume(openings)
    for k, v in deduct.items():
        print(f"  {k}: {v}")

    print("\n=== 砌体墙工程量 ===")
    wall = masonry_wall_volume(
        length_m=6.0,
        height_m=3.48,      # 3600 - 120mm板厚 = 3480mm
        thickness_m=0.24,
        openings=openings,
        embedded_rc_vol_m3=0.15,
    )
    print(f"公式: {wall['formula']}")
