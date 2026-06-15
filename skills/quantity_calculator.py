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
# 基础工程计算（垫层、承台、基础梁模板）
# 规则来源：D01#~D04# 实操总结，2026-06-08
# ─────────────────────────────────────────────

def calc_cushion_volume(
    foundation_width_mm: float,
    span_m: float,
    count: int,
    extend_mm: float = 100.0,
    thickness_mm: float = 100.0,
) -> dict:
    """
    梁下垫层体积（m³）。
    foundation_width_mm: 基础梁宽（mm）
    span_m: 梁净跨（m）
    count: 根数×栋数
    extend_mm: 每边外扩量（默认100mm）
    thickness_mm: ⚠️ 必须从图纸设计说明取值，不得使用默认值100mm
                  无地下室单体通常100mm C20；筏板/地下室通常150mm C15
    """
    cushion_width_m = (foundation_width_mm + extend_mm * 2) / 1000
    thickness_m = thickness_mm / 1000
    vol = round(cushion_width_m * span_m * thickness_m * count, 4)
    return {
        "foundation_width_mm": foundation_width_mm,
        "cushion_width_m": cushion_width_m,
        "span_m": span_m,
        "thickness_m": thickness_m,
        "count": count,
        "volume_m3": vol,
        "formula": f"{cushion_width_m}×{span_m}×{thickness_m}×{count} = {vol} m³",
    }


def calc_footing_cushion_volume(
    length_mm: float,
    width_mm: float,
    count: int,
    extend_mm: float = 100.0,
    thickness_mm: float = 100.0,
) -> dict:
    """
    承台下垫层体积（m³）。每边外扩 extend_mm。
    thickness_mm: ⚠️ 必须从图纸设计说明取值，不得使用默认值100mm
    """
    l = (length_mm + extend_mm * 2) / 1000
    w = (width_mm + extend_mm * 2) / 1000
    t = thickness_mm / 1000
    vol = round(l * w * t * count, 4)
    return {
        "cushion_length_m": l,
        "cushion_width_m": w,
        "thickness_m": t,
        "count": count,
        "volume_m3": vol,
        "formula": f"{l}×{w}×{t}×{count} = {vol} m³",
    }


def calc_cushion_formwork(
    span_m: float,
    count: int,
    thickness_mm: float = 100.0,
) -> dict:
    """
    梁下垫层侧面模板（m²）。两长侧面，端头不计。
    thickness_mm: ⚠️ 必须与垫层实际厚度一致，不得默认100mm
    """
    t = thickness_mm / 1000
    area = round(2 * span_m * t * count, 4)
    return {
        "span_m": span_m,
        "thickness_m": t,
        "count": count,
        "area_m2": area,
        "formula": f"2×{span_m}×{t}×{count} = {area} m²",
    }


def calc_footing_cushion_formwork(
    length_mm: float,
    width_mm: float,
    count: int,
    extend_mm: float = 100.0,
    thickness_mm: float = 100.0,
) -> dict:
    """
    承台下垫层四侧面模板（m²）。
    """
    l = (length_mm + extend_mm * 2) / 1000
    w = (width_mm + extend_mm * 2) / 1000
    t = thickness_mm / 1000
    area = round((l + w) * 2 * t * count, 4)
    return {
        "cushion_length_m": l,
        "cushion_width_m": w,
        "thickness_m": t,
        "count": count,
        "area_m2": area,
        "formula": f"({l}+{w})×2×{t}×{count} = {area} m²",
    }


def calc_footing_formwork(
    length_mm: float,
    width_mm: float,
    height_mm: float,
    count: int,
) -> dict:
    """
    承台四侧面模板（m²）。按侧面粘灰面计算。
    """
    l = length_mm / 1000
    w = width_mm / 1000
    h = height_mm / 1000
    area = round((l + w) * 2 * h * count, 4)
    return {
        "length_m": l,
        "width_m": w,
        "height_m": h,
        "count": count,
        "area_m2": area,
        "formula": f"({l}+{w})×2×{h}×{count} = {area} m²",
    }


