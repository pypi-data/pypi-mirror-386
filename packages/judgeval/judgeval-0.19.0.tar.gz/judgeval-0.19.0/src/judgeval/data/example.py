"""
Classes for representing examples in a dataset.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from judgeval.data.judgment_types import Example as JudgmentExample
from uuid import uuid4
from pydantic import Field


class ExampleParams(str, Enum):
    INPUT = "input"
    ACTUAL_OUTPUT = "actual_output"
    EXPECTED_OUTPUT = "expected_output"
    CONTEXT = "context"
    RETRIEVAL_CONTEXT = "retrieval_context"
    TOOLS_CALLED = "tools_called"
    EXPECTED_TOOLS = "expected_tools"
    ADDITIONAL_METADATA = "additional_metadata"


class Example(JudgmentExample):
    example_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().model_dump(warnings=False)
        return data

    def get_fields(self):
        excluded = {"example_id", "name", "created_at"}
        return self.model_dump(exclude=excluded)
