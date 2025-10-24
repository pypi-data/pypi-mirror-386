from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Iterable, TypeVar

if TYPE_CHECKING:
    from cartographer.interfaces.printer import MacroParams

T = TypeVar("T", bound=Enum)


def get_enum_choice(params: MacroParams, option: str, enum_type: type[T], default: T) -> T:
    choice = params.get(option, default=default.value)

    # Convert both the choice and enum values to lowercase for case-insensitive comparison
    lower_choice = str(choice).lower()
    lower_mapping = {str(v.value).lower(): v for v in enum_type}

    if lower_choice not in lower_mapping:
        msg = f"Invalid choice '{choice}' for option '{option}'"
        raise RuntimeError(msg)

    return lower_mapping[lower_choice]


K = TypeVar("K", bound=str)


def get_choice(params: MacroParams, option: str, choices: Iterable[K], default: K) -> K:
    choice = params.get(option, default=default)
    choice_str = choice.lower()

    for k in choices:
        if k.lower() == choice_str:
            return k

    valid_choices = ", ".join(f"'{k.lower()}'" for k in choices)
    msg = f"Invalid choice '{choice}' for option '{option}'. Valid choices are: {valid_choices}"
    raise RuntimeError(msg)


def get_int_tuple(params: MacroParams, option: str, default: tuple[int, int]) -> tuple[int, int]:
    param = params.get(option, default=None)
    if param is None:
        return default
    parts = param.split(",")
    if len(parts) != 2:
        msg = f"Expected two int values for '{option}', got {len(parts)}: {param}"
        raise ValueError(msg)

    return (int(parts[0]), int(parts[1]))


def get_float_tuple(params: MacroParams, option: str, default: tuple[float, float]) -> tuple[float, float]:
    param = params.get(option, default=None)
    if param is None:
        return default
    parts = param.split(",")
    if len(parts) != 2:
        msg = f"Expected two float values for '{option}', got {len(parts)}: {param}"
        raise ValueError(msg)

    return (float(parts[0]), float(parts[1]))
