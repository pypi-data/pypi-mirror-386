from __future__ import annotations

import inspect
from logging import getLogger
from typing import TYPE_CHECKING, ClassVar

from wrapt.decorators import decorator

if TYPE_CHECKING:
    from collections.abc import Callable

logger = getLogger("astrbot.injector")


class AstrbotInjector:
    """Astrbot依赖注入器..

    推荐用法:@AstrbotInjector.inject 或 @AstrbotInjector().inject
    支持全局依赖注入和局部依赖注入,类型安全

    例子:
        # 全局
        @AstrbotInjector.inject
        def my_function(db, config):
            ...

        AstrbotInjector.set("db", my_database_instance)
        my_function()  # 自动注入

        # 局部
        injector = AstrbotInjector()
        @injector.inject
        def my_function(db, config):
            ...
    """

    global_dependencies: ClassVar[dict[str, object]] = {}
    local_injector: ClassVar[dict[str, AstrbotInjector]] = {}

    def __init__(self, name: str = "") -> None:
        """初始化注入器."""
        self.name: str = name
        self.local_dependencies: dict[str, object] = {}
        self.dependencies: dict[str, object] = self.local_dependencies
        self.inject = self._inject_local
        self.set = self._set_local
        self.get = self._get_local
        self.remove = self._remove_local

    @classmethod
    def inject(cls, wrapped: object) -> object:
        """装饰器 (使用全局依赖)。"""
        dependencies = cls.global_dependencies

        if inspect.isclass(wrapped):
            for name, _value in list(wrapped.__dict__.items()):
                if name.startswith("__"):
                    continue
                if getattr(wrapped, name, None) is None and name in dependencies:
                    setattr(wrapped, name, dependencies[name])
            return wrapped

        @decorator
        def wrapper(
            wrapped_func: Callable[..., object],
            _instance: object,
            args: tuple[object, ...],
            kwargs: dict[str, object],
        ) -> object:
            sig = inspect.signature(wrapped_func)
            bound = sig.bind_partial(*args, **kwargs)
            for param in sig.parameters.values():
                if (
                    param.name not in bound.arguments
                    and param.name in dependencies
                    and param.default is inspect.Parameter.empty
                ):
                    kwargs[param.name] = dependencies[param.name]
            return wrapped_func(*args, **kwargs)

        return wrapper(wrapped)

    def _inject_local(self, wrapped: object) -> object:
        """装饰器 (使用实例依赖)。"""
        dependencies = self.dependencies

        if inspect.isclass(wrapped):
            for name, _value in list(wrapped.__dict__.items()):
                if name.startswith("__"):
                    continue
                if getattr(wrapped, name, None) is None and name in dependencies:
                    setattr(wrapped, name, dependencies[name])
            return wrapped

        @decorator
        def wrapper(
            wrapped_func: Callable[..., object],
            _instance: object,
            args: tuple[object, ...],
            kwargs: dict[str, object],
        ) -> object:
            sig = inspect.signature(wrapped_func)
            bound = sig.bind_partial(*args, **kwargs)
            for param in sig.parameters.values():
                if (
                    param.name not in bound.arguments
                    and param.name in dependencies
                    and param.default is inspect.Parameter.empty
                ):
                    kwargs[param.name] = dependencies[param.name]
            return wrapped_func(*args, **kwargs)

        return wrapper(wrapped)

    @classmethod
    def set(cls, name: str, value: object) -> None:
        cls.global_dependencies[name] = value

    @classmethod
    def get(cls, name: str) -> object | None:
        return cls.global_dependencies.get(name)

    @classmethod
    def remove(cls, name: str) -> None:
        _ = cls.global_dependencies.pop(name, None)

    def _set_local(self, name: str, value: object) -> None:
        self.local_dependencies[name] = value

    def _get_local(self, name: str) -> object | None:
        return self.local_dependencies.get(name)

    def _remove_local(self, name: str) -> None:
        _ = self.local_dependencies.pop(name, None)

    @classmethod
    def getInjector(cls, injector_name: str) -> AstrbotInjector:
        if injector_name not in cls.local_injector:
            cls.local_injector[injector_name] = AstrbotInjector(injector_name)
        return cls.local_injector[injector_name]
