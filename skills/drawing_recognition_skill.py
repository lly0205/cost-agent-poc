from skills.base_skill import BaseSkill
from agent.context import TaskContext


class DrawingRecognitionSkill(BaseSkill):
    """
    建筑平面图构件识别与清单抽取 Skill（一层平面图专项）
    依据：
      - 中国建设工程图纸识图与构件清单抽取规则 V1.0（2026-06-02）
        knowledge/standards/drawing_recognition_rules.md
      - GB/T 50104-2010 建筑制图标准
      - 22G101 系列国家建筑标准设计图集（结构平法）
      - GB/T 50854-2024 房屋建筑与装饰工程工程量计算标准

    核心原则（继承自 DrawingBOQSkill，专项扩展）：
      P1 先上下文、后图元——任何线条必须先放入专业-图名-视图-图例-说明的上下文中解释
      P2 多证据闭环——构件输出至少应有两类证据支撑；扫描图默认置信度降级
      P3 中国规范优先——制图语义、平法编号、工程量单位按中国现行国家标准执行

    适用场景：
      - 输入为单张或多张建筑平面图（含一层平面图、标准层、屋面层等）
      - 以图纸识别和构件清单抽取为主要目标
      - 不包含安装（水暖电）专业构件识别

    与 DrawingBOQSkill 的区别：
      - DrawingBOQSkill：综合型图纸识读+清单映射，适用于全专业完整图纸包
      - DrawingRecognitionSkill：建筑专业单图/单层专项识别，
        更细化地处理轴网、层高、外墙/内墙厚度推断、门窗统计、楼梯识别等建筑专项逻辑

    人工复核：所有识别结果必须经注册造价师复核后方可使用
    """

    @property
    def task_type(self) -> str:
        return "drawing_recognition"

    @property
    def guidance_files(self) -> list[str]:
        return [
            "general_principles",
            "drawing_recognition_rules",   # 主规则文件
            "gb50500_2013_pricing_rules",
            "uncertainty_handling",
            "human_review_rules",
        ]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：建筑平面图构件识别与清单抽取

{self._guidance_section(context)}

---

## 永久生效强制规则（优先级最高）

**P1【先上下文、后图元】**
- 任何线、块、填充、文字，必须先放入"专业-图名-视图类型-楼层-轴网-比例-图例-说明"的上下文中解释
- 未识别专业和图名前，禁止解释任何线条为具体构件

**P2【多证据闭环】**
- 构件输出至少应有两类证据支撑
- 扫描图（非矢量 PDF）识别置信度默认降低一个等级，所有尺寸来自标注而非比例换算
- 仅凭视觉相似性时，置信度不得高于 0.55，须降为候选构件

**P3【中国规范优先】**
- 制图语义按 GB/T 50001-2017 / GB/T 50104-2010 执行
- 结构构件按 22G101 系列平法逻辑识别
- 清单映射优先使用 GB/T 50854-2024（房建装饰）

**R-ARC-01【轴网优先确立】**
- 必须先完整提取横轴（数字轴）和纵轴（字母轴）编号及轴距
- 所有构件定位必须绑定到轴线交点或轴线范围
- 轴距不能靠视觉估算，必须来自尺寸标注

**R-ARC-02【外墙厚度取值规则】**
- 外墙厚度必须来自尺寸标注或设计说明
- 常见：240mm（一砖，砌体）、200mm（混凝土）、300mm（保温复合）
- 扫描图中无法读取标注时，仅输出候选值并标注"待设计说明确认"

**R-ARC-03【内墙厚度取值规则】**
- 隔墙厚度从墙线双线间距和标注读取
- 无标注时，仅输出候选值（100/120/200mm 常见）并降低置信度至 0.50

**R-ARC-04【门窗统计规则】**
- 门：M + 数字编号（M1、M2...）；宽×高见门窗表
- 窗：C + 数字编号（C1、C2...）；宽×高见门窗表
- 防火门：FM；玻璃门：BM；推拉门：TM（以项目图例为准）
- 平面图中门窗数量为主证据，门窗表为规格证据；两者冲突时输出疑问项
- 无门窗表时，宽度可从平面洞口估算，高度不可推断，列为待确认项

**R-ARC-05【楼梯识别规则】**
- 一层平面图中楼梯间：踏步线（多条平行细线）+ 上行箭头 + 剖断线
- 宽度可从平面读取，级数和层高需结合楼梯剖面或详图
- 不得仅凭踏步线确定楼梯类型（直跑/双跑/三跑）

**R-ARC-06【柱截面取值规则（Rule 1 扩展）】**
- 框架柱截面尺寸从柱表或平面标注读取
- 柱工程量高度 = 层高 - 楼板厚度（净高计算，必须扣板厚）
- 层高来源：建筑立面/剖面；板厚来源：结构楼板配筋图
- 扫描图无柱表时，截面列为候选值

**R-ARC-07【砌体墙门窗扣减（Rule 2 扩展）】**
- 砌体墙工程量必须扣除所有门、窗洞口体积/面积
- 门窗洞口尺寸严格按《门窗表》取值，不得自行估算
- 无门窗表时，洞口扣减为待计算项，在疑问项中明确记录

**R-ARC-08【房间面积与做法绑定规则】**
- 每个房间须绑定：房间名称 + 轴线范围 + 净面积（墙内面积）
- 地面做法、墙面做法、天棚做法须来自设计说明中的"做法表"或"装修表"
- 无做法表时，不得按房间名推断做法，列为待确认项

---

