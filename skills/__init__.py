from skills.drawing_review_skill import DrawingReviewSkill
from skills.quantity_takeoff_skill import QuantityTakeoffSkill
from skills.boq_check_skill import BOQCheckSkill
from skills.variation_claim_skill import VariationClaimSkill
from skills.glodon_integration_skill import GlodonIntegrationSkill
from skills.evaluation_skill import EvaluationSkill
from skills.drawing_boq_skill import DrawingBOQSkill
from skills.drawing_recognition_skill import DrawingRecognitionSkill
from skills.attachment_upload_skill import AttachmentUploadSkill

SKILL_REGISTRY = {
    "drawing_review": DrawingReviewSkill(),
    "quantity_takeoff": QuantityTakeoffSkill(),
    "boq_check": BOQCheckSkill(),
    "variation_claim": VariationClaimSkill(),
    "glodon_integration": GlodonIntegrationSkill(),
    "evaluation": EvaluationSkill(),
    "drawing_boq": DrawingBOQSkill(),
    "drawing_recognition": DrawingRecognitionSkill(),
    "attachment_upload": AttachmentUploadSkill(),
}


def get_skill(task_type: str):
    return SKILL_REGISTRY.get(task_type)