def calc_beam_formwork(
    beam_h_mm: float,
    span_m: float,
    count: int,
    beam_w_mm: float = 0.0,
    is_foundation: bool = True,
) -> dict:
    """
    梁模板面积（m²）。
    is_foundation=True  → 基础梁：仅两侧面 = 梁高×2×净跨×根数
    is_foundation=False → 楼层/屋面梁：三面 = (梁高×2+梁宽)×净跨×根数
    """
    h = beam_h_mm / 1000
    w = beam_w_mm / 1000
    if is_foundation:
        perimeter = h * 2
        sides = "两侧面"
    else:
        if beam_w_mm <= 0:
            raise ValueError("楼层梁/屋面梁需传入 beam_w_mm（梁宽）")
        perimeter = h * 2 + w
        sides = "三面（底+两侧）"
    area = round(perimeter * span_m * count, 4)
    return {
        "beam_h_m": h,
        "beam_w_m": w,
        "span_m": span_m,
        "count": count,
        "is_foundation": is_foundation,
        "sides": sides,
        "area_m2": area,
        "formula": f"{perimeter:.3f}×{span_m}×{count} = {area} m²  ({sides})",
    }


def calc_pile_cap_in_raft(
    cap_l_mm: float,
    cap_w_mm: float,
    cap_h_total_mm: float,
    raft_thickness_mm: float,
    count: int,
) -> dict:
    """
    筏板+承台组合中承台体积（m³）。R11规则：仅计筏板底以下部分。
    cap_h_total_mm: 承台详图总高（mm）
    raft_thickness_mm: 筏板厚度（mm）
    计算高度 = cap_h_total_mm − raft_thickness_mm
    """
    h = (cap_h_total_mm - raft_thickness_mm) / 1000
    if h <= 0:
        raise ValueError(
            f"承台有效高度为负（{h:.3f}m），请检查承台总高{cap_h_total_mm}mm是否大于筏板厚{raft_thickness_mm}mm"
        )
    l = cap_l_mm / 1000
    w = cap_w_mm / 1000
    vol = round(l * w * h * count, 4)
    return {
        "cap_length_m": l,
        "cap_width_m": w,
        "cap_total_height_mm": cap_h_total_mm,
        "raft_thickness_mm": raft_thickness_mm,
        "effective_height_m": h,
        "count": count,
        "volume_m3": vol,
        "formula": f"{l}×{w}×({cap_h_total_mm/1000:.3f}−{raft_thickness_mm/1000:.3f})×{count} = {vol} m³",
        "note": "R11: 仅计筏板底以下，H=详图总高−筏板厚",
    }


def calc_sump_concrete(
    inner_l_mm: float,
    inner_w_mm: float,
    inner_depth_mm: float,
    slab_thickness_mm: float,
    count: int,
    edge_dist_mm: float = None,
) -> dict:
    """
    集水坑（坑中坑）混凝土体积（m³）。R12规则。
    inner_l_mm / inner_w_mm: 坑内净空平面尺寸（mm）
    inner_depth_mm: 净坑深（mm，自筏板顶面向下）
    slab_thickness_mm: 所在板厚（mm），默认出边距 = 板厚
    edge_dist_mm: 出边距（mm），None时默认=slab_thickness_mm
    外框 = 内净空 + 2×出边距；外框总深 = 净坑深 + 板厚
    """
    edge = edge_dist_mm if edge_dist_mm is not None else slab_thickness_mm
    outer_l = (inner_l_mm + 2 * edge) / 1000
    outer_w = (inner_w_mm + 2 * edge) / 1000
    outer_d = (inner_depth_mm + slab_thickness_mm) / 1000
    il = inner_l_mm / 1000
    iw = inner_w_mm / 1000
    id_ = inner_depth_mm / 1000
    outer_vol = round(outer_l * outer_w * outer_d, 4)
    inner_vol = round(il * iw * id_, 4)
    net_vol = round((outer_vol - inner_vol) * count, 4)
    return {
        "inner_l_m": il,
        "inner_w_m": iw,
        "inner_depth_m": id_,
        "edge_dist_mm": edge,
        "outer_l_m": outer_l,
        "outer_w_m": outer_w,
        "outer_total_depth_m": outer_d,
        "count": count,
        "outer_volume_m3": outer_vol,
        "inner_volume_m3": inner_vol,
        "net_volume_m3": net_vol,
        "formula": (
            f"({outer_l}×{outer_w}×{outer_d}−{il}×{iw}×{id_})×{count} = {net_vol} m³"
        ),
        "note": "R12: 外框总深=净坑深+板厚；出边距默认=板厚",
    }


