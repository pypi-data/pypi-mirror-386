import collections.abc
import numbers

import numerical
import numpy.typing

from . import typeface


DataType = typeface.TypeVar(
    'DataType',
    int,
    float,
    numbers.Number,
    numpy.number,
    numpy.typing.ArrayLike,
    numpy.typing.NDArray,
)


@typeface.runtime_checkable
class Quantity(numerical.Quantity[DataType], typeface.Protocol):
    """Protocol for numerical objects with metadata."""

    _meta: collections.abc.Mapping[str, typeface.Any]


class Object(numerical.Real, typeface.Generic[DataType]):
    """A real-valued object with metadata attributes."""

    def __init__(
        self,
        __data: DataType,
        **metadata,
    ) -> None:
        if not isinstance(__data, numerical.Real):
            raise TypeError("Data input to Object must be real-valued")
        self._data = __data
        self._meta = metadata

    def __repr__(self):
        """Called for repr(self)."""
        try:
            datastr = numpy.array2string(
                self._data,
                separator=", ",
                threshold=6,
                edgeitems=2,
                prefix=f"{self.__class__.__qualname__}(",
                suffix=")"
            )
        except Exception:
            datastr = str(self._data)
        metastr = "metadata={" + ", ".join(f"{k!r}" for k in self._meta) + "}"
        return f"{self.__class__.__qualname__}({datastr}, {metastr})"

