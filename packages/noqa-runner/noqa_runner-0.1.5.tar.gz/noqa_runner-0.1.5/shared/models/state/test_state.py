from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from shared.models.state.condition import Condition
from shared.models.state.step import Step


class TestStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    STOPPED = "stopped"


def merge_dicts(current: dict, update: dict) -> dict:
    result = current.copy()
    result.update(update)
    return result


class TestState(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow any types
        use_enum_values=True,  # Use enum values
        validate_assignment=True,  # Validate on assignment
    )

    case_name: str | None = None
    case_instructions: str = Field(min_length=1)
    test_id: str | None = None

    app_name: str | None = None
    app_description: str | None = None
    bundle_id: str | None = None
    app_context: str | None = None

    conditions: list[Condition] = Field(default_factory=list)
    resolution: dict | None = None
    action_system_prompt: str = ""

    status: TestStatus = TestStatus.IN_PROGRESS
    result_summary: str | None = None

    steps: Annotated[dict[int, Step], merge_dicts] = Field(default_factory=dict)

    @property
    def sorted_steps(self) -> list[Step]:
        """Get steps sorted by step number"""
        if not self.steps:
            return []
        sorted_step_numbers = sorted(self.steps.keys())
        return [self.steps[num] for num in sorted_step_numbers]

    @property
    def current_step(self) -> Step | None:
        """Get current (last) step"""
        sorted_steps = self.sorted_steps
        return sorted_steps[-1] if sorted_steps else None

    @property
    def previous_step(self) -> Step | None:
        """Get previous step"""
        sorted_steps = self.sorted_steps
        return sorted_steps[-2] if len(sorted_steps) >= 2 else None

    def export_dict(self) -> dict:
        """Export test data for external systems"""
        return {
            "case_instructions": self.case_instructions,
            "status": self.status,
            "message": self.result_summary,
            "test_conditions": [
                condition.model_dump() for condition in self.conditions
            ],
            "resolution": self.resolution,
            "steps": [
                {
                    "number": step.number,
                    "action": (
                        step.action_data.action.name if step.action_data else None
                    ),
                    "element": (
                        element.model_dump()
                        if step.action_data
                        and (
                            element := getattr(step.action_data.action, "element", None)
                        )
                        else None
                    ),
                    "screenshot_url": (
                        step.screen.screenshot_url if step.screen else None
                    ),
                }
                for step in self.sorted_steps
            ],
        }
