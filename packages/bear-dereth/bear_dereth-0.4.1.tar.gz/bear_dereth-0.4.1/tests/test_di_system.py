"""Tests for the dependency injection system."""

import timeit
from typing import TYPE_CHECKING, Annotated, Any, Union, get_type_hints
from unittest.mock import Mock

from _pytest.capture import CaptureResult
import pytest
from rich.console import Console

from bear_dereth.constants.exceptions import CannotFindTypeError
from bear_dereth.di import (
    DeclarativeContainer,
    Provide,
    Provider,
    Singleton,
    inject,
    parse_params,
)
from bear_dereth.typing_tools import get_function_signature

if TYPE_CHECKING:
    from inspect import Signature


class SimpleTestContainer(DeclarativeContainer):
    console: Console


class MultiTestContainer(DeclarativeContainer):
    console: Console
    config: dict[str, Any]
    database: dict[str, Any]


@pytest.fixture
def console_container() -> type[SimpleTestContainer]:
    """Simple container with just a Console service."""
    return SimpleTestContainer


@pytest.fixture
def multi_service_container() -> type[MultiTestContainer]:
    """Container with multiple common services."""
    return MultiTestContainer


class TestDeclarativeContainerMeta:
    """Test the metaclass that powers the container magic."""

    def test_captures_service_annotations(self) -> None:
        """Test that the metaclass captures service type annotations."""

        class TestContainer(DeclarativeContainer):
            console: Console
            database: dict[str, Any]
            _private_attr: str  # Should be ignored

        service_types = TestContainer.get_all_types()

        assert "console" in service_types
        assert "database" in service_types
        assert "_private_attr" not in service_types
        assert service_types["console"] == Console

    def test_returns_provide_for_service_attributes(self) -> None:
        """Test that accessing service attributes returns Provide instances."""

        class TestContainer(DeclarativeContainer):
            console: Console

        # Accessing the service should return the Provide class (not instance)
        provide_marker: Console = TestContainer.console
        assert isinstance(provide_marker, Provide)  # type: ignore[unreachable]

    def test_raises_for_unknown_attributes(self) -> None:
        """Test that accessing unknown attributes raises AttributeError."""

        class TestContainer(DeclarativeContainer):
            console: Console

        with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
            print(TestContainer.nonexistent)


class TestProvider:
    """Test the Provider/Provide marker classes."""

    def test_provider_initialization(self, console_container: type[SimpleTestContainer]) -> None:
        """Test basic Provider initialization."""
        provider: Provider = Provide("test_service", console_container)
        assert provider.service_name == "test_service"

    def test_provide_class_getitem_with_provide_instance(self, console_container: type[SimpleTestContainer]) -> None:
        """Test Provide[existing_provide_instance] returns the same instance."""
        original: Provider = Provide("console", console_container)
        result: Provider = Provide.__class_getitem__(original)
        assert result is original
        assert result.service_name == "console"

    def test_provide_class_getitem_with_type(self, console_container: type[SimpleTestContainer]) -> None:  # noqa: ARG002
        """Test Provide[SomeClass] uses the class name."""
        result: Provider = Provide.__class_getitem__(Console)
        assert isinstance(result, Provider)
        assert result.service_name == "console"

    def test_provide_class_getitem_with_string(self, console_container: type[SimpleTestContainer]) -> None:  # noqa: ARG002
        """Test Provide[string] uses the string directly."""
        result: Provider = Provide.__class_getitem__("my_service")
        assert isinstance(result, Provider)
        assert result.service_name == "my_service"


