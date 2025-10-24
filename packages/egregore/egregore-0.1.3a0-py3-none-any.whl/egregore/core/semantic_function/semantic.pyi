"""Type stubs for semantic function decorator.

This stub file tells type checkers that @semantic replaces function implementations.
Decorated functions don't need a body - the decorator provides the implementation.

When users write:
    @semantic
    def my_func(x: str) -> str:
        '''Template: {{x}}'''

Type checkers will NOT complain about missing return statements because this
stub declares the decorator returns a fully-implemented callable.
"""

from typing import Any, Callable, TypeVar, overload, Generic, ParamSpec
from egregore.core.semantic_function.errors import HandlerResult
from egregore.core.workflow.nodes import Node

T = TypeVar('T')
P = ParamSpec('P')

class SemanticFunction(Node, Generic[T]):
    """LLM-powered semantic function."""
    name: str
    config: dict[str, Any]
    prompt_template: str
    return_type: type
    param_names: list[str]
    use_schema_override: bool
    error_handlers: dict[type[Exception], Callable[..., HandlerResult]]
    func: Callable[..., T]

    def __init__(self, func: Callable[..., T], config: dict[str, Any]) -> None: ...
    def __call__(self, *args: Any, **kwargs: Any) -> T: ...
    def execute(self, *args: Any, **kwargs: Any) -> T: ...
    def on_error(self, exceptions: type[Exception] | list[type[Exception]]) -> Callable[[Callable[..., HandlerResult]], Callable[..., HandlerResult]]: ...
    def alias(self, name: str) -> SemanticFunction[T]: ...
    @property
    def label(self) -> str: ...
    @label.setter
    def label(self, value: str) -> None: ...

class SemanticFunctionDecorator:
    """Global semantic function decorator.

    When applied to a function, this decorator:
    1. Extracts the docstring as a prompt template
    2. Parses the return type annotation
    3. Returns a callable that makes LLM calls with the template

    The stub signature tells type checkers that the returned callable is
    fully implemented, so they won't check the original function body.
    """
    _config: dict[str, Any]

    def config(self, **kwargs: Any) -> SemanticFunctionDecorator: ...

    # Direct decoration: @semantic
    # Returns a SemanticFunction which is callable - the original function body is replaced
    @overload
    def __call__(self, func: Callable[P, T], /) -> SemanticFunction[T]: ...

    # Parameterized decoration: @semantic(...)
    @overload
    def __call__(self, **override_kwargs: Any) -> Callable[[Callable[P, T]], SemanticFunction[T]]: ...

semantic: SemanticFunctionDecorator
