from skills.base_skill import BaseSkill
from agent.context import TaskContext


class DrawingBOQSkill(BaseSkill):
    """
    图纸识读与构件清单抽取 Skill
    依据：
      - 中国建设工程图纸识图与构件清单抽取逻辑_Agent规则版 V1.0（2026-06-02）
      - GB50500-2013 建设工程工程量清单计价规范
      - GB/T 50854-2024 房屋建筑与装饰工程工程量计算标准（2025-09-01实施）
    核心原则：
      P1 先上下文、后图元——任何线条必须先放入专业-图名-视图-图例-说明的上下文中解释
      P2 多证据闭环——构件输出至少应有两类证据支撑
      P3 中国规范优先——制图语义、平法编号、工程量单位按中国现行国家标准执行
    输出：构件清单初稿（含置信度、证据来源、清单映射建议、疑问项）
    人工复核：所有识别结果必须经注册造价师复核后方可使用
    """

    @property
    def task_type(self) -> str:
        return "drawing_boq"

    @property
    def guidance_files(self) -> list[str]:
        return [
            "general_principles",
            "drawing_recognition_rules",
            "gb50500_2013_pricing_rules",
            "gb50854_quantity_rules",
            "uncertainty_handling",
            "human_review_rules",
        ]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：图纸识读与构件清单抽取

{self._guidance_section(context)}

---

## 永久生效强制规则（优先级最高）

**P1【先上下文、后图元】**
- 任何线、块、填充、文字，必须先放入"专业-图名-视图类型-楼层-轴网-比例-图例-说明"的上下文中解释
- 不能把线型直接等同于构件；同一根线在不同专业和视图中代表完全不同的构件

**P2【多证据闭环】**
- 构件输出至少应有两类证据支撑
- 仅凭单一视觉相似性时，置信度不得高于0.55，须降为候选构件

**P3【中国规范优先】**
- 制图语义按 GB/T 50001-2017/50104-2010/50105-2010 执行
- 结构构件按 22G101 系列平法逻辑识别
- 清单映射优先使用 GB/T 50854-2024（房建装饰）或 GB/T 50856-2024（安装）

**Rule 1【框架柱/构造柱净高】**
- 框架柱、构造柱工程量计算时，必须扣除现浇楼板的板厚，按净高计算柱高度
- 净高 = 层高 - 楼板厚度

**Rule 2【砌体墙门窗扣减】**
- 砌体墙工程量必须扣除所有门、窗洞口体积/面积
- 所有门窗洞口尺寸，严格按照图纸《门窗表》中的对应规格取值，不得自行估算尺寸

---

## 案例信息
案例编号：{context.case_id}

## 输入材料

{self._format_input_section(context)}

---

## 任务要求

### 第一步：图纸上下文识别（必须先完成）
1. 识别图纸包版本、图纸目录、专业代码
2. 读取项目图例、设计说明、材料做法表、门窗表、设备表
3. 每张图纸先识别：标题栏 → 图名 → 专业 → 版本 → 比例 → 楼层/标高 → 视图类型
4. 未完成第一步前，禁止解释任何线条为具体构件

### 第二步：构件识别与清单抽取

**识别规则（严格按优先级）：**
1. 项目图例/说明（最高）
2. 单张图纸局部标注/索引详图
3. 国家标准（制图标准/平法图集）
4. CAD图层/块名（辅助，不单独定性）
5. 几何形态/视觉推断（最低，只能作候选）

**专业识别要点：**
- 建筑图：墙/门窗/楼梯/洞口——按 GB/T 50104-2010
- 结构图：柱/梁/板/墙——按 22G101 平法逻辑；KZ/KL/LL/Q/GBZ 等需绑定编号-规格-楼层
- 装饰图：面层/做法——按房间做法表和节点详图
- 安装图：管线/设备——按系统图例、管径/规格识别；平面图和系统图分别用途不同

### 第三步：去重与合并
- 同一构件在多图出现时，生成一个主对象并保留多来源证据，不重复计数
- 典型层展开必须保留楼层明细，排除避难层/设备层/转换层例外
- 详图/大样默认不新增数量，只补充做法和规格

### 第四步：清单映射
- 房屋建筑与装饰：优先映射 GB/T 50854-2024
- 安装工程：优先映射 GB/T 50856-2024
- 不能确定编码时：输出候选章节 + "需人工确认"，禁止伪造编码

---

## 输出格式（严格 JSON）

```json
{{
  "task_type": "drawing_boq",
  "case_id": "{context.case_id}",
  "drawing_package_version": "",
  "applied_rules": ["P1-先上下文后图元", "P2-多证据闭环", "P3-中国规范优先", "Rule1-柱净高扣板厚", "Rule2-砌体墙扣门窗"],
  "recognition_summary": {{
    "total_components": 0,
    "high_confidence": 0,
    "medium_confidence": 0,
    "low_confidence": 0,
    "very_low_confidence": 0,
    "unresolved_count": 0
  }},
  "components": [
    {{
      "component_uid": "C-001",
      "discipline": "建筑/结构/给排水/暖通/电气/总图/装饰",
      "sheet_id": "图纸编号",
      "sheet_name": "图名",
      "view_type": "平面/立面/剖面/详图/系统图/表格",
      "floor_level": "楼层或标高",
      "axis_location": "轴网或坐标",
      "component_category": "构件大类",
      "component_name": "构件名称",
      "component_id": "图纸编号（如M1/KL1/KZ1）",
      "specification": {{
        "size": "尺寸/截面/管径/型号",
        "material": "材质",
        "grade": "强度/防火/保温等级",
        "installation": "安装方式/标高"
      }},
      "quantity_preliminary": {{
        "value": null,
        "unit": "m/m2/m3/台/套/个/t/樘/根",
        "calc_basis": "几何来源+参数来源+计算规则来源+是否扣减/展开",
        "is_final": false
      }},
      "boq_mapping": {{
        "standard": "GB/T50854-2024 或 GB/T50856-2024",
        "candidate_chapter_or_item": "候选章节/项目",
        "suggested_code": null,
        "needs_human_confirmation": true
      }},
      "evidence": [
        {{
          "type": "图名/图例/文字/表格/图层/尺寸/坐标",
          "source": "图纸编号+页码/表格行列/图元ID",
          "text": "原始标注或识别结果"
        }}
      ],
      "confidence": 0.0,
      "warnings": ["冲突、缺项、需人工确认事项"]
    }}
  ],
  "unresolved_questions": [
    {{
      "id": "Q-001",
      "component_ref": "C-xxx",
      "question_type": "图纸冲突/缺图/OCR误差/典型层例外/尺寸矛盾",
      "description": "",
      "action_required": "",
      "impact": "高/中/低"
    }}
  ],
  "review_notes": "以上构件清单为 AI 识图初稿，依据中国建设工程制图标准和清单计价规范整理。所有识别结果标注为初判/待审核，数量均为估算值，必须经注册造价工程师审核签字后方可用于工程量计算、清单编制或报价，不得直接引用。"
}}
```
"""