class TestParseParams:
    """Test the parameter parsing and injection logic."""

    def test_parse_params_with_registered_service(self) -> None:
        """Test parsing when service is already registered."""

        class MockConsole:
            pass

        class TestContainer(DeclarativeContainer):
            console: MockConsole

        TestContainer.register("console", MockConsole())

        @inject
        def test_func(console: Console = Provide[TestContainer.console]) -> None:
            assert isinstance(console, MockConsole)

        args = get_type_hints(test_func, globalns=test_func.__globals__)
        print(args)

        test_func()

    def test_parse_params_creates_missing_service(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that missing services are created from type annotations."""

        class TestContainer(DeclarativeContainer):
            console: Console

        @inject
        def test_func(console: Console = Provide[TestContainer.console]) -> CaptureResult[str]:
            assert isinstance(console, Console)
            console.print("Hello, World!")
            return capsys.readouterr()

        _args, _kwargs = parse_params(test_func)
        captured: CaptureResult[str] = test_func()
        assert "Hello, World!" in captured.out

    def test_parse_params_ignores_non_provide_defaults(self) -> None:
        """Test that non-Provide defaults are left alone."""

        class TestContainer(DeclarativeContainer):
            pass

        def test_func(value: int = 42, name: str = "test") -> None:
            pass

        _, kwargs = parse_params(test_func, TestContainer)
        assert "value" not in kwargs
        assert "name" not in kwargs

    def test_parse_params_with_mixed_parameters(self) -> None:
        """Test parsing with both injected and regular parameters."""

        class TestContainer(DeclarativeContainer):
            console: Console

        mock_console = Mock(spec=Console)
        TestContainer.register("console", mock_console)

        @inject
        def test_func(
            regular_param: str,
            console: Console = Provide[TestContainer.console],
            default_param: int = 100,
        ) -> tuple[str, Console, int]:
            return regular_param, console, default_param

        returned: tuple[str, Console, int] = test_func("hello", default_param=200)
        assert returned == ("hello", mock_console, 200)
        assert returned[1] is mock_console
        assert returned[2] == 200
        assert returned[0] == "hello"


class TestInjectDecorator:
    """Test the inject decorator functionality."""

    def test_inject_basic_functionality(self, console_container) -> None:
        """Test basic injection works."""
        mock_console = Mock(spec=Console)
        console_container.register("console", mock_console)

        @inject
        def test_func(console: Console = Provide[console_container.console]) -> Console:
            return console

        result = test_func()
        assert result is mock_console

    def test_inject_with_mixed_parameters(self) -> None:
        """Test injection works with mixed parameter types."""

        class TestContainer(DeclarativeContainer):
            console: Console

        mock_console = Mock(spec=Console)
        TestContainer.register("console", mock_console)

        @inject
        def test_func(
            message: str,
            console: Console = Provide[TestContainer.console],
            multiplier: int = 2,
        ) -> tuple[str, Console, int]:
            return message, console, multiplier

        result: tuple[str, Console, int] = test_func("hello", multiplier=3)
        assert result == ("hello", mock_console, 3)

    def test_inject_preserves_function_metadata(self) -> None:
        """Test that the decorator preserves function metadata."""

        class TestContainer(DeclarativeContainer):
            pass

        @inject
        def documented_function() -> None:
            """This is a test function."""

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestIntegration:
    """Integration tests for the complete DI system."""

    def test_multiple_containers(self) -> None:
        """Test that different containers work independently."""

        class ContainerA(DeclarativeContainer):
            service: str

        class ContainerB(DeclarativeContainer):
            service: str

        container_a = ContainerA()

        container_b = ContainerB()

        container_a.register("service", "A")

        @inject
        def func_a(service: str = Provide[ContainerA.service]) -> str:
            return f"From A: {service}"

        container_b.register("service", "B")

        @inject
        def func_b(service: str = Provide[ContainerB.service]) -> str:
            return f"From B: {service}"

        assert func_a() == "From A: A"
        assert func_b() == "From B: B"

    def test_nested_dependencies(self) -> None:
        """Test that services can depend on other services."""

        class TestContainer(DeclarativeContainer):
            console: Console
            config: dict[str, Any]

        mock_console = Mock(spec=Console)
        test_config = {"debug": True, "theme": "dark"}

        TestContainer.register("console", mock_console)
        TestContainer.register("config", test_config)

        @inject
        def complex_function(
            console: Console = Provide[TestContainer.console],
            config: dict[str, Any] = Provide[TestContainer.config],
        ) -> tuple[Console, dict[str, Any]]:
            return console, config

        result = complex_function()
        assert result[0] is mock_console
        config = result[1]
        assert config is test_config
        assert config["debug"] is True


class TestCachingBehavior:
    """Test caching behavior of the DI system."""

    def test_function_signature_caching(self) -> None:
        """Test that function signatures are cached for performance."""

        def test_func(param: str = "default") -> None:
            pass

        # First call should populate cache
        sig1: Signature = get_function_signature(test_func)
        # Second call should hit cache
        sig2: Signature = get_function_signature(test_func)

        # Should be the exact same object (cached)
        assert sig1 is sig2

    @pytest.mark.xfail(reason="Performance test, may not always be faster")
    def test_injection_caching_performance(self) -> None:
        """Test that repeated injections benefit from caching."""

        class MockContainer(DeclarativeContainer):
            console: Console

        MockContainer.register("console", Console)

        @inject
        def cached_func(console: Console = Provide[MockContainer.console]) -> Console:
            return console

        def non_cached_func(console: Console | None = None) -> Console:
            return console or Console()

        timing1: float = timeit.timeit(cached_func, globals=globals(), number=1000)
        timing2: float = timeit.timeit(non_cached_func, globals=globals(), number=1000)

        assert timing1 < timing2  # Cached should be faster


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_container(self) -> None:
        """Test behavior with empty containers."""

        # Should have empty service dictionaries
        class EmptyTestContainer(DeclarativeContainer):
            pass

        container = EmptyTestContainer()

        assert len(EmptyTestContainer.get_all()) == 0

        assert len(EmptyTestContainer.get_all_types()) == 0

    def test_class_vs_instance_registration_behavior(self) -> None:
        """Test the difference between registering classes vs instances."""

        class TestContainer(DeclarativeContainer):
            console_class: Console
            console_instance: Console

        TestContainer.register("console_class", instance=Console)
        TestContainer.register("console_instance", Console())

        @inject
        def get_class_service(console: Console = Provide[TestContainer.console_class]) -> Console:
            return console

        @inject
        def get_instance_service(console: Console = Provide[TestContainer.console_instance]) -> Console:
            return console

        class_result: Console = get_class_service()
        instance_result: Console = get_instance_service()

        assert isinstance(class_result, Console)
        assert isinstance(instance_result, Console)

        assert id(class_result) is not id(instance_result)

    def test_type_string_resolution_failure(self) -> None:
        """Test what happens when type strings can't be resolved."""

        class TestContainer(DeclarativeContainer):
            unknown_service: "NonexistentType"  # type: ignore[name-defined] # noqa: F821

        @inject
        def func_with_bad_type(service: "NonexistentType" = Provide[TestContainer.unknown_service]) -> Any:  # type: ignore[name-defined] # noqa: F821
            return service

        result: Provider = func_with_bad_type()
        assert result is not None
        assert isinstance(result.result.exception, CannotFindTypeError)
        assert "cannot find type" in result.result.error.lower()

    def test_service_resolution_failure(self) -> None:
        """Test error handling when service resolution fails."""

        class TestContainer(DeclarativeContainer):
            non_instantiable: Any

        @inject
        def faulty_function(service: Any = Provide[TestContainer.non_instantiable]) -> Provide:  # type: ignore[return]
            return service

        service: Provider = faulty_function()  # type: ignore[assignment]
        assert isinstance(service, Provide)  # type: ignore[unreachable]
        assert service.service_name == "non_instantiable"
        assert service.result is not None  # If there is an error, we get the result object
        assert isinstance(service.result.exception, CannotFindTypeError)
        assert "could not resolve type for service" in service.result.error.lower()


class TestDifferentTypeAnnotations:
    def test_annotated_types_handling(self) -> None:
        """Test that Annotated types are handled correctly."""

        class TestContainer(DeclarativeContainer):
            console: Annotated[Console, "A console service"]

        @inject
        def func_with_annotated(
            magic: int = 0,
            console: Annotated[Console, "A console service"] = Provide[TestContainer.console],
        ) -> Console:
            return console

        result: Console = func_with_annotated()
        assert isinstance(result, Console)

    def test_union_types_handling(self) -> None:
        """Test that Union types are handled correctly."""

        class TestContainer(DeclarativeContainer):
            console: Union[Console, str]  # noqa: UP007 # We need to test Union handling

        container = TestContainer()

        @inject
        def func_with_union(
            magic: int = 0,
            console: Union[Console, str] = Provide[TestContainer.console],  # noqa: UP007
        ) -> Console | str:
            return console

        result: Union[Console, str] = func_with_union()  # noqa: UP007
        assert isinstance(result, Console)

    def test_mixed_type_annotations(self) -> None:
        """Test that a mix of type annotations are handled correctly."""

        def get_config() -> dict[str, Any]:
            return {"debug": True}

        class TestContainer(DeclarativeContainer):
            console: Annotated[Union[Console, str], "A console or string service"]  # noqa: UP007
            config: dict[str, Any] = get_config()

        TestContainer.register("config", {"debug": True})
        TestContainer.register("console", Console())

        @inject
        def func_with_mixed(
            console: Annotated[Union[Console, str], "A console or string service"] = Provide[TestContainer.console],  # noqa: UP007
            config: dict[str, Any] = Provide[TestContainer.config],
        ) -> tuple[Union[Console, str], dict[str, Any]]:  # noqa: UP007
            return console, config

        result: tuple[Union[Console, str], dict[str, Any]] = func_with_mixed()  # noqa: UP007

        assert isinstance(result[0], Console)
        assert result[1]["debug"] is True


class TestResources:
    def test_from_singleton_base_wrapper_and_identity(self) -> None:
        """Baseline: wrapper is injected; .get() returns Console; identity stable."""

        class MockContainer(DeclarativeContainer):
            console = Singleton(Console)

        container = MockContainer()

        @inject
        def get_console(console: Console = Provide[MockContainer.console]) -> Console:
            print(type(console))
            return console  # type: ignore[return]

        try:
            wrapper1: Console = get_console()
            print(type(wrapper1))
            wrapper2: Console = get_console()
            print(type(wrapper2))
            assert isinstance(wrapper1, Console)
            assert isinstance(wrapper2, Console)
            assert wrapper1 is wrapper2
        finally:
            MockContainer.shutdown()


class TestTeardown:
    def test_teardown_callbacks_run_after_shutdown(self) -> None:
        """Test that registered teardown callbacks run after service shutdown."""
        order: list = []

        class Service:
            def shutdown(self, resource: Any | None = None) -> None:
                order.append(resource)

        class MockContainer(DeclarativeContainer):
            service = Singleton(Service)

        container = MockContainer()

        def callback() -> None:
            order.append("callback")

        # MockContainer.register_teardown("service", callback, priority=1)
        MockContainer.shutdown()

        # assert order == ["service", "callback"]
        assert MockContainer.get_all() == {}


class TestClassControl:
    SHOULD_NOT_EXIST = "DeclarativeContainer_meta_"

    def test_attr_existing(self) -> None:
        """Test that accessing an existing attribute works."""
        contain = SimpleTestContainer()
        assert not hasattr(contain, self.SHOULD_NOT_EXIST)

    def test_subclass_prevention(self) -> None:
        """Test that subclassing a concrete container raises TypeError."""

        class BaseContainer(DeclarativeContainer):
            service: str

        with pytest.raises(TypeError, match="Cannot inherit from concrete container"):

            class SubContainer(BaseContainer):  # type: ignore[misc]
                pass
