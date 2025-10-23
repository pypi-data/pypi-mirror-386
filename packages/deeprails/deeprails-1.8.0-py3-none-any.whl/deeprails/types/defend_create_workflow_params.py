# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Literal, Required, TypedDict

__all__ = ["DefendCreateWorkflowParams"]


class DefendCreateWorkflowParams(TypedDict, total=False):
    improvement_action: Required[Literal["regen", "fixit", "do_nothing"]]
    """
    The action used to improve outputs that fail one or guardrail metrics for the
    workflow events. May be `regen`, `fixit`, or `do_nothing`. ReGen runs the user's
    input prompt with minor induced variance. FixIt attempts to directly address the
    shortcomings of the output using the guardrail failure rationale. Do Nothing
    does not attempt any improvement.
    """

    name: Required[str]
    """Name of the workflow."""

    type: Required[Literal["automatic", "custom"]]
    """Type of thresholds to use for the workflow, either `automatic` or `custom`.

    Automatic thresholds are assigned internally after the user specifies a
    qualitative tolerance for the metrics, whereas custom metrics allow the user to
    set the threshold for each metric as a floating point number between 0.0 and
    1.0.
    """

    automatic_hallucination_tolerance_levels: Dict[str, Literal["low", "medium", "high"]]
    """
    Mapping of guardrail metrics to hallucination tolerance levels (either `low`,
    `medium`, or `high`). Possible metrics are `completeness`,
    `instruction_adherence`, `context_adherence`, `ground_truth_adherence`, or
    `comprehensive_safety`.
    """

    custom_hallucination_threshold_values: Dict[str, float]
    """Mapping of guardrail metrics to floating point threshold values.

    Possible metrics are `correctness`, `completeness`, `instruction_adherence`,
    `context_adherence`, `ground_truth_adherence`, or `comprehensive_safety`.
    """

    description: str
    """Description for the workflow."""

    max_improvement_attempt: int
    """Max.

    number of improvement action retries until a given event passes the guardrails.
    Defaults to 10.
    """
