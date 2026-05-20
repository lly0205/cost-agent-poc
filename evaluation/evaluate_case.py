"""
Evaluation script: compare AI output vs human golden answer.

Usage:
  python evaluation/evaluate_case.py --case sample_case_001
  python evaluation/evaluate_case.py --case sample_case_001 --ai-file outputs/sample_case_001/quantity_takeoff_20240101_120000.json
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from evaluation.metrics import EvaluationScores, ItemComparison

PROJECT_ROOT = Path(__file__).parent.parent


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def find_latest_ai_output(case_id: str) -> Path:
    output_dir = PROJECT_ROOT / "outputs" / case_id
    if not output_dir.exists():
        raise FileNotFoundError(f"outputs/{case_id}/ 目录不存在，请先运行算量任务。")
    # Prefer quantity_takeoff, then any output
    files = sorted(output_dir.glob("quantity_takeoff_*.json"), reverse=True)
    if not files:
        files = sorted(output_dir.glob("*.json"), reverse=True)
        files = [f for f in files if not f.name.startswith("evaluation_")]
    if not files:
        raise FileNotFoundError(f"outputs/{case_id}/ 中未找到 AI 输出文件。")
    return files[0]


def compare_items(ai_items: list, golden_items: list) -> list[ItemComparison]:
    comparisons = []

    golden_by_name = {
        item.get("name", item.get("id", "")): item
        for item in golden_items
    }
    ai_by_name = {
        item.get("name", item.get("id", "")): item
        for item in ai_items
    }

    # Check all golden items
    for name, g_item in golden_by_name.items():
        a_item = ai_by_name.get(name)
        comp = ItemComparison(
            item_name=name,
            ai_quantity=float(a_item["quantity"]) if a_item and "quantity" in a_item else None,
            golden_quantity=float(g_item.get("quantity", 0)) if g_item.get("quantity") else None,
            unit=g_item.get("unit", ""),
        )
        comp.compute_deviation()
        comparisons.append(comp)

    # Extra AI items (not in golden)
    for name, a_item in ai_by_name.items():
        if name not in golden_by_name:
            comp = ItemComparison(
                item_name=name,
                ai_quantity=float(a_item.get("quantity", 0)),
                golden_quantity=None,
                unit=a_item.get("unit", ""),
                status="extra",
            )
            comparisons.append(comp)

    return comparisons


def compute_scores(
    ai_data: dict,
    golden_data: dict,
    comparisons: list[ItemComparison],
) -> EvaluationScores:
    scores = EvaluationScores()
    ai_items = ai_data.get("items", [])
    golden_items = golden_data.get("items", [])

    total_golden = len(golden_items)
    if total_golden == 0:
        scores.accuracy_comment = "人工答案为空，无法评测"
        return scores

    matched = [c for c in comparisons if c.status in ("matched", "minor_deviation")]
    omitted = [c for c in comparisons if c.status == "omission"]
    extras = [c for c in comparisons if c.status == "extra"]
    deviations = [c for c in comparisons if c.status == "deviation"]

    # 1. 准确率
    scores.accuracy = round(len(matched) / total_golden * 100, 1)
    scores.accuracy_comment = f"{len(matched)}/{total_golden} 条目偏差 ≤5%"

    # 2. 漏项率
    scores.omission_rate = round(len(omitted) / total_golden * 100, 1)
    scores.omission_comment = f"漏项 {len(omitted)} 条"

    # 3. 重复计算率 (simplified: check for duplicate names in AI output)
    ai_names = [item.get("name", "") for item in ai_items]
    dup_count = len(ai_names) - len(set(ai_names))
    scores.duplication_rate = round(dup_count / max(len(ai_names), 1) * 100, 1)
    scores.duplication_comment = f"发现 {dup_count} 条疑似重复"

    # 4. 数量偏差率 (average over matched items)
    matched_devs = [c.deviation_pct for c in comparisons if c.deviation_pct is not None and c.status not in ("omission", "extra")]
    if matched_devs:
        scores.quantity_deviation = round(sum(matched_devs) / len(matched_devs), 1)
        scores.quantity_deviation_comment = f"匹配条目平均偏差 {scores.quantity_deviation}%"
    else:
        scores.quantity_deviation_comment = "无可比较的匹配条目"

    # 5. 可解释性 (items with formula AND drawing_ref)
    if ai_items:
        explained = sum(
            1 for item in ai_items
            if item.get("formula") and item.get("drawing_ref")
        )
        scores.explainability = round(explained / len(ai_items) * 100, 1)
        scores.explainability_comment = f"{explained}/{len(ai_items)} 条有计算式和图纸依据"

    # 6. 复核成本 (heuristic: fewer uncertain items = lower review cost = higher score)
    uncertain_count = len(ai_data.get("uncertain_items", []))
    # Penalize if > 20% of items are uncertain
    if ai_items:
        uncertain_ratio = uncertain_count / len(ai_items)
        scores.review_cost_score = round(max(0, 100 - uncertain_ratio * 200), 1)
    scores.review_cost_comment = f"不确定项 {uncertain_count} 条"

    # 7. 图纸依据完整性
    if ai_items:
        with_ref = sum(1 for item in ai_items if item.get("drawing_ref"))
        scores.drawing_reference = round(with_ref / len(ai_items) * 100, 1)
        scores.drawing_reference_comment = f"{with_ref}/{len(ai_items)} 条有图纸依据"

    # 8. 不确定项标记 (penalize 0 uncertain items in a complex project — may mean AI didn't check)
    if uncertain_count > 0:
        scores.uncertainty_marking = 80.0
        scores.uncertainty_marking_comment = f"已标注 {uncertain_count} 个不确定项，需人工确认"
    else:
        scores.uncertainty_marking = 40.0
        scores.uncertainty_marking_comment = "未标注任何不确定项，请检查是否遗漏"

    return scores


def run_evaluation(case_id: str, ai_file: Path = None) -> dict:
    # Load golden answer
    golden_path = PROJECT_ROOT / "cases" / case_id / "golden_answer" / "human_answer.json"
    golden_data = load_json(golden_path)

    # Load AI output
    if ai_file is None:
        ai_file = find_latest_ai_output(case_id)
    ai_data = load_json(ai_file)

    print(f"\n评测案例: {case_id}")
    print(f"  AI 输出: {ai_file.name}")
    print(f"  人工答案: {golden_path.name}")

    # Compare items
    comparisons = compare_items(
        ai_data.get("items", []),
        golden_data.get("items", []),
    )

    # Compute scores
    scores = compute_scores(ai_data, golden_data, comparisons)

    # Build report
    report = {
        "case_id": case_id,
        "ai_output_file": str(ai_file.name),
        "golden_answer_reviewer": golden_data.get("reviewer", "未知"),
        "evaluation_timestamp": datetime.now().isoformat(),
        "scores": scores.to_dict(),
        "item_comparisons": [
            {
                "item": c.item_name,
                "ai_quantity": c.ai_quantity,
                "golden_quantity": c.golden_quantity,
                "unit": c.unit,
                "deviation_pct": round(c.deviation_pct, 2) if c.deviation_pct is not None else None,
                "status": c.status,
            }
            for c in comparisons
        ],
        "summary": {
            "total_golden_items": len(golden_data.get("items", [])),
            "total_ai_items": len(ai_data.get("items", [])),
            "total_uncertain_items": len(ai_data.get("uncertain_items", [])),
            "overall_score": scores.overall_score,
        },
    }

    # Save report
    output_dir = PROJECT_ROOT / "outputs" / case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"evaluation_report_{ts}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n评测结果：")
    print(f"  综合评分: {scores.overall_score} / 100")
    print(f"  准确率: {scores.accuracy}%")
    print(f"  漏项率: {scores.omission_rate}%")
    print(f"  可解释性: {scores.explainability}%")
    print(f"\n  报告已保存: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Cost Engineer AI Agent — 评测工具")
    parser.add_argument("--case", required=True, help="案例 ID")
    parser.add_argument("--ai-file", default=None, help="指定 AI 输出文件路径（可选）")
    args = parser.parse_args()

    ai_file = Path(args.ai_file) if args.ai_file else None
    run_evaluation(args.case, ai_file)


if __name__ == "__main__":
    main()
