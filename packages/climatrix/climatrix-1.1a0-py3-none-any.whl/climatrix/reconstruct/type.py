import logging
from enum import Enum

log = logging.getLogger(__name__)

from climatrix.reconstruct.base import BaseReconstructor

ReconstructionType = Enum(
    "ReconstructionType",
    {name.upper(): cls for name, cls in BaseReconstructor._registry.items()},
)


def __missing__(cls, value):
    raise ValueError(f"Unknown reconstruction method: {value}")


def get(cls, value: str | ReconstructionType):
    """
    Get the reconstruction type given by `value`.

    If `value` is an instance of ReconstructionType,
    return it as is.
    If `value` is a string, return the corresponding
    ReconstructionType.
    If `value` is neither an instance of ReconstructionType
    nor a string,
    raise a ValueError.

    Parameters
    ----------
    value : str | ReconstructionType
        The reconstruction type to get.

    Returns
    -------
    ReconstructionType
        The reconstruction type.

    Raises
    ------
    ValueError
        If `value` is not a valid reconstruction type.
    """
    if isinstance(value, cls):
        return value
    if not isinstance(value, str):
        raise TypeError(
            f"Invalid reconstruction type: {value!r}. "
            "Expected a string or an instance of ReconstructionType."
        )
    try:
        return cls[value.upper()]
    except KeyError:
        raise ValueError(
            f"Unknown reconstruction type: {value}. "
            f"Supported types are: ({', '.join(cls.list())})."
            "Ensure that the required packages are installed."
        )


def list(cls) -> list[str]:
    """
    List all available reconstruction types.

    Returns
    -------
    list[str]
        A list of all available reconstruction types.
    """
    return [name.lower() for name in cls.__members__.keys()]


setattr(ReconstructionType, "__missing__", classmethod(__missing__))
setattr(ReconstructionType, "get", classmethod(get))
setattr(ReconstructionType, "list", classmethod(list))
