from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class TaskContext:
    task_type: str
    case_id: str
    extra_input: Optional[str] = None
    model_override: Optional[str] = None
    dry_run: bool = False

    # Populated by orchestrator
    case_path: Path = field(default=None)
    input_files: dict = field(default_factory=dict)
    guidance_text: str = ""
    knowledge_text: str = ""

    def __post_init__(self):
        if self.case_path is None:
            self.case_path = PROJECT_ROOT / "cases" / self.case_id

    @property
    def output_dir(self) -> Path:
        path = PROJECT_ROOT / "outputs" / self.case_id
        path.mkdir(parents=True, exist_ok=True)
        return path


@dataclass
class OrchestratorResult:
    success: bool
    output_path: Optional[Path] = None
    uncertain_count: int = 0
    review_required: bool = True
    error: Optional[str] = None
