from skills.base_skill import BaseSkill
from agent.context import TaskContext


class QuantityTakeoffSkill(BaseSkill):
    """
    工程量初算 Skill
    输入：图纸、项目说明、专业类型
    输出：工程量清单初稿（含计算式、依据、不确定项）
    人工复核点：所有计算结果必须经注册造价师复核
    """

    @property
    def task_type(self) -> str:
        return "quantity_takeoff"

    @property
    def guidance_files(self) -> list[str]:
        return [
            "general_principles",
            "decoration_quantity",
            "door_window_quantity",
            "uncertainty_handling",
            "human_review_rules",
        ]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：工程量初算

{self._guidance_section(context)}

## 案例信息
案例编号：{context.case_id}

## 输入材料

{self._format_input_section(context)}

## 任务要求

请根据提供的图纸和说明，进行工程量初步计算，严格遵守以下规则：

1. **每条工程量必须包含**：
   - 项目名称（与清单编码对应）
   - 计量单位
   - 计算式（如：3.6×2.4×2 = 17.28）
   - 图纸依据（图纸编号 + 位置）
   - 初算数量

2. **不确定处理**：
   - 图纸信息不足的项目，放入 uncertain_items，不要猜测数字
   - 需要现场确认的，标注"需现场核实"
   - 不同图纸数据矛盾的，标注"图纸矛盾，需设计确认"

3. **禁止事项**：
   - 不得依据经验估算数字（除非明确标注为"估算"）
   - 不得假设不明确的构造做法
   - 不得使用无图纸依据的数据

## 输出格式（严格 JSON）

```json
{{
  "task_type": "quantity_takeoff",
  "case_id": "{context.case_id}",
  "discipline": "",
  "items": [
    {{
      "id": "QT-001",
      "name": "",
      "spec": "",
      "unit": "",
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
      "impact": "影响工程量估算"
    }}
  ],
  "missing_info": [],
  "summary": "",
  "total_items": 0,
  "uncertain_count": 0,
  "review_notes": "以上工程量为 AI 初稿，所有数据必须经注册造价师审核后方可使用，不得直接用于报价或结算。"
}}
```
"""
