from skills.drawing_review_skill import DrawingReviewSkill
from skills.quantity_takeoff_skill import QuantityTakeoffSkill
from skills.boq_check_skill import BOQCheckSkill
from skills.variation_claim_skill import VariationClaimSkill
from skills.glodon_integration_skill import GlodonIntegrationSkill
from skills.evaluation_skill import EvaluationSkill

SKILL_REGISTRY = {
    "drawing_review": DrawingReviewSkill(),
    "quantity_takeoff": QuantityTakeoffSkill(),
    "boq_check": BOQCheckSkill(),
    "variation_claim": VariationClaimSkill(),
    "glodon_integration": GlodonIntegrationSkill(),
    "evaluation": EvaluationSkill(),
}


def get_skill(task_type: str):
    return SKILL_REGISTRY.get(task_type)
