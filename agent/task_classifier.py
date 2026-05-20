from typing import Optional

TASK_KEYWORD_MAP = {
    "drawing_review": [
        "图纸审阅", "图纸审查", "图纸会审", "图纸复核", "图纸检查",
        "drawing review", "drawing_review",
    ],
    "quantity_takeoff": [
        "工程量初算", "工程量计算", "算量", "工程量",
        "quantity takeoff", "quantity_takeoff",
    ],
    "boq_check": [
        "清单复核", "清单检查", "工程量清单", "清单审核",
        "boq check", "boq_check",
    ],
    "variation_claim": [
        "变更", "签证", "变更单", "签证单", "工程变更",
        "variation", "claim", "variation_claim",
    ],
    "glodon_integration": [
        "广联达", "gtj", "gqi", "gccp", "glodon",
    ],
    "evaluation": [
        "评测", "评估", "对比", "精度", "准确率",
        "evaluation",
    ],
}

TASK_DISPLAY_NAMES = {
    "drawing_review": "图纸审阅",
    "quantity_takeoff": "工程量初算",
    "boq_check": "工程量清单复核",
    "variation_claim": "变更单/签证资料整理",
    "glodon_integration": "广联达集成",
    "evaluation": "AI结果评测",
}


def classify_task(text: str) -> Optional[str]:
    """Classify free-text input into a task type. Returns None if unclear."""
    text_lower = text.lower()
    for task_type, keywords in TASK_KEYWORD_MAP.items():
        if any(kw in text_lower for kw in keywords):
            return task_type
    return None


def get_task_display_name(task_type: str) -> str:
    return TASK_DISPLAY_NAMES.get(task_type, task_type)


def list_all_tasks() -> list[dict]:
    return [
        {"task_type": k, "display": v}
        for k, v in TASK_DISPLAY_NAMES.items()
    ]
