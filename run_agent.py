#!/usr/bin/env python3
"""
Cost Engineer AI Agent — CLI 入口

用法示例：
  python run_agent.py --task drawing_review  --case sample_case_001
  python run_agent.py --task quantity_takeoff --case sample_case_001
  python run_agent.py --task boq_check        --case sample_case_001
  python run_agent.py --task variation_claim  --case sample_case_001
  python run_agent.py --task evaluation       --case sample_case_001
  python run_agent.py --task quantity_takeoff --case sample_case_001 --dry-run
  python run_agent.py --list-tasks
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agent.orchestrator import Orchestrator
from agent.context import TaskContext
from agent.task_classifier import list_all_tasks

VALID_TASKS = [
    "drawing_review",
    "quantity_takeoff",
    "boq_check",
    "variation_claim",
    "glodon_integration",
    "evaluation",
]


def main():
    parser = argparse.ArgumentParser(
        prog="run_agent.py",
        description="Cost Engineer AI Agent — PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python run_agent.py --task drawing_review  --case sample_case_001
  python run_agent.py --task quantity_takeoff --case sample_case_001
  python run_agent.py --task boq_check        --case sample_case_001
  python run_agent.py --task evaluation       --case sample_case_001
  python run_agent.py --task quantity_takeoff --case sample_case_001 --dry-run
  python run_agent.py --list-tasks
        """,
    )
    parser.add_argument(
        "--task", choices=VALID_TASKS, default=None,
        help="任务类型",
    )
    parser.add_argument(
        "--case", default=None,
        help="案例 ID（cases/ 下的文件夹名）",
    )
    parser.add_argument(
        "--input", default=None,
        help="可选：直接输入文字（覆盖案例文件）",
    )
    parser.add_argument(
        "--model", default=None,
        help="指定 Claude 模型（默认：claude-sonnet-4-6）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只输出 prompt，不调用 AI",
    )
    parser.add_argument(
        "--list-tasks", action="store_true",
        help="列出所有可用任务类型",
    )
    parser.add_argument(
        "--list-cases", action="store_true",
        help="列出所有可用案例",
    )

    args = parser.parse_args()

    if args.list_tasks:
        print("\n可用任务类型：")
        for t in list_all_tasks():
            print(f"  {t['task_type']:<25} {t['display']}")
        return

    if args.list_cases:
        cases_dir = Path(__file__).parent / "cases"
        cases = [d.name for d in sorted(cases_dir.iterdir()) if d.is_dir()]
        print("\n可用案例：")
        for c in cases:
            print(f"  {c}")
        return

    if not args.task:
        parser.print_help()
        print("\n错误：请指定 --task 参数，或使用 --list-tasks 查看可用任务。")
        sys.exit(1)

    if not args.case:
        print("错误：请指定 --case 参数，或使用 --list-cases 查看可用案例。")
        sys.exit(1)

    context = TaskContext(
        task_type=args.task,
        case_id=args.case,
        extra_input=args.input,
        model_override=args.model,
        dry_run=args.dry_run,
    )

    print(f"\n{'=' * 55}")
    print(f"  Cost Engineer AI Agent — {args.task}")
    print(f"  案例: {args.case}")
    if args.dry_run:
        print("  模式: DRY RUN（不调用 AI）")
    print(f"{'=' * 55}")

    orchestrator = Orchestrator()
    result = orchestrator.run(context)

    if result.success:
        print(f"\n完成：{args.task} / {args.case}")
        if result.output_path:
            print(f"  输出文件：{result.output_path}")
        if result.uncertain_count > 0:
            print(f"  待人工确认项：{result.uncertain_count} 条（见输出文件 uncertain_items）")
        print(f"\n  【提醒】AI 输出仅供参考，使用前必须经造价师人工复核。")
    else:
        print(f"\n失败：{result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
