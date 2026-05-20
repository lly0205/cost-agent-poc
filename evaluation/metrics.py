"""
Evaluation metrics for Cost Engineer AI Agent.
8 dimensions for comparing AI output vs human golden answer.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ItemComparison:
    item_name: str
    ai_quantity: Optional[float]
    golden_quantity: Optional[float]
    unit: str = ""
    deviation_pct: Optional[float] = None
    status: str = ""  # matched / deviation / omission / extra

    def compute_deviation(self):
        if self.ai_quantity is not None and self.golden_quantity:
            self.deviation_pct = abs(
                (self.ai_quantity - self.golden_quantity) / self.golden_quantity * 100
            )
            if self.deviation_pct <= 2.0:
                self.status = "matched"
            elif self.deviation_pct <= 5.0:
                self.status = "minor_deviation"
            else:
                self.status = "deviation"
        elif self.ai_quantity is None and self.golden_quantity is not None:
            self.status = "omission"
            self.deviation_pct = 100.0
        elif self.ai_quantity is not None and self.golden_quantity is None:
            self.status = "extra"


@dataclass
class EvaluationScores:
    # 1. 准确率 (0-100): proportion of items within 5% deviation
    accuracy: float = 0.0
    accuracy_comment: str = ""

    # 2. 漏项率 (0-100, lower=better): proportion of golden items missing in AI
    omission_rate: float = 0.0
    omission_comment: str = ""

    # 3. 重复计算率 (0-100, lower=better): duplicate items in AI output
    duplication_rate: float = 0.0
    duplication_comment: str = ""

    # 4. 数量偏差率 (0-100, lower=better): average % deviation on matched items
    quantity_deviation: float = 0.0
    quantity_deviation_comment: str = ""

    # 5. 可解释性 (0-100): proportion of items with formula + drawing reference
    explainability: float = 0.0
    explainability_comment: str = ""

    # 6. 复核成本 (0-100, higher=lower review cost): estimated review effort
    review_cost_score: float = 0.0
    review_cost_comment: str = ""

    # 7. 图纸依据完整性 (0-100): proportion of items with drawing reference
    drawing_reference: float = 0.0
    drawing_reference_comment: str = ""

    # 8. 不确定项标记 (0-100): quality of uncertainty marking
    uncertainty_marking: float = 0.0
    uncertainty_marking_comment: str = ""

    @property
    def overall_score(self) -> float:
        weights = {
            "accuracy": 0.25,
            "omission_rate": 0.20,      # inverted: high score = low rate
            "duplication_rate": 0.10,   # inverted
            "quantity_deviation": 0.10, # inverted
            "explainability": 0.15,
            "review_cost_score": 0.05,
            "drawing_reference": 0.10,
            "uncertainty_marking": 0.05,
        }
        # For inverted metrics, score = 100 - rate
        omission_score = max(0, 100 - self.omission_rate)
        dup_score = max(0, 100 - self.duplication_rate)
        dev_score = max(0, 100 - self.quantity_deviation)

        total = (
            self.accuracy * weights["accuracy"]
            + omission_score * weights["omission_rate"]
            + dup_score * weights["duplication_rate"]
            + dev_score * weights["quantity_deviation"]
            + self.explainability * weights["explainability"]
            + self.review_cost_score * weights["review_cost_score"]
            + self.drawing_reference * weights["drawing_reference"]
            + self.uncertainty_marking * weights["uncertainty_marking"]
        )
        return round(total, 1)

    def to_dict(self) -> dict:
        return {
            "accuracy": {"score": round(self.accuracy, 1), "comment": self.accuracy_comment},
            "omission_rate": {"score": round(self.omission_rate, 1), "comment": self.omission_comment},
            "duplication_rate": {"score": round(self.duplication_rate, 1), "comment": self.duplication_comment},
            "quantity_deviation": {"score": round(self.quantity_deviation, 1), "comment": self.quantity_deviation_comment},
            "explainability": {"score": round(self.explainability, 1), "comment": self.explainability_comment},
            "review_cost_score": {"score": round(self.review_cost_score, 1), "comment": self.review_cost_comment},
            "drawing_reference": {"score": round(self.drawing_reference, 1), "comment": self.drawing_reference_comment},
            "uncertainty_marking": {"score": round(self.uncertainty_marking, 1), "comment": self.uncertainty_marking_comment},
            "overall_score": self.overall_score,
        }
