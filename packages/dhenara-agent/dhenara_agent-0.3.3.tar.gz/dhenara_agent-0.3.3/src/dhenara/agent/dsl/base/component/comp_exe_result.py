from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import Field

from dhenara.agent.dsl.base import (
    ExecutableTypeEnum,
    ExecutionStatusEnum,
    NodeExecutionResult,
    NodeID,
    NodeInputT,
    NodeOutcomeT,
    NodeOutputT,
)
from dhenara.agent.types.base import BaseModel


class ComponentExecutionResult(BaseModel, Generic[NodeInputT, NodeOutputT, NodeOutcomeT]):
    executable_type: ExecutableTypeEnum
    component_id: str
    is_rerun: bool
    start_hierarchy_path: str | None

    execution_status: ExecutionStatusEnum
    execution_results: dict[
        NodeID,
        NodeExecutionResult[
            NodeInputT,
            NodeOutputT,
            NodeOutcomeT,
        ],
    ] = Field(default_factory=dict, description="Individual node's execution result")

    error: str | None = None
    errors: list[str] | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # --- Aggregated usage / cost (derived from child node execution results) ---
    agg_usage_cost: float | None = Field(default=None, description="Sum of usage_cost across descendant nodes")
    agg_usage_charge: float | None = Field(
        default=None,
        description="Sum of usage_charge across descendant nodes (if any charge data present)",
    )
    agg_usage_prompt_tokens: int | None = Field(default=None)
    agg_usage_completion_tokens: int | None = Field(default=None)
    agg_usage_total_tokens: int | None = Field(default=None)


ComponentExeResultT = TypeVar("ComponentDefT", bound=ComponentExecutionResult)
# -----------------------------------------------------------------------------
# NodeExecutionResults = dict[NodeID, NodeExecutionResult[OutputT, OutcomeT]]
