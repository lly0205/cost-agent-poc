"""
广联达集成 Skill（预留占位）
当前版本仅提供接口定义和说明，不执行真实广联达操作。
三种未来路径：
  A. 官方 API / SDK（如广联达开放平台有提供）
  B. 文件导入导出（GBQ/GTJ 文件格式）
  C. RPA / GUI 自动化
"""
from skills.base_skill import BaseSkill
from agent.context import TaskContext


class GlodonIntegrationSkill(BaseSkill):

    @property
    def task_type(self) -> str:
        return "glodon_integration"

    @property
    def guidance_files(self) -> list[str]:
        return ["general_principles"]

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：广联达集成辅助

## 案例信息
案例编号：{context.case_id}

## 输入材料

{self._format_input_section(context)}

## 当前限制

广联达（Glodon）集成功能当前处于预留阶段。请根据以下材料，分析应使用哪种集成路径，并生成操作建议。

可选路径：
- **路径 A：官方 API/SDK**（需确认广联达是否已开放对应接口）
- **路径 B：文件导入导出**（GBQ5/GTJ/GQI 文件格式交换）
- **路径 C：RPA/GUI 自动化**（截图识别 + 键鼠操作）

## 任务要求

1. 分析当前任务适合哪种集成路径
2. 列出所需的输入文件格式
3. 列出预期输出文件格式
4. 描述人工操作步骤（如果当前只能手动操作）
5. 标注哪些步骤未来可以自动化

## 输出格式（严格 JSON）

```json
{{
  "task_type": "glodon_integration",
  "case_id": "{context.case_id}",
  "recommended_path": "A/B/C",
  "reason": "",
  "input_files_needed": [],
  "output_files_expected": [],
  "manual_steps": [
    {{"step": 1, "action": "", "tool": "", "notes": ""}}
  ],
  "automation_potential": [
    {{"step": 1, "can_automate": true, "method": ""}}
  ],
  "blockers": [],
  "uncertain_items": [],
  "summary": "",
  "review_notes": "广联达集成建议需由熟悉广联达软件的造价师确认可行性。"
}}
```
"""
