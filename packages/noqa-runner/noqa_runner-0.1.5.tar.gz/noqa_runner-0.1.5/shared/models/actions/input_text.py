from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

from shared.models.actions.base import BaseAction
from shared.models.state.screen import ActiveElement


class InputText(BaseAction):
    """Input text into a mobile element"""

    name: Literal["input_text"] = "input_text"
    element_number: int = Field(
        description="Number of the element to input text into", ge=1
    )
    text: str = Field(description="Text to input into the element", min_length=1)
    element: SkipJsonSchema[ActiveElement | None] = None
    elements_tree: SkipJsonSchema[str | None] = Field(default=None)

    def get_action_description(self) -> str:
        """Get description of input text action"""
        return f"Input text '{self.text}' in element: {self.element.string_description}"
