"""A Simple Stack implementation."""

from __future__ import annotations

from typing import Any

from bear_dereth.data_structs.cursor import BaseCursor
from bear_dereth.data_structs.stacks.simple import SimpleStack
from bear_dereth.operations.iterstuffs import dupes


class CursorMeta(type):
    """A metaclass for SimpleStackCursor to hold class-level attributes."""

    COLLECTION_ATTRS: tuple = (
        "__len__",
        "__bool__",
        "__iter__",
        "__contains__",
        "__getitem__",
        "__setitem__",
        "__slice__",
        "copy",
        "remove",
        "has",
        "join",
    )
    HANDLER_ATTRS: tuple = (
        "index",
        "head",
        "tick",
        "tock",
        "tail",
        "offset",
        "peek",
        "get",
        "current",
        "push",
        "pop",
        "reset",
        "size",
        "is_empty",
        "not_empty",
        "clear",
        "_update",
    )

    @property
    def duplicates(cls) -> list[str]:
        """Return a list of duplicate attributes in COLLECTION_ATTRS and HANDLER_ATTRS."""
        return list(dupes(cls.COLLECTION_ATTRS, cls.HANDLER_ATTRS))

    @property
    def fields(cls) -> dict[str, list[str]]:
        """Return a dictionary of what attribute it calls and the source of that attribute."""
        attrs: dict[str, list[str]] = {"collection": [], "handler": []}
        for attr in cls.COLLECTION_ATTRS:
            attrs["collection"].append(attr)
        for attr in cls.HANDLER_ATTRS:
            attrs["handler"].append(attr)
        return attrs


class SimpleStackCursor[T](metaclass=CursorMeta):
    """A simple stack implementation with a cursor."""

    META_ATTRS: tuple = ("COLLECTION_ATTRS", "HANDLER_ATTRS", "fields", "duplicates")

    def __init__[C: SimpleStack](self, data: T | None = None, handler: type[C] = SimpleStack) -> None:
        """Initialize an empty stack."""
        if duplicates := self.duplicates:
            raise ValueError(f"Duplicate attributes found in COLLECTION_ATTRS and HANDLER_ATTRS: {duplicates}")
        self.handler: BaseCursor[SimpleStack[T], T] = BaseCursor(handler, None)
        for item in (data,) if data is not None else ():
            self.push(item)

    def __getattr__(self, name: str) -> Any:
        if name in self.META_ATTRS:
            return getattr(self.__class__, name)
        if name == "stack":
            return self.handler.collection
        if name in self.COLLECTION_ATTRS:
            return getattr(self.handler.collection, name)
        if name in self.HANDLER_ATTRS:
            return getattr(self.handler, name)
        raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")


if __name__ == "__main__":
    # iterate through SimpleStackCursor and verify all attrs are present
    ssc: SimpleStackCursor[int] = SimpleStackCursor[int]()
    for attr in ssc.fields.values():
        for a in attr:
            assert hasattr(ssc, a), f"Missing attribute {a} in SimpleStackCursor"  # noqa: S101
    print("All attributes are present in SimpleStackCursor")
