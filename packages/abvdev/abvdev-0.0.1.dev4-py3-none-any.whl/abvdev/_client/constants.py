"""Constants used by the ABV OpenTelemetry integration.

This module defines constants used throughout the ABV OpenTelemetry integration.
"""

from typing import Literal, List, get_args, Union, Any
from typing_extensions import TypeAlias

ABV_TRACER_NAME = "abv-sdk"


"""Note: this type is used with .__args__ / get_args in some cases and therefore must remain flat"""
ObservationTypeGenerationLike: TypeAlias = Literal[
    "generation",
    "embedding",
]

ObservationTypeSpanLike: TypeAlias = Literal[
    "span",
    "agent",
    "tool",
    "chain",
    "retriever",
    "evaluator",
    "guardrail",
]

ObservationTypeLiteralNoEvent: TypeAlias = Union[
    ObservationTypeGenerationLike,
    ObservationTypeSpanLike,
]

"""Enumeration of valid observation types for ABV tracing.

This Literal defines all available observation types that can be used with the @observe
decorator and other ABV SDK methods.
"""
ObservationTypeLiteral: TypeAlias = Union[
    ObservationTypeLiteralNoEvent, Literal["event"]
]


def get_observation_types_list(
    literal_type: Any,
) -> List[str]:
    """Flattens the Literal type to provide a list of strings.

    Args:
        literal_type: A Literal type, TypeAlias, or union of Literals to flatten

    Returns:
        Flat list of all string values contained in the Literal type
    """
    result = []
    args = get_args(literal_type)

    for arg in args:
        if hasattr(arg, "__args__"):
            result.extend(get_observation_types_list(arg))
        else:
            result.append(arg)

    return result
