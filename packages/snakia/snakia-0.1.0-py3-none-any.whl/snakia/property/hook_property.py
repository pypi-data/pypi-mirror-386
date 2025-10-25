from typing import Any, Callable, cast

from snakia.types import empty


class HookProperty[T]:

    def __init__(
        self,
        name: str,
        on_set: Callable[[T], None] = empty.func,
        on_get: Callable[[T], None] = empty.func,
        on_del: Callable[[T], None] = empty.func,
    ) -> None:
        self.__name = name
        self.on_set: Callable[[T], None] = on_set
        self.on_get: Callable[[T], None] = on_get
        self.on_del: Callable[[T], None] = on_del

    def __get__(self, instance: Any, owner: type | None = None, /) -> T:
        value = cast(T, getattr(instance, self.__get_name(instance)))
        self.on_get(value)
        return value

    def __set__(self, instance: Any, value: T, /) -> None:
        self.on_set(value)
        setattr(instance, self.__get_name(instance), value)

    def __delete__(self, instance: Any, /) -> None:
        value = cast(T, getattr(instance, self.__get_name(instance)))
        self.on_del(value)
        delattr(instance, self.__get_name(instance))

    def __get_name(
        self,
        instance: Any,
    ) -> str:
        return f"_{id(instance)}__{self.__name}"
