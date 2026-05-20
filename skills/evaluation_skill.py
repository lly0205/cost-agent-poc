"""
AI 结果评测 Skill
对比 AI 输出与人工标准答案，生成评测报告。
也可直接调用 evaluation/evaluate_case.py 进行量化评测。
"""
import json
from pathlib import Path
from skills.base_skill import BaseSkill
from agent.context import TaskContext

PROJECT_ROOT = Path(__file__).parent.parent


class EvaluationSkill(BaseSkill):

    @property
    def task_type(self) -> str:
        return "evaluation"

    @property
    def guidance_files(self) -> list[str]:
        return ["general_principles", "human_review_rules"]

    def build_prompt(self, context: TaskContext) -> str:
        # Try to load AI output and golden answer for this case
        ai_output = self._load_latest_output(context)
        golden = self._load_golden_answer(context)

        ai_section = (
            f"```json\n{json.dumps(ai_output, ensure_ascii=False, indent=2)}\n```"
            if ai_output else "（未找到 AI 输出文件，请先运行其他任务生成输出）"
        )
        golden_section = (
            f"```json\n{json.dumps(golden, ensure_ascii=False, indent=2)}\n```"
            if golden else "（未找到人工标准答案，请在 cases/{context.case_id}/golden_answer/human_answer.json 中填写）"
        )

        return f"""# 任务：AI 结果评测

## 案例信息
案例编号：{context.case_id}

## AI 输出

{ai_section}

## 人工标准答案（Golden Answer）

{golden_section}

## 评测维度（8项）

请对比以上两个结果，按以下 8 个维度进行评分（0-100）并给出说明：

1. **准确率**：AI 工程量与人工答案接近的条目比例
2. **漏项率**：人工答案中有但 AI 未涉及的条目比例（越低越好）
3. **重复计算率**：AI 输出中重复计算的条目比例（越低越好）
4. **数量偏差率**：各条目数量偏差的平均值（越低越好）
5. **可解释性**：AI 是否提供了充分的计算式和依据（0=无依据，100=每条都有）
6. **复核成本**：人工复核该 AI 输出需要的估计工时（低=高分）
7. **图纸依据完整性**：是否每条工程量都标注了图纸依据
8. **不确定项标记**：AI 是否正确识别并标记了不确定内容

## 输出格式（严格 JSON）

```json
{{
  "task_type": "evaluation",
  "case_id": "{context.case_id}",
  "scores": {{
    "accuracy": {{"score": 0, "comment": ""}},
    "omission_rate": {{"score": 0, "comment": ""}},
    "duplication_rate": {{"score": 0, "comment": ""}},
    "quantity_deviation": {{"score": 0, "comment": ""}},
    "explainability": {{"score": 0, "comment": ""}},
    "review_cost": {{"score": 0, "comment": ""}},
    "drawing_reference": {{"score": 0, "comment": ""}},
    "uncertainty_marking": {{"score": 0, "comment": ""}}
  }},
  "overall_score": 0,
  "item_comparisons": [
    {{
      "item": "",
      "ai_quantity": 0.0,
      "golden_quantity": 0.0,
      "deviation_pct": 0.0,
      "status": "匹配/偏差/漏项/多余"
    }}
  ],
  "strengths": [],
  "weaknesses": [],
  "improvement_suggestions": [],
  "lessons_learned": [],
  "summary": ""
}}
```
"""

    def _load_latest_output(self, context: TaskContext) -> dict:
        output_dir = PROJECT_ROOT / "outputs" / context.case_id
        if not output_dir.exists():
            return {}
        files = sorted(output_dir.glob("quantity_takeoff_*.json"), reverse=True)
        if not files:
            files = sorted(output_dir.glob("*.json"), reverse=True)
        if files:
            try:
                return json.loads(files[0].read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _load_golden_answer(self, context: TaskContext) -> dict:
        golden_file = context.case_path / "golden_answer" / "human_answer.json"
        if golden_file.exists():
            try:
                return json.loads(golden_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}
