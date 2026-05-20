"""
Entry-point-agnostic orchestrator.
Called from: CLI (run_agent.py), Feishu bot, Slack adapter, WeCom adapter, etc.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from agent.context import TaskContext, OrchestratorResult
from agent.task_classifier import get_task_display_name

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """你是一个专业的中国建设工程造价助手 AI。

工作原则（必须严格遵守）：
1. 输出只能作为工程量初稿，不作为最终造价成果。
2. 所有工程量计算必须保留计算依据和计算式（格式：长×宽×数量 = 结果）。
3. 不确定内容必须明确标记为"人工确认项"，绝不猜测或推断。
4. 不得伪造图纸依据，找不到依据时明确说明"未见图纸依据"。
5. 输出必须是合法的 JSON 格式（用 ```json ... ``` 包裹）。
6. 信息不足时，列出缺少的信息，不编造数据。
7. 不同省市地区规则可能不同，不可假设规则一致。
8. 发现矛盾或疑问时，列入 uncertain_items，不要自行决断。

输出语言：中文（专业术语保持行业标准用法）。"""


class Orchestrator:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")

    def run(self, context: TaskContext) -> OrchestratorResult:
        try:
            # 1. Validate case
            if not context.case_path.exists():
                return OrchestratorResult(
                    success=False,
                    error=f"案例目录不存在: {context.case_path}"
                )

            # 2. Load input files
            from file_io.readers import read_case_files, read_guidance_files
            context.input_files = read_case_files(context.case_path / "input")

            # 3. Load guidance
            context.guidance_text = read_guidance_files(context.task_type)

            # 4. Load knowledge summary
            context.knowledge_text = self._load_knowledge_summary()

            # 5. Get skill
            from skills import get_skill
            skill = get_skill(context.task_type)
            if skill is None:
                return OrchestratorResult(
                    success=False,
                    error=f"未找到对应 skill: {context.task_type}"
                )

            # 6. Build prompt
            prompt = skill.build_prompt(context)

            if context.dry_run:
                preview = prompt[:4000]
                sep = "=" * 60
                output = f"\n{sep}\nDRY RUN — 完整 prompt 预览（前 4000 字符）：\n{sep}\n{preview}\n{sep}\n"
                sys.stdout.buffer.write(output.encode("utf-8"))
                sys.stdout.buffer.flush()
                return OrchestratorResult(success=True, review_required=False)

            # 7. Call Claude or stub
            if self.api_key:
                raw_response = self._call_claude(prompt, context)
            else:
                print("⚠  ANTHROPIC_API_KEY 未设置，使用存根模式运行（不调用 AI）。")
                raw_response = skill.stub_response(context)

            # 8. Parse response
            result_data = skill.parse_response(raw_response, context)

            # 9. Add metadata
            result_data["_meta"] = {
                "task_type": context.task_type,
                "task_display": get_task_display_name(context.task_type),
                "case_id": context.case_id,
                "model": context.model_override or DEFAULT_MODEL,
                "timestamp": datetime.now().isoformat(),
                "review_required": True,
                "disclaimer": (
                    "【重要免责声明】AI 输出仅作为工程量初稿参考，"
                    "不作为最终造价成果，必须经过注册造价师人工复核后方可使用。"
                ),
            }

            # 10. Write output
            from file_io.writers import write_output
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = write_output(
                result_data,
                context.output_dir / f"{context.task_type}_{ts}.json"
            )

            uncertain_count = len(result_data.get("uncertain_items", []))
            return OrchestratorResult(
                success=True,
                output_path=output_path,
                uncertain_count=uncertain_count,
                review_required=True,
            )

        except Exception as e:
            import traceback
            return OrchestratorResult(success=False, error=f"{e}\n{traceback.format_exc()}")

    def _call_claude(self, prompt: str, context: TaskContext) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        model = context.model_override or DEFAULT_MODEL

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _load_knowledge_summary(self) -> str:
        knowledge_file = PROJECT_ROOT / "knowledge" / "china_cost_engineering_tasks.md"
        if knowledge_file.exists():
            text = knowledge_file.read_text(encoding="utf-8")
            return text[:3000]
        return ""
