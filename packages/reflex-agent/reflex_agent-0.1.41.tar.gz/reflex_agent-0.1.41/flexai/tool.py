"""Base class to define agent tools."""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, get_origin, get_type_hints

JSON_SCHEMA_TYPES = Literal[
    "string", "integer", "number", "boolean", "array", "object", "null"
]

# Convert Python types to JSON schema types.
TYPE_MAP: dict[type | None, JSON_SCHEMA_TYPES] = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}

UNSPECIFIED_JSON_SCHEMA_TYPE = Literal["type_unspecified"]
TYPE_UNSPECIFIED = "type_unspecified"


# ToolType can be either a single type or a union of multiple types
ToolType = (
    JSON_SCHEMA_TYPES
    | UNSPECIFIED_JSON_SCHEMA_TYPE
    | tuple[JSON_SCHEMA_TYPES | UNSPECIFIED_JSON_SCHEMA_TYPE, ...]
)


def format_primitive_type(
    arg_type,
) -> JSON_SCHEMA_TYPES | UNSPECIFIED_JSON_SCHEMA_TYPE:
    return TYPE_MAP.get(get_origin(arg_type) or arg_type, TYPE_UNSPECIFIED)


def format_type(arg_type) -> ToolType:
    if isinstance(arg_type, types.UnionType):
        sub_types: list[JSON_SCHEMA_TYPES | UNSPECIFIED_JSON_SCHEMA_TYPE] = [
            format_primitive_type(sub_type) for sub_type in arg_type.__args__
        ]
        return tuple(sub_types)

    return format_primitive_type(arg_type)


@dataclass(frozen=True)
class Tool:
    """A tool is a function that can be called by an agent."""

    # The name of the tool.
    name: str

    # A description of how the tool works - this should be detailed
    description: str

    # The function parameters and their types.
    params: tuple[tuple[str, ToolType], ...]

    # The return type of the function.
    return_type: str

    # The function to call.
    fn: Callable

    # Whether the tool needs additional runtime context.
    requires_context: bool = False

    @classmethod
    def from_function(cls, func: Callable) -> Tool:
        """Create a tool from a function.

        Args:
            func: The function to convert to a tool.

        Returns:
            A new tool instance.
        """
        signature = inspect.signature(func)

        # Check for **kwargs parameter
        requires_context = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in signature.parameters.values()
        )

        # Filter out kwargs from params
        function_types = get_type_hints(func)
        params: tuple[tuple[str, ToolType], ...] = tuple(
            (
                name,
                format_type(function_types[name])
                if name in function_types
                else TYPE_UNSPECIFIED,
            )
            for name, param in signature.parameters.items()
            if param.kind != inspect.Parameter.VAR_KEYWORD
        )

        return_type = (
            signature.return_annotation.__name__
            if hasattr(signature.return_annotation, "__name__")
            else "No annotation"
        )
        description = inspect.getdoc(func) or "No description"
        return cls(
            name=func.__name__,
            description=description,
            params=params,
            return_type=return_type,
            fn=func,
            requires_context=requires_context,
        )


def send_message(message: str) -> None:
    """Send a final message to the user. This should be done after all internal processing is completed.

    Args:
        message: The message to send to the user.
    """
