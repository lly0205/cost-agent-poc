from skills.base_skill import BaseSkill
from agent.context import TaskContext


class BOQCheckSkill(BaseSkill):
    """
    工程量清单复核 Skill
    输入：清单（Excel/CSV/JSON）+ 图纸或工程量初算结果
    输出：漏项、重复、数量偏差、项目描述问题
    """

    @property
    def task_type(self) -> str:
        return "boq_check"

    @property
    def guidance_files(self) -> list[str]:
        return [
            "general_principles",
            "drawing_boq_consistency",
            "uncertainty_handling",
            "human_review_rules",
        ]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：工程量清单复核

{self._guidance_section(context)}

## 案例信息
案例编号：{context.case_id}

## 输入材料

{self._format_input_section(context)}

## 任务要求

请对工程量清单进行专业复核，检查以下内容：

1. **漏项检查**：对照图纸，清单中是否有明显缺漏项目。
2. **重复计算检查**：清单中是否存在同一工程量被重复列项。
3. **数量核对**：清单数量与图纸计算数量是否有明显偏差（偏差超过 5% 需标注）。
4. **项目描述检查**：项目特征描述是否完整、准确，是否符合计量规范要求。
5. **单位检查**：计量单位是否正确。
6. **编码规范**：清单编码是否符合规范（如 GB 50500 或地方规范）。

## 输出格式（严格 JSON）

```json
{{
  "task_type": "boq_check",
  "case_id": "{context.case_id}",
  "missing_items": [
    {{"item": "", "reason": "", "drawing_ref": "", "estimated_impact": ""}}
  ],
  "duplicate_items": [
    {{"item_1": "", "item_2": "", "overlap_description": ""}}
  ],
  "quantity_deviations": [
    {{
      "boq_item": "",
      "boq_quantity": 0.0,
      "calculated_quantity": 0.0,
      "deviation_pct": 0.0,
      "possible_reason": ""
    }}
  ],
  "description_issues": [
    {{"item": "", "issue": "", "suggested_revision": ""}}
  ],
  "unit_issues": [
    {{"item": "", "current_unit": "", "correct_unit": ""}}
  ],
  "code_issues": [
    {{"item": "", "current_code": "", "issue": ""}}
  ],
  "uncertain_items": [
    {{"item": "", "reason": "", "action_required": ""}}
  ],
  "summary": "",
  "overall_risk": "高/中/低",
  "review_notes": "本复核结果为 AI 初步分析，最终结论需造价师人工确认。"
}}
```
"""
