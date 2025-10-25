from typing import Any


def null(
    *args,
    **kwargs,
) -> None:
    return None


def set_inline(
    object,
    property,
    value,
) -> Any:
    object.__setitem__(property, value)

    return object
