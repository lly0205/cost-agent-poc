from skills.base_skill import BaseSkill
from agent.context import TaskContext


class QuantityTakeoffSkill(BaseSkill):
    """
    工程量初算 Skill
    依据：GB50854-2013 房屋建筑与装饰工程计量规范
    强制规则：
      Rule 1 - 框架柱/构造柱按净高计算（扣除现浇板厚）
      Rule 2 - 砌体墙扣门窗洞口，尺寸严格取自《门窗表》
    输出：工程量清单初稿（含项目编码、计算式、图纸依据）
    人工复核：所有计算结果必须经注册造价师复核后方可使用
    """

    @property
    def task_type(self) -> str:
        return "quantity_takeoff"

    @property
    def guidance_files(self) -> list[str]:
        return [
            "general_principles",
            "gb50854_quantity_rules",
            "door_window_quantity",
            "decoration_quantity",
            "uncertainty_handling",
            "human_review_rules",
        ]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：工程量初算（依据 GB50854-2013）

{self._guidance_section(context)}

## 永久生效强制规则（优先级最高）

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

按照 GB50854-2013 计算工程量，严格遵守以下规则：

### 必须包含的字段（每条清单项）
- 项目编码（如 010502001）
- 项目名称
- 项目特征描述（材料品种、规格、强度等级等）
- 计量单位
- 计算式（必须保留，格式：尺寸表达式 = 结果）
- 工程量
- 图纸依据（图纸编号 + 位置/轴线/楼层）
- 备注（含不确定说明）

### 计算要求
1. 柱类构件必须标注采用了Rule 1（净高 = 层高 - 板厚）
2. 砌体墙必须列出门窗洞口扣减明细（来自门窗表）
3. 钢筋计算必须给出：直径、长度、根数、单重、总重
4. 计量单位与规范一致（m³/㎡/m/t/根/樘/座/个）

### 不确定项处理
- 图纸信息不足 → 放入 uncertain_items，不猜测数字
- 图纸矛盾 → 标注"图纸矛盾，需设计确认"
- 门窗表缺失时 → 不得自估尺寸，列为不确定项

---

## 输出格式（严格 JSON）

```json
{{
  "task_type": "quantity_takeoff",
  "case_id": "{context.case_id}",
  "discipline": "",
  "applied_rules": ["GB50854-2013", "Rule1-柱净高扣板厚", "Rule2-砌体墙扣门窗"],
  "items": [
    {{
      "id": "QT-001",
      "code": "010502001",
      "name": "",
      "spec": "",
      "unit": "m³",
      "formula": "",
      "quantity": 0.0,
      "drawing_ref": "",
      "notes": ""
    }}
  ],
  "uncertain_items": [
    {{
      "id": "UC-001",
      "item": "",
      "reason": "",
      "action_required": "",
      "impact": ""
    }}
  ],
  "missing_info": [],
  "summary": "",
  "total_items": 0,
  "uncertain_count": 0,
  "review_notes": "以上工程量为 AI 初稿，依据 GB50854-2013 计算。所有数据必须经注册造价工程师审核签字后方可用于报价或结算，不得直接引用。"
}}
```
"""
