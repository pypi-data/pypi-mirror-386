"""Functions that operate on functions, this is considered experimental."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import LazyLoader

from bear_dereth.data_structs.const import Const

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    import inspect

    from bear_dereth.typing_tools import LitFalse, LitTrue
else:
    inspect = LazyLoader("inspect")


def const[T](value: T) -> Const[T]:
    """Create a constant function that always returns the given value.

    Use this when you just need the value to be returned by a function, but
    don't care about the arguments. If you want to have more control over
    the arguments, use the `Const` class directly.

    Args:
        value (Any): The value to be returned by the constant function.

    Returns:
        Callable[..., Any]: A function that takes any arguments and returns the specified value.
    """
    return Const[T](value)


def identity[T](x: T) -> T:
    """Return the input value unchanged.

    Args:
        x (T): The input value.

    Returns:
        T: The same input value.
    """
    return x


def compose(*funcs: Callable) -> Callable:
    """Compose multiple functions into a single function.

    Args:
        *funcs (Callable): Functions to compose. The functions are applied
            from right to left.

    Returns:
        Callable: A new function that is the composition of the input functions.
    """
    if not funcs:
        return identity

    def composed(x: Any) -> Any:
        """Apply the composed functions to the input value."""
        for f in reversed(funcs):
            x = f(x)
        return x

    return composed


def pipe(value: Any, *funcs: Callable) -> Any:
    """Pipe a value through a series of functions.

    Args:
        value (Any): The initial value to be processed.
        *funcs (Callable): Functions to apply to the value in sequence.

    Returns:
        Any: The final result after applying all functions.
    """
    for func in funcs:
        value = func(value)
    return value


def complement(f: Callable[[Any], bool]) -> Callable[[Any], bool]:
    """Return the complement of a predicate function.

    Args:
        f (Callable[[Any], bool]): A predicate function that returns a boolean value.

    Returns:
        Callable[[Any], bool]: A new function that returns the opposite boolean value of the input function.
    """

    def complemented(*args: Any, **kwargs: Any) -> bool:
        return not f(*args, **kwargs)

    return complemented


def has_attrs(seq: object, attrs: Sequence[str], true_only: bool = False) -> dict[str, bool]:
    """Check if an object has all specified attributes.

    Args:
        obj (Any): The object to check.
        attrs (list[str]): A list of attribute names to check for.

    Returns:
        dict[str, bool]: A dictionary mapping each attribute name to a boolean indicating its presence.
    """
    out: dict[str, bool] = {attr: hasattr(seq, attr) for attr in attrs}
    if true_only:
        out = {k: v for k, v in out.items() if v}
    return out


def if_in_list(item: Any, lst: list | tuple) -> bool:
    """Check if an item is in a collection (list, tuple, or set).

    Args:
        item: The item to check for.
        lst: The collection to check within.

    Returns:
        bool: True if the item is in the collection, False otherwise.
    """
    return item in lst


def if_is_instance(item: Any, types: type | tuple[type, ...]) -> bool:
    """Check if an item is an instance of a given type or types.

    Args:
        item: The item to check.
        types: The type or tuple of types to check against.

    Returns:
        bool: True if the item is an instance of the given type(s), False otherwise.
    """
    return isinstance(item, types)


def always_true(*_, **__) -> LitTrue:
    """A function that always returns True."""
    return True


def always_false(*_, **__) -> LitFalse:
    """A function that always returns False."""
    return False


def get_instance(obj: type | Any) -> Any | None:
    """Get an instance of a class or return the object itself if it's not a class.

    Args:
        service (Any): The service class or instance.
    """
    try:
        if inspect.isclass(obj):
            return obj()
        return obj
    except Exception:
        return None