## 案例信息
案例编号：{context.case_id}

## 输入材料

{self._format_input_section(context)}

---

## 任务步骤

### 第一步：图纸上下文识别（必须先完成）
按以下顺序提取，全部完成后才能进入第二步：
1. 标题栏：图名、图号、比例、设计单位、出图日期
2. 轴网：横轴编号+轴距，纵轴编号+轴距（来自尺寸标注）
3. 楼层标高：本层标高、层高（来自立面/剖面参考）
4. 图例说明：门窗图例、填充图例、特殊符号
5. 图纸完整性：是否有门窗表、做法表、楼梯详图、节点大样

### 第二步：构件逐类识别
按以下类别依次识别，每类输出置信度和证据：

1. **框架柱/构造柱**
   - 轴线交点处的矩形/圆形截面
   - 记录位置（轴线）、截面（需柱表或标注）
   - 注意：R-ARC-06，净高需扣板厚

2. **外墙**
   - 外轮廓双线，厚度需标注
   - 区分承重墙/非承重墙（需说明）
   - 注意：R-ARC-02，R-ARC-07

3. **内隔墙**
   - 内部分隔双线
   - 记录厚度、轴线范围
   - 注意：R-ARC-03，R-ARC-07

4. **门**
   - 洞口+开启弧线；绑定门编号（M 系列）
   - 注意：R-ARC-04

5. **窗**
   - 洞口+三线（窗台、窗顶、中间线）；绑定窗编号（C 系列）
   - 注意：R-ARC-04

6. **楼梯/坡道**
   - 踏步线+箭头+剖断线；识别楼梯间范围
   - 注意：R-ARC-05

7. **房间与装修做法**
   - 房间名称+轴线范围+净面积（扣除墙厚后的净面积）
   - 注意：R-ARC-08

8. **室外构件（散水/台阶/坡道）**
   - 外墙外侧细线范围
   - 宽度需标注或说明

### 第三步：疑问项汇总
- 扫描图识别不清晰处
- 缺少门窗表/做法表/柱表时，所有依赖这些表的构件属性
- 尺寸矛盾、图例缺失、标注遮挡

### 第四步：清单映射（仅候选）
- 构件 → GB/T 50854-2024 候选章节
- 全部标注"需人工确认"
- 不得伪造清单编码

---

## 输出格式（严格 JSON）

```json
{{
  "task_type": "drawing_recognition",
  "case_id": "{context.case_id}",
  "drawing_info": {{
    "sheet_name": "图名（如：一层平面图）",
    "sheet_id": "图号",
    "discipline": "建筑",
    "scale": "比例（如：1:100）",
    "floor_level": "楼层标高",
    "story_height": "层高（来源说明）",
    "design_institute": "设计单位",
    "draw_date": "出图日期",
    "axis_grid": {{
      "horizontal_axes": "如：1-2-3-4-5-6，轴距：3600/4200/3600...",
      "vertical_axes": "如：A-B-C-D-E，轴距：3300/3900/3300...",
      "data_source": "尺寸标注/推算"
    }},
    "supporting_documents": {{
      "door_window_schedule": "有/无/未见",
      "finish_schedule": "有/无/未见",
      "column_table": "有/无/未见",
      "stair_detail": "有/无/未见"
    }}
  }},
  "recognition_summary": {{
    "total_components": 0,
    "high_confidence": 0,
    "medium_confidence": 0,
    "low_confidence": 0,
    "very_low_confidence": 0,
    "unresolved_count": 0,
    "scan_quality": "清晰/一般/模糊"
  }},
  "components": [
    {{
      "component_uid": "C-001",
      "discipline": "建筑",
      "component_category": "柱/外墙/内墙/门/窗/楼梯/房间/散水/台阶",
      "component_name": "构件名称",
      "component_id": "图纸编号（如 M1/C2/KZ1）",
      "floor_level": "一层",
      "axis_location": "轴线位置（如：1/A-B 轴）",
      "specification": {{
        "size": "截面/宽×高/厚度/长度",
        "material": "材质（需说明确认）",
        "grade": "强度/防火等级"
      }},
      "quantity_preliminary": {{
        "value": null,
        "unit": "m/m2/m3/根/樘/处",
        "calc_basis": "几何来源说明",
        "deduction_rule": "是否需要扣减（如砌体墙扣门窗洞口，柱净高扣板厚）",
        "is_final": false
      }},
      "boq_mapping": {{
        "standard": "GB/T50854-2024",
        "candidate_chapter_or_item": "候选章节",
        "suggested_code": null,
        "needs_human_confirmation": true
      }},
      "evidence": [
        {{
          "type": "图名/图例/文字标注/尺寸线/几何形态",
          "source": "图纸区域或图元位置",
          "text": "原始标注或识别文字"
        }}
      ],
      "confidence": 0.0,
      "warnings": ["需确认事项"]
    }}
  ],
  "unresolved_questions": [
    {{
      "id": "Q-001",
      "component_ref": "C-xxx",
      "question_type": "缺门窗表/缺做法表/缺柱表/尺寸不清/扫描模糊",
      "description": "问题描述",
      "action_required": "需提供的资料或操作",
      "impact": "高/中/低"
    }}
  ],
  "review_notes": "以上构件清单为 AI 图纸识别初稿（建筑专业一层平面图）。所有尺寸、数量均为初判估算值，未经门窗表/做法表/柱表核实的属性均标注为待确认。必须经注册造价工程师审核签字后方可用于工程量计算或清单编制，不得直接引用。"
}}
```
"""
