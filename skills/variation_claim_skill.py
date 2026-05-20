from skills.base_skill import BaseSkill
from agent.context import TaskContext


class VariationClaimSkill(BaseSkill):
    """
    变更单/签证资料整理 Skill
    输入：变更通知单、签证单、原清单、施工日志等
    输出：变更/签证结构化清单、费用影响初估、资料完整性检查
    """

    @property
    def task_type(self) -> str:
        return "variation_claim"

    @property
    def guidance_files(self) -> list[str]:
        return [
            "general_principles",
            "uncertainty_handling",
            "human_review_rules",
        ]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：变更单/签证资料整理

{self._guidance_section(context)}

## 案例信息
案例编号：{context.case_id}

## 输入材料

{self._format_input_section(context)}

## 任务要求

请对变更/签证资料进行专业整理，输出以下内容：

1. **资料完整性检查**：
   - 变更/签证单是否有编号、日期、甲乙双方签字
   - 是否附有图纸或照片依据
   - 是否有监理确认

2. **变更/签证清单结构化**：
   - 变更内容摘要
   - 工程量变化（增减）
   - 费用影响初估（如有依据）

3. **风险提示**：
   - 资料缺失风险
   - 结算时可能被核减的风险
   - 超出合同范围的风险

4. **后续行动建议**：
   - 还需补充哪些资料
   - 是否需要重新核价

## 输出格式（严格 JSON）

```json
{{
  "task_type": "variation_claim",
  "case_id": "{context.case_id}",
  "documents": [
    {{
      "doc_id": "",
      "doc_type": "变更单/签证单/现场指令/其他",
      "doc_number": "",
      "date": "",
      "description": "",
      "is_signed_by_owner": null,
      "is_signed_by_contractor": null,
      "is_confirmed_by_supervisor": null,
      "has_drawing_evidence": null,
      "has_photo_evidence": null
    }}
  ],
  "quantity_changes": [
    {{
      "doc_ref": "",
      "item": "",
      "original_quantity": 0.0,
      "changed_quantity": 0.0,
      "unit": "",
      "formula": "",
      "drawing_ref": ""
    }}
  ],
  "cost_impact_estimate": {{
    "note": "费用影响为初步估算，需经正式核价后确认",
    "increase_items": [],
    "decrease_items": [],
    "net_change_estimated": "待核价"
  }},
  "risks": [
    {{"risk": "", "level": "高/中/低", "mitigation": ""}}
  ],
  "missing_documents": [],
  "action_items": [],
  "uncertain_items": [],
  "summary": "",
  "review_notes": "变更/签证整理结果需造价师及法务确认后方可用于结算。"
}}
```
"""