def calc_sump_formwork(
    inner_l_mm: float,
    inner_w_mm: float,
    outer_total_depth_mm: float,
    count: int,
) -> dict:
    """
    集水坑模板（m²）。R12规则：立面高度=外框总深（非净坑深）。
    inner_l_mm / inner_w_mm: 坑内净空平面尺寸
    outer_total_depth_mm: 外框总深 = 净坑深 + 板厚（⚠️ 必须传外框总深）
    """
    il = inner_l_mm / 1000
    iw = inner_w_mm / 1000
    d = outer_total_depth_mm / 1000
    perimeter = (il + iw) * 2
    side_area = round(perimeter * d * count, 4)
    bottom_area = round(il * iw * count, 4)
    total_area = round(side_area + bottom_area, 4)
    return {
        "inner_l_m": il,
        "inner_w_m": iw,
        "outer_total_depth_m": d,
        "count": count,
        "side_area_m2": side_area,
        "bottom_area_m2": bottom_area,
        "total_area_m2": total_area,
        "formula_side": f"({il}+{iw})×2×{d}×{count} = {side_area} m²",
        "formula_bottom": f"{il}×{iw}×{count} = {bottom_area} m²",
        "note": "R12: 立面高度=外框总深（净坑深+板厚），非净坑深",
    }


def calc_raft_formwork(
    perimeter_m: float,
    slab_thickness_m: float,
    step_length_m: float = 0.0,
    step_height_diff_m: float = 0.0,
) -> dict:
    """
    筏板外侧模板+踏步模板（m²）。R14规则。
    perimeter_m: 筏板外周长（m）
    slab_thickness_m: 板厚（m），用于外侧模高度
    step_length_m: 深浅区交界线长度（m），无踏步时传0
    step_height_diff_m: 深浅区高差（m），无踏步时传0
    踏步45°斜坡斜长 = √2 × 高差（45°放坡时）
    """
    outer_side = round(perimeter_m * slab_thickness_m, 4)
    step_vertical = round(step_length_m * slab_thickness_m, 4)
    step_slope = round(step_length_m * math.sqrt(2) * step_height_diff_m, 4) if step_height_diff_m > 0 else 0.0
    total = round(outer_side + step_vertical + step_slope, 4)
    return {
        "perimeter_m": perimeter_m,
        "slab_thickness_m": slab_thickness_m,
        "step_length_m": step_length_m,
        "step_height_diff_m": step_height_diff_m,
        "outer_side_m2": outer_side,
        "step_vertical_m2": step_vertical,
        "step_slope_m2": step_slope,
        "total_m2": total,
        "formula": (
            f"外侧: {perimeter_m}×{slab_thickness_m}={outer_side}; "
            f"踏步立面: {step_length_m}×{slab_thickness_m}={step_vertical}; "
            f"踏步斜面: {step_length_m}×√2×{step_height_diff_m}={step_slope}; "
            f"合计={total} m²"
        ),
    }


@dataclass
class RetainingWallSegment:
    """挡土墙段数据"""
    code: str          # 墙型编号，如 DWQ1
    length_m: float    # 段长（m）
    height_m: float    # 计算高度（m）
    thickness_m: float # 墙厚（m）
    count: int = 1     # 段数
    has_brick_mold: bool = False  # 该侧是否为砖胎模（砖胎模侧不计模板）


def calc_retaining_wall_volume(segments: list[RetainingWallSegment]) -> dict:
    """
    挡土墙分组混凝土体积汇总（m³）。R16规则：按墙型分组。
    附墙柱体积需在调用方单独计算后加入合计（R13）。
    """
    detail = {}
    total = 0.0
    for s in segments:
        vol = round(s.length_m * s.height_m * s.thickness_m * s.count, 4)
        detail[s.code] = {
            "length_m": s.length_m,
            "height_m": s.height_m,
            "thickness_m": s.thickness_m,
            "count": s.count,
            "volume_m3": vol,
            "formula": f"{s.length_m}×{s.height_m}×{s.thickness_m}×{s.count} = {vol} m³",
        }
        total += vol
    return {
        "segments": detail,
        "total_volume_m3": round(total, 4),
        "note": "R13: 附墙柱体积需另加；R16: 按墙型分组统计",
    }


