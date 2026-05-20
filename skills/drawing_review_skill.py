from skills.base_skill import BaseSkill
from agent.context import TaskContext


class DrawingReviewSkill(BaseSkill):
    """
    图纸审阅 Skill
    输入：图纸 PDF / 图纸说明文字
    输出：图纸问题清单、信息不足项、与清单不一致项
    """

    @property
    def task_type(self) -> str:
        return "drawing_review"

    @property
    def guidance_files(self) -> list[str]:
        return [
            "general_principles",
            "drawing_boq_consistency",
            "uncertainty_handling",
        ]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：图纸审阅

{self._guidance_section(context)}

## 案例信息
案例编号：{context.case_id}

## 输入材料

{self._format_input_section(context)}

## 任务要求

请对上述图纸材料进行专业审阅，输出以下内容：

1. **图纸基本信息**：工程名称、专业类型、图纸编号列表、版本、设计院。
2. **图纸完整性检查**：缺少哪些图纸或说明，对算量会产生什么影响。
3. **图纸问题清单**：标注、尺寸、做法等存在的问题或歧义。
4. **与清单的一致性**：如果有清单材料，指出图纸与清单不一致的地方。
5. **算量前置条件**：开始算量前需要造价师确认的事项。
6. **不确定项**：所有无法从现有图纸中确定的内容。

## 输出格式（严格 JSON）

请用 ```json ... ``` 包裹，格式如下：

```json
{{
  "task_type": "drawing_review",
  "case_id": "{context.case_id}",
  "drawing_info": {{
    "project_name": "",
    "disciplines": [],
    "drawing_numbers": [],
    "version": "",
    "design_institute": ""
  }},
  "completeness_issues": [
    {{"issue": "", "impact_on_quantity": ""}}
  ],
  "drawing_problems": [
    {{"location": "", "problem": "", "severity": "高/中/低", "suggested_action": ""}}
  ],
  "boq_inconsistencies": [
    {{"drawing_item": "", "boq_item": "", "discrepancy": ""}}
  ],
  "prerequisites_for_takeoff": [],
  "uncertain_items": [
    {{"item": "", "reason": "", "action_required": ""}}
  ],
  "summary": "",
  "review_notes": "本结果需造价师人工确认后方可使用。"
}}
```
"""
