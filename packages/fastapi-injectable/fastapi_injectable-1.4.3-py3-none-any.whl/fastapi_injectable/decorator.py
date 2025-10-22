import inspect
import types
from collections.abc import AsyncGenerator, Awaitable, Callable, Coroutine, Generator
from functools import wraps
from typing import TYPE_CHECKING, Annotated, Any, ParamSpec, TypeVar, Union, cast, get_args, get_origin, overload

import fastapi
import fastapi.params

from .concurrency import run_coroutine_sync
from .main import resolve_dependencies

T = TypeVar("T")
P = ParamSpec("P")

if TYPE_CHECKING:

    def set_original_func(wrapper: Any, target: Any) -> None:  # noqa: ANN401
        pass
else:

    def set_original_func(wrapper: Any, target: Any) -> None:  # noqa: ANN401
        wrapper.__original_func__ = target


def _override_func_dependency_signature(func: Callable[P, T] | Callable[P, Awaitable[T]]) -> None:  # pragma: no cover
    """Override the function signature to make dependency-injected parameters optional."""
    signature = inspect.signature(func)
    new_parameters = []
    for param in signature.parameters.values():
        using_annotated_and_default_is_empty = (
            get_origin(param.annotation) is Annotated
            and param.annotation.__metadata__
            and param.default is inspect.Parameter.empty
        )
        parameter = param
        if using_annotated_and_default_is_empty:
            fastapi_default = None
            for metadata in param.annotation.__metadata__:
                if type(metadata) is fastapi.params.Depends:
                    fastapi_default = metadata
                    break
            if fastapi_default:
                actual_type = get_args(param.annotation)[0]
                origin = get_origin(actual_type)

                base_for_class = actual_type
                if origin is Union or origin is types.UnionType:
                    union_args = get_args(actual_type)
                    base_for_class = next(
                        (t for t in union_args if t is not type(None)),
                        union_args[0] if union_args else object,
                    )

                base_class = get_origin(base_for_class) or base_for_class

                dynamic_default = types.new_class(
                    "Injected_" + getattr(base_class, "__name__", "Injected"),
                    (base_class,),
                    {},
                    lambda ns: ns.update(
                        {
                            "__init__": lambda self, *args, **kwargs: None,  # noqa: ARG005
                            **{
                                method: lambda *args, **kwargs: None  # noqa: ARG005
                                for method in getattr(base_class, "__abstractmethods__", [])  # noqa: B023
                            },
                        }
                    ),
                )
                parameter = inspect.Parameter.replace(param, default=dynamic_default())
        new_parameters.append(parameter)
    func.__signature__ = signature.replace(parameters=new_parameters)  # type: ignore[union-attr]


@overload
def injectable(
    func: Callable[P, Generator[T, Any, Any]],
    *,
    use_cache: bool = True,
) -> Callable[P, Generator[T, Any, Any]]: ...


@overload
def injectable(
    func: Callable[P, AsyncGenerator[T, Any]],
    *,
    use_cache: bool = True,
) -> Callable[P, AsyncGenerator[T, Any]]: ...


@overload
def injectable(
    func: Callable[P, T],
    *,
    use_cache: bool = True,
) -> Callable[P, T]: ...


@overload
def injectable(
    *,
    use_cache: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


# overloads above provide actual type-hints
# Callable[..., Any] is just a place holder
def injectable(
    func: Callable[..., Any] | None = None,
    *,
    use_cache: bool = True,
) -> Callable[..., Any]:
    """Decorator to inject dependencies into any callable, sync or async."""

    def decorator(
        target: Callable[P, T] | Callable[P, Awaitable[T]] | Callable[P, AsyncGenerator[T, Any]],
    ) -> Callable[P, T] | Callable[P, Awaitable[T]] | Callable[P, AsyncGenerator[T, Any]]:
        # Override the function signature to make dependency-injected parameters optional for packages like typer, cyclopt, etc.  # noqa: E501
        _override_func_dependency_signature(target)

        # Note, these are mutually exclusive
        is_async = inspect.iscoroutinefunction(target)
        is_async_generator = inspect.isasyncgenfunction(target)

        @wraps(target)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            dependencies = await resolve_dependencies(func=target, use_cache=use_cache, provided_kwargs=kwargs)
            return await cast("Callable[..., Coroutine[Any, Any, T]]", target)(*args, **{**dependencies, **kwargs})

        @wraps(target)
        async def async_gen_wrapper(*args: P.args, **kwargs: P.kwargs) -> AsyncGenerator[T, Any]:
            dependencies = await resolve_dependencies(func=target, use_cache=use_cache, provided_kwargs=kwargs)
            async for x in cast("Callable[..., AsyncGenerator[T, Any]]", target)(*args, **{**dependencies, **kwargs}):
                yield x

        @wraps(target)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            dependencies = run_coroutine_sync(
                resolve_dependencies(func=target, use_cache=use_cache, provided_kwargs=kwargs)
            )
            return cast("Callable[..., T]", target)(*args, **{**dependencies, **kwargs})

        if is_async_generator:
            set_original_func(async_gen_wrapper, target)
            return async_gen_wrapper

        if is_async:
            set_original_func(async_wrapper, target)
            return async_wrapper

        set_original_func(sync_wrapper, target)
        return sync_wrapper

    if func is None:
        return decorator

    decorated_func = decorator(func)
    set_original_func(decorated_func, func)
    return decorated_func