def calc_column_formwork(
    perimeters_m: list[float],
    heights_m: list[float],
    counts: list[int],
    beam_contact_area_m2: float = 0.0,
) -> dict:
    """
    框架柱模板面积（m²），扣除梁板接触面积。
    perimeters_m: 各规格柱截面周长列表（m）
    heights_m: 各规格柱净高列表（m）
    counts: 各规格根数列表
    beam_contact_area_m2: 梁板接触面积（m²），用于扣减
    """
    if not (len(perimeters_m) == len(heights_m) == len(counts)):
        raise ValueError("perimeters_m / heights_m / counts 长度必须相同")
    items = []
    gross = 0.0
    for p, h, n in zip(perimeters_m, heights_m, counts):
        a = round(p * h * n, 4)
        items.append({"perimeter_m": p, "height_m": h, "count": n, "area_m2": a,
                       "formula": f"{p}×{h}×{n}={a} m²"})
        gross += a
    net = round(gross - beam_contact_area_m2, 4)
    return {
        "items": items,
        "gross_area_m2": round(gross, 4),
        "beam_contact_deduct_m2": beam_contact_area_m2,
        "net_area_m2": net,
        "formula": f"Σ(周长×净高×根数) - {beam_contact_area_m2} = {net} m²",
    }


def calc_expansion_joint_band(
    band_area_m2: float,
    slab_thickness_m: float,
    end_count: int,
    band_perimeter_m: float,
) -> dict:
    """
    底板膨胀加强带工程量（R15规则）。
    band_area_m2: 加强带总面积（m²，图纸量取）
    slab_thickness_m: 板厚（m）
    end_count: 端头数量（每条带 2 端，3条带=6端）
    band_perimeter_m: 加强带总侧面展开长度（m），用于计算钢丝网面积
    """
    vol = round(band_area_m2 * slab_thickness_m, 4)
    end_formwork = round(end_count * slab_thickness_m * 2, 4)  # 端头截面近似2×板厚（带宽/板厚比）
    wire_mesh = round(band_perimeter_m * slab_thickness_m * 2, 4)  # 两侧
    return {
        "band_area_m2": band_area_m2,
        "slab_thickness_m": slab_thickness_m,
        "volume_m3": vol,
        "end_count": end_count,
        "end_formwork_m2": end_formwork,
        "wire_mesh_m2": wire_mesh,
        "formula_volume": f"{band_area_m2}×{slab_thickness_m} = {vol} m³",
        "formula_wire_mesh": f"{band_perimeter_m}×{slab_thickness_m}×2 = {wire_mesh} m²（两侧）",
        "note": "R15: 端头模板单独列项；钢丝网列为措施项",
    }


def flag_overhigh_formwork(
    formwork_area_m2: float,
    actual_height_m: float,
    threshold_m: float = 3.6,
) -> dict:
    """
    超高模板标记与面积拆分（R17规则）。
    formwork_area_m2: 该构件模板总面积（m²）
    actual_height_m: 构件净高（m）
    threshold_m: 超高起算高度（默认3.6m）
    返回：正常高度范围面积 + 超高部分面积（按高度比例拆分）
    """
    if actual_height_m <= threshold_m:
        return {
            "is_overhigh": False,
            "actual_height_m": actual_height_m,
            "threshold_m": threshold_m,
            "overhigh_height_m": 0.0,
            "normal_area_m2": formwork_area_m2,
            "overhigh_area_m2": 0.0,
            "total_area_m2": formwork_area_m2,
            "note": "未超高，清单全部按正常计",
        }
    overhigh_h = actual_height_m - threshold_m
    ratio = overhigh_h / actual_height_m
    overhigh_area = round(formwork_area_m2 * ratio, 4)
    normal_area = round(formwork_area_m2 - overhigh_area, 4)
    return {
        "is_overhigh": True,
        "actual_height_m": actual_height_m,
        "threshold_m": threshold_m,
        "overhigh_height_m": round(overhigh_h, 4),
        "normal_area_m2": normal_area,
        "overhigh_area_m2": overhigh_area,
        "total_area_m2": formwork_area_m2,
        "formula": (
            f"超高面积: {formwork_area_m2}×({overhigh_h:.3f}/{actual_height_m}) = {overhigh_area} m²"
        ),
        "note": "R17: 清单总量含超高部分；超高部分另列措施项",
    }


def get_beam_type(floor_has_basement: bool) -> str:
    """
    根据是否有地下室返回一层梁类型。
    无地下室 → 基础梁（010503001）
    有地下室 → 楼层梁（010503002）
    """
    return "基础梁（010503001）" if not floor_has_basement else "楼层梁（010503002）"


def parse_span_count(beam_label: str) -> tuple[int, bool]:
    """
    从集中标注解析跨数。
    如 'KL1(2)' → (2, True)；'KL1' → (1, False)
    返回 (跨数, 是否明确标注)
    """
    import re
    m = re.search(r'\((\d+)\)', beam_label)
    if m:
        return int(m.group(1)), True
    return 1, False


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
