"""Base class for all Cost Engineer skills."""
import json
import re
from abc import ABC, abstractmethod

from agent.context import TaskContext


class BaseSkill(ABC):

    @property
    @abstractmethod
    def task_type(self) -> str:
        pass

    @property
    @abstractmethod
    def guidance_files(self) -> list[str]:
        """Guidance file stems (without .md) to load for this skill."""
        pass

    @abstractmethod
    def build_prompt(self, context: TaskContext) -> str:
        pass

    # ------------------------------------------------------------------ #
    # Default helpers — override in subclasses if needed                   #
    # ------------------------------------------------------------------ #

    def parse_response(self, raw_response: str, context: TaskContext) -> dict:
        """Extract JSON from Claude response. Falls back to wrapping raw text."""
        # Try ```json ... ``` block
        m = re.search(r"```json\s*(.*?)\s*```", raw_response, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # Try bare JSON
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {
                "raw_response": raw_response,
                "parse_error": "AI 未按预期 JSON 格式输出，需人工审阅。",
                "uncertain_items": ["[整个响应需要人工审阅]"],
            }

    def stub_response(self, context: TaskContext) -> str:
        return (
            "```json\n"
            + json.dumps(
                {
                    "task_type": self.task_type,
                    "case_id": context.case_id,
                    "status": "stub_mode",
                    "items": [],
                    "uncertain_items": [
                        "【存根模式】未调用 Claude API，请设置 ANTHROPIC_API_KEY 环境变量。"
                    ],
                    "summary": "存根模式，未实际调用 AI。",
                    "review_notes": "请设置 ANTHROPIC_API_KEY 后重新运行以获取真实结果。",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n```"
        )

    def _format_input_section(self, context: TaskContext) -> str:
        if not context.input_files:
            return (
                "（未找到输入文件。请将项目文件放入 "
                f"cases/{context.case_id}/input/ 目录后重新运行。）"
            )
        parts = []
        for fname, content in context.input_files.items():
            parts.append(f"### 文件：{fname}\n{content}\n")
        return "\n".join(parts)

    def _guidance_section(self, context: TaskContext) -> str:
        if context.guidance_text:
            return f"## 作业指导（Guidance）\n\n{context.guidance_text}\n"
        return ""
