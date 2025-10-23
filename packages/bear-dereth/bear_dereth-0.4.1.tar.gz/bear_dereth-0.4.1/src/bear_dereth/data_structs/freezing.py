"""Utilities for making objects immutable and hashable."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, NoReturn, Self, TypedDict, overload

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from bear_dereth.typing_tools import LitFalse, LitTrue, NoReturnCall

AllowableTypes = dict | list | set


class FrozenDict(dict):
    """An immutable dictionary.

    This is used to generate stable hashes for queries that contain dicts.
    Usually, Python dicts are not hashable because they are mutable. This
    class removes the mutability and implements the ``__hash__`` method.
    """

    def __hash__(self) -> int:  # type: ignore[override]
        """Calculate the has by hashing a tuple of all dict items"""
        return hash(tuple(sorted(self.items())))

    def _immutable(self, *args, **kws) -> NoReturn:
        """Disable any method that would modify the dict."""
        raise TypeError("FrozenDict is immutable!")

    __setitem__: NoReturnCall = _immutable
    __delitem__: NoReturnCall = _immutable
    clear: NoReturnCall = _immutable
    setdefault: NoReturnCall = _immutable  # type: ignore[override]
    popitem: NoReturnCall = _immutable
    update: NoReturnCall = _immutable  # type: ignore[override]
    pop: NoReturnCall = _immutable  # type: ignore[override]


@overload
def freeze(obj: dict) -> FrozenDict: ...
@overload
def freeze(obj: TypedDict) -> FrozenDict: ...  # type: ignore[misc]
@overload
def freeze(obj: list) -> tuple: ...
@overload
def freeze(obj: set) -> frozenset: ...
@overload
def freeze(obj: object) -> object: ...


def freeze(obj: AllowableTypes | object) -> FrozenDict | tuple | frozenset | object:
    """Freeze an object by making it immutable and thus hashable.

    Args:
        obj (AllowableTypes): The object to freeze. Can be a dict, list, or set.

    Returns:
        FrozenDict | tuple | frozenset | object: The frozen version of the object.

    Note:
        This function only handles dicts, lists, and sets. All other objects are returned as
        is without modification.

        If the input is a dict, it is converted to a ``FrozenDict``.
        If the input is a list, it is converted to a tuple.
        If the input is a set, it is converted to a ``frozenset``.
        Other types are returned unchanged.
    """
    if isinstance(obj, dict):
        return FrozenDict((k, freeze(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return tuple(freeze(el) for el in obj)
    if isinstance(obj, set):
        return frozenset(obj)
    return obj


ThawTypes = FrozenDict | tuple | frozenset


@overload
def thaw(obj: FrozenDict) -> dict: ...
@overload
def thaw(obj: tuple) -> list: ...
@overload
def thaw(obj: frozenset) -> set: ...
@overload
def thaw(obj: Any) -> Any: ...


def thaw(obj: ThawTypes | Any) -> AllowableTypes:
    """Thaw a frozen object back to its mutable form.

    Args:
        obj (Any): The object to thaw. Can be a FrozenDict, tuple, or frozenset.

    Returns:
        Any: The thawed version of the object.

    Note:
        This function only handles FrozenDicts, tuples, and frozensets. All other objects
        are returned as is without modification.
        If the input is a FrozenDict, it is converted to a dict.
        If the input is a tuple, it is converted to a list.
        If the input is a frozenset, it is converted to a set.
        Other types are returned unchanged.
    """
    if isinstance(obj, FrozenDict):
        return {k: thaw(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return [thaw(el) for el in obj]
    if isinstance(obj, frozenset):
        return set(obj)
    return obj


class FrozenModel(BaseModel):
    """A frozen Pydantic model that is immutable and hashable."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    cacheable: bool = Field(default=True, exclude=True)

    def get_hash(self) -> int:
        """Get the hash of the model based on its frozen representation."""
        return hash(self.model_dump())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FrozenModel):
            return NotImplemented
        return self.frozen == other.frozen

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, FrozenModel):
            return NotImplemented
        return self.frozen != other.frozen

    def __hash__(self) -> int:
        if not self.cacheable:
            raise TypeError("This HashValue is not cacheable")
        return self.get_hash()

    @classmethod
    def not_cacheable(cls) -> Self:
        """Mark this hash value as not cacheable."""
        return cls(cacheable=False)

    @property
    def frozen(self) -> FrozenDict:
        """Get a frozen representation of the model."""
        return self.model_dump(frozen=True)

    def frozen_dump(self) -> FrozenDict:
        """Dump the model to a frozen dictionary."""
        return self.model_dump(frozen=True)

    @overload
    def model_dump(self, frozen: LitTrue = True, *args, **kwargs) -> FrozenDict: ...

    @overload
    def model_dump(self, freeze: LitFalse = False, *args, **kwargs) -> dict: ...

    def model_dump(self, frozen: bool = True, *args, **kwargs) -> dict | FrozenDict:  # type: ignore[override]
        """Dump the model to a dictionary or frozen dictionary.

        Args:
            frozen (bool, optional): Whether to return a frozen dictionary. Defaults to False.
            *args: Additional positional arguments for Pydantic's model_dump.
            **kwargs: Additional keyword arguments for Pydantic's model_dump.

        Returns:
            dict | FrozenDict: The model as a dictionary or frozen dictionary.
        """
        if not frozen:
            return super().model_dump(*args, **kwargs)
        return freeze(super().model_dump(*args, **kwargs))


class BaseNotCacheable(BaseModel):
    """A singleton representing a non-cacheable value."""

    _instance: ClassVar[Self | None] = None

    model_config = ConfigDict(frozen=True)
    cacheable: bool = Field(default=False, exclude=True, frozen=True)

    def __new__(cls) -> Self:
        """Ensure only one instance of BaseNotCacheable exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            super(BaseNotCacheable, cls._instance).__init__()
        return cls._instance

    def __init__(self) -> None:
        """Cannot reinitialize the singleton."""

    def __hash__(self) -> int:
        raise TypeError("This object is not cacheable")


class BaseHashValue(FrozenModel):
    """A simple frozen model to hold a hash value for query caching."""

    value: list[Any] | None = None

    def combine(self, other: BaseHashValue, **kwargs) -> BaseHashValue:
        """Combine multiple hash values into one."""
        return BaseHashValue(value=[self, other], **kwargs)

    def __hash__(self) -> int:
        if not self.cacheable:
            raise TypeError("This HashValue is not cacheable")
        return super().__hash__()


class NotCacheable(BaseHashValue, BaseNotCacheable):
    """A singleton representing a non-cacheable hash value, contains a frozen cacheable=False flag."""

    def __init__(self) -> None:
        """Cannot reinitialize the singleton."""

    def __hash__(self) -> int:
        raise TypeError("This HashValue is not cacheable")


# ruff: noqa: ARG002
